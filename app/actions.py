import uuid
from typing import Dict, Any
from .db import create_pending_action, get_pending_action, update_action_status
from .ingestion import store

def propose_escalation(user: Dict[str, Any], account_id: str, ticket_id: str, reason: str, severity: str, summary: str) -> Dict[str, Any]:
    action_id = str(uuid.uuid4())
    payload = {
        "account_id": account_id,
        "ticket_id": ticket_id,
        "reason": reason,
        "severity": severity,
        "summary": summary
    }
    create_pending_action(action_id, user.get("id"), "ESCALATE_TICKET", payload)
    return {
        "status": "PENDING_CONFIRMATION",
        "action_id": action_id,
        "message": "Action prepared. Please ask the user to confirm.",
        "proposed_action": payload
    }

def confirm_action(action_id: str) -> Dict[str, Any]:
    action = get_pending_action(action_id)
    if not action:
        return {"success": False, "message": "Action not found."}
    if action["status"] != "PENDING":
        return {"success": False, "message": f"Action already processed ({action['status']})."}
        
    # Execute mutation based on type
    if action["action_type"] == "ESCALATE_TICKET":
        ticket_id = action["payload"]["ticket_id"]
        if ticket_id in store.tickets:
            # We mutate the in-memory store for demo
            store.tickets[ticket_id].status = "escalated"
            store.tickets[ticket_id].notes = action["payload"]["summary"]
            update_action_status(action_id, "CONFIRMED")
            return {"success": True, "message": f"Ticket {ticket_id} escalated successfully."}
        else:
            update_action_status(action_id, "FAILED")
            return {"success": False, "message": "Ticket not found during execution."}
            
    return {"success": False, "message": "Unknown action type."}

def reject_action(action_id: str) -> Dict[str, Any]:
    action = get_pending_action(action_id)
    if not action or action["status"] != "PENDING":
        return {"success": False, "message": "Action not found or already processed."}
    
    update_action_status(action_id, "REJECTED")
    return {"success": True, "message": "Action cancelled."}
