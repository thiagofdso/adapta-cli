from pathlib import Path

from typer.testing import CliRunner

import adapta.cli as cli_module
from adapta.cli import app
from adapta.config import Settings


class DummyClient:
    def __init__(self) -> None:
        self.prompt_calls: list[tuple[str, str, list[str] | None]] = []
        self.chat_calls: list[
            tuple[str, str, list[dict[str, str]], list[str] | None]
        ] = []
        self.files = [
            {
                "filename": "a.pdf",
                "path": "uploads/a.pdf",
                "mediaType": "application/pdf",
                "size": 10,
            },
            {
                "filename": "b.csv",
                "path": "uploads/b.csv",
                "mediaType": "text/csv",
                "size": 20,
            },
        ]

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def prompt(self, *, model_backend: str, prompt: str) -> str:
        self.prompt_calls.append((model_backend, prompt, None))
        return "2"

    async def prompt_with_files(
        self,
        *,
        model_backend: str,
        prompt: str,
        files: list[dict[str, object]],
    ) -> str:
        self.prompt_calls.append(
            (model_backend, prompt, [str(file["filename"]) for file in files])
        )
        return "2"

    async def chat(
        self, *, model_backend: str, messages: list[dict[str, str]], chat_id: str
    ) -> str:
        self.chat_calls.append((model_backend, chat_id, list(messages), None))
        return "2"

    async def chat_with_files(
        self,
        *,
        model_backend: str,
        messages: list[dict[str, str]],
        chat_id: str,
        files: list[dict[str, object]],
    ) -> str:
        self.chat_calls.append(
            (
                model_backend,
                chat_id,
                list(messages),
                [str(file["filename"]) for file in files],
            )
        )
        return "2"

    async def upload_file(self, file_path: Path) -> dict[str, object]:
        return {
            "filename": file_path.name,
            "url": f"https://files.example/{file_path.name}",
            "size": file_path.stat().st_size,
            "mediaType": "application/pdf",
            "path": f"uploads/{file_path.name}",
        }

    async def delete_chat(self, chat_id: str) -> None:
        return None

    async def list_files(self) -> list[dict[str, object]]:
        return list(self.files)


def test_prompt_command_prints_response(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    client = DummyClient()

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: Settings(
            adapta_login="user@example.com",
            adapta_password="secret",
            adapta_model=None,
            env_file_path=tmp_path / ".env",
        ),
    )
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

    result = runner.invoke(
        app,
        [
            "prompt",
            "--model",
            "gpt",
            "--prompt",
            "quanto é 1+1 responda somente o valor",
        ],
    )

    assert result.exit_code == 0
    assert result.stdout.strip() == "2"
    assert client.prompt_calls == [
        ("GPT_5", "quanto é 1+1 responda somente o valor", None)
    ]


def test_models_command_lists_available_models() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["models"])

    assert result.exit_code == 0
    assert "gpt\tGPT-5\tGPT_5" in result.stdout
    assert "claude\tClaude 4.5 Sonnet\tCLAUDE_4_5_SONNET" in result.stdout


def test_list_files_command_lists_existing_files(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    client = DummyClient()

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: Settings(
            adapta_login="user@example.com",
            adapta_password="secret",
            adapta_model=None,
            env_file_path=tmp_path / ".env",
        ),
    )
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

    result = runner.invoke(app, ["list-files"])

    assert result.exit_code == 0
    assert "filename\tpath\tmediaType\tsize" in result.stdout
    assert "a.pdf\tuploads/a.pdf\tapplication/pdf\t10" in result.stdout
    assert "b.csv\tuploads/b.csv\ttext/csv\t20" in result.stdout


