from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import secrets
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import httpx

from adapta.models import Settings

SEARCH_LIMIT_ERROR = "[ERR:661]"


logger = logging.getLogger(__name__)

SESSION_HOME_DIRNAME = ".adapta"
SESSION_CACHE_FILENAME = "cookies.json"

AGENT_BASE_URL = "https://agent.adapta.one"
API_AGENT_BASE_URL = "https://api-agent.adapta.one"
CLERK_BASE_URL = "https://clerk.agent.adapta.one/v1"
CLERK_API_VERSION = "2025-11-10"
CLERK_JS_VERSION = "5.125.7"
DEFAULT_MODEL = "CLAUDE_4_5_SONNET"
LOGIN_THROTTLE_SECONDS = 2.0
TOKEN_REFRESH_THROTTLE_SECONDS = 120.0
FILE_UPLOAD_ENDPOINT = f"{API_AGENT_BASE_URL}/api/file/upload"
FILES_LIST_ENDPOINT = f"{AGENT_BASE_URL}/api/files/v2"
FILES_DELETE_ENDPOINT = f"{AGENT_BASE_URL}/api/files/delete/v1"
FOLDERS_LIST_ENDPOINT = f"{AGENT_BASE_URL}/api/folders/v2"
SKILLS_ENDPOINT = f"{AGENT_BASE_URL}/api/skills/v1"

SUPPORTED_UPLOAD_FORMATS = {
    ".txt",
    ".pdf",
    ".docx",
    ".xlsx",
    ".xls",
    ".csv",
    ".png",
    ".jpg",
    ".jpeg",
}

MIME_TYPES = {
    ".txt": "text/plain",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".csv": "text/csv",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


@dataclass
class AuthResult:
    session_id: str
    cookies: dict[str, str]


@dataclass
class ChatCompletionResult:
    messages: list[dict[str, str]]


class ToolExecutionError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        tool_name: str | None = None,
        tool_call_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.tool_name = tool_name
        self.tool_call_id = tool_call_id


class RateLimiter:
    def __init__(self, min_interval: float) -> None:
        self._min_interval = min_interval
        self._last_run = 0.0
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_run
            if elapsed < self._min_interval:
                await asyncio.sleep(self._min_interval - elapsed)
            self._last_run = time.monotonic()


def _generate_uuid7_like() -> str:
    uuid7_factory = getattr(uuid, "uuid7", None)
    if callable(uuid7_factory):
        return str(uuid7_factory())

    timestamp_ms = int(time.time() * 1000) & ((1 << 48) - 1)
    rand_a = secrets.randbits(12)
    rand_b = secrets.randbits(62)
    uuid_int = (
        (timestamp_ms << 80) | (0x7 << 76) | (rand_a << 64) | (0x2 << 62) | rand_b
    )
    return str(uuid.UUID(int=uuid_int))


def _first_non_none(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _resolve_session_cache_path(path: Path | None = None) -> Path:
    target = path or (Path.home() / SESSION_HOME_DIRNAME / SESSION_CACHE_FILENAME)
    return target.expanduser().resolve()


class AdaptaHttpSession:
    def __init__(self, *, transport: httpx.BaseTransport | None = None) -> None:
        self._transport = transport
        self._client: httpx.AsyncClient | None = None
        self._client_loop: asyncio.AbstractEventLoop | None = None
        self._auth_cookies: dict[str, str] = {}

    async def ensure_client(self) -> httpx.AsyncClient:
        current_loop = asyncio.get_running_loop()
        if self._client is not None:
            if (
                self._client.is_closed
                or self._client_loop is None
                or self._client_loop is not current_loop
            ):
                await self._client.aclose()
                self._client = None
                self._client_loop = None

        if self._client is None:
            timeout = httpx.Timeout(timeout=1200.0, connect=15.0, read=1200.0)
            headers = {
                "user-agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
                ),
                "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "origin": AGENT_BASE_URL,
            }
            self._client = httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
                headers=headers,
                transport=self._transport,
            )
            self._client_loop = current_loop
            if self._auth_cookies:
                self._client.cookies.update(self._auth_cookies)

        return self._client

    def remember_cookies(self, cookies: dict[str, str]) -> None:
        self._auth_cookies = dict(cookies)
        if self._client is not None:
            self._client.cookies.update(cookies)

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
        self._client = None
        self._client_loop = None

    async def logout(self) -> None:
        if not self._session_id:
            self._clear_session_cache()
            return

        client = await self._session.ensure_client()

        try:
            await self._touch_session(client, self._session_id)
        except httpx.HTTPError as exc:
            logger.debug("Falha ao tocar sessao antes do logout: %s", exc)

        await self._notify_logout_navigation(client)
        await self._delete_session(client)
        self._session_id = None
        self._bearer_token = None
        self._bearer_token_exp = 0.0
        self._used_production_token = False
        self._cached_cookies = {}
        self._cached_headers = {}
        self._session.remember_cookies({})
        client.cookies.clear()
        self._clear_session_cache()

    async def _notify_logout_navigation(self, client: httpx.AsyncClient) -> None:
        headers = {
            "accept": "text/x-component",
            "content-type": "text/plain;charset=UTF-8",
            "origin": AGENT_BASE_URL,
            "referer": f"{AGENT_BASE_URL}/agentic-chat",
        }
        try:
            await client.post(
                f"{AGENT_BASE_URL}/agentic-chat",
                headers=headers,
                content="[]",
            )
        except httpx.HTTPError as exc:
            logger.debug("Falha ao notificar navegação de logout: %s", exc)

    async def _delete_session(self, client: httpx.AsyncClient) -> None:
        params = {
            "__clerk_api_version": CLERK_API_VERSION,
            "_clerk_js_version": CLERK_JS_VERSION,
            "_method": "DELETE",
        }
        headers = {
            "accept": "*/*",
            "content-type": "application/x-www-form-urlencoded",
            "origin": AGENT_BASE_URL,
            "referer": f"{AGENT_BASE_URL}/",
        }
        try:
            await client.post(
                f"{CLERK_BASE_URL}/client/sessions",
                params=params,
                headers=headers,
            )
        except httpx.HTTPError as exc:
            logger.debug("Falha ao encerrar sessão: %s", exc)


