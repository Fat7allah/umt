import frappe
from frappe.model.document import Document
from frappe.utils import getdate, add_years

class AcademicYear(Document):
    def validate(self):
        """Validate academic year data"""
        self.validate_dates()
        self.validate_active_year()
        
    def validate_dates(self):
        """Validate start and end dates"""
        if getdate(self.start_date) >= getdate(self.end_date):
            frappe.throw("تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
            
        # Check if dates overlap with other academic years
        overlapping_years = frappe.db.sql("""
            SELECT name, year_name FROM `tabAcademic Year`
            WHERE (start_date BETWEEN %s AND %s OR end_date BETWEEN %s AND %s)
            AND name != %s
        """, (self.start_date, self.end_date, self.start_date, self.end_date, self.name), as_dict=1)
        
        if overlapping_years:
            years = ", ".join([d.year_name for d in overlapping_years])
            frappe.throw(f"تتداخل التواريخ مع السنوات الدراسية التالية: {years}")
    
    def validate_active_year(self):
        """Ensure only one academic year is active"""
        if self.is_active:
            active_years = frappe.get_all("Academic Year",
                filters={
                    "is_active": 1,
                    "name": ["!=", self.name]
                }
            )
            
            if active_years:
                for year in active_years:
                    frappe.db.set_value("Academic Year", year.name, "is_active", 0)
    
    def on_update(self):
        """Handle updates to academic year"""
        if self.is_active:
            self.update_current_academic_year()
    
    def update_current_academic_year(self):
        """Update system defaults with current academic year"""
        frappe.db.set_default("current_academic_year", self.name)
    
    @frappe.whitelist()
    def create_next_academic_year(self):
        """Create next academic year based on current one"""
        next_year = frappe.new_doc("Academic Year")
        
        # Calculate next year's name (e.g., 2024-2025 -> 2025-2026)
        current_years = self.year_name.split("-")
        next_start_year = str(int(current_years[1]))
        next_end_year = str(int(next_start_year) + 1)
        
        next_year.year_name = f"{next_start_year}-{next_end_year}"
        next_year.start_date = add_years(self.start_date, 1)
        next_year.end_date = add_years(self.end_date, 1)
        next_year.is_active = 0
        
        return next_year
    
    def get_dashboard_data(self):
        """Get dashboard data for academic year"""
        return {
            "fieldname": "academic_year",
            "transactions": [
                {
                    "label": frappe._("Members"),
                    "items": ["Member"]
                },
                {
                    "label": frappe._("Finance"),
                    "items": ["Income_Entry", "Expense_Entry"]
                }
            ]
        }
