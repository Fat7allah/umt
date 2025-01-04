import frappe
from frappe import _
from frappe.utils import add_months, getdate, today, flt

def get_context(context):
    """Add admin dashboard data to the context"""
    if not is_admin():
        frappe.throw(_("غير مصرح لك بالوصول إلى لوحة التحكم"))
    
    context.quick_stats = get_quick_stats()
    context.recent_activities = get_recent_activities()
    return context

def is_admin():
    """Check if current user is admin"""
    return frappe.session.user == 'Administrator' or 'System Manager' in frappe.get_roles()

def get_quick_stats():
    """Get quick statistics for dashboard"""
    current_month = getdate(today())
    last_month = add_months(current_month, -1)
    
    stats = []
    
    # Total Members
    current_members = get_member_count(current_month)
    last_month_members = get_member_count(last_month)
    member_change = calculate_change(current_members, last_month_members)
    
    stats.append({
        "label": _("مجموع الأعضاء"),
        "value": current_members,
        "change": member_change
    })
    
    # Active Cards
    current_cards = get_active_card_count(current_month)
    last_month_cards = get_active_card_count(last_month)
    card_change = calculate_change(current_cards, last_month_cards)
    
    stats.append({
        "label": _("البطاقات النشطة"),
        "value": current_cards,
        "change": card_change
    })
    
    # Monthly Income
    current_income = get_monthly_income(current_month)
    last_month_income = get_monthly_income(last_month)
    income_change = calculate_change(current_income, last_month_income)
    
    stats.append({
        "label": _("مداخيل الشهر"),
        "value": f"{current_income:,.2f} MAD",
        "change": income_change
    })
    
    # Monthly Expenses
    current_expenses = get_monthly_expenses(current_month)
    last_month_expenses = get_monthly_expenses(last_month)
    expenses_change = calculate_change(current_expenses, last_month_expenses)
    
    stats.append({
        "label": _("مصاريف الشهر"),
        "value": f"{current_expenses:,.2f} MAD",
        "change": expenses_change
    })
    
    return stats

def get_recent_activities():
    """Get recent system activities"""
    activities = []
    
    # Get member activities
    member_activities = frappe.get_all(
        "Member Log",
        fields=["activity_type", "description", "creation as time"],
        order_by="creation desc",
        limit=5
    )
    
    for activity in member_activities:
        activities.append({
            "icon": "user",
            "description": activity.description,
            "time": format_datetime(activity.time)
        })
    
    # Get financial activities
    financial_activities = frappe.get_all(
        "Payment Entry",
        fields=["payment_type", "paid_amount", "creation as time"],
        filters={"docstatus": 1},
        order_by="creation desc",
        limit=5
    )
    
    for activity in financial_activities:
        activities.append({
            "icon": "money",
            "description": _("{0}: {1} درهم").format(
                activity.payment_type,
                activity.paid_amount
            ),
            "time": format_datetime(activity.time)
        })
    
    # Sort combined activities by time
    activities.sort(key=lambda x: x["time"], reverse=True)
    return activities[:10]

def get_member_count(date):
    """Get total member count for a given date"""
    return frappe.db.count("Member", filters={
        "creation": ["<=", date],
        "docstatus": 1
    })

def get_active_card_count(date):
    """Get active card count for a given date"""
    return frappe.db.count("Membership_Card", filters={
        "creation": ["<=", date],
        "status": "Active",
        "docstatus": 1
    })

def get_monthly_income(date):
    """Get total income for a given month"""
    return flt(frappe.db.sql("""
        SELECT IFNULL(SUM(amount), 0)
        FROM `tabIncome_Entry`
        WHERE MONTH(posting_date) = MONTH(%s)
        AND YEAR(posting_date) = YEAR(%s)
        AND docstatus = 1
    """, (date, date))[0][0])

def get_monthly_expenses(date):
    """Get total expenses for a given month"""
    return flt(frappe.db.sql("""
        SELECT IFNULL(SUM(amount), 0)
        FROM `tabExpense_Entry`
        WHERE MONTH(posting_date) = MONTH(%s)
        AND YEAR(posting_date) = YEAR(%s)
        AND docstatus = 1
    """, (date, date))[0][0])

def calculate_change(current, previous):
    """Calculate percentage change"""
    if not previous:
        return 100 if current else 0
    return round(((current - previous) / previous) * 100, 1)

def format_datetime(dt):
    """Format datetime for display"""
    from frappe.utils import pretty_date
    return pretty_date(dt)
