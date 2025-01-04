import frappe
from frappe import _
from frappe.utils import cstr
import json

def get_context(context):
    """Add member management data to the context"""
    if not is_admin():
        frappe.throw(_("غير مصرح لك بالوصول إلى صفحة إدارة الأعضاء"))
    
    context.members = get_members()
    context.provinces = get_provinces()
    context.academic_years = get_academic_years()
    context.pagination = get_pagination()
    return context

def is_admin():
    """Check if current user is admin"""
    return frappe.session.user == 'Administrator' or 'System Manager' in frappe.get_roles()

def get_members(filters=None, limit_start=0, limit_page_length=25):
    """Get members list with filters"""
    if not filters:
        filters = {}
    
    filters["docstatus"] = 1
    
    return frappe.get_all(
        "Member",
        filters=filters,
        fields=[
            "name", "full_name", "province", "membership_status",
            "current_card", "membership_date"
        ],
        order_by="creation desc",
        limit_start=limit_start,
        limit_page_length=limit_page_length
    )

def get_provinces():
    """Get list of provinces"""
    return frappe.get_all("Province", fields=["name"])

def get_academic_years():
    """Get list of academic years"""
    return frappe.get_all(
        "Academic Year",
        fields=["name", "year_name"],
        order_by="start_date desc"
    )

def get_pagination():
    """Generate pagination HTML"""
    total = frappe.db.count("Member", {"docstatus": 1})
    pages = (total // 25) + (1 if total % 25 else 0)
    
    if pages <= 1:
        return ""
    
    html = ['<nav><ul class="pagination">']
    
    for i in range(pages):
        page = i + 1
        active = 'active' if page == 1 else ''
        html.append(f'''
            <li class="page-item {active}">
                <a class="page-link" href="#" onclick="changePage({page})">{page}</a>
            </li>
        ''')
    
    html.append('</ul></nav>')
    return ''.join(html)

@frappe.whitelist()
def save_member(data):
    """Save or update member"""
    if isinstance(data, str):
        data = json.loads(data)
    
    try:
        if data.get("name"):
            # Update existing member
            doc = frappe.get_doc("Member", data["name"])
            doc.update(data)
            doc.save()
        else:
            # Create new member
            doc = frappe.get_doc({
                "doctype": "Member",
                **data
            })
            doc.insert()
        
        return {"success": True, "message": _("تم حفظ العضو بنجاح")}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("خطأ في حفظ العضو"))
        return {"success": False, "message": str(e)}

@frappe.whitelist()
def get_member(name):
    """Get member details"""
    return frappe.get_doc("Member", name)

@frappe.whitelist()
def delete_member(name):
    """Delete member"""
    try:
        doc = frappe.get_doc("Member", name)
        doc.delete()
        return {"success": True, "message": _("تم حذف العضو بنجاح")}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("خطأ في حذف العضو"))
        return {"success": False, "message": str(e)}

@frappe.whitelist()
def export_members():
    """Export members to Excel"""
    from frappe.utils.xlsxutils import make_xlsx
    
    # Get filters from request
    filters = {
        "province": frappe.form_dict.get("province"),
        "membership_status": frappe.form_dict.get("status"),
        "academic_year": frappe.form_dict.get("year")
    }
    
    # Remove empty filters
    filters = {k: v for k, v in filters.items() if v}
    
    # Get members data
    members = get_members(filters=filters, limit_page_length=None)
    
    # Prepare data for export
    data = []
    headers = [
        _("رقم العضوية"),
        _("الإسم الكامل"),
        _("الإقليم"),
        _("حالة العضوية"),
        _("رقم البطاقة"),
        _("تاريخ الإنضمام")
    ]
    data.append(headers)
    
    for member in members:
        row = [
            member.name,
            member.full_name,
            member.province,
            _(member.membership_status),
            member.current_card or "",
            member.membership_date
        ]
        data.append(row)
    
    xlsx_file = make_xlsx(data, "Member Export")
    
    frappe.response['filename'] = 'members_export.xlsx'
    frappe.response['filecontent'] = xlsx_file.getvalue()
    frappe.response['type'] = 'binary'
