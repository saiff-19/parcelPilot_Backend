from typing import Dict, Any
import pandas as pd

def calculate_cancellation_fee(order: Dict[str, Any], account: Dict[str, Any], cancel_request_time: str) -> Dict[str, Any]:
    status = order.get("status")
    if status == "DELIVERED":
        return {"eligible": False, "fee": 0, "reason": "DELIVERED orders cannot be cancelled."}
    
    if status == "PICKED_UP":
        return {"eligible": False, "fee": 0, "reason": "PICKED_UP orders cannot be cancelled. Use return-to-origin workflow."}
    
    booked_at = pd.to_datetime(order.get("booked_at"))
    req_time = pd.to_datetime(cancel_request_time)
    
    if account.get("account_id") == "ACCT-001":
        return {"eligible": True, "fee": 0, "reason": "Northstar Enterprise Agreement waives cancellation fee for BOOKED shipments."}
        
    if status == "DRAFT":
        return {"eligible": True, "fee": 0, "reason": "DRAFT orders can be cancelled with no fee."}
        
    time_diff = (req_time - booked_at).total_seconds() / 60.0
    if time_diff <= 30:
        return {"eligible": True, "fee": 0, "reason": "Cancelled within 30 minutes of booking (SOP)."}
    else:
        return {"eligible": True, "fee": 250, "reason": "Cancelled after 30 minutes of booking (SOP default fee)."}

def calculate_service_credit(order: Dict[str, Any], account: Dict[str, Any], evaluation_time: str) -> Dict[str, Any]:
    if not order.get("carrier_fault") or order.get("customer_fault"):
        return {"eligible": False, "amount": 0, "reason": "Service credit requires carrier fault and no customer fault."}
        
    pickup_window_end = pd.to_datetime(order.get("pickup_window_end"))
    
    if order.get("pickup_actual_at") and not pd.isna(order.get("pickup_actual_at")):
        actual = pd.to_datetime(order.get("pickup_actual_at"))
    else:
        actual = pd.to_datetime(evaluation_time)
        
    delay_hours = (actual - pickup_window_end).total_seconds() / 3600.0
    
    if account.get("account_id") == "ACCT-002":
        if delay_hours > 4:
            return {"eligible": True, "amount": 300, "reason": "LumenWorks Service Agreement: > 4h delay = INR 300 credit."}
        else:
            return {"eligible": False, "amount": 0, "reason": "LumenWorks Service Agreement: delay must be > 4h for credit."}
            
    if delay_hours > 2:
        fee = order.get("shipment_fee_inr", 0)
        amount = min(500, 0.10 * fee)
        return {"eligible": True, "amount": amount, "reason": f"SOP default: > 2h delay = min(500, 10% of {fee})."}
    else:
        return {"eligible": False, "amount": 0, "reason": "SOP default: delay must be > 2h for credit."}
