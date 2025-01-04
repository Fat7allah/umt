import frappe
from frappe import _
from frappe.utils import flt, today, add_months, getdate
import json
from datetime import datetime

def get_context(context):
    """
    Prepare and return the context for the financial management page.
    
    This function:
    1. Validates user permissions
    2. Retrieves financial summaries
    3. Loads transaction data
    4. Prepares supporting data (payment methods, years)
    
    Returns:
        dict: Context dictionary with all required data for the template
    """
    if not has_finance_access():
        frappe.throw(_("غير مصرح لك بالوصول إلى صفحة الإدارة المالية"))
    
    current_date = getdate(today())
    
    # Prepare all required data
    context.update({
        "total_income": get_monthly_total("Income_Entry", current_date),
        "total_expenses": get_monthly_total("Expense_Entry", current_date),
        "balance": get_current_balance(),
        "pending_count": get_pending_count(),
        "transactions": get_transactions(),
        "payment_methods": get_payment_methods(),
        "academic_years": get_academic_years()
    })
    
    return context

def has_finance_access():
    """
    Check if current user has finance access permissions.
    
    Returns:
        bool: True if user has required permissions, False otherwise
    """
    allowed_roles = {"System Manager", "Finance Manager", "Finance User"}
    user_roles = set(frappe.get_roles())
    return bool(allowed_roles & user_roles)

def get_monthly_total(doctype, date):
    """
    Calculate total amount for a given doctype in the current month.
    
    Args:
        doctype (str): Document type to query
        date (datetime): Date to calculate the monthly total for
    
    Returns:
        float: Total amount for the month
    """
    return flt(frappe.db.sql("""
        SELECT IFNULL(SUM(amount), 0)
        FROM `tab{0}`
        WHERE MONTH(posting_date) = MONTH(%s)
        AND YEAR(posting_date) = YEAR(%s)
        AND docstatus = 1
        AND status = 'Approved'
    """.format(doctype), (date, date))[0][0])

def get_current_balance():
    """
    Calculate current balance by subtracting total expenses from total income.
    
    Returns:
        float: Current balance
    """
    total_income = flt(frappe.db.sql("""
        SELECT IFNULL(SUM(amount), 0)
        FROM `tabIncome_Entry`
        WHERE docstatus = 1
        AND status = 'Approved'
    """)[0][0])
    
    total_expenses = flt(frappe.db.sql("""
        SELECT IFNULL(SUM(amount), 0)
        FROM `tabExpense_Entry`
        WHERE docstatus = 1
        AND status = 'Approved'
    """)[0][0])
    
    return total_income - total_expenses

def get_pending_count():
    """
    Get count of pending transactions awaiting approval.
    
    Returns:
        int: Number of pending transactions
    """
    return frappe.db.count("Income_Entry", {"status": "Pending"}) + \
           frappe.db.count("Expense_Entry", {"status": "Pending"})

def get_transactions(filters=None):
    """
    Retrieve financial transactions based on filters.
    
    Args:
        filters (dict, optional): Filters to apply to the query
    
    Returns:
        list: List of transaction dictionaries
    """
    if not filters:
        filters = {}
    
    # Get income entries
    income_entries = frappe.get_all(
        "Income_Entry",
        fields=[
            "name", "posting_date", "'income' as type",
            "description", "amount", "payment_method",
            "status", "modified", "owner"
        ],
        filters=filters,
        order_by="posting_date desc"
    )
    
    # Get expense entries
    expense_entries = frappe.get_all(
        "Expense_Entry",
        fields=[
            "name", "posting_date", "'expense' as type",
            "description", "amount", "payment_method",
            "status", "modified", "owner"
        ],
        filters=filters,
        order_by="posting_date desc"
    )
    
    # Combine and sort transactions
    transactions = income_entries + expense_entries
    transactions.sort(key=lambda x: x.posting_date, reverse=True)
    
    return transactions

def get_payment_methods():
    """
    Get list of available payment methods.
    
    Returns:
        list: List of payment method dictionaries
    """
    return frappe.get_all(
        "Payment_Method",
        fields=["name", "description"],
        filters={"enabled": 1}
    )

def get_academic_years():
    """
    Get list of academic years ordered by start date.
    
    Returns:
        list: List of academic year dictionaries
    """
    return frappe.get_all(
        "Academic_Year",
        fields=["name", "year_name"],
        order_by="start_date desc"
    )

@frappe.whitelist()
def save_transaction(data):
    """
    Save a new financial transaction or update existing one.
    
    Args:
        data (dict): Transaction data including type, amount, description, etc.
    
    Returns:
        dict: Response indicating success or failure
    """
    if isinstance(data, str):
        data = json.loads(data)
    
    try:
        # Determine doctype based on transaction type
        doctype = "Income_Entry" if data.get("transaction_type") == "income" else "Expense_Entry"
        
        if data.get("name"):
            # Update existing transaction
            doc = frappe.get_doc(doctype, data["name"])
            doc.update(data)
        else:
            # Create new transaction
            doc = frappe.get_doc({
                "doctype": doctype,
                "posting_date": today(),
                "status": "Pending",
                **data
            })
        
        doc.save()
        
        return {
            "success": True,
            "message": _("تم حفظ المعاملة بنجاح"),
            "transaction": doc.name
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("خطأ في حفظ المعاملة المالية"))
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist()
def update_transaction_status(name, status):
    """
    Update the status of a financial transaction.
    
    Args:
        name (str): Transaction name/ID
        status (str): New status value
    
    Returns:
        dict: Response indicating success or failure
    """
    try:
        # Determine doctype from name prefix
        doctype = "Income_Entry" if "INC" in name else "Expense_Entry"
        
        doc = frappe.get_doc(doctype, name)
        doc.status = status
        doc.save()
        
        return {
            "success": True,
            "message": _("تم تحديث حالة المعاملة بنجاح")
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("خطأ في تحديث حالة المعاملة"))
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist()
def export_transactions():
    """
    Export financial transactions to Excel based on filters.
    
    This function:
    1. Retrieves filtered transactions
    2. Formats data for export
    3. Generates Excel file
    4. Returns file for download
    """
    from frappe.utils.xlsxutils import make_xlsx
    
    # Get filters from request
    filters = {
        "type": frappe.form_dict.get("type"),
        "status": frappe.form_dict.get("status"),
        "posting_date": ["between", [
            frappe.form_dict.get("date_from"),
            frappe.form_dict.get("date_to")
        ]] if frappe.form_dict.get("date_from") and frappe.form_dict.get("date_to") else None
    }
    
    # Remove empty filters
    filters = {k: v for k, v in filters.items() if v}
    
    # Get transactions
    transactions = get_transactions(filters)
    
    # Prepare data for export
    data = []
    headers = [
        _("الرقم المرجعي"),
        _("التاريخ"),
        _("النوع"),
        _("الوصف"),
        _("المبلغ"),
        _("طريقة الدفع"),
        _("الحالة")
    ]
    data.append(headers)
    
    for trans in transactions:
        row = [
            trans.name,
            trans.posting_date,
            _(trans.type),
            trans.description,
            trans.amount,
            trans.payment_method,
            _(trans.status)
        ]
        data.append(row)
    
    xlsx_file = make_xlsx(data, "Finance Export")
    
    frappe.response['filename'] = 'finance_export.xlsx'
    frappe.response['filecontent'] = xlsx_file.getvalue()
    frappe.response['type'] = 'binary'
