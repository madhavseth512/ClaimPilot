import operator
from typing import TypedDict, List, Optional, Annotated
from langgraph.graph import StateGraph, END


# ─── State Schema ─────────────────────────────────────────────────────────────

class ClaimState(TypedDict):
    user_id: str
    case_id: str
    intent: str
    required_docs: List[str]
    collected_docs: List[str]
    pending_docs: List[str]
    conversation_history: Annotated[List[dict], operator.add]
    case_status: str                    # active | complete | escalated
    is_new_user: bool
    current_query: Optional[str]
    last_response: Optional[str]
    input_type: Optional[str]           # text | file | resume
    claim_subtype: Optional[str]        # e.g. cashless, theft, accidental_death
    awaiting_subtype: bool              # True when waiting for sub-type answer
    last_uploaded_doc: Optional[str]    # document type label of most recently uploaded file


# ─── Document Checklists (IRDAI-sourced) ──────────────────────────────────────

DOCUMENT_CHECKLISTS = {
    "motor_claim": [
        "FIR Copy",
        "RC Book (Registration Certificate)",
        "Driving Licence",
        "Insurance Policy Copy",
        "Repair Estimate from Authorised Garage",
        "Claim Form",
    ],
    "health_claim": [
        "Claim Form",
        "Doctor's Prescription and Treatment Records",
        "Hospital Discharge Summary",
        "Original Bills and Receipts",
        "Lab Reports and Investigation Reports",
        "Insurance Policy Copy",
        "Photo ID Proof",
    ],
    "life_insurance": [
        "Original Policy Document",
        "Death Certificate",
        "Claim Form",
        "Photo ID and Address Proof of Nominee",
        "Bank Account Details of Nominee",
    ],
    "travel_insurance": [
        "Travel Insurance Policy Copy",
        "Travel Tickets and Boarding Passes",
        "Claim Form",
    ],
    "home_property": [
        "Insurance Policy Copy",
        "Claim Form",
        "FIR Copy",
        "Fire Brigade Report",
        "List of Damaged Items with Estimated Value",
        "Photographs of Damage",
        "Repair Estimates from Contractor",
        "Ownership Proof of Property",
    ],
    "personal_accident": [
        "Claim Form",
        "FIR or Accident Report",
        "Medical Certificate from Treating Doctor",
        "Hospital Bills and Discharge Summary",
        "Photo ID Proof",
        "Disability Certificate",
    ],
}

# Extra documents added based on claim sub-type answer
CONDITIONAL_DOCS = {
    ("health_claim",    "cashless"):         ["Pre-authorisation Form from Hospital"],
    ("health_claim",    "reimbursement"):    ["Bank Account Details for NEFT Transfer"],
    ("motor_claim",     "theft"):            ["Cancelled RC and NOC from Financer"],
    ("motor_claim",     "third_party"):      ["Court Summons (if applicable)"],
    ("life_insurance",  "accidental_death"): ["Post-mortem Report"],
    ("life_insurance",  "illness_death"):    ["Medical Attendant Certificate"],
}

# Follow-up question asked after confident intent classification
SUBTYPE_QUESTIONS = {
    "motor_claim": (
        "To confirm the complete document list — was this a theft, a third-party accident, "
        "or own damage only?\n"
        "  1. Theft\n"
        "  2. Third-party accident\n"
        "  3. Own damage only"
    ),
    "health_claim": (
        "Is this a cashless or reimbursement claim?\n"
        "  1. Cashless (hospital is on your insurer's network)\n"
        "  2. Reimbursement (you paid the bills yourself)"
    ),
    "life_insurance": (
        "What was the cause of death?\n"
        "  1. Accidental death\n"
        "  2. Death due to illness"
    ),
}

# Keywords used to parse the user's sub-type answer
SUBTYPE_KEYWORDS = {
    "motor_claim": {
        "theft":        ["theft", "stolen", "1"],
        "third_party":  ["third", "third-party", "accident", "someone", "another vehicle", "2"],
        "own_damage":   ["own", "damage", "self", "pole", "wall", "3"],
    },
    "health_claim": {
        "cashless":      ["cashless", "network", "1"],
        "reimbursement": ["reimburse", "reimbursement", "paid", "bills", "2"],
    },
    "life_insurance": {
        "accidental_death": ["accident", "accidental", "1"],
        "illness_death":    ["illness", "disease", "sick", "natural", "2"],
    },
}

