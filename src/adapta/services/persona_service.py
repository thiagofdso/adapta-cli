from __future__ import annotations

import json
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

from adapta.registry import get_model_option
from adapta.services.chat_service import create_chat_session, send_chat_message
from adapta.services.output_service import persist_output


DEFAULT_PERSONA_MODEL_KEY = "claude"
PERSONA_HOME_DIRNAME = ".adapta"
PERSONA_OUTPUT_DIRNAME = "persona"
PERSONA_CONTENT_START = "<<<PERSONA_CONTENT_START>>>"
PERSONA_CONTENT_END = "<<<PERSONA_CONTENT_END>>>"

PERSONA_BLOCKS: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] = (
    (
        "Bloco 1: Identidade & Contexto Profissional",
        (
            ("nome", "Qual é o nome da persona?"),
            ("cargo", "Qual é o cargo/título profissional?"),
            ("setor", "Em qual setor/indústria ela trabalha?"),
            ("idade", "Qual é a faixa etária?"),
            (
                "tamanho_empresa",
                "Qual é o tamanho da empresa onde ela trabalha? (startup, PME, enterprise)",
            ),
        ),
    ),
    (
        "Bloco 2: Contexto Psicológico & Valores",
        (
            ("valores", "Quais são seus 3 valores profissionais principais?"),
            ("comunicacao", "Qual é o estilo de comunicação preferido?"),
            ("senioridade", "Qual é o nível de experiência/senioridade?"),
        ),
    ),
    (
        "Bloco 3: Objetivos, Esperanças & Aspirações",
        (
            (
                "objetivo_6_12m",
                "Qual é o objetivo principal dela no trabalho (próximos 6-12 meses)?",
            ),
            ("aspiracao_3_5a", "O que ela quer alcançar em 3-5 anos?"),
            ("dia_perfeito", 'Qual seria um "dia de trabalho perfeito" para ela?'),
        ),
    ),
    (
        "Bloco 4: Dores, Medos & Frustrações",
        (
            ("dores", "Quais são seus 3 maiores problemas/dores no dia a dia?"),
            ("tira_sono", 'O que "tira o sono" dela profissionalmente?'),
            ("medos", "Quais são seus maiores medos ou ansiedades?"),
        ),
    ),
    (
        "Bloco 5: Comportamento & Personalidade",
        (
            (
                "forma_trabalho",
                "Como ela prefere trabalhar? (independente, colaborativo, híbrido)",
            ),
            (
                "inovacao",
                "Qual é seu nível de abertura para inovação e mudanças?",
            ),
            (
                "aprendizado",
                "Como ela aprende melhor? (prática, teórica, mentoria, autodidata)",
            ),
        ),
    ),
    (
        "Bloco 6: Voz & Maneirismos",
        (
            (
                "tom_voz",
                "Qual é o tom de voz dela? (formal, descontraído, direto, empático)",
            ),
            ("maneirismos", "Quais são seus maneirismos ou expressões típicas?"),
            ("motiva_desmotiva", "O que a motiva e o que a desmotiva?"),
        ),
    ),
)

