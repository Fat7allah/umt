app_name = "umt"
app_title = "UNEM Management System"
app_publisher = "UNEM"
app_description = "Comprehensive management system for UNEM (Union Nationale de l'Enseignement au Maroc)"
app_email = "admin@unem.ma"
app_license = "MIT"

# Document Events
doc_events = {
    "Member": {
        "after_insert": "umt.doctype.member.member.generate_membership_card",
        "on_update": "umt.doctype.member.member.update_membership_status"
    }
}

# Fixtures
fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [
            ["dt", "in", (
                "Member",
                "Membership_Card",
                "UNEM_Structure",
                "Mutual_Structure",
                "Income_Entry",
                "Expense_Entry"
            )]
        ]
    }
]

# Translation
translation_modules = ["py", "js"]

# Language
language_data = {
    "ar": {
        "name": "Arabic",
        "direction": "rtl"
    }
}

# Workspaces
default_workspaces = {
    "UNEM": {
        "category": "Modules",
        "icon": "education",
        "type": "module",
        "link": "modules/UNEM",
        "label": "UNEM"
    }
}
