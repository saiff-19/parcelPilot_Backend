import pytest
from app.ingestion import store
from app.tools import lookup_account, lookup_order, UnauthorizedAccess
from app.retrieval import search_documents
from app.calculations import calculate_cancellation_fee, calculate_service_credit
from app.actions import propose_escalation, confirm_action

@pytest.fixture(autouse=True)
def setup_store():
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    resource_dir = os.path.join(os.path.dirname(base_dir), "resourcePack")
    store.load(resource_dir)

def test_data_lookup():
    user = {"id": "test", "role": "admin", "allowed_accounts": ["*"]}
    acc = lookup_account(user, "ACCT-001")
    assert acc["account_name"] == "Northstar Logistics"
    
def test_security():
    user = {"id": "test", "role": "agent", "allowed_accounts": ["ACCT-001"]}
    with pytest.raises(UnauthorizedAccess):
        lookup_account(user, "ACCT-002")
    
    # Try looking up order for unauthorized account
    with pytest.raises(UnauthorizedAccess):
        lookup_order(user, "ORD-2001") # ORD-2001 belongs to ACCT-002

def test_retrieval_precedence():
    res = search_documents("cancellation fee", "ACCT-001")
    assert len(res) > 0
    # Northstar agreement should be ranked highest (authority 1)
    assert res[0]["metadata"]["doc_type"] == "Agreement"
    assert res[0]["metadata"]["authority_level"] == 1

def test_reasoning_calculations():
    # ACCT-001 has no cancellation fee due to agreement
    user = {"id": "test", "role": "admin", "allowed_accounts": ["*"]}
    acc = lookup_account(user, "ACCT-001")
    order = lookup_order(user, "ORD-1001")
    fee = calculate_cancellation_fee(order, acc, "2026-08-16 11:00")
    assert fee["fee"] == 0
    assert fee["eligible"] == True
    
def test_action_workflow():
    user = {"id": "test", "role": "admin", "allowed_accounts": ["*"]}
    action = propose_escalation(user, "ACCT-001", "TKT-501", "Test", "High", "Sum")
    assert action["status"] == "PENDING_CONFIRMATION"
    
    res = confirm_action(action["action_id"])
    assert res["success"] == True
    assert store.tickets["TKT-501"].status == "escalated"
