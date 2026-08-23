from typing import Dict, Any, List, Optional
from .ingestion import store

def lookup_account(account_id: str) -> Optional[Dict[str, Any]]:
    account = store.accounts.get(account_id)
    return account.model_dump() if account else None

def lookup_order(order_id: str) -> Optional[Dict[str, Any]]:
    order = store.orders.get(order_id)
    return order.model_dump() if order else None

def lookup_tickets_for_account(account_id: str) -> List[Dict[str, Any]]:
    tickets = [t.model_dump() for t in store.tickets.values() if t.account_id == account_id]
    return tickets

def lookup_orders_for_account(account_id: str) -> List[Dict[str, Any]]:
    orders = [o.model_dump() for o in store.orders.values() if o.account_id == account_id]
    return orders

def lookup_ticket(ticket_id: str) -> Optional[Dict[str, Any]]:
    ticket = store.tickets.get(ticket_id)
    return ticket.model_dump() if ticket else None
