import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    
    return columns, data

def get_columns():
    """Return columns for the report"""
    return [
        {
            "fieldname": "province",
            "label": _("الإقليم"),
            "fieldtype": "Link",
            "options": "Province",
            "width": 150
        },
        {
            "fieldname": "total_members",
            "label": _("مجموع الأعضاء"),
            "fieldtype": "Int",
            "width": 120
        },
        {
            "fieldname": "active_members",
            "label": _("الأعضاء النشطاء"),
            "fieldtype": "Int",
            "width": 120
        },
        {
            "fieldname": "inactive_members",
            "label": _("الأعضاء غير النشطاء"),
            "fieldtype": "Int",
            "width": 120
        },
        {
            "fieldname": "expired_members",
            "label": _("العضويات المنتهية"),
            "fieldtype": "Int",
            "width": 120
        },
        {
            "fieldname": "paid_cards",
            "label": _("البطاقات المؤداة"),
            "fieldtype": "Int",
            "width": 120
        },
        {
            "fieldname": "unpaid_cards",
            "label": _("البطاقات غير المؤداة"),
            "fieldtype": "Int",
            "width": 120
        }
    ]

def get_data(filters):
    """Get report data based on filters"""
    data = []
    conditions = get_conditions(filters)
    
    # Get data by province
    provinces = frappe.get_all("Province", fields=["name"])
    
    for province in provinces:
        row = {
            "province": province.name,
            "total_members": get_member_count(province.name, conditions),
            "active_members": get_member_count(province.name, conditions + " AND membership_status = 'Active'"),
            "inactive_members": get_member_count(province.name, conditions + " AND membership_status = 'Inactive'"),
            "expired_members": get_member_count(province.name, conditions + " AND membership_status = 'Expired'"),
            "paid_cards": get_card_count(province.name, conditions, "المؤداة"),
            "unpaid_cards": get_card_count(province.name, conditions, "غير المؤداة")
        }
        data.append(row)
    
    # Add total row
    if data:
        total_row = {
            "province": "المجموع",
            "total_members": sum(d["total_members"] for d in data),
            "active_members": sum(d["active_members"] for d in data),
            "inactive_members": sum(d["inactive_members"] for d in data),
            "expired_members": sum(d["expired_members"] for d in data),
            "paid_cards": sum(d["paid_cards"] for d in data),
            "unpaid_cards": sum(d["unpaid_cards"] for d in data)
        }
        data.append(total_row)
    
    return data

def get_conditions(filters):
    """Build conditions based on filters"""
    conditions = "1=1"
    
    if filters.get("academic_year"):
        conditions += f" AND academic_year = '{filters.get('academic_year')}'"
        
    if filters.get("from_date"):
        conditions += f" AND membership_date >= '{filters.get('from_date')}'"
        
    if filters.get("to_date"):
        conditions += f" AND membership_date <= '{filters.get('to_date')}'"
        
    return conditions

def get_member_count(province, conditions):
    """Get member count based on conditions"""
    return frappe.db.count("Member", filters=f"province = '{province}' AND {conditions}")

def get_card_count(province, conditions, payment_status):
    """Get card count based on conditions and payment status"""
    return frappe.db.count("Membership_Card",
        filters=f"""
            member IN (SELECT name FROM tabMember WHERE province = '{province}' AND {conditions})
            AND payment_status = '{payment_status}'
            AND status = 'Active'
        """
    )
