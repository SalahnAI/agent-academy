"""The agents of the academy.

- planner: builds a short ordered syllabus for the topic
- teacher: writes the lesson (and re-teaches, targeting the coach's feedback)
- quizzer: generates a quiz on the lesson
- ask:     human-in-the-loop — the graph pauses until the learner answers
- coach:   grades the answers and decides mastered / re-teach
"""

import re

from langchain_anthropic import ChatAnthropic
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from .config import (
    LANGUAGE,
    MAX_TOKENS,
    MODEL_NAME,
    NOTES_DIR,
    NUM_CONCEPTS,
    NUM_QUESTIONS,
)
from .state import AcademyState

llm = ChatAnthropic(model=MODEL_NAME, max_tokens=MAX_TOKENS)

PLANNER_PROMPT = f"""You are a curriculum designer. Break the topic below into
an ordered syllabus of exactly {NUM_CONCEPTS} concepts for one study session,
from foundations to more advanced, tailored to the learner's level. Each
concept is a short title (a few words)."""

TEACHER_PROMPT = f"""You are a passionate teacher. Write a focused lesson
(300-500 words, markdown) in {LANGUAGE} on the concept below, for the given
learner level. Use one concrete analogy, one worked example, and end with a
'Key takeaways' list. Output only the lesson."""

RETEACH_PROMPT = f"""You are a patient teacher. Your student did NOT master
this concept — the coach's diagnosis of their gaps is below. Re-explain the
concept in {LANGUAGE} DIFFERENTLY: new angle, simpler analogy, address each
gap explicitly. Output only the lesson."""

QUIZZER_PROMPT = f"""You are an examiner. From the lesson below, write exactly
{NUM_QUESTIONS} short open questions in {LANGUAGE} testing understanding (not
memorization): at least one 'explain in your own words' and one application
question. Questions only — no answers."""

COACH_PROMPT = f"""You are a learning coach. Grade the learner's answers
against the lesson. Be encouraging but honest: a vague or empty answer is not
mastery. Write your feedback in {LANGUAGE}: what was right, what is missing,
one tip. Declare the concept mastered only if the answers show real
understanding (score >= 70)."""


class Syllabus(BaseModel):
    concepts: list[str] = Field(description=f"Exactly {NUM_CONCEPTS} ordered concept titles")


class Quiz(BaseModel):
    questions: list[str] = Field(description=f"Exactly {NUM_QUESTIONS} open questions")


class Grade(BaseModel):
    score: int = Field(description="Overall grade 0-100")
    mastered: bool = Field(description="True only if answers show real understanding")
    feedback: str = Field(description="Encouraging, specific feedback with the gaps to fix")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:50]


def planner_node(state: AcademyState) -> AcademyState:
    planner = llm.with_structured_output(Syllabus)
    result = planner.invoke(
        f"{PLANNER_PROMPT}\n\nTopic: {state['topic']}\nLearner level: {state['level']}"
    )
    return {"syllabus": result.concepts[:NUM_CONCEPTS]}


def teacher_node(state: AcademyState) -> AcademyState:
    concept = state["syllabus"][state["idx"]]
    if state.get("feedback"):
        prompt = (
            f"{RETEACH_PROMPT}\n\nTopic: {state['topic']}\nConcept: {concept}"
            f"\nLearner level: {state['level']}"
            f"\n\n# Previous lesson\n{state['lesson']}"
            f"\n\n# Coach's diagnosis\n{state['feedback']}"
        )
    else:
        prompt = (
            f"{TEACHER_PROMPT}\n\nTopic: {state['topic']}\nConcept: {concept}"
            f"\nLearner level: {state['level']}"
        )
    lesson = llm.invoke(prompt).content

    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    suffix = f"-bis{state['remediations']}" if state.get("feedback") else ""
    (NOTES_DIR / f"{state['idx']:02d}-{_slug(concept)}{suffix}.md").write_text(
        f"# {concept}\n\n{lesson}\n"
    )
    return {"lesson": lesson}


def quizzer_node(state: AcademyState) -> AcademyState:
    quizzer = llm.with_structured_output(Quiz)
    result = quizzer.invoke(f"{QUIZZER_PROMPT}\n\n# Lesson\n{state['lesson']}")
    return {"questions": result.questions[:NUM_QUESTIONS]}


def ask_node(state: AcademyState) -> AcademyState:
    # Pauses the graph; the CLI resumes it with the learner's answers.
    answers = interrupt(
        {
            "concept": state["syllabus"][state["idx"]],
            "progress": f"{state['idx'] + 1}/{len(state['syllabus'])}",
            "is_remediation": bool(state.get("feedback")),
            "lesson": state["lesson"],
            "questions": state["questions"],
        }
    )
    return {"answers": [str(a) for a in answers]}


def coach_node(state: AcademyState) -> AcademyState:
    qa = "\n\n".join(
        f"Q{i + 1}: {q}\nAnswer: {a or '(no answer)'}"
        for i, (q, a) in enumerate(zip(state["questions"], state["answers"]))
    )
    coach = llm.with_structured_output(Grade)
    grade = coach.invoke(f"{COACH_PROMPT}\n\n# Lesson\n{state['lesson']}\n\n# Quiz\n{qa}")
    update: AcademyState = {
        "score": grade.score,
        "mastered": grade.mastered,
        "feedback": grade.feedback,
    }
    if not grade.mastered:
        update["remediations"] = state.get("remediations", 0) + 1
    return update


def advance_node(state: AcademyState) -> AcademyState:
    # Move to the next concept with a clean slate.
    return {"idx": state["idx"] + 1, "feedback": "", "remediations": 0, "mastered": False}
