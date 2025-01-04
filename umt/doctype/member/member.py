import frappe
from frappe.model.document import Document
from frappe.utils import today, add_years, getdate

class Member(Document):
    def validate(self):
        """Validate member data before saving"""
        self.validate_dates()
        if not self.membership_date:
            self.membership_date = today()
        
    def validate_dates(self):
        """Validate birth date and membership dates"""
        if self.birth_date and getdate(self.birth_date) > getdate(today()):
            frappe.throw("تاريخ الازدياد لا يمكن أن يكون في المستقبل")
            
        if self.last_renewal_date and getdate(self.last_renewal_date) > getdate(today()):
            frappe.throw("تاريخ التجديد لا يمكن أن يكون في المستقبل")
    
    def after_insert(self):
        """Generate membership card after member creation"""
        self.generate_membership_card()
    
    def on_update(self):
        """Update membership status based on renewal date"""
        self.update_membership_status()
    
    def generate_membership_card(self):
        """Generate a new membership card for the member"""
        if not self.card_number:
            # Generate unique card number
            year = frappe.utils.today()[:4]
            province_code = self.get_province_code()
            sequence = frappe.db.count('Member', {'province': self.province}) + 1
            
            self.card_number = f"{year}{province_code}{sequence:04d}"
            self.db_update()
            
            # Create membership card record
            frappe.get_doc({
                'doctype': 'Membership_Card',
                'member': self.name,
                'card_number': self.card_number,
                'issue_date': today(),
                'expiry_date': add_years(today(), 1),
                'status': 'Active'
            }).insert()
    
    def get_province_code(self):
        """Get two-digit code for province"""
        province_codes = {
            'عمالة طنجة': '01',
            'عمالة تطوان': '02',
            'إقليم الفحص أنجرة': '03'
        }
        return province_codes.get(self.province, '00')
    
    def update_membership_status(self):
        """Update membership status based on card expiry"""
        if not self.last_renewal_date:
            return
            
        today_date = getdate(today())
        renewal_date = getdate(self.last_renewal_date)
        expiry_date = add_years(renewal_date, 1)
        
        if today_date > expiry_date:
            self.membership_status = 'Expired'
        elif not self.is_active:
            self.membership_status = 'Inactive'
        else:
            self.membership_status = 'Active'
            
        self.db_update()
