import frappe
from frappe import _
import json
from typing import Dict, List, Optional, Union
import os
from datetime import datetime
from frappe.utils import cint, get_site_name
from frappe.utils.backups import backup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_context(context: Dict) -> Dict:
    """
    Prepare and return the context for the settings management page.
    """
    if not has_settings_access():
        frappe.throw(_("غير مصرح لك بالوصول إلى صفحة الإعدادات"))
    
    context.update({
        "settings": get_system_settings(),
        "languages": get_languages(),
        "payment_methods": get_payment_methods(),
        "notifications": get_notification_settings(),
        "backups": get_backup_list(),
        "last_backup_date": get_last_backup_date()
    })
    
    return context

def has_settings_access() -> bool:
    """Check if current user has settings management access permissions."""
    return frappe.has_permission("System Settings", "write")

def get_system_settings() -> Dict:
    """Retrieve current system settings."""
    settings = frappe.get_single("System Settings")
    
    return {
        "organization_name": frappe.defaults.get_global_default('company_name'),
        "address": frappe.defaults.get_global_default('company_address'),
        "phone": frappe.defaults.get_global_default('company_phone'),
        "email": frappe.defaults.get_global_default('company_email'),
        "default_language": frappe.local.lang,
        "session_expiry": settings.session_expiry_timeout,
        "two_factor_auth": settings.enable_two_factor_auth,
        "force_password_reset": settings.force_user_to_reset_password
    }

def get_languages() -> List[Dict]:
    """Get list of available languages."""
    return [
        {"code": "ar", "name": _("العربية")},
        {"code": "en", "name": _("English")},
        {"code": "fr", "name": _("Français")}
    ]

def get_payment_methods() -> List[Dict]:
    """Get list of payment methods."""
    return frappe.get_all(
        "Payment Method",
        fields=["name", "method_name", "description", "enabled", "instructions"]
    )

def get_notification_settings() -> List[Dict]:
    """Get notification settings."""
    settings = frappe.get_single("Notification Settings")
    return [
        {
            "name": "membership_expiry",
            "title": _("تنبيه انتهاء العضوية"),
            "description": _("إرسال تنبيه قبل انتهاء العضوية"),
            "enabled": settings.enable_membership_expiry
        },
        {
            "name": "new_member",
            "title": _("عضو جديد"),
            "description": _("إشعار عند تسجيل عضو جديد"),
            "enabled": settings.enable_new_member
        },
        {
            "name": "payment_received",
            "title": _("استلام دفعة"),
            "description": _("إشعار عند استلام دفعة جديدة"),
            "enabled": settings.enable_payment_received
        }
    ]

def get_backup_list() -> List[Dict]:
    """Get list of available backups."""
    site_path = frappe.get_site_path()
    backup_path = os.path.join(site_path, "private", "backups")
    backups = []
    
    if os.path.exists(backup_path):
        for file in os.listdir(backup_path):
            if file.endswith(".sql.gz"):
                file_path = os.path.join(backup_path, file)
                stat = os.stat(file_path)
                backups.append({
                    "name": file,
                    "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "size": format_size(stat.st_size)
                })
    
    return sorted(backups, key=lambda x: x["date"], reverse=True)

def get_last_backup_date() -> Optional[str]:
    """Get the date of the last backup."""
    backups = get_backup_list()
    return backups[0]["date"] if backups else None