class AdaptaAuthenticator:
    def __init__(
        self,
        *,
        session: AdaptaHttpSession,
        login: str,
        password: str,
        session_cache_path: Path | None = None,
    ) -> None:
        if not login or not password:
            raise ValueError("ADAPTA_LOGIN e ADAPTA_PASSWORD são obrigatórios.")

        self._session = session
        self._login = login
        self._password = password
        self._session_id: str | None = None
        self._bearer_token: str | None = None
        self._bearer_token_exp = 0.0
        self._used_production_token = False
        self._auth_lock = asyncio.Lock()
        self._login_rate_limiter = RateLimiter(LOGIN_THROTTLE_SECONDS)
        self._token_refresh_rate_limiter = RateLimiter(TOKEN_REFRESH_THROTTLE_SECONDS)
        self._session_cache_path = _resolve_session_cache_path(session_cache_path)
        self._cached_cookies: dict[str, str] = {}
        self._cached_headers: dict[str, str] = {}
        self._restore_session_cache()

    @property
    def session_id(self) -> str | None:
        return self._session_id

    def _restore_session_cache(self) -> None:
        if not self._session_cache_path:
            return
        try:
            payload_text = self._session_cache_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return
        except OSError:
            logger.warning(
                "Não foi possível ler o cache de sessão em %s",
                self._session_cache_path,
            )
            return

        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError:
            logger.warning(
                "Conteúdo inválido no cache de sessão %s", self._session_cache_path
            )
            return

        session_id = payload.get("session_id")
        cookies = payload.get("cookies")
        bearer_token = payload.get("bearer_token")
        bearer_token_exp = payload.get("bearer_token_exp")
        used_production_token = payload.get("used_production_token")
        headers = payload.get("headers")

        if isinstance(session_id, str) and session_id:
            self._session_id = session_id

        if isinstance(cookies, dict):
            normalized_cookies = {
                str(key): str(value)
                for key, value in cookies.items()
                if isinstance(key, str) and isinstance(value, str)
            }
            if normalized_cookies:
                self._cached_cookies = normalized_cookies
                self._session.remember_cookies(normalized_cookies)

        if isinstance(bearer_token, str) and bearer_token:
            self._bearer_token = bearer_token
            if isinstance(bearer_token_exp, (int, float)):
                self._bearer_token_exp = float(bearer_token_exp)
            self._used_production_token = bool(used_production_token)

        if isinstance(headers, dict):
            self._cached_headers = {
                str(key): str(value)
                for key, value in headers.items()
                if isinstance(key, str) and isinstance(value, str)
            }

    def _persist_session_state(self) -> None:
        if not self._session_cache_path or not self._session_id:
            return

        cookies = self._cached_cookies or getattr(self._session, "_auth_cookies", {})
        payload: dict[str, Any] = {
            "session_id": self._session_id,
            "cookies": dict(cookies),
        }
        if self._bearer_token:
            payload["bearer_token"] = self._bearer_token
            payload["bearer_token_exp"] = self._bearer_token_exp
            payload["used_production_token"] = self._used_production_token
        if self._cached_headers:
            payload["headers"] = self._cached_headers

        try:
            self._session_cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._session_cache_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            logger.warning(
                "Não foi possível gravar o cache de sessão em %s",
                self._session_cache_path,
            )

    def _clear_session_cache(self) -> None:
        if not self._session_cache_path:
            return
        try:
            self._session_cache_path.unlink(missing_ok=True)
        except OSError:
            logger.warning(
                "Não foi possível remover o cache de sessão em %s",
                self._session_cache_path,
            )

    async def simulate_login(self) -> AuthResult:
        await self._login_rate_limiter.wait()
        async with self._auth_lock:
            client = await self._session.ensure_client()
            await self._fetch_sign_in_page(client)
            attempt_id = await self._start_sign_in_attempt(client)
            payload = await self._attempt_password_first_factor(client, attempt_id)

            self._session_id = self._extract_session_id(payload)
            if not self._session_id:
                raise RuntimeError(
                    "Não foi possível identificar o session_id retornado pela API."
                )

            await self._touch_session(client, self._session_id, intent="select_session")

            cookies = self._collect_auth_cookies(client)
            self._session.remember_cookies(cookies)
            self._cached_cookies = dict(cookies)
            self._persist_session_state()
            return AuthResult(session_id=self._session_id, cookies=cookies)

    async def ensure_authenticated(self) -> None:
        client = await self._session.ensure_client()
        if not self._session_id:
            await self.simulate_login()
            return
        try:
            await self._touch_session(client, self._session_id)
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code if exc.response else None
            if status_code == 401:
                await self.reset_authentication(drop_cache=True)
                await self.simulate_login()
                return
            raise

    async def ensure_bearer_token(self) -> str:
        async with self._auth_lock:
            if self._bearer_token and not self._token_expired():
                return self._bearer_token

            if not self._session_id:
                raise RuntimeError("Sessão não disponível para obtenção de token.")

            client = await self._session.ensure_client()
            if not self._used_production_token:
                token = await self._fetch_production_token(client)
                self._used_production_token = True
            else:
                token = await self._refresh_session_token(client)

            self._bearer_token = token
            self._bearer_token_exp = self._extract_token_exp(token)
            self._persist_session_state()
            return token

    async def reset_authentication(self, *, drop_cache: bool) -> None:
        self._session_id = None
        self._bearer_token = None
        self._bearer_token_exp = 0.0
        self._used_production_token = False
        self._cached_cookies = {}
        self._cached_headers = {}
        await self._session.close()
        if drop_cache:
            self._clear_session_cache()

    async def close(self) -> None:
        if should_logout():
            await self.reset_authentication(drop_cache=True)

    async def _fetch_sign_in_page(self, client: httpx.AsyncClient) -> None:
        response = await client.get(
            f"{AGENT_BASE_URL}/sign-in",
            headers={
                "accept": (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
                    "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
                ),
                "referer": f"{AGENT_BASE_URL}/",
            },
        )
        response.raise_for_status()

    async def _start_sign_in_attempt(self, client: httpx.AsyncClient) -> str:
        response = await self._post_with_retry(
            client,
            f"{CLERK_BASE_URL}/client/sign_ins",
            params=self._clerk_params(),
            data={"locale": "pt-BR", "identifier": self._login},
            headers=self._form_headers(),
        )
        attempt_id = self._extract_sign_in_attempt_id(response.json())
        if not attempt_id:
            raise RuntimeError("Não foi possível obter o id da tentativa de login")
        return attempt_id

    async def _attempt_password_first_factor(
        self, client: httpx.AsyncClient, attempt_id: str
    ) -> dict[str, Any]:
        response = await self._post_with_retry(
            client,
            f"{CLERK_BASE_URL}/client/sign_ins/{attempt_id}/attempt_first_factor",
            params=self._clerk_params(),
            data={"strategy": "password", "password": self._password},
            headers=self._form_headers(),
        )
        return response.json()

    async def _touch_session(
        self, client: httpx.AsyncClient, session_id: str, *, intent: str | None = None
    ) -> None:
        data: dict[str, Any] = {"active_organization_id": ""}
        if intent is not None:
            data["intent"] = intent
        response = await self._post_with_retry(
            client,
            f"{CLERK_BASE_URL}/client/sessions/{session_id}/touch",
            params=self._clerk_params(),
            data=data,
            headers=self._form_headers(referer=f"{AGENT_BASE_URL}/"),
        )
        response.raise_for_status()

    def _collect_auth_cookies(self, client: httpx.AsyncClient) -> dict[str, str]:
        relevant: dict[str, str] = {}
        for cookie_name in (
            "__client",
            "__client_uat",
            "clerk_active_session",
            "clerk_active_context",
            "__session",
        ):
            try:
                value = client.cookies.get(cookie_name)
            except httpx.CookieConflict:
                value = next(
                    (
                        cookie.value
                        for cookie in client.cookies.jar
                        if cookie.name == cookie_name
                    ),
                    None,
                )
            if not value:
                continue
            if cookie_name == "clerk_active_context" and value.endswith(":"):
                value = value[:-1]
            relevant[cookie_name] = value
        self._cached_cookies = dict(relevant)
        return relevant

    def _clerk_params(self) -> dict[str, str]:
        return {
            "__clerk_api_version": CLERK_API_VERSION,
            "_clerk_js_version": CLERK_JS_VERSION,
        }

    def _form_headers(
        self, *, referer: str = f"{AGENT_BASE_URL}/sign-in"
    ) -> dict[str, str]:
        return {
            "accept": "*/*",
            "content-type": "application/x-www-form-urlencoded",
            "origin": AGENT_BASE_URL,
            "referer": referer,
        }

    async def _post_with_retry(
        self,
        client: httpx.AsyncClient,
        url: str,
        *,
        params: dict[str, str] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        max_attempts: int = 3,
    ) -> httpx.Response:
        attempt = 1
        while True:
            response = await client.post(url, params=params, data=data, headers=headers)
            if response.status_code != 429:
                response.raise_for_status()
                return response
            if attempt >= max_attempts:
                response.raise_for_status()
            await asyncio.sleep(self._retry_delay_from_headers(response.headers))
            attempt += 1

    def _retry_delay_from_headers(self, headers: httpx.Headers) -> float:
        raw_retry = headers.get("Retry-After")
        if raw_retry:
            raw_retry = raw_retry.strip()
            if raw_retry.isdigit():
                delay = float(raw_retry)
                if delay > 0:
                    return delay
            else:
                try:
                    retry_dt = parsedate_to_datetime(raw_retry)
                except (TypeError, ValueError):
                    retry_dt = None
                if retry_dt is not None:
                    if retry_dt.tzinfo is None:
                        retry_dt = retry_dt.replace(tzinfo=timezone.utc)
                    delta = (retry_dt - datetime.now(timezone.utc)).total_seconds()
                    if delta > 0:
                        return delta
        return max(LOGIN_THROTTLE_SECONDS, 5.0)

    def _extract_session_id(self, payload: dict[str, Any]) -> str | None:
        response = payload.get("response") if isinstance(payload, dict) else None
        if isinstance(response, dict):
            session_id = response.get("created_session_id")
            if isinstance(session_id, str) and session_id:
                return session_id

        client_block = payload.get("client") if isinstance(payload, dict) else None
        if isinstance(client_block, dict):
            session_id = client_block.get("last_active_session_id")
            if isinstance(session_id, str) and session_id:
                return session_id
            sessions = client_block.get("sessions")
            if isinstance(sessions, list) and sessions:
                first = sessions[0]
                if isinstance(first, dict):
                    session_id = first.get("id")
                    if isinstance(session_id, str) and session_id:
                        return session_id
        return None

    def _extract_sign_in_attempt_id(self, payload: dict[str, Any]) -> str | None:
        response = payload.get("response") if isinstance(payload, dict) else None
        if isinstance(response, dict):
            attempt_id = response.get("id")
            if isinstance(attempt_id, str) and attempt_id:
                return attempt_id
        client_block = payload.get("client") if isinstance(payload, dict) else None
        if isinstance(client_block, dict):
            sign_in = client_block.get("sign_in")
            if isinstance(sign_in, dict):
                attempt_id = sign_in.get("id")
                if isinstance(attempt_id, str) and attempt_id:
                    return attempt_id
        return None

    async def _fetch_production_token(self, client: httpx.AsyncClient) -> str:
        response = await client.post(
            f"{CLERK_BASE_URL}/client/sessions/{self._session_id}/tokens/Production",
            params=self._clerk_params(),
            headers=self._form_headers(referer=f"{AGENT_BASE_URL}/"),
        )
        response.raise_for_status()
        token = response.json().get("jwt")
        if not isinstance(token, str) or not token:
            raise RuntimeError("Resposta de token inválida.")
        return token

    async def _refresh_session_token(self, client: httpx.AsyncClient) -> str:
        await self._token_refresh_rate_limiter.wait()
        response = await client.post(
            f"{CLERK_BASE_URL}/client/sessions/{self._session_id}/tokens",
            params=self._clerk_params(),
            headers=self._form_headers(referer=f"{AGENT_BASE_URL}/"),
        )
        response.raise_for_status()
        token = response.json().get("jwt")
        if not isinstance(token, str) or not token:
            raise RuntimeError("Resposta de renovação de token inválida.")
        return token

    def _extract_token_exp(self, token: str) -> float:
        parts = token.split(".")
        if len(parts) < 2:
            return 0.0
        padding = "=" * (-len(parts[1]) % 4)
        try:
            payload_bytes = base64.urlsafe_b64decode(parts[1] + padding)
            payload_data = json.loads(payload_bytes)
        except (ValueError, json.JSONDecodeError):
            return 0.0
        exp = payload_data.get("exp")
        if isinstance(exp, (int, float)):
            return float(exp) - 30.0
        return 0.0

    def _token_expired(self) -> bool:
        return time.time() >= self._bearer_token_exp


