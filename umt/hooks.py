app_name = "umt"
app_title = "UNEM Management System"
app_publisher = "UNEM"
app_description = "Comprehensive management system for UNEM (Union Nationale de l'Enseignement au Maroc)"
app_email = "admin@unem.ma"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/umt/css/umt.css"
# app_include_js = "/assets/umt/js/umt.js"

# include js, css files in header of web template
web_include_css = [
    "/assets/umt/css/umt.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css"
]
web_include_js = [
    "/assets/umt/js/umt.js"
]

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Member": {
        "after_insert": "umt.doctype.member.member.generate_membership_card",
        "on_update": "umt.doctype.member.member.update_membership_status"
    },
    "Payment Method": {
        "on_update": "umt.umt.doctype.payment_method.payment_method.on_update",
    },
    "Notification Settings": {
        "on_update": "umt.umt.doctype.notification_settings.notification_settings.on_update",
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

# Website Route Rules
# ------------------

website_route_rules = [
    {"from_route": "/admin/settings", "to_route": "admin/settings"},
    {"from_route": "/admin/dashboard", "to_route": "admin/dashboard"},
    {"from_route": "/admin/members", "to_route": "admin/members"},
    {"from_route": "/admin/structure", "to_route": "admin/structure"}
]

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
