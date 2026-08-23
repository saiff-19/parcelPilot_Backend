import os
import pandas as pd
import PyPDF2
from typing import List, Dict, Any
from datetime import datetime
from .models.domain import Account, Order, Ticket, DocumentMetadata, DocumentChunk

def load_xlsx_data(file_path: str) -> Dict[str, Any]:
    xls = pd.ExcelFile(file_path)
    
    # Load Accounts
    df_accounts = pd.read_excel(xls, sheet_name='accounts')
    accounts = []
    for _, row in df_accounts.iterrows():
        accounts.append(Account(
            account_id=str(row['account_id']),
            account_name=str(row['account_name']),
            plan=str(row['plan']),
            status=str(row['status']),
            csm=str(row['csm']),
            contract_file=str(row['contract_file']) if pd.notna(row['contract_file']) else None,
            premium_support=bool(row['premium_support']),
            notes=str(row['notes']) if pd.notna(row['notes']) else None
        ))
        
    # Load Orders
    df_orders = pd.read_excel(xls, sheet_name='orders')
    orders = []
    for _, row in df_orders.iterrows():
        orders.append(Order(
            order_id=str(row['order_id']),
            account_id=str(row['account_id']),
            carrier=str(row['carrier']),
            status=str(row['status']),
            booked_at=pd.to_datetime(row['booked_at']),
            pickup_window_start=pd.to_datetime(row['pickup_window_start']),
            pickup_window_end=pd.to_datetime(row['pickup_window_end']),
            pickup_actual_at=pd.to_datetime(row['pickup_actual_at']) if pd.notna(row['pickup_actual_at']) else None,
            shipment_fee_inr=float(row['shipment_fee_inr']),
            carrier_fault=bool(row['carrier_fault']),
            customer_fault=bool(row['customer_fault']),
            cancellation_requested_at=pd.to_datetime(row['cancellation_requested_at']) if pd.notna(row['cancellation_requested_at']) else None,
            notes=str(row['notes']) if pd.notna(row['notes']) else None
        ))
        
    # Load Tickets
    df_tickets = pd.read_excel(xls, sheet_name='tickets')
    tickets = []
    for _, row in df_tickets.iterrows():
        tickets.append(Ticket(
            ticket_id=str(row['ticket_id']),
            account_id=str(row['account_id']),
            created_at=pd.to_datetime(row['created_at']),
            status=str(row['status']),
            subject=str(row['subject']),
            description=str(row['description']),
            channel=str(row['channel']),
            assigned_to=str(row['assigned_to']),
            last_customer_message_at=pd.to_datetime(row['last_customer_message_at']) if pd.notna(row['last_customer_message_at']) else None,
            historical_resolution=str(row['historical_resolution']) if pd.notna(row['historical_resolution']) else None
        ))
        
    return {
        "accounts": {a.account_id: a for a in accounts},
        "orders": {o.order_id: o for o in orders},
        "tickets": {t.ticket_id: t for t in tickets}
    }


def ingest_documents(directory: str) -> List[DocumentChunk]:
    chunks = []
    for filename in os.listdir(directory):
        if not filename.endswith('.pdf'):
            continue
            
        filepath = os.path.join(directory, filename)
        
        # Determine metadata
        doc_type = "Policy"
        status = "CURRENT"
        authority = 2 # default to policy level
        applicability = None
        
        if "DEPRECATED" in filename:
            status = "DEPRECATED"
            authority = 5
        elif "SOP" in filename:
            doc_type = "SOP"
            authority = 2
        elif "Operations_Guide" in filename:
            doc_type = "Guide"
            authority = 3
        elif "Northstar" in filename:
            doc_type = "Agreement"
            authority = 1
            applicability = "ACCT-001"
        elif "LumenWorks" in filename:
            doc_type = "Agreement"
            authority = 1
            applicability = "ACCT-002"
            
        metadata = DocumentMetadata(
            doc_id=filename.replace('.pdf', ''),
            title=filename.replace('.pdf', '').replace('_', ' '),
            doc_type=doc_type,
            status=status,
            authority_level=authority,
            customer_applicability=applicability,
            source_path=filepath
        )
        
        text = ""
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
                
        # Split by paragraph
        # The PDF extraction had many newlines (e.g., one per word), so we need to fix it.
        # Let's split by double newline or numbered sections.
        # Actually, let's just do a basic split by number headers if we can, or just arbitrary chunks.
        # A simple chunking of fixed word length is safer if text is messy.
        words = text.split()
        chunk_size = 200
        for i in range(0, len(words), chunk_size):
            chunk_text = " ".join(words[i:i+chunk_size])
            if not chunk_text.strip():
                continue
            chunks.append(DocumentChunk(
                chunk_id=f"{metadata.doc_id}-chunk-{i//chunk_size}",
                content=chunk_text,
                metadata=metadata
            ))
            
    return chunks

class DataStore:
    def __init__(self):
        self.accounts = {}
        self.orders = {}
        self.tickets = {}
        self.document_chunks = []
        
    def load(self, resource_dir: str):
        xlsx_path = os.path.join(resource_dir, "ParcelPilot_Assessment_Data.xlsx")
        data = load_xlsx_data(xlsx_path)
        self.accounts = data["accounts"]
        self.orders = data["orders"]
        self.tickets = data["tickets"]
        self.document_chunks = ingest_documents(resource_dir)

store = DataStore()
