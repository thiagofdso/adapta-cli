import json
from pathlib import Path

from typer.testing import CliRunner

import adapta.cli as cli_module
from adapta.cli import app
from adapta.config import Settings
from adapta.services import persona_service


class DummyClient:
    def __init__(self) -> None:
        self.prompt_calls: list[tuple[str, str, list[str] | None]] = []
        self.deleted_chats: list[str] = []
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
        self.deleted_chats.append(chat_id)
        return None

    async def list_files(self) -> list[dict[str, object]]:
        return list(self.files)


def _get_settings(tmp_path: Path, model: str | None = None) -> Settings:
    return Settings(
        adapta_login="user@example.com",
        adapta_password="secret",
        adapta_model=model,
        env_file_path=tmp_path / ".env",
        data_dir=tmp_path / "data",
    )


def test_prompt_command_prints_response(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    client = DummyClient()

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: _get_settings(tmp_path),
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
    assert "2" in result.stdout
    assert client.prompt_calls == [
        ("GPT_54", "quanto é 1+1 responda somente o valor", None)
    ]


def test_models_command_lists_available_models() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["models"])

    assert result.exit_code == 0
    assert "gpt54\tGPT-5.4\tGPT_54" in result.stdout
    assert "one\tONE\tONE" in result.stdout


def test_list_files_command_lists_existing_files(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    client = DummyClient()

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: _get_settings(tmp_path),
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
        lambda env_file=None: _get_settings(tmp_path),
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
        lambda env_file=None: _get_settings(tmp_path),
    )
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

    result = runner.invoke(
        app, ["chat", "--model", "gpt"], input="quanto é 1+1\nexit\n"
    )

    assert result.exit_code == 0
    assert "2" in result.stdout
    assert client.chat_calls == [
        (
            "GPT_54",
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
        lambda env_file=None: _get_settings(tmp_path, model="gpt"),
    )
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

    result = runner.invoke(
        app, ["prompt", "--prompt", "quanto é 1+1 responda somente o valor"]
    )

    assert result.exit_code == 0
    assert "2" in result.stdout


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
        lambda env_file=None: _get_settings(tmp_path),
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
    assert client.prompt_calls == [("GPT_54", "resuma os anexos", ["a.pdf", "b.pdf"])]


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
        lambda env_file=None: _get_settings(tmp_path),
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
            "GPT_54",
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
        lambda env_file=None: _get_settings(tmp_path),
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
        lambda env_file=None: _get_settings(tmp_path),
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


def test_pipeline_command_rejects_missing_mode_arguments(tmp_path: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["pipeline"])

    assert result.exit_code == 1
    assert "Informe --input-dir e --output-dir" in result.stderr


def test_pipeline_command_shows_friendly_error_for_missing_input_dir(
    monkeypatch, tmp_path: Path
) -> None:
    runner = CliRunner()

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: _get_settings(tmp_path),
    )

    result = runner.invoke(
        app,
        [
            "pipeline",
            "--input-dir",
            str(tmp_path / "inexistente"),
            "--output-dir",
            str(tmp_path / "saida"),
        ],
    )

    assert result.exit_code == 1
    assert "Diretório de entrada não encontrado" in result.stderr
    assert "Traceback" not in result.stderr


def test_skill_create_command_rejects_missing_mode_arguments(tmp_path: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["skill-create"])

    assert result.exit_code == 1
    assert "Informe --input-dir e --output-dir" in result.stderr


def test_skill_create_command_shows_friendly_error_for_missing_input_dir(
    monkeypatch, tmp_path: Path
) -> None:
    runner = CliRunner()

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: _get_settings(tmp_path),
    )

    result = runner.invoke(
        app,
        [
            "skill-create",
            "--input-dir",
            str(tmp_path / "inexistente"),
            "--output-dir",
            str(tmp_path / "saida"),
        ],
    )

    assert result.exit_code == 1
    assert "Diretório de entrada não encontrado" in result.stderr
    assert "Traceback" not in result.stderr


import pytest

