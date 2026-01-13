# Copyright 2019 The Nacmara Company
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "HMO Management",
    "summary": "HMO Management System",
    "version": "19.0.1.0.1",
    "category": "Purchases",
    "website": "",
    "author": "MOdel Caarbon",
    "license": "AGPL-3",
    "depends": [
        "base",
        "product",
        "purchase",
        "sale_management",
    ],
    "sequence": -1,
    "data": [
        # Security must be loaded first
        "security/claims_security.xml",
        "security/ir.model.access.csv",
        
        # # Views
        "views/tariff_view.xml",
        "views/claims_diagnosis_view.xml",
        "views/claims_registration_view.xml",
        "views/benefits_view.xml",
        "views/icd_view.xml",
        "views/res_partner.xml",
        "views/claim_view.xml",
        # "views/company_view.xml",
        "views/account_move.xml",
        "views/policy_view.xml",
        "views/print_templates.xml",
        "views/capitation_report_view.xml",
        "views/invoice_view.xml",
        "views/enrollee_view.xml",
        "views/encounter_view.xml",
        "views/visitation_view.xml",
        "views/product_template_view.xml",
        "views/res_user.xml",
        
        # # Wizards
        "wizard/monthly_birthday_reports_view.xml",
        "wizard/create_policy_view.xml",
        "wizard/create_capitation_view.xml",
        "wizard/enrollee_operations_view.xml",
        "wizard/actuary_reports_view.xml",
        "wizard/actuary_reports_report.xml",
        
        # # Reports
        "views/dev_enr_profile_report_template.xml",
        "views/dev_enr_profile_report_call.xml",
        "report/template.xml",
        "report/cap_alone_report_template.xml",
        "report/cap_alone_report_call.xml",
        "report/enrollee_list_report_template.xml",
        "report/enrollee_list_coverage_report_template.xml",
        
        # # Menu (must be last)
        "views/menu.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}