import frappe
from frappe import _
from frappe.utils import flt, today, add_years

def get_context(context):
    """Add renewal data to the context"""
    if frappe.session.user == 'Guest':
        frappe.local.flags.redirect_location = '/login'
        raise frappe.Redirect
        
    context.member = get_member_info()
    context.renewal_fee = get_renewal_fee()
    context.payment_methods = get_payment_methods()
    context.bank_info = get_bank_info()
    
    return context

def get_member_info():
    """Get member information"""
    user = frappe.session.user
    member = frappe.get_all(
        "Member",
        filters={"user": user},
        fields=[
            "name", "membership_status", "current_card",
            "card_expiry", "province"
        ]
    )
    
    if not member:
        frappe.throw(_("عضو غير موجود"))
        
    return member[0]

def get_renewal_fee():
    """Get renewal fee based on member's province and status"""
    settings = frappe.get_single("UMT Settings")
    member = get_member_info()
    
    # Get base fee
    base_fee = settings.membership_fee
    
    # Apply late fee if membership is expired
    if member.membership_status == "Expired":
        base_fee += settings.late_fee
        
    return base_fee

def get_payment_methods():
    """Get available payment methods"""
    return frappe.get_all(
        "Payment Method",
        filters={"enabled": 1},
        fields=["name", "description", "method_type"]
    )

def get_bank_info():
    """Get bank account information"""
    settings = frappe.get_single("UMT Settings")
    return {
        "bank_name": settings.bank_name,
        "account_number": settings.bank_account,
        "beneficiary": settings.organization_name
    }

@frappe.whitelist()
def submit_renewal(payment_method, transaction_ref=None, receipt=None):
    """Submit membership renewal request"""
    if frappe.session.user == 'Guest':
        frappe.throw(_("يرجى تسجيل الدخول أولاً"))
        
    member = get_member_info()
    
    # Create renewal request
    renewal = frappe.get_doc({
        "doctype": "Membership Renewal",
        "member": member.name,
        "payment_method": payment_method,
        "amount": get_renewal_fee(),
        "transaction_reference": transaction_ref,
        "payment_receipt": receipt,
        "status": "Pending"
    })
    
    renewal.insert(ignore_permissions=True)
    
    # Create payment entry
    create_payment_entry(renewal)
    
    return {"message": _("تم تقديم طلب التجديد بنجاح")}

def create_payment_entry(renewal):
    """Create payment entry for renewal"""
    payment = frappe.get_doc({
        "doctype": "Payment Entry",
        "payment_type": "Receive",
        "party_type": "Member",
        "party": renewal.member,
        "posting_date": today(),
        "paid_amount": renewal.amount,
        "received_amount": renewal.amount,
        "reference_no": renewal.transaction_reference,
        "reference_date": today(),
        "remarks": _("تجديد العضوية - {0}").format(renewal.name)
    })
    
    payment.insert(ignore_permissions=True)
    
    if renewal.payment_method == "cash":
        payment.submit()
        update_membership(renewal.member)
