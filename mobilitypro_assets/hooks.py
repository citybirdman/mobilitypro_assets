from . import __version__ as app_version

app_name = "mobilitypro_assets"
app_title = "Mobilitypro Assets"
app_publisher = "Ahmed Zaytoon"
app_description = "Doctypes and custom more reports to deal with in mobility"
app_icon = "mobilitypro_assets/boxes.svg"
app_color = "green"
app_email = "citybirdman@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/mobilitypro_assets/css/mobilitypro_assets.css"
# app_include_js = "/assets/mobilitypro_assets/js/mobilitypro_assets.js"

# include js, css files in header of web template
# web_include_css = "/assets/mobilitypro_assets/css/mobilitypro_assets.css"
# web_include_js = "/assets/mobilitypro_assets/js/mobilitypro_assets.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "mobilitypro_assets/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

before_install = "mobilitypro_assets.install.before_install"
# after_install = "mobilitypro_assets.install.after_install"

# Uninstallation
# ------------

before_uninstall = "mobilitypro_assets.uninstall.before_uninstall"
# after_uninstall = "mobilitypro_assets.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "mobilitypro_assets.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"mobilitypro_assets.tasks.make_expense_entries"
	],
#	"daily": [
#		"mobilitypro_assets.tasks.daily"
#	],
#	"hourly": [
#		"mobilitypro_assets.tasks.hourly"
#	],
#	"weekly": [
#		"mobilitypro_assets.tasks.weekly"
#	]
#	"monthly": [
#		"mobilitypro_assets.tasks.monthly"
#	]
}

# Testing
# -------

# before_tests = "mobilitypro_assets.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "mobilitypro_assets.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "mobilitypro_assets.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Request Events
# ----------------
# before_request = ["mobilitypro_assets.utils.before_request"]
# after_request = ["mobilitypro_assets.utils.after_request"]

# Job Events
# ----------
# before_job = ["mobilitypro_assets.utils.before_job"]
# after_job = ["mobilitypro_assets.utils.after_job"]

# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"mobilitypro_assets.auth.validate"
# ]