ONBOARDING_MESSAGE = (
    "Hello! I am ClaimPilot, your personal insurance assistant.\n\n"
    "I can help you with:\n"
    "  1. Filing a new insurance claim\n"
    "  2. Checking on an existing claim\n"
    "  3. Answering general insurance queries\n\n"
    "To get started, could you tell me what brings you here today?\n"
    "You can describe your situation in your own words —\n"
    "for example: \"I had a car accident\" or \"I was hospitalised last week.\"\n\n"
    "I will guide you through the rest."
)


# ─── Helper ───────────────────────────────────────────────────────────────────

def _detect_subtype(intent: str, message: str) -> Optional[str]:
    message_lower = message.lower()
    for subtype, keywords in SUBTYPE_KEYWORDS.get(intent, {}).items():
        if any(kw in message_lower for kw in keywords):
            return subtype
    return None


# ─── Nodes ────────────────────────────────────────────────────────────────────

def onboarding_node(state: ClaimState) -> dict:
    return {
        "is_new_user": False,
        "last_response": ONBOARDING_MESSAGE,
        "conversation_history": [{"role": "assistant", "content": ONBOARDING_MESSAGE}],
    }


def session_resume_node(state: ClaimState) -> dict:
    pending = state.get("pending_docs", [])
    intent_label = state.get("intent", "insurance").replace("_", " ")

    if pending:
        pending_list = "\n".join(f"  - {doc}" for doc in pending)
        response = (
            f"Welcome back! Your {intent_label} claim is still in progress.\n"
            f"I'm still waiting for:\n{pending_list}\n\n"
            "Would you like to continue from where we left off?"
        )
    else:
        response = (
            f"Welcome back! Your {intent_label} claim is complete. "
            "Is there anything else I can help you with?"
        )

    return {
        "last_response": response,
        "conversation_history": [{"role": "assistant", "content": response}],
    }


def intent_classification_node(state: ClaimState) -> dict:
    from core.intent_classifier import IntentClassifier
    from db.postgres import SessionLocal, Case

    message = state.get("current_query", "")

    # ── Handle sub-type answer ────────────────────────────────────────────────
    if state.get("awaiting_subtype") and message:
        intent = state["intent"]
        subtype = _detect_subtype(intent, message)

        if subtype:
            extra_docs = CONDITIONAL_DOCS.get((intent, subtype), [])
            updated_pending = list(state["pending_docs"]) + extra_docs
            updated_required = list(state["required_docs"]) + extra_docs
            response = (
                f"Thank you. I've noted that this is a "
                f"{subtype.replace('_', ' ')} claim.\n"
                "Your complete document checklist is ready. Let's get started."
            )
            return {
                "claim_subtype": subtype,
                "awaiting_subtype": False,
                "pending_docs": updated_pending,
                "required_docs": updated_required,
                "last_response": response,
                "conversation_history": [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": response},
                ],
            }

        # Could not detect sub-type — ask again
        question = SUBTYPE_QUESTIONS.get(state["intent"], "")
        response = f"I didn't quite catch that. {question}"
        return {
            "last_response": response,
            "conversation_history": [
                {"role": "user", "content": message},
                {"role": "assistant", "content": response},
            ],
        }

    # ── Classify intent ───────────────────────────────────────────────────────
    classifier = IntentClassifier()
    result = classifier.classify(message)

    if not classifier.is_confident(result):
        response = (
            "I want to make sure I understand your situation correctly. "
            "Could you tell me a bit more about what happened?\n"
            "For example — was this related to your vehicle, health, home, or something else?"
        )
        return {
            "last_response": response,
            "conversation_history": [
                {"role": "user", "content": message},
                {"role": "assistant", "content": response},
            ],
        }

    intent = result["intent"]
    base_docs = list(DOCUMENT_CHECKLISTS.get(intent, []))
    intent_label = intent.replace("_", " ")

    # Persist Case to PostgreSQL
    db = SessionLocal()
    try:
        case = Case(
            case_id=state["case_id"],
            user_id=state["user_id"],
            intent=intent,
            case_status="active",
        )
        db.merge(case)
        db.commit()
    finally:
        db.close()

    # Intents with sub-types: ask follow-up before finalising checklist
    if intent in SUBTYPE_QUESTIONS:
        question = SUBTYPE_QUESTIONS[intent]
        response = f"I understand — this is a {intent_label} situation.\n\n{question}"
        return {
            "intent": intent,
            "required_docs": base_docs,
            "pending_docs": base_docs,
            "awaiting_subtype": True,
            "last_response": response,
            "conversation_history": [
                {"role": "user", "content": message},
                {"role": "assistant", "content": response},
            ],
        }

    # No sub-type needed (travel_insurance, home_property, personal_accident)
    response = (
        f"I understand — this is a {intent_label} situation.\n"
        f"I'll guide you through collecting the {len(base_docs)} required documents."
    )
    return {
        "intent": intent,
        "required_docs": base_docs,
        "pending_docs": base_docs,
        "awaiting_subtype": False,
        "last_response": response,
        "conversation_history": [
            {"role": "user", "content": message},
            {"role": "assistant", "content": response},
        ],
    }


