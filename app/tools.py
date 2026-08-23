from typing import Dict, Any, List, Optional
from .ingestion import store

class UnauthorizedAccess(Exception):
    pass

def verify_access(user: Dict[str, Any], account_id: str):
    # Support managers might have wildcard '*' access, but standard agents only specific accounts
    allowed = user.get("allowed_accounts", [])
    if "*" not in allowed and account_id not in allowed:
        print(f"SECURITY ALERT: User {user.get('id')} denied access to {account_id}")
        raise UnauthorizedAccess(f"User {user.get('id')} is not authorized to access account {account_id}")

def lookup_account(user: Dict[str, Any], account_id: str) -> Optional[Dict[str, Any]]:
    verify_access(user, account_id)
    account = store.accounts.get(account_id)
    return account.model_dump() if account else None

def lookup_order(user: Dict[str, Any], order_id: str) -> Optional[Dict[str, Any]]:
    order = store.orders.get(order_id)
    if order:
        verify_access(user, order.account_id)
        return order.model_dump()
    return None

def lookup_tickets_for_account(user: Dict[str, Any], account_id: str) -> List[Dict[str, Any]]:
    verify_access(user, account_id)
    tickets = [t.model_dump() for t in store.tickets.values() if t.account_id == account_id]
    return tickets

def lookup_orders_for_account(user: Dict[str, Any], account_id: str) -> List[Dict[str, Any]]:
    verify_access(user, account_id)
    orders = [o.model_dump() for o in store.orders.values() if o.account_id == account_id]
    return orders

def lookup_ticket(user: Dict[str, Any], ticket_id: str) -> Optional[Dict[str, Any]]:
    ticket = store.tickets.get(ticket_id)
    if ticket:
        verify_access(user, ticket.account_id)
        return ticket.model_dump()
    return None