@pytest.mark.skip(reason="Ignorado a pedido do usuario")
def test_import_cookies_command_updates_cache(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    source_path = tmp_path / "session.json"
    cache_dir = tmp_path / ".adapta"
    cache_path = cache_dir / "cookies.json"
    source_path.write_text(
        json.dumps(
            [
                {"name": "clerk_active_context", "value": "sess_imported:"},
                {
                    "name": "__session",
                    "value": "eyJhbGciOiJub25lIn0.eyJzaWQiOiJzZXNzX2ltcG9ydGVkIn0.",
                },
            ]
        ),
        encoding="utf-8",
    )
    original_import = cli_module.import_cookies_to_session_cache
    monkeypatch.setattr(
        cli_module,
        "import_cookies_to_session_cache",
        lambda input, **kwargs: original_import(input, target_path=cache_path, **kwargs),
    )

    result = runner.invoke(app, ["import-cookies", "--input", str(source_path)])

    assert result.exit_code == 0
    assert cache_path.exists()
    assert "Cookies importados para" in result.stdout
    assert "session_id: sess_imported" in result.stdout


def test_prompt_command_uses_persona(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    client = DummyClient()
    data_dir = tmp_path / "data"
    persona_dir = data_dir / "persona"
    persona_dir.mkdir(parents=True)
    persona_dir.joinpath("desenvolvedor-backend.md").write_text(
        "## Persona\nVocê é especialista em incidentes.\n", encoding="utf-8"
    )

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: _get_settings(tmp_path),
    )
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

    result = runner.invoke(
        app,
        [
            "prompt",
            "--model",
            "gpt54",
            "--prompt",
            "Faça um resumo",
            "--persona",
            "desenvolvedor-backend",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert client.prompt_calls
    combined_prompt = client.prompt_calls[0][1]
    assert "Você é especialista em incidentes." in combined_prompt
    assert combined_prompt.strip().endswith("Faça um resumo")


def test_persona_command_lists_existing_personas(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    data_dir = tmp_path / "data"
    persona_dir = data_dir / "persona"
    persona_dir.mkdir(parents=True)
    persona_dir.joinpath("dev.json").write_text(
        json.dumps({"nome": "Dev Backend", "cargo": "Engenheiro"}), encoding="utf-8"
    )

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: _get_settings(tmp_path),
    )

    result = runner.invoke(app, ["persona", "--list"])

    assert result.exit_code == 0, result.stdout
    assert "dev" in result.stdout
    assert "Dev Backend" in result.stdout


def test_persona_command_reprompts_invalid_name(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    client = DummyClient()

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: _get_settings(tmp_path, model="gpt"),
    )
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

    result = runner.invoke(
        app,
        ["persona"],
        input="   \n@@@\nAna Lider\nGerente de Produto\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n",
    )

    assert result.exit_code == 0, result.stderr
    assert "Nome da persona inválido" in result.stdout
    assert "Resultado salvo em" in result.stdout


def test_persona_command_requires_non_empty_cargo(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    client = DummyClient()

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: _get_settings(tmp_path),
    )
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

    result = runner.invoke(
        app,
        ["persona"],
        input="Ana Lider\n   \nGerente de Produto\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n",
    )

    assert result.exit_code == 0, result.stderr
    assert "O cargo/título profissional não pode ser vazio." in result.stdout


def test_persona_command_confirms_overwrite(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    client = DummyClient()
    data_dir = tmp_path / "data"
    output_path = data_dir / "persona" / "ana-lider.md"
    output_path.parent.mkdir(parents=True)
    output_path.write_text("anterior", encoding="utf-8")

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: _get_settings(tmp_path),
    )
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

    reject = runner.invoke(app, ["persona"], input="Ana Lider\nn\n")

    assert reject.exit_code == 0
    assert output_path.read_text(encoding="utf-8") == "anterior"
    assert "Operação cancelada." in reject.stdout

    accept = runner.invoke(
        app,
        ["persona"],
        input="Ana Lider\ns\nGerente de Produto\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n",
    )

    assert accept.exit_code == 0, accept.stderr
    # DummyClient returns "2" for prompt
    assert output_path.read_text(encoding="utf-8") == "2\n"


def test_persona_command_warns_when_cleanup_fails(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()

    class CleanupFailClient(DummyClient):
        async def chat(
            self, *, model_backend: str, messages: list[dict[str, str]], chat_id: str
        ) -> str:
            self.chat_calls.append((model_backend, chat_id, list(messages), None))
            return "# Persona\n"

        async def delete_chat(self, chat_id: str) -> None:
            raise RuntimeError("cleanup falhou")

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: _get_settings(tmp_path),
    )
    monkeypatch.setattr(
        cli_module, "create_client", lambda settings: CleanupFailClient()
    )

    result = runner.invoke(
        app,
        ["persona"],
        input="Ana Lider\nGerente de Produto\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n",
    )

    assert result.exit_code == 0, result.stderr
    assert "Falha ao limpar chat remoto: cleanup falhou" in result.stderr


def test_persona_command_accepts_custom_model_option(
    monkeypatch, tmp_path: Path
) -> None:
    runner = CliRunner()
    client = DummyClient()

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: _get_settings(tmp_path),
    )
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

    result = runner.invoke(
        app,
        ["persona", "--model", "gpt"],
        input="Ana Lider\nGerente de Produto\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n",
    )

    assert result.exit_code == 0, result.stderr
    assert client.chat_calls[0][0] == "GPT_54"


def test_persona_command_accepts_input_file(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    client = DummyClient()
    input_file = tmp_path / "persona.json"
    input_file.write_text(
        json.dumps(
            {"nome": "Ana Lider", "cargo": "Gerente de Produto", "setor": "SaaS"}
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: _get_settings(tmp_path),
    )
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

    result = runner.invoke(app, ["persona", "--input-file", str(input_file)])

    assert result.exit_code == 0, result.stderr
    data_dir = tmp_path / "data"
    assert (data_dir / "persona" / "ana-lider.md").exists()
    assert (data_dir / "persona" / "ana-lider.json").exists()


def test_persona_command_update_reuses_saved_json(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    client = DummyClient()
    data_dir = tmp_path / "data"
    persona_dir = data_dir / "persona"
    persona_dir.mkdir(parents=True)
    (persona_dir / "ana-lider.json").write_text(
        json.dumps(
            {
                "nome": "Ana Lider",
                "cargo": "Gerente de Produto",
                "setor": "SaaS",
            }
        ),
        encoding="utf-8",
    )
    (persona_dir / "ana-lider.md").write_text("anterior", encoding="utf-8")

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: _get_settings(tmp_path),
    )
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

    result = runner.invoke(
        app,
        ["persona", "--update"],
        input="Ana Lider\nAna Lider\ns\n\nMarketing\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n",
    )

    assert result.exit_code == 0, result.stderr
    saved_json = (persona_dir / "ana-lider.json").read_text(encoding="utf-8")
    assert '"setor": "Marketing"' in saved_json
