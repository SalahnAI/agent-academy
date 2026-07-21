"""Command-line entry point: `agent-academy "topic" [level]`."""

import sys

from langgraph.types import Command
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .config import NOTES_DIR
from .graph import build_graph

console = Console()


def _run_until_interrupt(graph, input_, config):
    """Stream the graph, displaying agent events, until it pauses or ends."""
    for update in graph.stream(input_, config, stream_mode="updates"):
        for node, payload in update.items():
            if node == "planner":
                syllabus = "\n".join(f"{i + 1}. {c}" for i, c in enumerate(payload["syllabus"]))
                console.print(Panel(syllabus, title="📋 your syllabus", border_style="magenta"))
                console.print("[cyan]👨‍🏫 Teacher — writing your lesson...[/cyan]")
            elif node == "coach":
                verdict = "mastered ✅" if payload["mastered"] else "not yet — re-teaching 🔁"
                console.print(
                    Panel(
                        f"score: {payload['score']}/100 — {verdict}\n\n{payload['feedback']}",
                        title="🧑‍⚖️ coach",
                        border_style="green" if payload["mastered"] else "red",
                    )
                )
            elif node == "advance":
                console.print("[cyan]👨‍🏫 Teacher — next concept...[/cyan]")
            elif node == "__interrupt__":
                return payload
    return None


def _collect_answers(questions: list[str]) -> list[str]:
    answers = []
    for i, q in enumerate(questions, 1):
        console.print(f"\n[bold yellow]Q{i}.[/bold yellow] {q}")
        try:
            answers.append(console.input("[bold]your answer › [/bold]"))
        except EOFError:
            answers.append("")
    return answers


def main() -> None:
    if len(sys.argv) < 2:
        console.print('Usage: agent-academy "topic to learn" [level]', style="bold red")
        raise SystemExit(1)

    topic = sys.argv[1]
    level = sys.argv[2] if len(sys.argv) > 2 else "beginner"
    console.print(
        Panel(f"[bold]Topic:[/bold] {topic}\n[bold]Level:[/bold] {level}", title="agent-academy 🎓")
    )

    graph = build_graph()
    config = {"configurable": {"thread_id": "study-session"}}

    console.print("[cyan]📋 Planner — building your syllabus...[/cyan]")
    pending = _run_until_interrupt(
        graph, {"topic": topic, "level": level, "idx": 0, "remediations": 0}, config
    )

    while pending:
        quiz = pending[0].value
        title = f"Lesson {quiz['progress']} — {quiz['concept']}"
        if quiz["is_remediation"]:
            title += "  (re-explained 🔁)"
        console.print(Panel(Markdown(quiz["lesson"]), title=title, border_style="cyan"))

        answers = _collect_answers(quiz["questions"])
        console.print("\n[cyan]🧑‍⚖️  Coach — grading your answers...[/cyan]")
        pending = _run_until_interrupt(graph, Command(resume=answers), config)

    console.rule("[bold green]Session complete")
    console.print(f"Your study notes are saved in [bold]{NOTES_DIR}/[/bold] 📚")


if __name__ == "__main__":
    main()
