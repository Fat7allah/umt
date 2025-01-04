import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today, date_diff

class UNEMStructure(Document):
    def validate(self):
        """Validate structure data before saving"""
        self.validate_dates()
        self.validate_position()
        self.update_status()
    
    def validate_dates(self):
        """Validate start and end dates"""
        if self.end_date and getdate(self.start_date) > getdate(self.end_date):
            frappe.throw("تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
            
        if getdate(self.start_date) > getdate(today()):
            frappe.throw("تاريخ البداية لا يمكن أن يكون في المستقبل")
    
    def validate_position(self):
        """Validate position and role combinations"""
        # Validate executive office roles
        if self.position_type == "المكتب التنفيذي":
            if self.region or self.province:
                frappe.throw("المكتب التنفيذي لا يحتاج إلى تحديد الجهة أو الإقليم")
                
        # Validate regional office requirements
        elif self.position_type == "المكاتب الجهوية":
            if not self.region:
                frappe.throw("يجب تحديد الجهة للمكاتب الجهوية")
                
        # Validate provincial office requirements
        elif self.position_type in ["المكاتب الإقليمية", "المكاتب المحلية"]:
            if not self.province:
                frappe.throw("يجب تحديد الإقليم للمكاتب الإقليمية والمحلية")
    
    def update_status(self):
        """Update active status based on end date"""
        if self.end_date and getdate(self.end_date) < getdate(today()):
            self.is_active = 0
    
    def on_update(self):
        """Handle position updates"""
        self.update_member_roles()
    
    def update_member_roles(self):
        """Update member's roles based on position"""
        if self.is_active:
            # Add UNEM Manager role for executive positions
            if self.position_type == "المكتب التنفيذي" and self.role in [
                "الكاتب الوطني",
                "نائب الكاتب الوطني",
                "الكاتب العام",
                "أمين المال"
            ]:
                self.add_unem_manager_role()
        else:
            # Remove UNEM Manager role if position is inactive
            self.remove_unem_manager_role()
    
    def add_unem_manager_role(self):
        """Add UNEM Manager role to member"""
        user = frappe.db.get_value("Member", self.member, "email")
        if user:
            user_doc = frappe.get_doc("User", user)
            user_doc.add_roles("UNEM Manager")
    
    def remove_unem_manager_role(self):
        """Remove UNEM Manager role from member"""
        user = frappe.db.get_value("Member", self.member, "email")
        if user:
            user_doc = frappe.get_doc("User", user)
            user_doc.remove_roles("UNEM Manager")
