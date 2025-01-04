import frappe
from frappe import _
import json
from frappe.utils import cstr
from typing import Dict, List, Optional, Union

def get_context(context: Dict) -> Dict:
    """
    Prepare and return the context for the structure management page.
    
    This function:
    1. Validates user permissions
    2. Retrieves organizational structure data
    3. Loads roles and permissions
    4. Prepares statistics
    
    Args:
        context (Dict): Base context dictionary
    
    Returns:
        Dict: Enhanced context with structure management data
    """
    if not has_structure_access():
        frappe.throw(_("غير مصرح لك بالوصول إلى صفحة إدارة الهياكل"))
    
    # Prepare all required data
    context.update({
        "organization_tree": get_organization_tree(),
        "provinces": get_provinces(),
        "roles": get_roles(),
        "permissions": get_permissions(),
        "province_count": get_structure_count("Province"),
        "office_count": get_structure_count("Office"),
        "position_count": get_structure_count("Position"),
        "vacant_count": get_vacant_positions_count()
    })
    
    return context

def has_structure_access() -> bool:
    """
    Check if current user has structure management access permissions.
    
    Returns:
        bool: True if user has required permissions, False otherwise
    """
    allowed_roles = {"System Manager", "Structure Manager", "HR Manager"}
    user_roles = set(frappe.get_roles())
    return bool(allowed_roles & user_roles)

def get_organization_tree() -> List[Dict]:
    """
    Build the complete organizational structure tree.
    
    Returns:
        List[Dict]: List of tree nodes with their relationships
    """
    def build_node(doc: Dict) -> Dict:
        """Helper function to build a tree node"""
        return {
            "id": doc.name,
            "text": doc.title,
            "icon": get_node_icon(doc.type),
            "state": {"opened": True},
            "children": []
        }
    
    def get_node_icon(node_type: str) -> str:
        """Helper function to get appropriate icon for node type"""
        icons = {
            "province": "fa fa-building",
            "office": "fa fa-briefcase",
            "department": "fa fa-folder",
            "position": "fa fa-user"
        }
        return icons.get(node_type, "fa fa-circle")
    
    # Get all structures
    structures = frappe.get_all(
        "Organization_Structure",
        fields=["name", "title", "parent_structure", "type"],
        order_by="creation"
    )
    
    # Build tree structure
    tree = []
    node_map = {}
    
    for structure in structures:
        node = build_node(structure)
        node_map[structure.name] = node
        
        if structure.parent_structure:
            parent = node_map.get(structure.parent_structure)
            if parent:
                parent["children"].append(node)
        else:
            tree.append(node)
    
    return tree

def get_provinces(filters: Optional[Dict] = None) -> List[Dict]:
    """
    Retrieve provinces with their related information.
    
    Args:
        filters (Optional[Dict]): Additional filters to apply
    
    Returns:
        List[Dict]: List of provinces with counts and status
    """
    if not filters:
        filters = {}
    
    provinces = frappe.get_all(
        "Province",
        fields=[
            "name", "head_name", "status",
            "(select count(*) from tabOffice where province = name) as office_count",
            "(select count(*) from tabMember where province = name) as member_count"
        ],
        filters=filters,
        order_by="name"
    )
    
    return provinces

def get_roles() -> List[Dict]:
    """
    Get list of roles with their member counts.
    
    Returns:
        List[Dict]: List of roles and their usage statistics
    """
    roles = frappe.get_all(
        "Role",
        fields=[
            "name", "description",
            "(select count(*) from `tabHas Role` where role = name) as member_count"
        ],
        filters={"disabled": 0}
    )
    
    return roles

def get_permissions() -> List[Dict]:
    """
    Get list of available permissions.
    
    Returns:
        List[Dict]: List of permissions with descriptions
    """
    return frappe.get_all(
        "Permission",
        fields=["name", "description"],
        filters={"enabled": 1}
    )

def get_structure_count(doctype: str) -> int:
    """
    Get count of structures by type.
    
    Args:
        doctype (str): Document type to count
    
    Returns:
        int: Count of structures
    """
    return frappe.db.count(doctype)

def get_vacant_positions_count() -> int:
    """
    Get count of vacant positions.
    
    Returns:
        int: Number of vacant positions
    """
    return frappe.db.count("Position", {"status": "Vacant"})

