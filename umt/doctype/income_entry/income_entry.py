import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today, flt

class IncomeEntry(Document):
    def validate(self):
        """Validate income entry data before saving"""
        self.validate_dates()
        self.validate_amounts()
        self.validate_member()
        
    def validate_dates(self):
        """Validate posting and payment dates"""
        if getdate(self.posting_date) > getdate(today()):
            frappe.throw("تاريخ التسجيل لا يمكن أن يكون في المستقبل")
            
        if getdate(self.payment_date) > getdate(today()):
            frappe.throw("تاريخ الدفع لا يمكن أن يكون في المستقبل")
            
        if getdate(self.payment_date) > getdate(self.posting_date):
            frappe.throw("تاريخ الدفع لا يمكن أن يكون بعد تاريخ التسجيل")
    
    def validate_amounts(self):
        """Validate payment amounts"""
        if flt(self.amount) <= 0:
            frappe.throw("يجب أن يكون المبلغ أكبر من صفر")
    
    def validate_member(self):
        """Validate member details for membership card payments"""
        if self.entry_type == "بطاقة الإنخراط" and not self.member:
            frappe.throw("يجب تحديد العضو لدفع بطاقة الإنخراط")
    
    def on_submit(self):
        """Handle submission of income entry"""
        self.update_membership_card()
        self.create_gl_entry()
    
    def on_cancel(self):
        """Handle cancellation of income entry"""
        self.update_membership_card(cancel=True)
        self.cancel_gl_entry()
    
    def update_membership_card(self, cancel=False):
        """Update membership card payment status"""
        if self.entry_type == "بطاقة الإنخراط" and self.member:
            card = frappe.get_list("Membership_Card",
                filters={
                    "member": self.member,
                    "status": "Active"
                },
                order_by="creation desc",
                limit=1
            )
            
            if card:
                card_doc = frappe.get_doc("Membership_Card", card[0].name)
                card_doc.payment_status = "غير المؤداة" if cancel else "المؤداة"
                card_doc.save()
    
    def create_gl_entry(self):
        """Create General Ledger entries for income"""
        # This method will be implemented when accounting module is set up
        pass
    
    def cancel_gl_entry(self):
        """Cancel General Ledger entries"""
        # This method will be implemented when accounting module is set up
        pass
