from dotenv import load_dotenv
import os
from typing import TypedDict

# Load env
load_dotenv()

# LangGraph
from langgraph.graph import StateGraph, END

# LLM (LM Studio)
from langchain_openai import ChatOpenAI

# Your modules
from prompts import SYSTEM_PROMPT
from rag import retrieve_answer, create_vectorstore
from tools import mock_lead_capture


# ------------------ LLM SETUP ------------------
llm = ChatOpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio",  # dummy key
    model="mistral-7b-instruct-v0.1"
)

# ------------------ VECTOR DB ------------------
db = create_vectorstore()


# ------------------ STATE ------------------
class AgentState(TypedDict, total=False):
    input: str
    response: str
    lead: dict
    intent: str
    ask: str


# ------------------ NODE 1: AGENT ------------------
def agent_node(state: AgentState):
    user_input = state.get("input", "")
    prompt = SYSTEM_PROMPT + "\nUser: " + user_input

    response = llm.invoke(prompt)
    result = response.content if hasattr(response, "content") else str(response)

    intent = "general"
    response_text = result

    # Parse Intent + Response
    for line in result.split("\n"):
        if "Intent:" in line:
            intent = line.replace("Intent:", "").strip()
        elif "Response:" in line:
            response_text = line.replace("Response:", "").strip()
            
            # 🔥 ADD THIS BLOCK HERE
    user_input_lower = user_input.lower()

    if "join" in user_input_lower or "work" in user_input_lower or "buy" in user_input_lower:
        intent = "high_intent"
    elif "what" in user_input_lower or "how" in user_input_lower:
        intent = "question"
    elif "hi" in user_input_lower or "hello" in user_input_lower:
        intent = "greeting"
# 🔥 ADD THIS HERE
    if intent == "high_intent":
        return {
            "input": user_input,
            "lead": state.get("lead", {}),
            "intent": "high_intent",
            "response": None
        }
    return {
        "input": user_input,
        "response": response_text,
        "lead": state.get("lead", {}),
        "intent": intent
    }


# ------------------ NODE 2: RAG ------------------
def rag_node(state: AgentState):
    query = state.get("input", "")
    context = retrieve_answer(query, db)

    return {
        "input": state.get("input"),
        "response": context,
        "lead": state.get("lead", {})
    }


# ------------------ NODE 3: LEAD ------------------
def lead_node(state: AgentState):
    data = state.get("lead", {})

    if "name" not in data:
        return {"ask": "What is your name?", "lead": data}

    if "email" not in data:
        return {"ask": "What is your email?", "lead": data}

    if "platform" not in data:
        return {"ask": "Which platform do you use? (YouTube/Instagram)", "lead": data}

    # Final tool call
    result = mock_lead_capture(
        data["name"],
        data["email"],
        data["platform"]
    )

    return {
        "response": result,
        "lead": {},        # 🔥 reset lead after completion
        "intent": "done",
        "ask": None   # 🔥 mark flow complete
    }


# ------------------ GRAPH ------------------
def build_graph():
    builder = StateGraph(AgentState)

    # Nodes
    builder.add_node("agent", agent_node)
    builder.add_node("rag", rag_node)
    builder.add_node("lead", lead_node)

    # Entry
    builder.set_entry_point("agent")

    # 🔥 Routing function
    def route(state):
        if state.get("intent") == "done":
            return END
        if state.get("intent") == "question":
            return "rag"
        elif state.get("intent") == "high_intent":
            return "lead"
        else:
            return END

    # 🔥 IMPORTANT (this was your issue)
    builder.add_conditional_edges("agent", route)

    # Flow ends
    builder.add_edge("rag", END)
    builder.add_edge("lead", END)

    return builder.compile()