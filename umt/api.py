import frappe
from frappe import _

@frappe.whitelist()
def get_member_details(member_id):
    """Get member details"""
    if not member_id:
        frappe.throw(_("Member ID is required"))
        
    return frappe.get_doc("Member", member_id)

@frappe.whitelist()
def update_member_status(member_id, status):
    """Update member status"""
    if not member_id or not status:
        frappe.throw(_("Member ID and status are required"))
        
    doc = frappe.get_doc("Member", member_id)
    doc.status = status
    doc.save()