def document_request_node(state: ClaimState) -> dict:
    pending = state.get("pending_docs", [])
    collected = state.get("collected_docs", [])
    intent_label = state.get("intent", "").replace("_", " ")

    if not pending:
        response = (
            f"I now have all the required documents for your {intent_label} claim.\n"
            "Your case has been submitted successfully.\n"
            "Is there anything else I can help you with?"
        )
        return {
            "case_status": "complete",
            "last_response": response,
            "conversation_history": [{"role": "assistant", "content": response}],
        }

    next_doc = pending[0]
    if not collected:
        response = (
            f"Let's start collecting your documents.\n\n"
            f"First, I'll need your {next_doc}.\n"
            "Please upload it when you are ready."
        )
    else:
        response = (
            f"Next, I'll need your {next_doc}.\n"
            "Please upload it when you are ready."
        )

    return {
        "last_response": response,
        "conversation_history": [{"role": "assistant", "content": response}],
    }


def document_processing_node(state: ClaimState) -> dict:
    """
    Triggered after the upload route has processed a file and updated
    collected_docs, pending_docs, and last_uploaded_doc in the state.
    Generates the combined acknowledgement + next document request.
    """
    last_doc = state.get("last_uploaded_doc", "document")
    pending = state.get("pending_docs", [])
    intent_label = state.get("intent", "").replace("_", " ")

    if pending:
        response = (
            f"Thank you, I've received your {last_doc}.\n"
            f"Next, I'll need your {pending[0]}.\n"
            "Please upload it when you are ready."
        )
        return {
            "last_response": response,
            "conversation_history": [{"role": "assistant", "content": response}],
        }

    response = (
        f"Thank you, I've received your {last_doc}.\n\n"
        f"I now have all the required documents for your {intent_label} claim.\n"
        "Your case has been submitted successfully.\n"
        "Is there anything else I can help you with?"
    )
    return {
        "case_status": "complete",
        "last_response": response,
        "conversation_history": [{"role": "assistant", "content": response}],
    }