PERSONA_PROMPT_TEMPLATE = """VOCÊ É UM GERADOR INTELIGENTE DE PROMPTS DE PERSONA

Sua tarefa: Receber dados INCOMPLETOS sobre uma persona e gerar um prompt
que seja ROBUSTO, ADAPTADO e COERENTE - usando APENAS os dados fornecidos.

---

REGRAS CRÍTICAS:

1. **NÃO invente dados:** Se um campo está vazio, não preencha com suposições.
2. **Adapte a estrutura:** Se faltam dados, a persona fica mais concisa, mas sempre autêntica.
3. **Priorize o que existe:** Foque nos dados fornecidos; construa a persona a partir deles.
4. **Coerência interna:** Conecte logicamente os dados existentes (não deixe contradições).
5. **Humanização:** Mesmo com dados escassos, a persona deve "respirar" - parecer real.

---

DADOS RECEBIDOS (em formato JSON):

__PERSONA_PAYLOAD_JSON__

---

ALGORITMO DE GERAÇÃO:

1. **Verificar quais campos foram preenchidos**
2. **Criar estrutura dinâmica:** Incluir APENAS seções com dados
3. **Conectar dados existentes:** Se há objetivo mas não aspiração, ainda assim criar fluxo coerente
4. **Gerar instruções para o agente:** Baseadas APENAS no que existe
5. **Exemplo de resposta:** Contextualizar ao que foi fornecido

---

ESTRUTURA DO PROMPT DE SAÍDA (Adaptativa):

Saída obrigatória:

{start_delimiter}

[INÍCIO DO PROMPT DE PERSONA]

# Você é {NOME_OU_SKIP}

{SE NOME_VAZIO: "# Você"}

## {SEÇÃO INCLUÍDA SÓ SE HOUVER DADOS}
Identidade Profissional

{SE cargo PREENCHIDO: "- **Cargo:** {cargo}"}
{SE setor PREENCHIDO: "- **Setor:** {setor}"}
{SE idade PREENCHIDO: "- **Idade:** {idade}"}
{SE tamanho_empresa PREENCHIDO: "- **Empresa:** {tamanho_empresa}"}
{SE senioridade PREENCHIDO: "- **Experiência:** {senioridade}"}
{SE valores PREENCHIDO: "- **Valores:** {valores}"}

## {SEÇÃO INCLUÍDA SÓ SE HOUVER DADOS}
O Que Você Quer

{SE objetivo_6_12m PREENCHIDO: "**Seus objetivos (6-12 meses):** {objetivo_6_12m}"}
{SE aspiracao_3_5a PREENCHIDO: "**Suas aspirações (3-5 anos):** {aspiracao_3_5a}"}
{SE dia_perfeito PREENCHIDO: "**Seu ideal de trabalho:** {dia_perfeito}"}

## {SEÇÃO INCLUÍDA SÓ SE HOUVER DADOS}
Seus Desafios

{SE dores PREENCHIDO: "**Dores no dia a dia:** {dores}"}
{SE tira_sono PREENCHIDO: "**O que tira seu sono:** {tira_sono}"}
{SE medos PREENCHIDO: "**Medos/ansiedades:** {medos}"}

## {SEÇÃO INCLUÍDA SÓ SE HOUVER DADOS}
Como Você É

{SE tom_voz PREENCHIDO: "**Tom de voz:** {tom_voz}"}
{SE maneirismos PREENCHIDO: "**Maneirismos:** {maneirismos}"}
{SE comunicacao PREENCHIDO: "**Estilo de comunicação:** {comunicacao}"}
{SE forma_trabalho PREENCHIDO: "**Forma de trabalho:** {forma_trabalho}"}
{SE inovacao PREENCHIDO: "**Abertura à inovação:** {inovacao}"}
{SE aprendizado PREENCHIDO: "**Como aprende:** {aprendizado}"}
{SE motiva_desmotiva PREENCHIDO: "**Motiva/desmotiva:** {motiva_desmotiva}"}

---

## Instruções para o Agente

1. **Seja autêntico:** Responda como essa persona responderia.
2. **Respeite o escopo:** Use APENAS as características fornecidas.
3. **Preencha silenciosamente:** Onde há lacunas, deixe a persona ser naturalmente flexível.
4. **Profundidade nas respostas:** Mesmo com dados limitados, mostre pensamento crítico.

{SE FEW_DADOS: "⚠️ **Nota:** Essa persona foi criada com dados limitados. Adapte-se conforme aprende mais sobre o contexto."}

---

## Exemplo de Resposta

Se perguntarem algo relevante:

Uma resposta autêntica seria:
"{EXEMPLO_COERENTE_COM_DADOS_FORNECIDOS}"

[FIM DO PROMPT DE PERSONA]

{end_delimiter}

---

INSTRUÇÕES FINAIS PARA O GERADOR:

✅ **Inclusão dinâmica:** Sempre teste se há dados antes de incluir uma seção
✅ **Sem preenchimento:** Nunca invente valores para campos vazios
✅ **Coerência:** Se há objetivo mas não aspiração, use o objetivo para contextualizar
✅ **Tom natural:** O prompt deve ser legível e natural, não robótico
✅ **Aviso discreto:** Se dados são muito escassos (< 5 campos), avise sutilmente
✅ **Sem prefácio:** Não explique o que você vai fazer. Retorne apenas o conteúdo entre os delimitadores informados
"""


@dataclass(frozen=True)
class PersonaQuestionnaire:
    nome: str
    cargo: str
    setor: str = ""
    idade: str = ""
    tamanho_empresa: str = ""
    valores: str = ""
    comunicacao: str = ""
    senioridade: str = ""
    objetivo_6_12m: str = ""
    aspiracao_3_5a: str = ""
    dia_perfeito: str = ""
    dores: str = ""
    tira_sono: str = ""
    medos: str = ""
    forma_trabalho: str = ""
    inovacao: str = ""
    aprendizado: str = ""
    tom_voz: str = ""
    maneirismos: str = ""
    motiva_desmotiva: str = ""


@dataclass(frozen=True)
class PersonaGenerationResult:
    text: str
    cleanup_warning: str | None = None


def questionnaire_to_dict(questionnaire: PersonaQuestionnaire) -> dict[str, str]:
    return asdict(questionnaire)


