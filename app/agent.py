import os
from typing import TypedDict, Annotated, Sequence, Any, Dict, List, Optional
import operator
import json
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import ToolNode

from .tools import lookup_account, lookup_order, lookup_ticket, lookup_tickets_for_account
from .retrieval import search_documents
from .calculations import calculate_cancellation_fee, calculate_service_credit
from .actions import propose_escalation

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user: Dict[str, Any]
    
def build_tools(user: Dict[str, Any]):
    def _search_docs(query: str, account_id: Optional[str] = None) -> str:
        """Search policies, SOPs, and agreements."""
        res = search_documents(query, account_id)
        return json.dumps(res, default=str) if res else "No documents found."
        
    def _get_account(account_id: str) -> str:
        """Lookup account details by ID."""
        try:
            return json.dumps(lookup_account(user, account_id), default=str)
        except Exception as e:
            return str(e)
            
    def _get_order(order_id: str) -> str:
        """Lookup order by ID."""
        try:
            return json.dumps(lookup_order(user, order_id), default=str)
        except Exception as e:
            return str(e)
            
    def _get_ticket(ticket_id: str) -> str:
        """Lookup ticket by ID."""
        try:
            return json.dumps(lookup_ticket(user, ticket_id), default=str)
        except Exception as e:
            return str(e)

    def _calc_cancel_fee(order_id: str, cancel_request_time: str) -> str:
        """Calculate cancellation fee based on order status, booking time, and policies. Returns fee details."""
        try:
            order = lookup_order(user, order_id)
            if not order: return "Order not found or unauthorized."
            account = lookup_account(user, order["account_id"])
            return json.dumps(calculate_cancellation_fee(order, account, cancel_request_time), default=str)
        except Exception as e:
            return str(e)
            
    def _calc_service_credit(order_id: str, evaluation_time: str) -> str:
        """Calculate service credit for a late pickup."""
        try:
            order = lookup_order(user, order_id)
            if not order: return "Order not found or unauthorized."
            account = lookup_account(user, order["account_id"])
            return json.dumps(calculate_service_credit(order, account, evaluation_time), default=str)
        except Exception as e:
            return str(e)
            
    def _propose_escalation(account_id: str, ticket_id: str, reason: str, severity: str, summary: str) -> str:
        """Propose an escalation. This will prepare a pending action requiring explicit UI confirmation."""
        res = propose_escalation(user, account_id, ticket_id, reason, severity, summary)
        return json.dumps(res, default=str)

    return [
        StructuredTool.from_function(_search_docs, name="search_docs"),
        StructuredTool.from_function(_get_account, name="get_account"),
        StructuredTool.from_function(_get_order, name="get_order"),
        StructuredTool.from_function(_get_ticket, name="get_ticket"),
        StructuredTool.from_function(_calc_cancel_fee, name="calc_cancel_fee"),
        StructuredTool.from_function(_calc_service_credit, name="calc_service_credit"),
        StructuredTool.from_function(_propose_escalation, name="propose_escalation")
    ]

# We need a dynamic tool node because tools depend on user context
def dynamic_tool_node(state: AgentState):
    tools = build_tools(state["user"])
    tool_node = ToolNode(tools)
    return tool_node.invoke(state)

def call_model(state: AgentState):
    messages = state["messages"]
    user = state["user"]
    tools = build_tools(user)
    
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0).bind_tools(tools)
    
    # Prepend system prompt
    system_prompt = SystemMessage(content=f"""
You are the ParcelPilot AI Support Copilot.
You have access to tools for looking up accounts, orders, tickets, searching policies, and calculating fees/credits.
Current user role: {user.get('role', 'agent')}
Current dataset reference time: 2026-08-16 11:00 Asia/Kolkata

RULES:
1. Do not hardcode answers. Use the tools.
2. If data conflicts, use precedence: Customer Agreement > Current Policy > Guide.
3. Highlight your source of evidence when answering.
4. If you lack sufficient evidence to resolve something, explicitly state uncertainty and recommend escalation.
5. You cannot mutate data directly. You must use 'propose_escalation' which requires UI confirmation.
""")
    
    response = llm.invoke([system_prompt] + list(messages))
    return {"messages": [response]}

def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

# Build Graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", dynamic_tool_node)

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
workflow.add_edge("tools", "agent")

graph = workflow.compile()