def query_handling_node(state: ClaimState) -> dict:
    from core.query_router import QueryRouter
    from agents.query_responder import QueryResponder

    query = state.get("current_query", "")
    routing = QueryRouter().route(query)
    category = routing.get("category", "ambiguous")
    history = state.get("conversation_history", [])
    responder = QueryResponder()

    if category == "personal_doc":
        answer = responder.respond_from_user_docs(
            query=query,
            user_id=state["user_id"],
            case_id=state["case_id"],
            conversation_history=history,
        )
    elif category == "general_insurance":
        answer = responder.respond_from_irdai(
            query=query,
            conversation_history=history,
        )
    elif category == "off_topic":
        answer = (
            "I'm sorry, I can only assist with insurance-related queries. "
            "For other concerns, please reach out to the appropriate service.\n"
            "Is there anything related to your insurance claim I can help you with?"
        )
    else:  # ambiguous
        answer = (
            "I want to make sure I understand your question correctly. "
            "Could you provide a bit more detail — are you asking about your "
            "specific policy documents, or a general insurance question?"
        )

    # Remind user of pending document after answering
    pending = state.get("pending_docs", [])
    if pending and category not in ("off_topic", "ambiguous"):
        answer += (
            f"\n\nI hope that answers your question. "
            f"Coming back to your claim — I still need your {pending[0]}. "
            "Please upload it when you are ready."
        )

    return {
        "last_response": answer,
        "conversation_history": [
            {"role": "user", "content": query},
            {"role": "assistant", "content": answer},
        ],
    }


# ─── Routing Functions ────────────────────────────────────────────────────────

def _route_entry(state: ClaimState) -> str:
    if state.get("is_new_user", True):
        return "onboarding"

    input_type = state.get("input_type", "text")
    if input_type == "resume":
        return "session_resume"
    if input_type == "file":
        return "document_processing"

    intent = state.get("intent", "")
    if not intent or intent == "unknown" or state.get("awaiting_subtype"):
        return "intent_classification"

    return "query_handling"


def _route_after_intent(state: ClaimState) -> str:
    # Go to document_request only when intent is confirmed and sub-type is resolved
    if (
        state.get("intent")
        and state.get("intent") != "unknown"
        and not state.get("awaiting_subtype")
    ):
        return "document_request"
    return END


# ─── Graph Builder ────────────────────────────────────────────────────────────

def build_graph():
    from db.postgres import get_checkpointer

    graph = StateGraph(ClaimState)

    graph.add_node("router",                lambda state: {})
    graph.add_node("onboarding",            onboarding_node)
    graph.add_node("session_resume",        session_resume_node)
    graph.add_node("intent_classification", intent_classification_node)
    graph.add_node("document_request",      document_request_node)
    graph.add_node("document_processing",   document_processing_node)
    graph.add_node("query_handling",        query_handling_node)

    graph.set_entry_point("router")

    # Router dispatches to the correct node based on state
    graph.add_conditional_edges(
        "router",
        _route_entry,
        {
            "onboarding":            "onboarding",
            "session_resume":        "session_resume",
            "intent_classification": "intent_classification",
            "document_request":      "document_request",
            "document_processing":   "document_processing",
            "query_handling":        "query_handling",
        },
    )

    # After onboarding → wait for user to describe their situation
    graph.add_edge("onboarding", END)

    # After session_resume → ask for next pending document
    graph.add_edge("session_resume", "document_request")

    # After intent_classification → document_request if intent confirmed, else END
    graph.add_conditional_edges(
        "intent_classification",
        _route_after_intent,
        {"document_request": "document_request", END: END},
    )

    # After document_request → wait for upload or next message
    graph.add_edge("document_request", END)

    # After document_processing → wait for next message
    graph.add_edge("document_processing", END)

    # After query_handling → wait for next message
    graph.add_edge("query_handling", END)

    checkpointer = get_checkpointer()
    checkpointer.setup()
    return graph.compile(checkpointer=checkpointer)


# ─── Singleton accessor ───────────────────────────────────────────────────────

_compiled_graph = None


def get_graph():
    """Return the compiled LangGraph graph, building it once on first call."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def make_initial_state(user_id: str, case_id: str, message: str) -> dict:
    """Build the full initial ClaimState for a brand-new case thread."""
    return {
        "user_id": user_id,
        "case_id": case_id,
        "intent": "",
        "required_docs": [],
        "collected_docs": [],
        "pending_docs": [],
        "conversation_history": [],
        "case_status": "active",
        "is_new_user": True,
        "current_query": message,
        "last_response": None,
        "input_type": "text",
        "claim_subtype": None,
        "awaiting_subtype": False,
        "last_uploaded_doc": None,
    }
