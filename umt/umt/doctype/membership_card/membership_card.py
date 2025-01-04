import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today, date_diff

class MembershipCard(Document):
    def validate(self):
        """Validate card data before saving"""
        self.validate_dates()
        self.update_status()
    
    def validate_dates(self):
        """Validate issue and expiry dates"""
        if getdate(self.issue_date) > getdate(self.expiry_date):
            frappe.throw("تاريخ الإصدار يجب أن يكون قبل تاريخ الانتهاء")
            
        if getdate(self.issue_date) > getdate(today()):
            frappe.throw("تاريخ الإصدار لا يمكن أن يكون في المستقبل")
    
    def update_status(self):
        """Update card status based on expiry date"""
        if getdate(self.expiry_date) < getdate(today()):
            self.status = 'Expired'
        elif self.status != 'Cancelled':
            self.status = 'Active'
            
    def on_update(self):
        """Update member's last renewal date when card is renewed"""
        if self.status == 'Active' and self.payment_status == 'المؤداة':
            frappe.db.set_value('Member', self.member, 'last_renewal_date', self.issue_date)
            
    def on_trash(self):
        """Prevent deletion of active cards"""
        if self.status == 'Active':
            frappe.throw("لا يمكن حذف البطاقات النشطة")
