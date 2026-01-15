# Copyright 2019 Nacmara
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from logging import getLogger

from odoo import tools
import dateutil.parser

from datetime import datetime, time
from dateutil.relativedelta import relativedelta

from markupsafe import escape, Markup
from pytz import timezone, UTC
from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, format_amount, format_date, formatLang, get_lang, groupby
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError, ValidationError

_logger = getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    _order = "date_order desc, id desc"

    nhis = fields.Boolean(string = 'NHIS')
    is_nhis = fields.Boolean (string = 'Is NHIS')
    hcp_id = fields.Many2one('res.partner', string='HCP', domain=['&',('supplier','=',True),('hcp','=',True)])
    enrollee_id = fields.Many2one('enrollee', string='Enrollee')
    admission_date = fields.Date(string ='Date of Admission')
    discharge_date = fields.Date(string ='Date of Discharge')
    amount_difference = fields.Monetary(string = 'Tariff Difference', compute='_compute_amount')
    analytic_id = fields.Many2one('account.analytic.account',string='Employer')
    diagnosis_lines = fields.One2many('claims.diagnosis','claim_id',string= 'Diagnosis & Investigations',copy=True)
    override = fields.Boolean(string = 'Override duplicate claims warning')
    plan_id = fields.Many2one('product.product', related='enrollee_id.plan', string = 'Health Plan', readonly=True, domain=[('sale_ok','=',True)])
    claim_reg_id = fields.Many2one('claims.registration', string = 'Claim Registration No.')
    primary_provider_id = fields.Many2one('res.partner', string='Secondary Provider',domain=['&',('supplier','=',True),('hcp','=',True)])
    claim_type = fields.Selection([('claim', 'Claim'), ('refund','Refund')], string='Claim Type')
    expiry = fields.Char (string = 'Days to coverage expiry')
    provider_total = fields.Monetary(string = 'Provider Total')
    x_m_id = fields.Integer(string="Migration_ID")
    state = fields.Selection([
        ('draft', 'Pre-Auth/Draft'),
        ('auth claim', 'Authorization Request'),
        ('auth reject', 'Rejected Request'),
        ('submitted','Submitted'),
        ('draft claim', 'Draft Claim'),
        ('sent', 'Pre-Auth Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Approved'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
        ], string='Status', readonly=True, select=True, copy=False, default='draft', tracking=3)
    nhis_ref = fields.Char(related='partner_id.nhis_ref', string='NHIS Ref')
    audit_check = fields.Boolean(string='Audit Check', track_visibility='onchange')
    audit_check_readonly = fields.Boolean(related='audit_check', string='Checked by Auditor')
    enrollee_code = fields.Char(related='enrollee_id.code', string='Code', store=True)
    diagnosis = fields.Char(string='Diagnosis',compute='_get_diagnosis',)

    @api.depends('diagnosis_lines.diagnosis')
    def _get_diagnosis(self):
        for part in self:
            part.diagnosis=False
            for line in part.diagnosis_lines:
                if line.diagnosis:
                    part.diagnosis = line.diagnosis
                else:
                    part.diagnosis = line.details
    
    #@api.depends('order_line.invoice_lines.move_id')
    def _compute_invoices(self):
        orders = self.env['purchase.order'].search([('invoice_count','=',False),('state','=','purchase')])
        for order in orders:
            invoices = order.mapped('order_line.invoice_lines.move_id')
            order.invoice_ids = invoices
            order.invoice_count = len(invoices)
            
    #@api.depends('order_line.invoice_lines.move_id')
    def _compute_invoice_manual(self):
        #for order in self: 
        orders = self.env['purchase.order'].search([('invoice_count','=',False)])
        raise UserError(_("%s") % len(orders))
        for order in orders: #if self.invoice_count == 0 or self.invoice_count == False:
            invoices = []
            for line in order.order_line:
                #raise UserError("Holl1")
                invoice_lines = self.env['account.move.line'].search([('purchase_line_id','=',line.id)])
                if invoice_lines:
                    raise UserError("Holla2")
                for invoice_line in invoice_lines:
                    invoice = self.env['account.move'].search([('id','=',invoice_line.move_id)])
                    #raise UserError("Holla")
                    invoices.append(invoice)
            order.invoice_count = len(invoices)
            order.invoice_ids = invoices

    @api.depends('provider_total','amount_total')
    def _compute_amount(self):
        for part in self:
            part.amount_difference = part.provider_total - part.amount_total

    #
    #def _amount_all_old(self):
    #    for order in self:
    #        amount_untaxed = amount_tax = provider_total = 0.0
    #        anal_id = None
    #        if order.enrollee_id:
    #            sql="select id from account_analytic_account where partner_id = (select employer from enrollee where id = " + str(order.enrollee_id.id) + ")"
    #            rc = self.env.cr.execute(sql)
    #            
    #            for row in self.env.cr.dictfetchall():
    #                anal_id	 = row['id']
    #
    #        for line in order.order_line:
    #            amount_untaxed += line.price_subtotal
    #            amount_tax += line.price_tax
    #            line.account_analytic_id=anal_id
    #            provider_total += line.provider_price
    #        order.update({
    #            'amount_untaxed': order.currency_id.round(amount_untaxed),
    #            'amount_tax': order.currency_id.round(amount_tax),
    #            'amount_total': amount_untaxed + amount_tax,
    #            'provider_total': provider_total,
    #        })

    @api.depends('order_line.price_total')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = provider_total = 0.0
                        
            order_lines = order.order_line.filtered(lambda x: not x.display_type)
            #order_lines.account_analytic_id = anal_id
            order.amount_untaxed = sum(order_lines.mapped('price_subtotal'))
            order.amount_tax = sum(order_lines.mapped('price_tax'))
            order.amount_total = order.amount_untaxed + order.amount_tax
            order.provider_total = sum(order_lines.mapped('provider_price'))

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        # Ensures all properties and fiscal positions
        # are taken with the company of the order
        # if not defined, with_company doesn't change anything.
        self = self.with_company(self.company_id)
        default_currency = self._context.get("default_currency_id")
        if not self.partner_id:
            self.fiscal_position_id = False
            self.currency_id = default_currency or self.env.company.currency_id.id
        else:
            self.fiscal_position_id = self.env['account.fiscal.position']._get_fiscal_position(self.partner_id)
            self.payment_term_id = self.partner_id.property_supplier_payment_term_id.id
            self.currency_id = default_currency or self.partner_id.property_purchase_currency_id.id or self.env.company.currency_id.id
            if self.partner_id.nhis:
                self.nhis = True
            else:
                self.nhis = False
        return {}

    @api.onchange('is_nhis')
    def onchange_is_nhis(self):
        #toggle to view only nhis or private providers
        domain = {}
        if self.is_nhis== False:
            domain = {'partner_id':[('hcp','=',True),('nhis','=',False)]}
        elif self.is_nhis == True:
            domain = {'partner_id':[('nhis','=',True)]}
        return {'domain':domain}

    @api.onchange('enrollee_id')
    def _onchange_enrollee(self):
        self.expiry = " "
        if self.enrollee_id:
            #if not self.partner_id:
            self.primary_provider_id = self.enrollee_id.hcp.id
            if self.enrollee_id.end_date:
                od = datetime.strptime(str(self.date_order),"%Y-%m-%d %H:%M:%S")
                ed = datetime.strptime(str(self.enrollee_id.end_date),"%Y-%m-%d")
                diff =  ed - od
                self.expiry = diff
            sql="select id from account_analytic_account where partner_id = (select employer from enrollee where id = " + str(self.enrollee_id.id) + ")"
            rc = self.env.cr.execute(sql)
            anal_id = None
            for row in self.env.cr.dictfetchall():
                anal_id	 = row['id']
            self.analytic_id = anal_id
			
    
    def check_limit(self):
        limit = False
        amount_used = 0.00
        amount_used = self.get_utilization()
        if not self.enrollee_id.enforce and self.enrollee_id.policy_start_date != False:
            if amount_used + self.amount_total > self.enrollee_id.plan.plan_limit:
                limit = True
        return limit

    
    def get_utilization(self):
        limit=0.00
        sql="select coalesce(sum(amount_total),0.00)as sum from purchase_order o inner join enrollee e on o.enrollee_id = e.id where date_order >= e.policy_start_date and (o.state = 'purchase' or o.state = 'done') and e.id = " + str(self.enrollee_id.id)
        rc = self.env.cr.execute(sql)
        for row in self.env.cr.dictfetchall():
            limit = row['sum']
        return limit

    
    def button_draft_claim(self):
        self.write({'state': 'draft claim'})
        if self.api_ref:
            self.action_upload_auth(1)
        return {}
		
    
    def button_auth_claim(self):
        self.write({'state': 'auth claim'})
        return {}

    
    def button_done(self):
        self.write({'state': 'done','invoice_status':'no'})
        return {}
        
    def button_reject(self):
        self.write({'state': 'auth reject'})
        if self.api_ref != False:
            self.action_upload_auth(1)
        return {}

    
  
    def button_confirm(self):
        for order in self:
            if not order.order_line:
                raise UserError(_('Cannot confirm claim without any lines'))
            if not order.claim_reg_id and order.claim_type == 'claim':
                raise UserError(_('Cannot confirm claim without registration number'))
            if order.claim_type in ('claim','refund'):
                #if order.check_limit():
                #    raise UserError(_('Enrollee has reached plan limit. Contact H/Ops to override this limit.'))
                if order.provider_total < order.amount_total:
                    raise UserError(_('Cannot confirm claim. Amount on Bill is less than Vetted Amount.'))
                dt = order.date_order.date()
                sql="select coalesce(count(id),0) as count from purchase_order where enrollee_id = " + str(order.enrollee_id.id) + " and partner_id = " + str(order.partner_id.id) + " and date(date_order) = '" + str(dt) + "' and provider_total = " + str(order.provider_total)  + " and name <> '" + str(order.name) + "'"
                rc = self.env.cr.execute(sql)
                for row in self.env.cr.dictfetchall():
                    if row['count'] > 0 and not order.override and order.provider_total > 0 :
                        raise UserError(_('Cannot confirm claim. Claim has already been captured.'))
                        
            if order.state not in ['draft claim', 'sent','submitted']:
                continue
            order.order_line._validate_analytic_distribution()
            order._add_supplier_to_product()
            # Deal with double validation process
            #if order._approval_allowed():
            #    order.button_approve()
            #else:
            order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    line_date = fields.Datetime(related='order_id.date_order', string='Date')
    pricing_difference = fields.Selection([
        ('tariff difference','Tariff Difference'),
        ('capitated','Capitated Drugs'),
        ('capitated_service','Capitated Service'),
        ('50sec','50% cost of Sec. Drugs'),
        ('60chron','60% cost of Chronic Drugs'),
        ('90drug','90% cost of Drugs'),
        ('not justified','Not Justified'),
        ('not covered','Not Covered'),
        ('nil','Nil Approval'),
        ('unnecessary','Not Medically Necessary'),
        ('drug overcharge','Overcharge')],
        string = 'Variation Remarks')
    provider_price = fields.Float(string = 'Provider Price')
    x_m_id = fields.Integer(string="Migration_ID")
    account_analytic_id = fields.Many2one('account.analytic.account', string='Employer', related='order_id.analytic_id', store=True)
    enrollee_id = fields.Many2one('enrollee', related='order_id.enrollee_id', string='Enrollee', store=True, 
        help='Associated Enrollee. Filled in automatically when a claim is chosen on the vendor bill.')
    _domain_product_ids = fields.Many2many(
        'product.product',
        string='Allowed Products',
        store=False,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product'
    )



    #@api.depends('order_id.partner_id')
    def _compute_product_domain(self):
        for line in self:
            partner = line.order_id.partner_id
            if partner.tariff_id:
                line._domain_product_ids = partner.tariff_id.product_ids
            else:
                line._domain_product_ids = self.env['product.product']
   

    #@api.depends('order_id.partner_id')
    def _compute_product_domain_old(self):
        for line in self:
            partner = line.order_id.partner_id
            if partner.tariff_id:
                template_ids = self.env['tariff.lines'].search([
                    ('tariff_id', '=', partner.tariff_id.id)
                ]).mapped('product_id')
                # Get matching product.product records
                products = self.env['product.product'].search([
                    ('product_tmpl_id', 'in', template_ids.ids)
                ])
            else:
                products = self.env['product.product'].search([])  # Or whatever logic you want
            line._domain_product_ids = products

    @api.onchange('order_id')
    def _onchange_order_domain(self):
        """Set product domain when line is added or order changes."""
        for line in self:
            domain = [('is_drug', '=', True)]
            partner = line.order_id.partner_id
            _logger.info("hellpppp")
            if partner and partner.tariff_id and partner.tariff_id.product_ids:
                domain.append(('id', 'in', partner.tariff_id.product_ids.ids))
            return {'domain': {'product_id': domain}}
    #new_enrollee_id = fields.Many2one('enrollee', string='Enrollee')

    #@api.onchange('product_id')
    #def onchange_product_id(self):
    #    if not self.product_id:
    #        return

    #    # Reset date, price and quantity since _onchange_quantity will provide default values
    #    self.price_unit = self.product_qty = 0.0
    #    
    #    self.new_enrollee_id = self.order_id.enrollee_id

    #    self._product_id_change()

    #    self._suggest_quantity()        
        
    @api.depends('product_qty', 'product_uom_id')
    def _compute_price_unit_and_date_planned_and_name(self):
        for line in self:
            if not line.product_id or line.invoice_lines:
                continue
            params = {'order_id': line.order_id}
            seller = line.product_id._select_seller(
                partner_id=line.partner_id,
                quantity=line.product_qty,
                date=line.order_id.date_order and line.order_id.date_order.date(),
                uom_id=line.product_uom_id,
                params=params)

            if seller or not line.date_planned:
                line.date_planned = line._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            # If not seller, use the standard price. It needs a proper currency conversion.
            if not seller:
                unavailable_seller = line.product_id.seller_ids.filtered(
                    lambda s: s.partner_id == line.order_id.partner_id)
                if not unavailable_seller and line.price_unit and line.product_uom_id == line._origin.product_uom_id:
                    # Avoid to modify the price unit if there is no price list for this partner and
                    # the line has already one to avoid to override unit price set manually.
                    continue
                po_line_uom = line.product_uom_id or line.product_id.uom_po_id
                price_unit = line.env['account.tax']._fix_tax_included_price_company(
                    line.product_id.uom_id._compute_price(line.product_id.standard_price, po_line_uom),
                    line.product_id.supplier_taxes_id,
                    line.taxes_id,
                    line.company_id,
                )
                price_unit = line.product_id.currency_id._convert(
                    price_unit,
                    line.currency_id,
                    line.company_id,
                    line.date_order,
                    False
                )
                line.price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places, self.env['decimal.precision'].precision_get('Product Price')))
                continue
                
            pricelist = self.partner_id.tariff_id.id

            price_unit = line.env['account.tax']._fix_tax_included_price_company(seller.price, line.product_id.supplier_taxes_id, line.taxes_id, line.company_id) if seller else 0.0
            price_unit = seller.currency_id._convert(price_unit, line.currency_id, line.company_id, line.date_order, False)
            price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places, self.env['decimal.precision'].precision_get('Product Price')))
            if self.partner_id.tariff_id:
                price_unit = self.env['tariff.lines'].on_product_change(self.product_id.id, self.partner_id.tariff_id.id, price_unit)
            line.price_unit = seller.product_uom_id._compute_price(price_unit, line.product_uom_id)

            # record product names to avoid resetting custom descriptions
            default_names = []
            vendors = line.product_id._prepare_sellers({})
            for vendor in vendors:
                product_ctx = {'seller_id': vendor.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
                default_names.append(line._get_product_purchase_description(line.product_id.with_context(product_ctx)))
            if not line.name or line.name in default_names:
                product_ctx = {'seller_id': seller.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
                line.name = line._get_product_purchase_description(line.product_id.with_context(product_ctx))

    
    @api.depends('product_qty', 'product_uom_id')
    def _compute_price_unit_and_date_planned_and_name(self):
        for line in self:
            if not line.product_id or line.invoice_lines:
                continue
            params = {'order_id': line.order_id}
            seller = line.product_id._select_seller(
                partner_id=line.partner_id,
                quantity=line.product_qty,
                date=line.order_id.date_order and line.order_id.date_order.date(),
                uom_id=line.product_uom_id,
                params=params)

            if seller or not line.date_planned:
                line.date_planned = line._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            # If not seller, use the standard price. It needs a proper currency conversion.
            if not seller:
                unavailable_seller = line.product_id.seller_ids.filtered(
                    lambda s: s.partner_id == line.order_id.partner_id)
                if not unavailable_seller and line.price_unit and line.product_uom_id == line._origin.product_uom_id:
                    # Avoid to modify the price unit if there is no price list for this partner and
                    # the line has already one to avoid to override unit price set manually.
                    continue
                po_line_uom = line.product_uom_id or line.product_id.uom_po_id
                price_unit = line.env['account.tax']._fix_tax_included_price_company(
                    line.product_id.uom_id._compute_price(line.product_id.standard_price, po_line_uom),
                    line.product_id.supplier_taxes_id,
                    line.tax_ids,
                    line.company_id,
                )
                price_unit = line.product_id.currency_id._convert(
                    price_unit,
                    line.currency_id,
                    line.company_id,
                    line.date_order,
                    False
                )
                line.price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places, self.env['decimal.precision'].precision_get('Product Price')))
                continue

            price_unit = line.env['account.tax']._fix_tax_included_price_company(seller.price, line.product_id.supplier_taxes_id, line.taxes_id, line.company_id) if seller else 0.0
            price_unit = seller.currency_id._convert(price_unit, line.currency_id, line.company_id, line.date_order, False)
            price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places, self.env['decimal.precision'].precision_get('Product Price')))
            
            if line.partner_id.tariff_id:
                price_unit = self.env['tariff.lines'].on_product_change(self.product_id.id, self.partner_id.tariff_id.id, price_unit)
            
            line.price_unit = seller.product_uom_id._compute_price(price_unit, line.product_uom_id)

            # record product names to avoid resetting custom descriptions
            default_names = []
            vendors = line.product_id._prepare_sellers({})
            for vendor in vendors:
                product_ctx = {'seller_id': vendor.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
                default_names.append(line._get_product_purchase_description(line.product_id.with_context(product_ctx)))
            if not line.name or line.name in default_names:
                product_ctx = {'seller_id': seller.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
                line.name = line._get_product_purchase_description(line.product_id.with_context(product_ctx))

class AccountInvoiceLine(models.Model):
    """ Override AccountInvoice_line to add the link to the purchase order line it is related to"""
    _inherit = 'account.move.line'

    enrollee_id = fields.Many2one('enrollee', related='purchase_line_id.order_id.enrollee_id', string='Enrollee', store=False, readonly=True,
        help='Associated Enrollee. Filled in automatically when a claim is chosen on the vendor bill.')
    line_date = fields.Datetime(related='purchase_line_id.order_id.date_order', string='Claims Date', store=False, readonly=True)
    provider_cost = fields.Float(related='purchase_line_id.provider_price', string='Provider Cost', readonly=True)
    x_m_id = fields.Integer(string="Migration_ID")
	
class AccountInvoice(models.Model):
    """ Override AccountInvoice_line to add the link to the purchase order line it is related to"""
    _inherit = 'account.move'

    x_m_id = fields.Integer(string="Migration_ID")
    nhis_ref = fields.Char(related='partner_id.nhis_ref', string='NHIS Ref')

class AuditClaim(models.TransientModel):
    _name = "audit.claim"
    _description = "Audit Claim"
    
    def validate_move(self):
        if self._context.get('active_model') == 'purchase.order':
            domain = [('id', 'in', self._context.get('active_ids', [])), ('state', '=', 'purchase'),('audit_check','=',False)]
        else:
            raise UserError(_("Missing 'active_model' in context."))

        claims = self.env['purchase.order'].search(domain)
        if not claims:
            raise UserError(_('There are no claims to check'))
        for claim in claims:
            claim.audit_check = True
        return {'type': 'ir.actions.act_window_close'}