import frappe
from frappe import _

def after_install():
    """After install tasks"""
    # Create default records
    create_default_records()
    
def create_default_records():
    """Create default records for the application"""
    if not frappe.db.exists("Role", "UMT Manager"):
        doc = frappe.new_doc("Role")
        doc.role_name = "UMT Manager"
        doc.desk_access = 1
        doc.insert(ignore_permissions=True)
        
    if not frappe.db.exists("Role", "UMT Member"):
        doc = frappe.new_doc("Role")
        doc.role_name = "UMT Member"
        doc.desk_access = 0
        doc.insert(ignore_permissions=True)
