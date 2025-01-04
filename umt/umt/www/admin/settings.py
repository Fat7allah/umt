import frappe
from frappe import _
import json
from typing import Dict, List, Optional, Union
import os
import shutil
from datetime import datetime
from frappe.utils import get_site_path, get_files_path, cint
from frappe.utils.password import get_decrypted_password
from frappe.utils.file_manager import save_file
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_context(context: Dict) -> Dict:
    """
    Prepare and return the context for the settings management page.
    
    This function:
    1. Validates user permissions
    2. Retrieves current settings
    3. Loads supporting data (languages, payment methods, etc.)
    4. Prepares backup information
    
    Args:
        context (Dict): Base context dictionary
    
    Returns:
        Dict: Enhanced context with settings data
    """
    if not has_settings_access():
        frappe.throw(_("غير مصرح لك بالوصول إلى صفحة الإعدادات"))
    
    # Prepare all required data
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
    """
    Check if current user has settings management access permissions.
    
    Returns:
        bool: True if user has required permissions, False otherwise
    """
    allowed_roles = {"System Manager", "Administrator"}
    user_roles = set(frappe.get_roles())
    return bool(allowed_roles & user_roles)

def get_system_settings() -> Dict:
    """
    Retrieve current system settings.
    
    Returns:
        Dict: System settings
    """
    settings = frappe.get_doc("System Settings")
    email_settings = frappe.get_doc("Email Settings")
    
    return {
        # General Settings
        "organization_name": settings.organization_name,
        "address": settings.address,
        "phone": settings.phone,
        "email": settings.email,
        "default_language": settings.language,
        
        # Email Settings
        "smtp_server": email_settings.smtp_server,
        "smtp_port": email_settings.smtp_port,
        "smtp_user": email_settings.smtp_user,
        "from_email": email_settings.from_address,
        
        # Security Settings
        "session_expiry": settings.session_expiry_time,
        "two_factor_auth": settings.enable_two_factor_auth,
        "force_password_reset": settings.force_password_reset_days > 0
    }

def get_languages() -> List[Dict]:
    """
    Get list of available languages.
    
    Returns:
        List[Dict]: List of language dictionaries
    """
    return [
        {"code": "ar", "name": _("العربية")},
        {"code": "en", "name": _("English")},
        {"code": "fr", "name": _("Français")}
    ]

def get_payment_methods() -> List[Dict]:
    """
    Get list of payment methods.
    
    Returns:
        List[Dict]: List of payment method dictionaries
    """
    return frappe.get_all(
        "Payment Method",
        fields=["name", "description", "enabled", "instructions"]
    )

def get_notification_settings() -> List[Dict]:
    """
    Get list of notification settings.
    
    Returns:
        List[Dict]: List of notification setting dictionaries
    """
    return [
        {
            "name": "membership_expiry",
            "title": _("تنبيه انتهاء العضوية"),
            "description": _("إرسال تنبيه قبل انتهاء العضوية"),
            "enabled": True
        },
        {
            "name": "new_member",
            "title": _("عضو جديد"),
            "description": _("إشعار عند تسجيل عضو جديد"),
            "enabled": True
        },
        {
            "name": "payment_received",
            "title": _("استلام دفعة"),
            "description": _("إشعار عند استلام دفعة جديدة"),
            "enabled": True
        }
    ]

def get_backup_list() -> List[Dict]:
    """
    Get list of available backups.
    
    Returns:
        List[Dict]: List of backup dictionaries with metadata
    """
    backup_path = os.path.join(get_site_path(), "private", "backups")
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
    """
    Get the date of the last backup.
    
    Returns:
        Optional[str]: Date string of last backup or None if no backups exist
    """
    backups = get_backup_list()
    return backups[0]["date"] if backups else None

