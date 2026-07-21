"""Shared state passed between the agents of the academy."""

from typing import TypedDict


class AcademyState(TypedDict, total=False):
    topic: str            # what the learner wants to study
    level: str            # learner's self-declared level
    syllabus: list[str]   # ordered concepts chosen by the planner
    idx: int              # index of the concept being taught
    lesson: str           # current lesson written by the teacher
    questions: list[str]  # quiz for the current lesson
    answers: list[str]    # learner's answers (collected via interrupt)
    score: int            # coach's grade for the last quiz, 0-100
    mastered: bool        # coach's verdict on the current concept
    feedback: str         # coach's feedback (drives remediation)
    remediations: int     # re-teaching rounds used on the current concept
