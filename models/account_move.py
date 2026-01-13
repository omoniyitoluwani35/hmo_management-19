# Copyright 2019 Nacmara
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from logging import getLogger

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime
from odoo import tools
import dateutil.parser

_logger = getLogger(__name__)

class AccountInvoiceLine(models.Model):
    """ Override AccountInvoice_line to add the link to the purchase order line it is related to"""
    _inherit = 'account.move.line'

    enrollee_id = fields.Many2one('enrollee', related='purchase_line_id.order_id.enrollee_id', string='Enrollee', store=False, readonly=True,
        help='Associated Enrollee. Filled in automatically when a claim is chosen on the vendor bill.')
    line_date = fields.Datetime(related='purchase_line_id.order_id.date_order', string='Claims Date', store=False, readonly=True)
    provider_cost = fields.Float(related='purchase_line_id.provider_price', string='Provider Cost', readonly=True)
    purchase_id = fields.Many2one(related='purchase_line_id.order_id', string='Claim Number', readonly=True)
    x_m_id = fields.Integer(string="Migration_ID")
	
class AccountInvoice(models.Model):
    """ Override AccountInvoice_line to add the link to the purchase order line it is related to"""
    _inherit = 'account.move'

    x_m_id = fields.Integer(string="Migration_ID")
    nhis_ref = fields.Char(related='partner_id.nhis_ref', string='NHIS Ref')
    line_account_id = fields.Many2one('account.account', string='Account')
    enrollee_id = fields.Many2one('enrollee', string='Enrollee', compute='_get_enrollee',readonly=True)
    partner_id_category = fields.Char(related='partner_id.category_id.name', string='Category')
    
    def _get_enrollee(self):
        for record in self:
            #raise UserError('Hello')
            if record.partner_id.category_id.name == 'refund':
                for line in record.invoice_line_ids:
                    #if line.partner_id.name == 'Refund Provider' :
                    record.enrollee_id = line.enrollee_id.id
                    #raise UserError(_('Enrollee %s ') % line.enrollee_id.code)
                    break
            else:
                record.enrollee_id = None

    @api.onchange('line_account_id')
    def onchange_line_account_id(self):
        for line in self.line_ids:
            line.account_id = line.move_id.line_account_id.id
        return {}


class Account(models.Model):
    _inherit = 'account.account'

    account_expense_type = fields.Selection([('private', 'Private Capitation Account'),('nhis','NHIS Capitation Account'),('payable','Payable Account'),('bank','Bank')], string='Capitation Wizard Accounts')