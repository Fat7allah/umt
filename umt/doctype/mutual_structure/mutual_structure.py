import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today, date_diff, add_years

class MutualStructure(Document):
    def validate(self):
        """Validate structure data before saving"""
        self.validate_dates()
        self.validate_mandate()
        self.update_status()
    
    def validate_dates(self):
        """Validate mandate start and end dates"""
        if self.mandate_end_date and getdate(self.mandate_start_date) > getdate(self.mandate_end_date):
            frappe.throw("تاريخ بداية الولاية يجب أن يكون قبل تاريخ نهايتها")
            
        if getdate(self.mandate_start_date) > getdate(today()):
            frappe.throw("تاريخ بداية الولاية لا يمكن أن يكون في المستقبل")
            
        # Set default end date if not specified (4 years from start)
        if not self.mandate_end_date:
            self.mandate_end_date = add_years(self.mandate_start_date, 4)
    
    def validate_mandate(self):
        """Validate mandate number and position requirements"""
        # Check for duplicate mandate numbers
        existing = frappe.db.exists("Mutual_Structure", {
            "mandate_number": self.mandate_number,
            "position_type": self.position_type,
            "name": ["!=", self.name]
        })
        
        if existing:
            frappe.throw(f"رقم الولاية {self.mandate_number} مستخدم بالفعل لهذا النوع من المناصب")
            
        # Validate executive office roles
        if self.position_type == "المكتب التنفيذي" and not self.role:
            frappe.throw("يجب تحديد المنصب لأعضاء المكتب التنفيذي")
    
    def update_status(self):
        """Update active status based on mandate end date"""
        if getdate(self.mandate_end_date) < getdate(today()):
            self.is_active = 0
    
    def on_update(self):
        """Handle position updates"""
        self.update_member_roles()
    
    def update_member_roles(self):
        """Update member's roles based on position"""
        if self.is_active:
            # Add Mutual Manager role for executive positions
            if self.position_type == "المكتب التنفيذي" and self.role in [
                "الرئيس",
                "نائب الرئيس",
                "الكاتب العام",
                "أمين المال"
            ]:
                self.add_mutual_manager_role()
        else:
            # Remove Mutual Manager role if position is inactive
            self.remove_mutual_manager_role()
    
    def add_mutual_manager_role(self):
        """Add Mutual Manager role to member"""
        user = frappe.db.get_value("Member", self.member, "email")
        if user:
            user_doc = frappe.get_doc("User", user)
            user_doc.add_roles("Mutual Manager")
    
    def remove_mutual_manager_role(self):
        """Remove Mutual Manager role from member"""
        user = frappe.db.get_value("Member", self.member, "email")
        if user:
            user_doc = frappe.get_doc("User", user)
            user_doc.remove_roles("Mutual Manager")
