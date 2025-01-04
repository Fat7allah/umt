# Copyright (c) 2024, UMT and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PaymentMethod(Document):
    def validate(self):
        """Validate payment method data"""
        if not self.method_name:
            frappe.throw(_("Method Name is required"))
        
        # Check for duplicate method names
        if self.is_new():
            if frappe.db.exists("Payment Method", {"method_name": self.method_name, "name": ["!=", self.name]}):
                frappe.throw(_("Payment method with this name already exists"))

def on_update(doc, method=None):
    """Handle payment method updates"""
    frappe.cache().delete_key('payment_methods')
    frappe.clear_cache()
    
    # Log the change
    frappe.log_error(
        message=f"Payment Method {doc.method_name} was {'enabled' if doc.enabled else 'disabled'}",
        title="Payment Method Status Change"
    )
