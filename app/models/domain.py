from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class Account(BaseModel):
    account_id: str
    account_name: str
    plan: str
    status: str
    csm: str
    contract_file: Optional[str] = None
    premium_support: bool
    notes: Optional[str] = None

class Order(BaseModel):
    order_id: str
    account_id: str
    carrier: str
    status: str
    booked_at: datetime
    pickup_window_start: datetime
    pickup_window_end: datetime
    pickup_actual_at: Optional[datetime] = None
    shipment_fee_inr: float
    carrier_fault: bool
    customer_fault: bool
    cancellation_requested_at: Optional[datetime] = None
    notes: Optional[str] = None

class Ticket(BaseModel):
    ticket_id: str
    account_id: str
    created_at: datetime
    status: str
    subject: str
    description: str
    channel: str
    assigned_to: str
    last_customer_message_at: Optional[datetime] = None
    historical_resolution: Optional[str] = None

class DocumentMetadata(BaseModel):
    doc_id: str
    title: str
    doc_type: str
    status: str # e.g. CURRENT, DEPRECATED
    effective_date: Optional[datetime] = None
    customer_applicability: Optional[str] = None # e.g. ACCT-001
    authority_level: int # Lower number = higher authority (1=Agreement, 2=Policy, 3=Docs, 4=Historical)
    source_path: str

class DocumentChunk(BaseModel):
    chunk_id: str
    content: str
    metadata: DocumentMetadata