def format_size(size: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size (int): Size in bytes
    
    Returns:
        str: Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

@frappe.whitelist()
def save_settings(settings: Union[str, Dict]) -> Dict:
    """
    Save system settings.
    
    Args:
        settings (Union[str, Dict]): Settings data to save
    
    Returns:
        Dict: Response indicating success or failure
    """
    if isinstance(settings, str):
        settings = json.loads(settings)
    
    try:
        # Update System Settings
        sys_settings = frappe.get_doc("System Settings")
        sys_settings.update(settings.get("general", {}))
        sys_settings.save()
        
        # Update Email Settings
        email_settings = frappe.get_doc("Email Settings")
        email_settings.update(settings.get("email", {}))
        email_settings.save()
        
        # Update Notification Settings
        update_notification_settings(settings.get("notifications", []))
        
        # Update Security Settings
        security = settings.get("security", {})
        sys_settings.session_expiry_time = cint(security.get("session_expiry"))
        sys_settings.enable_two_factor_auth = security.get("two_factor_auth")
        sys_settings.force_password_reset_days = 90 if security.get("force_password_reset") else 0
        sys_settings.save()
        
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
def test_email_settings(settings: Union[str, Dict]) -> Dict:
    """
    Test email settings by sending a test email.
    
    Args:
        settings (Union[str, Dict]): Email settings to test
    
    Returns:
        Dict: Response indicating success or failure
    """
    if isinstance(settings, str):
        settings = json.loads(settings)
    
    try:
        # Create test email
        msg = MIMEMultipart()
        msg["From"] = settings["from_email"]
        msg["To"] = frappe.session.user
        msg["Subject"] = _("اختبار إعدادات البريد الإلكتروني")
        
        body = _("هذا بريد اختباري للتحقق من صحة إعدادات البريد الإلكتروني.")
        msg.attach(MIMEText(body, "plain"))
        
        # Connect to SMTP server and send
        with smtplib.SMTP(settings["smtp_server"], int(settings["smtp_port"])) as server:
            server.starttls()
            server.login(settings["smtp_user"], settings["smtp_password"])
            server.send_message(msg)
        
        return {
            "success": True,
            "message": _("تم إرسال بريد الاختبار بنجاح")
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("خطأ في اختبار إعدادات البريد"))
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist()
def save_payment_method(data: Union[str, Dict]) -> Dict:
    """
    Save a new payment method or update existing one.
    
    Args:
        data (Union[str, Dict]): Payment method data
    
    Returns:
        Dict: Response indicating success or failure
    """
    if isinstance(data, str):
        data = json.loads(data)
    
    try:
        if frappe.db.exists("Payment Method", data["name"]):
            doc = frappe.get_doc("Payment Method", data["name"])
            doc.update(data)
        else:
            doc = frappe.get_doc({
                "doctype": "Payment Method",
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
    """
    Toggle payment method status.
    
    Args:
        name (str): Payment method name
        enabled (bool): New enabled status
    
    Returns:
        Dict: Response indicating success or failure
    """
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
    """
    Create a new system backup.
    
    Returns:
        Dict: Response indicating success or failure
    """
    try:
        from frappe.utils.backups import backup
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
    """
    Download a backup file.
    
    Args:
        name (str): Backup file name
    """
    if not has_settings_access():
        frappe.throw(_("غير مصرح لك بتحميل النسخ الاحتياطية"))
    
    backup_path = os.path.join(get_site_path(), "private", "backups", name)
    
    if os.path.exists(backup_path):
        with open(backup_path, "rb") as f:
            frappe.response["filename"] = os.path.basename(backup_path)
            frappe.response["filecontent"] = f.read()
            frappe.response["type"] = "download"
    else:
        frappe.throw(_("ملف النسخة الاحتياطية غير موجود"))

@frappe.whitelist()
def delete_backup(name: str) -> Dict:
    """
    Delete a backup file.
    
    Args:
        name (str): Backup file name
    
    Returns:
        Dict: Response indicating success or failure
    """
    try:
        backup_path = os.path.join(get_site_path(), "private", "backups", name)
        
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
    """
    Update notification settings in the system.
    
    Args:
        notifications (List[str]): List of enabled notification types
    """
    settings = frappe.get_doc("Notification Settings")
    
    for notification in get_notification_settings():
        setattr(settings, f"enable_{notification['name']}", 
                notification['name'] in notifications)
    
    settings.save()
