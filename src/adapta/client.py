from __future__ import annotations

import asyncio
import base64
import json
import logging
import secrets
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

from adapta.models import Settings


logger = logging.getLogger(__name__)

AGENT_BASE_URL = "https://agent.adapta.one"
CLERK_BASE_URL = "https://clerk.agent.adapta.one/v1"
CLERK_API_VERSION = "2025-11-10"
CLERK_JS_VERSION = "5.125.7"
DEFAULT_MODEL = "CLAUDE_4_5_SONNET"
LOGIN_THROTTLE_SECONDS = 2.0
TOKEN_REFRESH_THROTTLE_SECONDS = 120.0


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


class AdaptaAuthenticator:
    def __init__(
        self, *, session: AdaptaHttpSession, login: str, password: str
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

    @property
    def session_id(self) -> str | None:
        return self._session_id

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
            return AuthResult(session_id=self._session_id, cookies=cookies)

    async def ensure_authenticated(self) -> None:
        client = await self._session.ensure_client()
        if not self._session_id:
            await self.simulate_login()
            return
        await self._touch_session(client, self._session_id)

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
            return token

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
        *, messages: list[dict[str, Any]] | None, prompt: str | None
    ) -> list[dict[str, Any]]:
        if not messages:
            if prompt is None:
                raise ValueError("Não é possível construir a mensagem sem prompt.")
            return [{"role": "user", "parts": [{"type": "text", "text": prompt}]}]

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
            normalized.append({"role": role, "parts": parts})
        return normalized

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
    ) -> ChatCompletionResult:
        if prompt is None and not messages:
            raise ValueError("call_model() requer prompt ou messages.")

        chunks: list[str] = []
        async for event_type, payload in self._chat_event_stream(
            prompt=prompt, messages=messages, model=model, chat_id=chat_id
        ):
            if event_type == "answer":
                chunks.append(payload)
        return ChatCompletionResult(
            messages=[{"kind": "answer", "text": "".join(chunks)}]
        )

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

    async def _chat_event_stream(
        self,
        *,
        prompt: str | None,
        messages: list[dict[str, Any]] | None,
        model: str,
        chat_id: str | None,
    ):
        client = await self._session.ensure_client()
        await self._authenticator.ensure_authenticated()
        token = await self._authenticator.ensure_bearer_token()

        chat_identifier = chat_id or _generate_uuid7_like()
        payload = {
            "mandatoryTools": [],
            "chatId": chat_identifier,
            "contextsIds": [],
            "meetingContextsIds": [],
            "modelAi": model,
            "id": chat_identifier,
            "messages": ChatPayloadBuilder.prepare_messages_payload(
                messages=messages, prompt=prompt
            ),
            "trigger": "submit-message",
        }
        headers = {
            "accept": "*/*",
            "authorization": f"Bearer {token}",
            "content-type": "application/json",
            "origin": AGENT_BASE_URL,
            "referer": f"{AGENT_BASE_URL}/",
        }

        pending_surrogate: str | None = None
        async with client.stream(
            "POST",
            f"{AGENT_BASE_URL}/api/chat/stream/v1",
            headers=headers,
            json=payload,
        ) as response:
            response.raise_for_status()
            async for raw_line in response.aiter_lines():
                if not raw_line or not raw_line.startswith("data:"):
                    continue
                payload_str = raw_line[5:].strip()
                if not payload_str:
                    continue
                if payload_str == "[DONE]":
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

    async def prompt(self, *, model_backend: str, prompt: str) -> str:
        result = await self._conversations.call_model(
            prompt=prompt, model=model_backend
        )
        return extract_answer_text(result)

    async def chat(
        self, *, model_backend: str, messages: list[dict[str, str]], chat_id: str
    ) -> str:
        result = await self._conversations.call_model(
            messages=messages, model=model_backend, chat_id=chat_id
        )
        return extract_answer_text(result)

    async def delete_chat(self, chat_id: str) -> None:
        await self._conversations.delete_chat(chat_id)


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