def format_size(size: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

@frappe.whitelist()
def save_settings(settings: Union[str, Dict]) -> Dict:
    """Save system settings."""
    if not has_settings_access():
        frappe.throw(_("غير مصرح لك بتعديل الإعدادات"))
        
    if isinstance(settings, str):
        settings = json.loads(settings)
    
    try:
        # Update System Settings
        sys_settings = frappe.get_single("System Settings")
        general = settings.get("general", {})
        
        # Update company defaults
        frappe.defaults.set_global_default('company_name', general.get('organization_name'))
        frappe.defaults.set_global_default('company_address', general.get('address'))
        frappe.defaults.set_global_default('company_phone', general.get('phone'))
        frappe.defaults.set_global_default('company_email', general.get('email'))
        
        # Update security settings
        security = settings.get("security", {})
        sys_settings.session_expiry_timeout = cint(security.get("session_expiry"))
        sys_settings.enable_two_factor_auth = security.get("two_factor_auth")
        sys_settings.force_user_to_reset_password = security.get("force_password_reset")
        sys_settings.save()
        
        # Update notification settings
        update_notification_settings(settings.get("notifications", []))
        
        frappe.clear_cache()
        
        return {
            "success": True,
            "message": _("تم حفظ الإعدادات بنجاح")
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("خطأ في حفظ الإعدادات"))
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist()
def save_payment_method(data: Union[str, Dict]) -> Dict:
    """Save a payment method."""
    if not has_settings_access():
        frappe.throw(_("غير مصرح لك بتعديل طرق الدفع"))
        
    if isinstance(data, str):
        data = json.loads(data)
    
    try:
        method_name = data.pop("name", None)
        if frappe.db.exists("Payment Method", method_name):
            doc = frappe.get_doc("Payment Method", method_name)
            doc.update(data)
        else:
            doc = frappe.get_doc({
                "doctype": "Payment Method",
                "method_name": method_name,
                **data
            })
        
        doc.save()
        
        return {
            "success": True,
            "message": _("تم حفظ طريقة الدفع بنجاح")
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("خطأ في حفظ طريقة الدفع"))
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist()
def toggle_payment_method(name: str, enabled: bool) -> Dict:
    """Toggle payment method status."""
    if not has_settings_access():
        frappe.throw(_("غير مصرح لك بتعديل طرق الدفع"))
        
    try:
        doc = frappe.get_doc("Payment Method", name)
        doc.enabled = enabled
        doc.save()
        
        return {
            "success": True,
            "message": _("تم تحديث حالة طريقة الدفع")
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("خطأ في تحديث حالة طريقة الدفع"))
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist()
def create_backup() -> Dict:
    """Create a new system backup."""
    if not has_settings_access():
        frappe.throw(_("غير مصرح لك بإنشاء نسخة احتياطية"))
        
    try:
        backup_manager = backup(ignore_files=False, force=True)
        return {
            "success": True,
            "message": _("تم إنشاء النسخة الاحتياطية بنجاح"),
            "backup_path": backup_manager.backup_path_db
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("خطأ في إنشاء النسخة الاحتياطية"))
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist()
def download_backup(name: str) -> None:
    """Download a backup file."""
    if not has_settings_access():
        frappe.throw(_("غير مصرح لك بتحميل النسخ الاحتياطية"))
    
    backup_path = os.path.join(frappe.get_site_path(), "private", "backups", name)
    
    if os.path.exists(backup_path):
        with open(backup_path, "rb") as f:
            frappe.response["filename"] = os.path.basename(backup_path)
            frappe.response["filecontent"] = f.read()
            frappe.response["type"] = "download"
    else:
        frappe.throw(_("ملف النسخة الاحتياطية غير موجود"))

@frappe.whitelist()
def delete_backup(name: str) -> Dict:
    """Delete a backup file."""
    if not has_settings_access():
        frappe.throw(_("غير مصرح لك بحذف النسخ الاحتياطية"))
        
    try:
        backup_path = os.path.join(frappe.get_site_path(), "private", "backups", name)
        
        if os.path.exists(backup_path):
            os.remove(backup_path)
            return {
                "success": True,
                "message": _("تم حذف النسخة الاحتياطية بنجاح")
            }
        else:
            return {
                "success": False,
                "message": _("ملف النسخة الاحتياطية غير موجود")
            }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("خطأ في حذف النسخة الاحتياطية"))
        return {
            "success": False,
            "message": str(e)
        }

def update_notification_settings(notifications: List[str]) -> None:
    """Update notification settings."""
    if not has_settings_access():
        frappe.throw(_("غير مصرح لك بتعديل إعدادات الإشعارات"))
        
    settings = frappe.get_single("Notification Settings")
    
    for notification in get_notification_settings():
        setattr(settings, f"enable_{notification['name']}", 
                notification['name'] in notifications)
    
    settings.save()