def test_prompt_command_writes_output_file(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    output_file = tmp_path / "saida.txt"
    client = DummyClient()

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: Settings(
            adapta_login="user@example.com",
            adapta_password="secret",
            adapta_model=None,
            env_file_path=tmp_path / ".env",
        ),
    )
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

    result = runner.invoke(
        app,
        [
            "prompt",
            "--model",
            "gpt",
            "--prompt",
            "quanto é 1+1 responda somente o valor",
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert output_file.read_text(encoding="utf-8").strip() == "2"


def test_chat_command_runs_until_exit(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    client = DummyClient()

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: Settings(
            adapta_login="user@example.com",
            adapta_password="secret",
            adapta_model=None,
            env_file_path=tmp_path / ".env",
        ),
    )
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

    result = runner.invoke(
        app, ["chat", "--model", "gpt"], input="quanto é 1+1\nexit\n"
    )

    assert result.exit_code == 0
    assert "2" in result.stdout
    assert client.chat_calls == [
        (
            "GPT_5",
            client.chat_calls[0][1],
            [{"role": "user", "content": "quanto é 1+1"}],
            None,
        )
    ]


def test_prompt_command_uses_default_model(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    client = DummyClient()

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: Settings(
            adapta_login="user@example.com",
            adapta_password="secret",
            adapta_model="gpt",
            env_file_path=tmp_path / ".env",
        ),
    )
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

    result = runner.invoke(
        app, ["prompt", "--prompt", "quanto é 1+1 responda somente o valor"]
    )

    assert result.exit_code == 0
    assert result.stdout.strip() == "2"


def test_prompt_command_accepts_file_attachments(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    client = DummyClient()
    attachment_a = tmp_path / "a.pdf"
    attachment_b = tmp_path / "b.pdf"
    attachment_a.write_bytes(b"%PDF-1.4\n")
    attachment_b.write_bytes(b"%PDF-1.4\n")

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: Settings(
            adapta_login="user@example.com",
            adapta_password="secret",
            adapta_model=None,
            env_file_path=tmp_path / ".env",
        ),
    )
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

    result = runner.invoke(
        app,
        [
            "prompt",
            "--model",
            "gpt",
            "--prompt",
            "resuma os anexos",
            "--file",
            f"{attachment_a},{attachment_b}",
        ],
    )

    assert result.exit_code == 0
    assert client.prompt_calls == [("GPT_5", "resuma os anexos", ["a.pdf", "b.pdf"])]


def test_chat_command_accepts_file_attachments(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    client = DummyClient()
    attachment_a = tmp_path / "a.pdf"
    attachment_b = tmp_path / "b.pdf"
    attachment_a.write_bytes(b"%PDF-1.4\n")
    attachment_b.write_bytes(b"%PDF-1.4\n")

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: Settings(
            adapta_login="user@example.com",
            adapta_password="secret",
            adapta_model=None,
            env_file_path=tmp_path / ".env",
        ),
    )
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

    result = runner.invoke(
        app,
        ["chat", "--model", "gpt", "--file", f"{attachment_a},{attachment_b}"],
        input="analise\nexit\n",
    )

    assert result.exit_code == 0
    assert client.chat_calls == [
        (
            "GPT_5",
            client.chat_calls[0][1],
            [{"role": "user", "content": "analise"}],
            ["a.pdf", "b.pdf"],
        )
    ]


def test_prompt_command_rejects_more_than_five_files(
    monkeypatch, tmp_path: Path
) -> None:
    runner = CliRunner()
    files = []
    for index in range(6):
        path = tmp_path / f"{index}.pdf"
        path.write_bytes(b"%PDF-1.4\n")
        files.append(str(path))

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: Settings(
            adapta_login="user@example.com",
            adapta_password="secret",
            adapta_model=None,
            env_file_path=tmp_path / ".env",
        ),
    )

    result = runner.invoke(
        app,
        ["prompt", "--model", "gpt", "--prompt", "oi", "--file", ",".join(files)],
    )

    assert result.exit_code == 1
    assert "entre 1 e 5 arquivos" in result.stderr


def test_prompt_command_shows_friendly_error_without_traceback(monkeypatch) -> None:
    runner = CliRunner()

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: (_ for _ in ()).throw(
            ValueError("ADAPTA_LOGIN e ADAPTA_PASSWORD são obrigatórios.")
        ),
    )

    result = runner.invoke(
        app,
        [
            "prompt",
            "--model",
            "gpt",
            "--prompt",
            "quanto é 1+1 responda somente o valor",
        ],
    )

    assert result.exit_code == 1
    assert "ADAPTA_LOGIN e ADAPTA_PASSWORD são obrigatórios." in result.stderr
    assert "Traceback" not in result.stderr


def test_debate_command_reprompts_invalid_agent_count(
    monkeypatch, tmp_path: Path
) -> None:
    runner = CliRunner()

    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def prompt(self, *, model_backend: str, prompt: str) -> str:
            return "conclusao final"

        async def chat(
            self, *, model_backend: str, messages: list[dict[str, str]], chat_id: str
        ) -> str:
            return f"{model_backend}:{len(messages)}"

        async def delete_chat(self, chat_id: str | list[str]) -> None:
            return None

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ADAPTA_DEBATE_CONFIG", raising=False)
    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: Settings(
            adapta_login="user@example.com",
            adapta_password="secret",
            adapta_model=None,
            env_file_path=tmp_path / ".env",
        ),
    )
    monkeypatch.setattr(cli_module, "create_client", lambda settings: DummyClient())

    result = runner.invoke(
        app,
        ["debate", "--prompt", "Defina uma arquitetura"],
        input="abc\n1\n2\n1\narquiteto\n4\ndesenvolvedor\nxyz\n2\n",
    )

    assert result.exit_code == 0, result.stderr
    assert "Informe um número inteiro válido." in result.stdout
    assert "Informe um número maior ou igual a 2." in result.stdout
    assert (tmp_path / "debate.json").exists()


def test_destilador_command_rejects_missing_mode_arguments(tmp_path: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["destilador"])

    assert result.exit_code == 1
    assert "Informe --input e --output" in result.stderr
