"""Wires the academy as a LangGraph state machine with human-in-the-loop.

    planner -> teacher -> quizzer -> ask (interrupt) -> coach
                  ^                                       |
                  +--- re-teach (not mastered) -----------+
                  +--- advance (next concept) ------------+
                                                          +--> END (syllabus done)
"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .config import MAX_REMEDIATIONS
from .nodes import advance_node, ask_node, coach_node, planner_node, quizzer_node, teacher_node
from .state import AcademyState


def after_coach(state: AcademyState) -> str:
    done_with_concept = state["mastered"] or state["remediations"] > MAX_REMEDIATIONS
    if not done_with_concept:
        return "teacher"  # re-teach, targeting the coach's feedback
    if state["idx"] + 1 < len(state["syllabus"]):
        return "advance"
    return END


def build_graph(checkpointer=None):
    graph = StateGraph(AcademyState)
    graph.add_node("planner", planner_node)
    graph.add_node("teacher", teacher_node)
    graph.add_node("quizzer", quizzer_node)
    graph.add_node("ask", ask_node)
    graph.add_node("coach", coach_node)
    graph.add_node("advance", advance_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "teacher")
    graph.add_edge("teacher", "quizzer")
    graph.add_edge("quizzer", "ask")
    graph.add_edge("ask", "coach")
    graph.add_conditional_edges("coach", after_coach, ["teacher", "advance", END])
    graph.add_edge("advance", "teacher")

    # interrupt() requires a checkpointer to resume from.
    return graph.compile(checkpointer=checkpointer or MemorySaver())