@frappe.whitelist()
def get_parent_structures() -> List[Dict]:
    """
    Get list of structures that can be parents.
    
    Returns:
        List[Dict]: List of potential parent structures
    """
    return frappe.get_all(
        "Organization_Structure",
        fields=["name", "title"],
        filters={"type": ["in", ["province", "office", "department"]]}
    )

@frappe.whitelist()
def save_structure(data: Union[str, Dict]) -> Dict:
    """
    Save a new structure or update existing one.
    
    Args:
        data (Union[str, Dict]): Structure data
    
    Returns:
        Dict: Response indicating success or failure
    """
    if isinstance(data, str):
        data = json.loads(data)
    
    try:
        if data.get("name"):
            # Update existing structure
            doc = frappe.get_doc("Organization_Structure", data["name"])
            doc.update(data)
        else:
            # Create new structure
            doc = frappe.get_doc({
                "doctype": "Organization_Structure",
                **data
            })
        
        doc.save()
        
        return {
            "success": True,
            "message": _("تم حفظ الهيكل بنجاح"),
            "structure": doc.name
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("خطأ في حفظ الهيكل"))
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist()
def save_role(data: Union[str, Dict]) -> Dict:
    """
    Save a new role or update existing one.
    
    Args:
        data (Union[str, Dict]): Role data including permissions
    
    Returns:
        Dict: Response indicating success or failure
    """
    if isinstance(data, str):
        data = json.loads(data)
    
    try:
        permissions = json.loads(data.pop("permissions", "[]"))
        
        if data.get("role_name"):
            # Update existing role
            doc = frappe.get_doc("Role", data["role_name"])
            doc.update(data)
        else:
            # Create new role
            doc = frappe.get_doc({
                "doctype": "Role",
                **data
            })
        
        # Update permissions
        doc.permissions = []
        for perm in permissions:
            doc.append("permissions", {"permission": perm})
        
        doc.save()
        
        return {
            "success": True,
            "message": _("تم حفظ الدور بنجاح"),
            "role": doc.name
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("خطأ في حفظ الدور"))
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist()
def get_province(name: str) -> Dict:
    """
    Get province details.
    
    Args:
        name (str): Province name/ID
    
    Returns:
        Dict: Province details
    """
    return frappe.get_doc("Province", name).as_dict()

@frappe.whitelist()
def delete_province(name: str) -> Dict:
    """
    Delete a province if it has no dependencies.
    
    Args:
        name (str): Province name/ID
    
    Returns:
        Dict: Response indicating success or failure
    """
    try:
        # Check for dependencies
        if frappe.db.count("Office", {"province": name}) > 0:
            raise ValueError(_("لا يمكن حذف الإقليم لوجود مكاتب مرتبطة به"))
        
        if frappe.db.count("Member", {"province": name}) > 0:
            raise ValueError(_("لا يمكن حذف الإقليم لوجود أعضاء مرتبطين به"))
        
        frappe.delete_doc("Province", name)
        
        return {
            "success": True,
            "message": _("تم حذف الإقليم بنجاح")
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("خطأ في حذف الإقليم"))
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist()
def get_role(name: str) -> Dict:
    """
    Get role details including permissions.
    
    Args:
        name (str): Role name
    
    Returns:
        Dict: Role details with permissions
    """
    doc = frappe.get_doc("Role", name)
    return {
        "name": doc.name,
        "description": doc.description,
        "permissions": [p.permission for p in doc.permissions]
    }

@frappe.whitelist()
def delete_role(name: str) -> Dict:
    """
    Delete a role if it has no users assigned.
    
    Args:
        name (str): Role name
    
    Returns:
        Dict: Response indicating success or failure
    """
    try:
        # Check for users with this role
        if frappe.db.count("Has Role", {"role": name}) > 0:
            raise ValueError(_("لا يمكن حذف الدور لوجود مستخدمين مرتبطين به"))
        
        frappe.delete_doc("Role", name)
        
        return {
            "success": True,
            "message": _("تم حذف الدور بنجاح")
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("خطأ في حذف الدور"))
        return {
            "success": False,
            "message": str(e)
        }
