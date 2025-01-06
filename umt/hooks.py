app_name = "umt"
app_title = "UNEM Management Tool"
app_publisher = "UMT"
app_description = "UNEM Management Tool"
app_email = "admin@unem.ma"
app_license = "MIT"

# Includes in <head>
app_include_css = "/assets/umt/css/umt.css"
app_include_js = "/assets/umt/js/umt.js"

# Document Events
doc_events = {
    "Member": {
        "after_insert": "umt.doctype.member.member.generate_membership_card",
        "validate": "umt.doctype.member.member.validate_member",
        "on_update": "umt.doctype.member.member.update_member"
    },
    "Payment Method": {
        "on_update": "umt.doctype.payment_method.payment_method.on_update",
    },
    "Notification Settings": {
        "on_update": "umt.doctype.notification_settings.notification_settings.on_update",
    }
}

# Website Route Rules
website_route_rules = [
    {"from_route": "/admin/settings", "to_route": "admin/settings"},
    {"from_route": "/admin/dashboard", "to_route": "admin/dashboard"},
    {"from_route": "/admin/members", "to_route": "admin/members"},
    {"from_route": "/admin/structure", "to_route": "admin/structure"}
]

# Scheduled Tasks
scheduler_events = {
    "daily": [
        "umt.tasks.daily"
    ],
    "weekly": [
        "umt.tasks.weekly"
    ],
    "monthly": [
        "umt.tasks.monthly"
    ]
}

# DocType JS
doctype_js = {
    "Member": "public/js/member.js",
    "Payment Method": "public/js/payment_method.js"
}
