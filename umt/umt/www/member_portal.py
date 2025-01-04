import frappe
from frappe import _

def get_context(context):
    """Add member data to the context"""
    if frappe.session.user != 'Guest':
        context.member = get_member_info()
        context.activities = get_recent_activities()
    return context

def get_member_info():
    """Get member information for the logged-in user"""
    user = frappe.session.user
    member = frappe.get_all(
        "Member",
        filters={"user": user},
        fields=[
            "name", "full_name", "membership_status", "membership_date",
            "province", "current_card", "card_expiry"
        ]
    )
    
    if member:
        return member[0]
    return None

def get_recent_activities():
    """Get recent activities for the member"""
    user = frappe.session.user
    activities = []
    
    # Get membership activities
    membership_logs = frappe.get_all(
        "Member Log",
        filters={"member": get_member_info().name},
        fields=["date", "activity_type", "description"],
        order_by="date desc",
        limit=5
    )
    
    # Get payment activities
    payment_logs = frappe.get_all(
        "Payment Entry",
        filters={"member": get_member_info().name},
        fields=["posting_date as date", "payment_type", "amount"],
        order_by="posting_date desc",
        limit=5
    )
    
    # Format payment activities
    for payment in payment_logs:
        activities.append({
            "date": payment.date,
            "description": _("دفع {0} درهم - {1}").format(
                payment.amount,
                payment.payment_type
            )
        })
    
    # Format membership activities
    for log in membership_logs:
        activities.append({
            "date": log.date,
            "description": log.description
        })
    
    # Sort combined activities by date
    activities.sort(key=lambda x: x["date"], reverse=True)
    return activities[:5]
