import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today, flt

class ExpenseEntry(Document):
    def validate(self):
        """Validate expense entry data before saving"""
        self.validate_dates()
        self.validate_amounts()
        self.validate_attachments()
        
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
    
    def validate_attachments(self):
        """Validate required attachments based on amount"""
        if flt(self.amount) > 1000 and not self.attach_receipt:
            frappe.throw("يجب إرفاق وصل للمصاريف التي تتجاوز 1000 درهم")
    
    def on_submit(self):
        """Handle submission of expense entry"""
        self.create_gl_entry()
        self.update_budget()
    
    def on_cancel(self):
        """Handle cancellation of expense entry"""
        self.cancel_gl_entry()
        self.update_budget(cancel=True)
    
    def create_gl_entry(self):
        """Create General Ledger entries for expense"""
        # This method will be implemented when accounting module is set up
        pass
    
    def cancel_gl_entry(self):
        """Cancel General Ledger entries"""
        # This method will be implemented when accounting module is set up
        pass
    
    def update_budget(self, cancel=False):
        """Update budget utilization"""
        # This method will be implemented when budgeting module is set up
        pass
    
    def get_expense_analytics(self):
        """Get analytics for this expense type"""
        return frappe.get_all("Expense_Entry",
            filters={
                "expense_type": self.expense_type,
                "academic_year": self.academic_year,
                "docstatus": 1
            },
            fields=["sum(amount) as total_amount"],
            group_by="expense_type"
        )
