import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    summary = get_summary(data)
    
    return columns, data, None, chart, summary

def get_columns():
    """Return columns for the report"""
    return [
        {
            "fieldname": "month",
            "label": _("الشهر"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "card_income",
            "label": _("مداخيل البطاقات"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "other_income",
            "label": _("مداخيل أخرى"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "total_income",
            "label": _("مجموع المداخيل"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "admin_expenses",
            "label": _("مصاريف إدارية"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "activity_expenses",
            "label": _("مصاريف الأنشطة"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "other_expenses",
            "label": _("مصاريف أخرى"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "total_expenses",
            "label": _("مجموع المصاريف"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "balance",
            "label": _("الرصيد"),
            "fieldtype": "Currency",
            "width": 150
        }
    ]

def get_data(filters):
    """Get report data based on filters"""
    data = []
    conditions = get_conditions(filters)
    
    # Get data by month
    months = get_months(filters)
    
    for month in months:
        row = {
            "month": month,
            "card_income": get_income(month, "بطاقة الإنخراط", conditions),
            "other_income": get_income(month, "مداخيل أخرى", conditions),
            "admin_expenses": get_expenses(month, "مصاريف إدارية", conditions),
            "activity_expenses": get_expenses(month, "مصاريف الأنشطة", conditions),
            "other_expenses": get_expenses(month, "مصاريف أخرى", conditions)
        }
        
        # Calculate totals
        row["total_income"] = flt(row["card_income"]) + flt(row["other_income"])
        row["total_expenses"] = flt(row["admin_expenses"]) + flt(row["activity_expenses"]) + flt(row["other_expenses"])
        row["balance"] = row["total_income"] - row["total_expenses"]
        
        data.append(row)
    
    return data

def get_chart(data):
    """Generate chart data"""
    labels = [d.get("month") for d in data]
    income_data = [d.get("total_income") for d in data]
    expense_data = [d.get("total_expenses") for d in data]
    balance_data = [d.get("balance") for d in data]
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": _("المداخيل"),
                    "values": income_data,
                    "chartType": "bar"
                },
                {
                    "name": _("المصاريف"),
                    "values": expense_data,
                    "chartType": "bar"
                },
                {
                    "name": _("الرصيد"),
                    "values": balance_data,
                    "chartType": "line"
                }
            ]
        },
        "type": "bar",
        "colors": ["#28a745", "#dc3545", "#007bff"]
    }

def get_summary(data):
    """Generate report summary"""
    total_income = sum(d.get("total_income") for d in data)
    total_expenses = sum(d.get("total_expenses") for d in data)
    net_balance = total_income - total_expenses
    
    return [
        {
            "value": total_income,
            "label": _("مجموع المداخيل"),
            "datatype": "Currency",
            "currency": "MAD"
        },
        {
            "value": total_expenses,
            "label": _("مجموع المصاريف"),
            "datatype": "Currency",
            "currency": "MAD"
        },
        {
            "value": net_balance,
            "label": _("الرصيد الصافي"),
            "datatype": "Currency",
            "currency": "MAD",
            "indicator": "Green" if net_balance > 0 else "Red"
        }
    ]

def get_conditions(filters):
    """Build conditions based on filters"""
    conditions = "docstatus = 1"
    
    if filters.get("academic_year"):
        conditions += f" AND academic_year = '{filters.get('academic_year')}'"
        
    if filters.get("from_date"):
        conditions += f" AND posting_date >= '{filters.get('from_date')}'"
        
    if filters.get("to_date"):
        conditions += f" AND posting_date <= '{filters.get('to_date')}'"
        
    return conditions

def get_months(filters):
    """Get list of months based on filters"""
    return frappe.db.sql("""
        SELECT DISTINCT
            DATE_FORMAT(posting_date, '%Y-%m') as month
        FROM
            `tabIncome_Entry`
        WHERE
            docstatus = 1
            AND {conditions}
        UNION
        SELECT DISTINCT
            DATE_FORMAT(posting_date, '%Y-%m') as month
        FROM
            `tabExpense_Entry`
        WHERE
            docstatus = 1
            AND {conditions}
        ORDER BY
            month
    """.format(conditions=get_conditions(filters)), as_dict=0)

def get_income(month, type, conditions):
    """Get income amount for a specific month and type"""
    return frappe.db.sql("""
        SELECT
            IFNULL(SUM(amount), 0) as amount
        FROM
            `tabIncome_Entry`
        WHERE
            DATE_FORMAT(posting_date, '%Y-%m') = %s
            AND entry_type = %s
            AND {conditions}
    """.format(conditions=conditions), (month, type))[0][0]

def get_expenses(month, type, conditions):
    """Get expense amount for a specific month and type"""
    return frappe.db.sql("""
        SELECT
            IFNULL(SUM(amount), 0) as amount
        FROM
            `tabExpense_Entry`
        WHERE
            DATE_FORMAT(posting_date, '%Y-%m') = %s
            AND expense_type = %s
            AND {conditions}
    """.format(conditions=conditions), (month, type))[0][0]
