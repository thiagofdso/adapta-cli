from __future__ import annotations

from pathlib import Path

from adapta.models import DebateResult


def persist_output(text: str, output_path: Path | None) -> None:
    if output_path is None:
        return
    output_path.write_text(text, encoding="utf-8")


def format_debate_result(result: DebateResult) -> str:
    lines = ["# Debate Results", "", "## Topic", "", result.config.topic_prompt, ""]

    lines.extend(["## Agents", ""])
    for agent in result.config.agents:
        lines.append(f"- {agent.agent_id} ({agent.model_key})")
    lines.append("")

    for debate_round in result.rounds:
        lines.extend([f"## Round {debate_round.round_number}", ""])
        for turn in debate_round.turns:
            lines.extend(
                [
                    f"### {turn.agent_id} ({turn.model_key})",
                    "",
                    turn.response_text,
                    "",
                ]
            )

    lines.extend(["## Final Conclusion", "", result.final_conclusion, ""])

    if result.cleanup_warnings:
        lines.extend(["## Cleanup Warnings", ""])
        for warning in result.cleanup_warnings:
            lines.append(f"- {warning}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"
