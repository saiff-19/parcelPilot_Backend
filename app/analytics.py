import pandas as pd
from .ingestion import store

def detect_proactive_issues():
    issues = []
    
    # 1. Ticket Clustering (Simple keyword based cluster)
    bulk_upload_tickets = [t for t in store.tickets.values() if "bulk upload" in t.subject.lower() or "csv" in t.subject.lower() or "failing" in t.subject.lower()]
    if len(bulk_upload_tickets) >= 2:
        issues.append({
            "issue_type": "CLUSTER",
            "title": "Multiple complaints regarding Shipment Creation / Bulk Upload",
            "severity": "High",
            "affected_accounts": list(set(t.account_id for t in bulk_upload_tickets)),
            "ticket_count": len(bulk_upload_tickets),
            "recommendation": "Check Operations Guide for known issues (KI-208) and inform engineering if impact is growing."
        })
        
    # 2. SLA Risk Detection
    snapshot_time = pd.to_datetime("2026-08-16 11:00")
    for t in store.tickets.values():
        if t.status == "open":
            age_hours = (snapshot_time - t.created_at).total_seconds() / 3600.0
            account = store.accounts.get(t.account_id)
            
            sla_breached = False
            if account:
                if account.plan == "Enterprise" and age_hours > 0.5:
                    sla_breached = True
                elif account.plan == "Growth" and age_hours > 4.0:
                    sla_breached = True
                elif account.plan == "Standard" and age_hours > 8.0:
                    sla_breached = True
            
            if sla_breached:
                issues.append({
                    "issue_type": "SLA_RISK",
                    "title": f"Ticket {t.ticket_id} nearing or breaching SLA",
                    "severity": "Critical" if account.plan == "Enterprise" else "High",
                    "affected_accounts": [t.account_id],
                    "ticket_count": 1,
                    "recommendation": f"Immediate escalation required. Account {account.account_name} is on {account.plan} plan."
                })
                
    return issues