def normalize_persona_name(name: str) -> tuple[str, str]:
    display_name = name.strip()
    if not display_name:
        raise ValueError("Nome da persona inválido: informe um valor não vazio.")

    normalized = unicodedata.normalize("NFKD", display_name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    slug_chars = []
    last_was_dash = False
    for char in ascii_name.lower():
        if char.isalnum():
            slug_chars.append(char)
            last_was_dash = False
            continue
        if not last_was_dash:
            slug_chars.append("-")
            last_was_dash = True
    slug = "".join(slug_chars).strip("-")
    if not slug:
        raise ValueError("Nome da persona inválido: use letras ou números.")
    return display_name, slug


def build_persona_questionnaire(**answers: str) -> PersonaQuestionnaire:
    nome = answers.get("nome", "")
    cargo = (answers.get("cargo") or "").strip()
    display_name, _ = normalize_persona_name(nome)
    if not cargo:
        raise ValueError("O campo cargo/título profissional não pode ser vazio.")

    cleaned = {
        field: (answers.get(field) or "").strip()
        for field in PersonaQuestionnaire.__dataclass_fields__
    }
    cleaned["nome"] = display_name
    cleaned["cargo"] = cargo
    return PersonaQuestionnaire(**cleaned)


def get_persona_directory(home_path: Path | None = None) -> Path:
    base_path = home_path if home_path is not None else Path.home()
    return (
        (base_path / PERSONA_HOME_DIRNAME / PERSONA_OUTPUT_DIRNAME)
        .expanduser()
        .resolve()
    )


def resolve_persona_answers_path(name: str, home_path: Path | None = None) -> Path:
    _, slug = normalize_persona_name(name)
    return (get_persona_directory(home_path) / f"{slug}.json").resolve()


def resolve_persona_output_path(name: str, home_path: Path | None = None) -> Path:
    _, slug = normalize_persona_name(name)
    return (get_persona_directory(home_path) / f"{slug}.md").resolve()


def build_persona_prompt(questionnaire: PersonaQuestionnaire) -> str:
    payload_json = json.dumps(asdict(questionnaire), ensure_ascii=False, indent=2)
    return (
        PERSONA_PROMPT_TEMPLATE.replace("__PERSONA_PAYLOAD_JSON__", payload_json)
        .replace("{start_delimiter}", PERSONA_CONTENT_START)
        .replace("{end_delimiter}", PERSONA_CONTENT_END)
    )


def extract_persona_content(raw_text: str) -> str:
    text = raw_text.strip()
    start_index = text.find(PERSONA_CONTENT_START)
    end_index = text.find(PERSONA_CONTENT_END)
    if start_index != -1 and end_index != -1 and end_index > start_index:
        start = start_index + len(PERSONA_CONTENT_START)
        extracted = text[start:end_index].strip()
        if extracted:
            return extracted + "\n"

    for marker in ("# Você é", "# Você"):
        marker_index = text.find(marker)
        if marker_index != -1:
            extracted = text[marker_index:].strip()
            if extracted:
                return extracted + "\n"

    if not text:
        raise RuntimeError("A geração da persona retornou conteúdo vazio.")
    return text + "\n"


def load_persona_questionnaire_from_file(input_file: Path) -> PersonaQuestionnaire:
    if not input_file.exists() or not input_file.is_file():
        raise ValueError(f"Arquivo JSON não encontrado: {input_file}")
    try:
        payload = json.loads(input_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Arquivo JSON inválido: {input_file}") from exc
    if not isinstance(payload, dict):
        raise ValueError("O arquivo JSON da persona deve conter um objeto.")
    normalized_payload = {
        field: str(payload.get(field, "") or "")
        for field in PersonaQuestionnaire.__dataclass_fields__
    }
    return build_persona_questionnaire(**normalized_payload)


async def generate_persona_document(
    client,
    questionnaire: PersonaQuestionnaire,
    model_key: str = DEFAULT_PERSONA_MODEL_KEY,
) -> PersonaGenerationResult:
    option = get_model_option(model_key)
    session = create_chat_session(option.key)
    text: str | None = None
    cleanup_warning: str | None = None
    try:
        text = await send_chat_message(
            client,
            session,
            model_backend=option.backend_name,
            prompt_text=build_persona_prompt(questionnaire),
        )
        if not text.strip():
            raise RuntimeError("A geração da persona retornou conteúdo vazio.")
        text = extract_persona_content(text)
    finally:
        try:
            if session.cleanup_required:
                await client.delete_chat(session.chat_id)
        except Exception as exc:  # noqa: BLE001
            cleanup_warning = f"Falha ao limpar chat remoto: {exc}"
    if text is None:
        raise RuntimeError("A geração da persona não retornou conteúdo.")
    return PersonaGenerationResult(text=text, cleanup_warning=cleanup_warning)


def save_persona_document(text: str, output_path: Path, *, overwrite: bool) -> Path:
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Arquivo já existe: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    persist_output(text, output_path)
    return output_path


def save_persona_answers(
    questionnaire: PersonaQuestionnaire, output_path: Path, *, overwrite: bool
) -> Path:
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Arquivo já existe: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(questionnaire_to_dict(questionnaire), ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    return output_path
