# Copyright (c) 2024, UMT and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class NotificationSettings(Document):
    def validate(self):
        """Validate notification settings"""
        # Ensure at least one notification type is enabled
        if not any([
            self.enable_membership_expiry,
            self.enable_new_member,
            self.enable_payment_received
        ]):
            frappe.msgprint(
                _("Warning: All notifications are disabled. Users may miss important updates."),
                indicator="yellow",
                alert=True
            )

    def on_update(self, method=None):
        """Handle notification settings updates"""
        frappe.cache().delete_key('notification_settings')
        frappe.clear_cache()
        
        # Log the changes
        enabled_notifications = []
        if self.enable_membership_expiry:
            enabled_notifications.append("Membership Expiry")
        if self.enable_new_member:
            enabled_notifications.append("New Member")
        if self.enable_payment_received:
            enabled_notifications.append("Payment Received")
        
        frappe.log_error(
            message=f"Notification Settings updated. Enabled notifications: {', '.join(enabled_notifications)}",
            title="Notification Settings Update"
        )
