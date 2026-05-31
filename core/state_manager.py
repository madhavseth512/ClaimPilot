import operator
from typing import TypedDict, List, Optional, Annotated
from langgraph.graph import StateGraph, END


class ClaimState(TypedDict):
    user_id: str
    case_id: str
    intent: str
    required_docs: List[str]
    collected_docs: List[str]
    pending_docs: List[str]
    conversation_history: Annotated[List[dict], operator.add]
    case_status: str          # active | complete | escalated
    is_new_user: bool
    current_query: Optional[str]
    last_response: Optional[str]


# Graph nodes — implemented in Phase 6
def onboarding_node(state: ClaimState) -> ClaimState:
    raise NotImplementedError("Implemented in Phase 6")


def intent_classification_node(state: ClaimState) -> ClaimState:
    raise NotImplementedError("Implemented in Phase 6")


def document_request_node(state: ClaimState) -> ClaimState:
    raise NotImplementedError("Implemented in Phase 6")


def document_processing_node(state: ClaimState) -> ClaimState:
    raise NotImplementedError("Implemented in Phase 6")


def query_handling_node(state: ClaimState) -> ClaimState:
    raise NotImplementedError("Implemented in Phase 6")


def session_resume_node(state: ClaimState) -> ClaimState:
    raise NotImplementedError("Implemented in Phase 6")


def build_graph() -> StateGraph:
    graph = StateGraph(ClaimState)

    graph.add_node("onboarding", onboarding_node)
    graph.add_node("intent_classification", intent_classification_node)
    graph.add_node("document_request", document_request_node)
    graph.add_node("document_processing", document_processing_node)
    graph.add_node("query_handling", query_handling_node)
    graph.add_node("session_resume", session_resume_node)

    # Edges defined in Phase 6
    graph.set_entry_point("onboarding")

    return graph
