from odoo import fields, models

class ResUsers(models.Model):
    _inherit = 'res.users'

    group_enrollee_readonly = fields.Boolean(
        string='Read Only Access',
        implied_group='hmo_management.group_enrollee_readonly',
    )
    group_enrollee_operations = fields.Boolean(
        string='Operations Access',
        implied_group='hmo_management.group_enrollee_operations',
    )
    group_enrollee_admin = fields.Boolean(
        string='IT Admin Access',
        implied_group='hmo_management.group_enrollee_admin',
    )
    group_call_center = fields.Boolean(
        string='Call Center Access',
        implied_group='hmo_management.group_call_center',
    )
    group_executive = fields.Boolean(
        string='Executive Access',
        implied_group='hmo_management.group_executive',
    )
    group_health_services = fields.Boolean(
        string='Health Services Access',
        implied_group='hmo_management.group_health_services',
    )
    group_purchase_confirm_button = fields.Boolean(
        string='Purchase Confirm Button',
        implied_group='hmo_management.group_purchase_confirm_button',
    )
    group_approve_claims = fields.Boolean(
        string='Approve Claims Menu',
        implied_group='hmo_management.group_approve_claims',
    )
    group_actuary = fields.Boolean(
        string='Actuary Access',
        implied_group='hmo_management.group_actuary',
    )
    group_operations_menu = fields.Boolean(
        string='Operations Menu',
        implied_group='hmo_management.group_operations_menu',
    )
    group_provider_bill = fields.Boolean(
        string='Provider Bill Access',
        implied_group='hmo_management.group_provider_bill',
    )
    group_provider_portal = fields.Boolean(
        string='Provider Portal Access',
        implied_group='hmo_management.group_provider_portal',
    )
    group_purchase_menu = fields.Boolean(
        string='Purchase Menu',
        implied_group='hmo_management.group_purchase_menu',
    )
    group_process_claims = fields.Boolean(
        string='Process Claims',
        implied_group='hmo_management.group_process_claims',
    )