class ChatPayloadBuilder:
    @staticmethod
    def prepare_messages_payload(
        *,
        messages: list[dict[str, Any]] | None,
        prompt: str | None,
        files: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        if not messages:
            if prompt is None:
                raise ValueError("Não é possível construir a mensagem sem prompt.")
            parts = ChatPayloadBuilder.build_file_parts(files)
            parts.append({"type": "text", "text": prompt})
            return [{"id": _generate_uuid7_like(), "role": "user", "parts": parts}]

        normalized: list[dict[str, Any]] = []
        for message in messages:
            role = str(message.get("role") or "user")
            content = message.get("content")
            if isinstance(content, list):
                parts = [
                    part
                    for part in (
                        ChatPayloadBuilder.normalize_part(item) for item in content
                    )
                    if part
                ]
            elif content is None:
                parts = [{"type": "text", "text": ""}]
            else:
                parts = [{"type": "text", "text": str(content)}]
            normalized.append(
                {
                    "id": str(message.get("id") or _generate_uuid7_like()),
                    "role": role,
                    "parts": parts,
                }
            )

        file_parts = ChatPayloadBuilder.build_file_parts(files)
        if file_parts:
            target = next(
                (msg for msg in normalized if msg.get("role") == "user"), None
            )
            if target:
                target["parts"] = file_parts + target.get("parts", [])
            elif normalized:
                normalized[0]["parts"] = file_parts + normalized[0].get("parts", [])
        return normalized

    @staticmethod
    def build_file_parts(files: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
        file_parts: list[dict[str, Any]] = []
        if not files:
            return file_parts

        for file_info in files:
            formatted = {
                "type": "file",
                "filename": file_info.get("filename"),
                "url": file_info.get("url"),
                "size": file_info.get("size"),
                "mediaType": file_info.get("mediaType"),
                "path": file_info.get("path"),
            }
            formatted = {
                key: value for key, value in formatted.items() if value is not None
            }
            if len(formatted) > 1:
                file_parts.append(formatted)
        return file_parts

    @staticmethod
    def normalize_part(part: Any) -> dict[str, Any] | None:
        if part is None:
            return None
        if isinstance(part, str):
            return {"type": "text", "text": part}
        if isinstance(part, dict):
            if part.get("type") == "file":
                formatted = {
                    "type": "file",
                    "filename": part.get("filename"),
                    "url": part.get("url"),
                    "size": part.get("size"),
                    "mediaType": part.get("mediaType"),
                    "path": part.get("path"),
                }
                return {
                    key: value for key, value in formatted.items() if value is not None
                }
            text = part.get("text")
            if text is None:
                return None
            return {"type": "text", "text": str(text)}
        return {"type": "text", "text": str(part)}


class AdaptaConversationClient:
    def __init__(
        self, *, session: AdaptaHttpSession, authenticator: AdaptaAuthenticator
    ) -> None:
        self._session = session
        self._authenticator = authenticator

    async def call_model(
        self,
        prompt: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        *,
        model: str = DEFAULT_MODEL,
        chat_id: str | None = None,
        files: list[dict[str, Any]] | None = None,
        folder_id: str | None = None,
        context_ids: list[str] | None = None,
        expert_id: str | None = None,
    ) -> ChatCompletionResult:
        if prompt is None and not messages:
            raise ValueError("call_model() requer prompt ou messages.")

        for attempt in range(2):
            chunks: list[str] = []
            try:
                async for event_type, payload in self._chat_event_stream(
                    prompt=prompt,
                    messages=messages,
                    model=model,
                    chat_id=chat_id,
                    files=files,
                    folder_id=folder_id,
                    context_ids=context_ids,
                    expert_id=expert_id,
                ):
                    if event_type == "answer":
                        chunks.append(payload)
                return ChatCompletionResult(
                    messages=[{"kind": "answer", "text": "".join(chunks)}]
                )
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code if exc.response else None
                if status_code == 401 and attempt == 0:
                    await self._authenticator.reset_authentication(drop_cache=True)
                    continue
                raise
        raise RuntimeError("Falha ao executar o chat após reautenticação.")

    async def list_experts(self, *, is_public: bool = False) -> list[dict[str, Any]]:
        client = await self._session.ensure_client()
        await self._authenticator.ensure_authenticated()
        token = await self._authenticator.ensure_bearer_token()

        params = {"page": 1, "limit": 1000, "isPublic": "true" if is_public else "false"}
        response = await client.get(
            f"{AGENT_BASE_URL}/api/expert/getAll/v1",
            headers={
                "accept": "*/*",
                "authorization": f"Bearer {token}",
                "origin": AGENT_BASE_URL,
                "referer": f"{AGENT_BASE_URL}/expert/my-experts",
            },
            params=params,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("data") or []

    async def create_expert(
        self,
        *,
        name: str,
        description: str,
        instruction: str,
        model: str,
        category: str = "MANAGEMENT",
        creativity: int | None = None,
        ice_breakers: str | None = None,
    ) -> dict[str, Any]:
        client = await self._session.ensure_client()
        await self._authenticator.ensure_authenticated()
        token = await self._authenticator.ensure_bearer_token()

        # multipart/form-data
        data = {
            "name": name,
            "description": description,
            "instruction": instruction,
            "model": model,
            "category": category,
        }
        if creativity is not None:
            data["creativity"] = str(creativity)
        if ice_breakers:
            data["iceBreakers"] = ice_breakers

        response = await client.post(
            f"{API_AGENT_BASE_URL}/api/expert",
            headers={
                "accept": "*/*",
                "authorization": f"Bearer {token}",
                "origin": AGENT_BASE_URL,
                "referer": f"{AGENT_BASE_URL}/",
            },
            data=data,
        )
        response.raise_for_status()
        return response.json()

    async def delete_expert(self, expert_id: str) -> dict[str, Any]:
        client = await self._session.ensure_client()
        await self._authenticator.ensure_authenticated()
        token = await self._authenticator.ensure_bearer_token()

        response = await client.request(
            "DELETE",
            f"{AGENT_BASE_URL}/api/expert/delete/v1",
            headers={
                "accept": "*/*",
                "authorization": f"Bearer {token}",
                "content-type": "application/json",
                "origin": AGENT_BASE_URL,
                "referer": f"{AGENT_BASE_URL}/expert/my-experts",
            },
            json={"id": expert_id},
        )
        response.raise_for_status()
        return response.json()

    async def init_expert_chat(
        self, chat_id: str, expert_id: str, is_temporary: bool = False
    ) -> dict[str, Any]:
        client = await self._session.ensure_client()
        await self._authenticator.ensure_authenticated()
        token = await self._authenticator.ensure_bearer_token()

        response = await client.post(
            f"{AGENT_BASE_URL}/api/chat/init/v1",
            headers={
                "accept": "*/*",
                "authorization": f"Bearer {token}",
                "content-type": "application/json",
                "origin": AGENT_BASE_URL,
                "referer": f"{AGENT_BASE_URL}/agentic-chat",
            },
            json={
                "chatId": chat_id,
                "expertId": expert_id,
                "isTemporaryChat": is_temporary,
            },
        )
        response.raise_for_status()
        return response.json()

    async def list_context_folders(self) -> list[dict[str, Any]]:
        client = await self._session.ensure_client()
        await self._authenticator.ensure_authenticated()
        token = await self._authenticator.ensure_bearer_token()

        response = await client.get(
            f"{AGENT_BASE_URL}/api/folders/v2",
            headers={
                "accept": "*/*",
                "authorization": f"Bearer {token}",
                "origin": AGENT_BASE_URL,
                "referer": f"{AGENT_BASE_URL}/agentic-chat",
            },
            params={"type": "CONTEXTS", "scope": "PERSONAL"},
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("data") or []

    async def list_contexts(
        self, *, limit: int = 20, folder_id: str | None = None
    ) -> list[dict[str, Any]]:
        client = await self._session.ensure_client()
        await self._authenticator.ensure_authenticated()
        token = await self._authenticator.ensure_bearer_token()

        params: dict[str, Any] = {"limit": limit}
        if folder_id:
            params["folderId"] = folder_id

        response = await client.get(
            f"{AGENT_BASE_URL}/api/contexts/v1",
            headers={
                "accept": "*/*",
                "authorization": f"Bearer {token}",
                "origin": AGENT_BASE_URL,
                "referer": f"{AGENT_BASE_URL}/agentic-chat",
            },
            params=params,
        )
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data") or {}
        return data.get("contexts") or []

    async def create_context(
        self, title: str, content: str, folder_id: str | None = None
    ) -> dict[str, Any]:
        client = await self._session.ensure_client()
        await self._authenticator.ensure_authenticated()
        token = await self._authenticator.ensure_bearer_token()

        payload = {"title": title, "context": content}
        if folder_id:
            payload["folderId"] = folder_id

        response = await client.post(
            f"{AGENT_BASE_URL}/api/contexts/v1",
            headers={
                "accept": "*/*",
                "authorization": f"Bearer {token}",
                "content-type": "application/json",
                "origin": AGENT_BASE_URL,
                "referer": f"{AGENT_BASE_URL}/agentic-chat",
            },
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def delete_contexts(self, context_ids: list[str]) -> dict[str, Any]:
        client = await self._session.ensure_client()
        await self._authenticator.ensure_authenticated()
        token = await self._authenticator.ensure_bearer_token()

        response = await client.request(
            "DELETE",
            f"{AGENT_BASE_URL}/api/contexts/v1",
            headers={
                "accept": "*/*",
                "authorization": f"Bearer {token}",
                "content-type": "application/json",
                "origin": AGENT_BASE_URL,
                "referer": f"{AGENT_BASE_URL}/agentic-chat",
            },
            json={"contextIds": context_ids},
        )
        response.raise_for_status()
        return response.json()

    async def delete_chat(self, chat_ids: str | list[str]) -> dict[str, Any]:
        if isinstance(chat_ids, str):
            normalized = [chat_ids]
        elif isinstance(chat_ids, list):
            normalized = [chat_id for chat_id in chat_ids if chat_id]
        else:
            raise TypeError("delete_chat aceita string ou lista de strings.")

        if not normalized:
            return {
                "success": True,
                "data": None,
                "details": {"message": "Nenhum chatId informado."},
            }

        client = await self._session.ensure_client()
        await self._authenticator.ensure_authenticated()
        token = await self._authenticator.ensure_bearer_token()

        response = await client.request(
            "DELETE",
            f"{AGENT_BASE_URL}/api/chat/delete/v1",
            headers={
                "accept": "*/*",
                "authorization": f"Bearer {token}",
                "content-type": "application/json",
                "origin": AGENT_BASE_URL,
                "referer": f"{AGENT_BASE_URL}/agentic-chat",
            },
            json={"chatIds": normalized},
        )
        response.raise_for_status()
        return response.json()

    async def upload_file(self, file_path: Path) -> dict[str, Any]:
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        suffix = file_path.suffix.lower()
        if suffix not in SUPPORTED_UPLOAD_FORMATS:
            raise ValueError(f"Formato de arquivo não suportado: {suffix}")

        client = await self._session.ensure_client()
        await self._authenticator.ensure_authenticated()
        token = await self._authenticator.ensure_bearer_token()

        existing_file = await self._find_existing_file(file_path.name)
        if existing_file is not None:
            return existing_file

        mime_type = MIME_TYPES.get(suffix, "application/octet-stream")
        response = await client.post(
            FILE_UPLOAD_ENDPOINT,
            headers={
                "accept": "*/*",
                "authorization": f"Bearer {token}",
                "origin": AGENT_BASE_URL,
                "referer": f"{AGENT_BASE_URL}/",
            },
            files={"file": (file_path.name, file_path.read_bytes(), mime_type)},
        )
        response.raise_for_status()
        payload = response.json()

        upload_info = self._extract_first_file_entry(payload)
        if upload_info is None:
            raise RuntimeError(f"Resposta inesperada do upload: {payload}")

        return self._normalize_file_entry(
            upload_info,
            default_filename=file_path.name,
            default_size=file_path.stat().st_size,
            default_media_type=mime_type,
            default_path=file_path.name,
        )

    async def list_files(self, *, limit: int = 20) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit deve ser maior que zero.")

        client = await self._session.ensure_client()
        await self._authenticator.ensure_authenticated()
        token = await self._authenticator.ensure_bearer_token()

        files: list[dict[str, Any]] = []
        offset = 0

        while True:
            params: dict[str, Any] = {"limit": limit}
            if offset > 0:
                params["offset"] = offset
                params["skipStorage"] = "true"

            response = await client.get(
                FILES_LIST_ENDPOINT,
                headers={
                    "accept": "*/*",
                    "authorization": f"Bearer {token}",
                    "origin": AGENT_BASE_URL,
                    "referer": f"{AGENT_BASE_URL}/agentic-chat",
                },
                params=params,
            )
            response.raise_for_status()

            page_entries = self._extract_file_entries(response.json())
            files.extend(
                self._normalize_file_entry(entry)
                for entry in page_entries
                if isinstance(entry, dict)
            )
            if len(page_entries) < limit:
                break
            offset += limit

        return files

    async def list_folders(self) -> list[dict[str, Any]]:
        client = await self._session.ensure_client()
        await self._authenticator.ensure_authenticated()
        token = await self._authenticator.ensure_bearer_token()

        response = await client.get(
            FOLDERS_LIST_ENDPOINT,
            headers={
                "accept": "*/*",
                "authorization": f"Bearer {token}",
                "origin": AGENT_BASE_URL,
                "referer": f"{AGENT_BASE_URL}/agentic-chat",
            },
            params={"type": "CHATS", "scope": "PERSONAL"},
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("data") or []

    async def create_folder(self, name: str) -> dict[str, Any]:
        client = await self._session.ensure_client()
        await self._authenticator.ensure_authenticated()
        token = await self._authenticator.ensure_bearer_token()

        response = await client.post(
            FOLDERS_LIST_ENDPOINT,
            headers={
                "accept": "*/*",
                "authorization": f"Bearer {token}",
                "content-type": "application/json",
                "origin": AGENT_BASE_URL,
                "referer": f"{AGENT_BASE_URL}/agentic-chat",
            },
            json={"name": name, "type": "CHATS", "scope": "PERSONAL"},
        )
        response.raise_for_status()
        return response.json()

    async def delete_folder(self, folder_id: str) -> dict[str, Any]:
        client = await self._session.ensure_client()
        await self._authenticator.ensure_authenticated()
        token = await self._authenticator.ensure_bearer_token()

        response = await client.request(
            "DELETE",
            f"{AGENT_BASE_URL}/api/folders/{folder_id}/v2",
            headers={
                "accept": "*/*",
                "authorization": f"Bearer {token}",
                "origin": AGENT_BASE_URL,
                "referer": f"{AGENT_BASE_URL}/agentic-chat",
            },
        )
        response.raise_for_status()
        return response.json()

    async def list_skills(self) -> list[dict[str, Any]]:
        client = await self._session.ensure_client()
        await self._authenticator.ensure_authenticated()
        token = await self._authenticator.ensure_bearer_token()

        response = await client.get(
            SKILLS_ENDPOINT,
            headers={
                "accept": "*/*",
                "authorization": f"Bearer {token}",
                "origin": AGENT_BASE_URL,
                "referer": f"{AGENT_BASE_URL}/agentic-chat",
            },
        )
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data") or {}
        return data.get("skills") or []

    async def get_skill(self, skill_id: str) -> dict[str, Any]:
        client = await self._session.ensure_client()
        await self._authenticator.ensure_authenticated()
        token = await self._authenticator.ensure_bearer_token()

        response = await client.get(
            f"{AGENT_BASE_URL}/api/skills/{skill_id}/v1",
            headers={
                "accept": "*/*",
                "authorization": f"Bearer {token}",
                "origin": AGENT_BASE_URL,
                "referer": f"{AGENT_BASE_URL}/agentic-chat",
            },
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("data") or {}

    async def create_skill(
        self, title: str, description: str, instruction: str
    ) -> dict[str, Any]:
        client = await self._session.ensure_client()
        await self._authenticator.ensure_authenticated()
        token = await self._authenticator.ensure_bearer_token()

        response = await client.post(
            SKILLS_ENDPOINT,
            headers={
                "accept": "*/*",
                "authorization": f"Bearer {token}",
                "content-type": "application/json",
                "origin": AGENT_BASE_URL,
                "referer": f"{AGENT_BASE_URL}/agentic-chat",
            },
            json={
                "title": title,
                "description": description,
                "instruction": instruction,
            },
        )
        response.raise_for_status()
        return response.json()

    async def delete_skill(self, skill_id: str) -> dict[str, Any]:
        client = await self._session.ensure_client()
        await self._authenticator.ensure_authenticated()
        token = await self._authenticator.ensure_bearer_token()

        response = await client.request(
            "DELETE",
            f"{AGENT_BASE_URL}/api/skills/{skill_id}/v1",
            headers={
                "accept": "*/*",
                "authorization": f"Bearer {token}",
                "origin": AGENT_BASE_URL,
                "referer": f"{AGENT_BASE_URL}/agentic-chat",
            },
        )
        response.raise_for_status()
        return response.json()

    async def list_chats(
        self, *, limit: int = 20, page: int = 1, folder_id: str | None = None
    ) -> dict[str, Any]:
        client = await self._session.ensure_client()
        await self._authenticator.ensure_authenticated()
        token = await self._authenticator.ensure_bearer_token()

        params: dict[str, Any] = {"limit": limit, "page": page}
        if folder_id:
            params["folderId"] = folder_id

        response = await client.get(
            f"{AGENT_BASE_URL}/api/chat/v2",
            headers={
                "accept": "*/*",
                "authorization": f"Bearer {token}",
                "origin": AGENT_BASE_URL,
                "referer": f"{AGENT_BASE_URL}/agentic-chat",
            },
            params=params,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("data") or {}

    async def update_skill(self, skill_id: str, is_active: bool) -> dict[str, Any]:
        client = await self._session.ensure_client()
        await self._authenticator.ensure_authenticated()
        token = await self._authenticator.ensure_bearer_token()

        response = await client.patch(
            f"{AGENT_BASE_URL}/api/skills/{skill_id}/v1",
            headers={
                "accept": "*/*",
                "authorization": f"Bearer {token}",
                "content-type": "application/json",
                "origin": AGENT_BASE_URL,
                "referer": f"{AGENT_BASE_URL}/agentic-chat",
            },
            json={"id": skill_id, "isActive": is_active},
        )
        response.raise_for_status()
        return response.json()

    async def delete_file(self, file_paths: str | list[str]) -> dict[str, Any]:
        if isinstance(file_paths, str):
            normalized = [file_paths]
        elif isinstance(file_paths, list):
            normalized = [file_path for file_path in file_paths if file_path]
        else:
            raise TypeError("delete_file aceita string ou lista de strings.")

        if not normalized:
            return {"success": True}

        client = await self._session.ensure_client()
        await self._authenticator.ensure_authenticated()
        token = await self._authenticator.ensure_bearer_token()

        response = await client.request(
            "DELETE",
            FILES_DELETE_ENDPOINT,
            headers={
                "accept": "*/*",
                "authorization": f"Bearer {token}",
                "content-type": "application/json",
                "origin": AGENT_BASE_URL,
                "referer": f"{AGENT_BASE_URL}/agentic-chat",
            },
            json={"filesPaths": normalized},
        )
        response.raise_for_status()
        return response.json()

    async def _find_existing_file(self, filename: str) -> dict[str, Any] | None:
        for file_info in await self.list_files():
            if file_info.get("filename") == filename:
                return file_info
        return None

    def _extract_file_entries(self, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [entry for entry in payload if isinstance(entry, dict)]
        if not isinstance(payload, dict):
            return []

        candidates = [
            payload.get("data"),
            payload.get("files"),
            payload.get("items"),
            payload.get("results"),
        ]
        for candidate in candidates:
            if isinstance(candidate, list):
                return [entry for entry in candidate if isinstance(entry, dict)]
            if isinstance(candidate, dict):
                nested = self._extract_file_entries(candidate)
                if nested:
                    return nested
        return []

    def _extract_first_file_entry(self, payload: Any) -> dict[str, Any] | None:
        entries = self._extract_file_entries(payload)
        return entries[0] if entries else None

    def _normalize_file_entry(
        self,
        file_info: dict[str, Any],
        *,
        default_filename: str | None = None,
        default_size: int | None = None,
        default_media_type: str | None = None,
        default_path: str | None = None,
    ) -> dict[str, Any]:
        filename = (
            file_info.get("fileName")
            or file_info.get("filename")
            or file_info.get("name")
            or default_filename
        )
        path = _first_non_none(
            file_info.get("filePathOnStorage"),
            file_info.get("path"),
            file_info.get("fileKey"),
            file_info.get("key"),
            default_path,
            filename,
        )
        return {
            "filename": filename,
            "url": _first_non_none(file_info.get("signedUrl"), file_info.get("url")),
            "size": _first_non_none(
                file_info.get("fileSizeInBytes"),
                file_info.get("size"),
                default_size,
            ),
            "mediaType": _first_non_none(
                file_info.get("fileMimeType"),
                file_info.get("mediaType"),
                file_info.get("mimeType"),
                default_media_type,
            ),
            "path": path,
        }

    async def _chat_event_stream(
        self,
        *,
        prompt: str | None,
        messages: list[dict[str, Any]] | None,
        model: str,
        chat_id: str | None,
        files: list[dict[str, Any]] | None = None,
        folder_id: str | None = None,
        context_ids: list[str] | None = None,
        expert_id: str | None = None,
        search_workaround: str | None = None,
        search_continue_prompt: str | None = None,
        search_max_workarounds: int = 1,
    ):
        client = await self._session.ensure_client()
        await self._authenticator.ensure_authenticated()
        token = await self._authenticator.ensure_bearer_token()

        chat_identifier = chat_id or _generate_uuid7_like()
        prepared_messages = ChatPayloadBuilder.prepare_messages_payload(
            messages=messages,
            prompt=prompt,
            files=files,
        )
        message_identifier = next(
            (
                str(message.get("id"))
                for message in reversed(prepared_messages)
                if message.get("role") == "user" and message.get("id")
            ),
            _generate_uuid7_like(),
        )
        payload = {
            "mandatoryTools": [],
            "chatId": chat_identifier,
            "contextsIds": context_ids or [],
            "meetingContextsIds": [],
            "modelAi": model,
            "preloadedData": {
                "companyGlobalSettings": None,
                "deactivatedToolNames": [],
                "chatSummary": None,
                "userProfile": None,
                "chatFiles": {"images": [], "sheets": [], "presentations": []},
                "projectAutoContext": {
                    "contextsList": [],
                    "meetingContexts": "",
                    "chatFiles": {"images": [], "sheets": [], "presentations": []},
                    "projectContextCount": 0,
                    "projectFileCount": 0,
                },
                "chatDocument": {
                    "activeDocument": None,
                    "allDocuments": [],
                    "activeDocumentId": None,
                },
                "isMemoriesEnabled": True,
                "userDisabledTools": {},
                "contextsList": [],
                "meetingContexts": "",
            },
            "useMemoriesInChat": False,
            "id": chat_identifier,
            "messages": prepared_messages,
            "trigger": "submit-message",
            "messageId": message_identifier,
        }
        if folder_id:
            payload["folderId"] = folder_id
        if expert_id:
            payload["expertId"] = expert_id

        headers = {
            "accept": "*/*",
            "authorization": f"Bearer {token}",
            "content-type": "application/json",
            "origin": AGENT_BASE_URL,
            "referer": f"{AGENT_BASE_URL}/agentic-chat",
        }

        applied_workarounds = 0

        while True:
            pending_surrogate: str | None = None
            saw_done = False
            retry_requested = False
            continue_requested = False
            async with client.stream(
                "POST",
                f"{AGENT_BASE_URL}/api/chat/stream/v1",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for raw_line in response.aiter_lines():
                    if not raw_line:
                        continue
                    if SEARCH_LIMIT_ERROR in raw_line:
                        if search_workaround in {"retry", "continue"} and applied_workarounds < search_max_workarounds:
                            applied_workarounds += 1
                            logger.warning(
                                "Detectado %s no stream bruto. Aplicando workaround=%s (%s/%s).",
                                SEARCH_LIMIT_ERROR,
                                search_workaround,
                                applied_workarounds,
                                search_max_workarounds,
                            )
                            if search_workaround == "retry":
                                chat_identifier = _generate_uuid7_like()
                                payload["chatId"] = chat_identifier
                                payload["id"] = chat_identifier
                                retry_requested = True
                                break
                            if search_workaround == "continue":
                                continue_requested = True
                                break
                        yield ("raw-error", raw_line)
                        continue
                    if not raw_line.startswith("data:"):
                        continue
                    payload_str = raw_line[5:].strip()
                    if not payload_str:
                        continue
                    if payload_str == "[DONE]":
                        saw_done = True
                        if pending_surrogate is not None:
                            yield ("answer", "\ufffd")
                        yield ("answer_end", "")
                        break

                    try:
                        event = json.loads(payload_str)
                    except json.JSONDecodeError:
                        logger.warning("Evento SSE inválido recebido: %s", payload_str)
                        continue

                    event_type = event.get("type")
                    if event_type == "tool-output-error":
                        raise ToolExecutionError(
                            (
                                event.get("errorText") or "Erro desconhecido na ferramenta."
                            ).strip(),
                            tool_name=event.get("toolName"),
                            tool_call_id=event.get("toolCallId"),
                        )

                    if event_type == "tool-output-available":
                        output = event.get("output") or {}
                        content = output.get("content") or output.get("analysis")
                        if isinstance(content, str) and content.strip():
                            yield ("answer", content.strip())
                        continue

                    if event_type == "text-delta":
                        delta = event.get("delta")
                        if isinstance(delta, str) and delta:
                            safe_text, pending_surrogate = self._coalesce_surrogates(
                                delta, pending_surrogate
                            )
                            if safe_text:
                                yield ("answer", safe_text)
                        continue

                    if event_type == "text-end":
                        if pending_surrogate is not None:
                            yield ("answer", "\ufffd")
                            pending_surrogate = None
                        yield ("answer_end", "")
            if retry_requested:
                continue
            if continue_requested:
                prepared_messages = ChatPayloadBuilder.prepare_messages_payload(
                    messages=[{"role": "user", "content": search_continue_prompt or "continue a pesquisa"}],
                    prompt=None,
                    files=None,
                )
                message_identifier = next(
                    (
                        str(message.get("id"))
                        for message in reversed(prepared_messages)
                        if message.get("role") == "user" and message.get("id")
                    ),
                    _generate_uuid7_like(),
                )
                payload["messages"] = prepared_messages
                payload["messageId"] = message_identifier
                continue
            if saw_done or not search_workaround or applied_workarounds >= search_max_workarounds:
                break

    def _coalesce_surrogates(
        self, chunk: str, pending: str | None
    ) -> tuple[str, str | None]:
        safe_parts: list[str] = []
        index = 0

        if pending is not None:
            if chunk and self._is_low_surrogate(chunk[0]):
                safe_parts.append(self._surrogate_pair_to_char(pending, chunk[0]))
                index = 1
                pending = None
            else:
                safe_parts.append("\ufffd")
                pending = None

        while index < len(chunk):
            char = chunk[index]
            if self._is_high_surrogate(char):
                if index + 1 < len(chunk) and self._is_low_surrogate(chunk[index + 1]):
                    safe_parts.append(
                        self._surrogate_pair_to_char(char, chunk[index + 1])
                    )
                    index += 2
                    continue
                pending = char
                index += 1
                continue
            if self._is_low_surrogate(char):
                safe_parts.append("\ufffd")
                index += 1
                continue
            safe_parts.append(char)
            index += 1

        return "".join(safe_parts), pending

    def _is_high_surrogate(self, char: str) -> bool:
        return 0xD800 <= ord(char) <= 0xDBFF

    def _is_low_surrogate(self, char: str) -> bool:
        return 0xDC00 <= ord(char) <= 0xDFFF

    def _surrogate_pair_to_char(self, high: str, low: str) -> str:
        high_value = ord(high) - 0xD800
        low_value = ord(low) - 0xDC00
        return chr(0x10000 + ((high_value << 10) | low_value))


class AdaptaClientAdapter:
    def __init__(
        self, settings: Settings, *, transport: httpx.BaseTransport | None = None
    ) -> None:
        self._session = AdaptaHttpSession(transport=transport)
        self._authenticator = AdaptaAuthenticator(
            session=self._session,
            login=settings.adapta_login,
            password=settings.adapta_password,
        )
        self._conversations = AdaptaConversationClient(
            session=self._session,
            authenticator=self._authenticator,
        )

    async def __aenter__(self) -> "AdaptaClientAdapter":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        await self._session.close()
        await self._authenticator.close()

    async def prompt(
        self,
        *,
        model_backend: str,
        prompt: str,
        folder_id: str | None = None,
        context_ids: list[str] | None = None,
        expert_id: str | None = None,
    ) -> str:
        result = await self._conversations.call_model(
            prompt=prompt,
            model=model_backend,
            folder_id=folder_id,
            context_ids=context_ids,
            expert_id=expert_id,
        )
        return extract_answer_text(result)

    async def prompt_with_files(
        self,
        *,
        model_backend: str,
        prompt: str,
        files: list[dict[str, Any]],
        folder_id: str | None = None,
        context_ids: list[str] | None = None,
        expert_id: str | None = None,
    ) -> str:
        result = await self._conversations.call_model(
            prompt=prompt,
            model=model_backend,
            files=files,
            folder_id=folder_id,
            context_ids=context_ids,
            expert_id=expert_id,
        )
        return extract_answer_text(result)

    async def chat(
        self,
        *,
        model_backend: str,
        messages: list[dict[str, Any]],
        chat_id: str,
        folder_id: str | None = None,
        context_ids: list[str] | None = None,
        expert_id: str | None = None,
    ) -> str:
        result = await self._conversations.call_model(
            messages=messages,
            model=model_backend,
            chat_id=chat_id,
            folder_id=folder_id,
            context_ids=context_ids,
            expert_id=expert_id,
        )
        return extract_answer_text(result)

    async def chat_stream(
        self,
        *,
        model_backend: str,
        messages: list[dict[str, Any]],
        chat_id: str,
        files: list[dict[str, Any]] | None = None,
        folder_id: str | None = None,
        context_ids: list[str] | None = None,
        expert_id: str | None = None,
        search_workaround: str | None = None,
        search_continue_prompt: str | None = None,
        search_max_workarounds: int = 1,
    ):
        async for event in self._conversations._chat_event_stream(
            prompt=None,
            messages=messages,
            model=model_backend,
            chat_id=chat_id,
            files=files,
            folder_id=folder_id,
            context_ids=context_ids,
            expert_id=expert_id,
            search_workaround=search_workaround,
            search_continue_prompt=search_continue_prompt,
            search_max_workarounds=search_max_workarounds,
        ):
            yield event

    async def chat_with_files(
        self,
        *,
        model_backend: str,
        messages: list[dict[str, Any]],
        chat_id: str,
        files: list[dict[str, Any]],
        folder_id: str | None = None,
        context_ids: list[str] | None = None,
        expert_id: str | None = None,
    ) -> str:
        result = await self._conversations.call_model(
            messages=messages,
            model=model_backend,
            chat_id=chat_id,
            files=files,
            folder_id=folder_id,
            context_ids=context_ids,
            expert_id=expert_id,
        )
        return extract_answer_text(result)

    async def delete_chat(self, chat_id: str | list[str]) -> None:
        await self._conversations.delete_chat(chat_id)

    async def list_chats(
        self, *, limit: int = 20, page: int = 1, folder_id: str | None = None
    ) -> dict[str, Any]:
        return await self._conversations.list_chats(
            limit=limit, page=page, folder_id=folder_id
        )

    async def list_context_folders(self) -> list[dict[str, Any]]:
        return await self._conversations.list_context_folders()

    async def list_contexts(
        self, *, limit: int = 20, folder_id: str | None = None
    ) -> list[dict[str, Any]]:
        return await self._conversations.list_contexts(limit=limit, folder_id=folder_id)

    async def create_context(
        self, title: str, content: str, folder_id: str | None = None
    ) -> dict[str, Any]:
        return await self._conversations.create_context(
            title=title, content=content, folder_id=folder_id
        )

    async def delete_contexts(self, context_ids: list[str]) -> dict[str, Any]:
        return await self._conversations.delete_contexts(context_ids)

    async def list_experts(self, *, is_public: bool = False) -> list[dict[str, Any]]:
        return await self._conversations.list_experts(is_public=is_public)

    async def create_expert(
        self,
        *,
        name: str,
        description: str,
        instruction: str,
        model: str,
        category: str = "MANAGEMENT",
        creativity: int | None = None,
        ice_breakers: str | None = None,
    ) -> dict[str, Any]:
        return await self._conversations.create_expert(
            name=name,
            description=description,
            instruction=instruction,
            model=model,
            category=category,
            creativity=creativity,
            ice_breakers=ice_breakers,
        )

    async def delete_expert(self, expert_id: str) -> dict[str, Any]:
        return await self._conversations.delete_expert(expert_id)

    async def init_expert_chat(
        self, chat_id: str, expert_id: str, is_temporary: bool = False
    ) -> dict[str, Any]:
        return await self._conversations.init_expert_chat(
            chat_id, expert_id, is_temporary
        )

    async def upload_file(self, file_path: Path) -> dict[str, Any]:
        return await self._conversations.upload_file(file_path)

    async def list_files(self) -> list[dict[str, Any]]:
        return await self._conversations.list_files()

    async def list_folders(self) -> list[dict[str, Any]]:
        return await self._conversations.list_folders()

    async def create_folder(self, name: str) -> dict[str, Any]:
        return await self._conversations.create_folder(name)

    async def delete_folder(self, folder_id: str) -> dict[str, Any]:
        return await self._conversations.delete_folder(folder_id)

    async def list_skills(self) -> list[dict[str, Any]]:
        return await self._conversations.list_skills()

    async def get_skill(self, skill_id: str) -> dict[str, Any]:
        return await self._conversations.get_skill(skill_id)

    async def create_skill(
        self, title: str, description: str, instruction: str
    ) -> dict[str, Any]:
        return await self._conversations.create_skill(title, description, instruction)

    async def delete_skill(self, skill_id: str) -> dict[str, Any]:
        return await self._conversations.delete_skill(skill_id)

    async def update_skill(self, skill_id: str, is_active: bool) -> dict[str, Any]:
        return await self._conversations.update_skill(skill_id, is_active)

    async def delete_file(self, file_path: str | list[str]) -> None:
        await self._conversations.delete_file(file_path)

    async def logout(self) -> None:
        await self._authenticator.logout()


def create_client(settings: Settings) -> AdaptaClientAdapter:
    return AdaptaClientAdapter(settings)


def extract_answer_text(result: Any) -> str:
    if result is None:
        raise RuntimeError("Resposta vazia retornada pelo cliente Adapta.")
    if isinstance(result, str):
        return result.strip()

    messages = getattr(result, "messages", None)
    if isinstance(messages, list):
        answers = [
            entry.get("text", "")
            for entry in messages
            if isinstance(entry, dict) and entry.get("kind") == "answer"
        ]
        if any(chunk.strip() for chunk in answers):
            return "".join(answers).strip()
    return str(result).strip()


def should_logout() -> bool:
    value = os.environ.get("ADAPTA_LOGOUT", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _extract_session_id_from_cookies(cookies: dict[str, str]) -> str | None:
    context = cookies.get("clerk_active_context") or cookies.get("clerk_active_session")
    if isinstance(context, str) and context:
        normalized = context[:-1] if context.endswith(":") else context
        if normalized:
            return normalized
    token = cookies.get("__session")
    if isinstance(token, str) and token:
        parts = token.split(".")
        if len(parts) >= 2:
            padding = "=" * (-len(parts[1]) % 4)
            try:
                payload_bytes = base64.urlsafe_b64decode(parts[1] + padding)
                payload_data = json.loads(payload_bytes)
            except (ValueError, json.JSONDecodeError):
                payload_data = None
            if isinstance(payload_data, dict):
                session_id = payload_data.get("sid")
                if isinstance(session_id, str) and session_id:
                    return session_id
    return None


def import_cookies_to_session_cache(
    source_path: Path,
    *,
    target_path: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    raw_text = source_path.read_text(encoding="utf-8")
    payload = json.loads(raw_text)
    cookies, headers = _normalize_cookie_payload(payload)
    if not cookies:
        raise ValueError("Nenhum cookie encontrado no arquivo informado.")
    session_id = _extract_session_id_from_cookies(cookies)
    if not session_id:
        raise RuntimeError("Não foi possível inferir o session_id dos cookies.")

    destination = _resolve_session_cache_path(target_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    cache_payload: dict[str, Any] = {
        "session_id": session_id,
        "cookies": cookies,
    }
    if headers:
        cache_payload["headers"] = headers

    destination.write_text(
        json.dumps(cache_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return destination, cache_payload


def _normalize_cookie_payload(payload: Any) -> tuple[dict[str, str], dict[str, str]]:
    cookies: dict[str, str] = {}
    headers: dict[str, str] = {}

    if isinstance(payload, list):
        for entry in payload:
            if isinstance(entry, dict):
                name = entry.get("name")
                value = entry.get("value")
                if isinstance(name, str) and value is not None:
                    cookies[name] = str(value)
    elif isinstance(payload, dict):
        if isinstance(payload.get("cookies"), dict):
            cookies = {
                str(key): str(value)
                for key, value in payload["cookies"].items()
                if isinstance(key, str) and value is not None
            }
        else:
            cookies = {
                str(key): str(value)
                for key, value in payload.items()
                if isinstance(key, str) and value is not None
            }

        if isinstance(payload.get("headers"), dict):
            headers = {
                str(key): str(value)
                for key, value in payload["headers"].items()
                if isinstance(key, str) and value is not None
            }
    else:
        raise ValueError("Formato de export de cookies inválido.")

    cookies = {key: value for key, value in cookies.items() if key}
    headers = {key: value for key, value in headers.items() if key}
    return cookies, headers
