"""
Configuration for docs
"""

# source_link = "https://github.com/[org_name]/umt"
# headline = "App that does everything"
# sub_heading = "Yes, you got that right the first time, everything"

def get_context(context):
	context.brand_html = "UNEM Management Tool"
	context.favicon = 'assets/umt/images/favicon.ico'
	context.top_bar_items = [
		{"label": "Documentation", "url": "/docs"},
		{"label": "User Guide", "url": "/user-guide"},
		{"label": "API", "url": "/api"}
	]
