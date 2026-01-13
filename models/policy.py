# Copyright 2019 Nacmara
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from logging import getLogger

from odoo import _, api, fields, models, Command
from odoo.exceptions import UserError

_logger = getLogger(__name__)

class Pricelist(models.Model):
    _inherit = "product.pricelist"
    
    x_m_id = fields.Integer(string='Migration ID')
    
class SaleOrder(models.Model):
    _inherit = "sale.order"

    policy_start = fields.Boolean(string = 'Policy Start')
    start_date = fields.Date(string ='Start Date')
    end_date = fields.Date(string ='End Date')
    summary = fields.Char (string = 'Totals')
    x_m_id = fields.Integer(string='Migration ID')
    doc_type = fields.Selection([('order','Order'),('policy','Policy')], string='Document Type', select=True, copy=False, readonly=True, default='order', track_visibility='onchange')
    
    
    
    def _get_forbidden_state_confirm(self):
        return {'done', 'cancel'}

    def action_confirm(self):
        """ Confirm the given quotation(s) and set their confirmation date.

        If the corresponding setting is enabled, also locks the Sale Order.

        :return: True
        :rtype: bool
        
        :raise: UserError if trying to confirm locked or cancelled SO's
        """
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                "It is not allowed to confirm an order in the following states: %s",
                ", ".join(self._get_forbidden_state_confirm()),
            ))

        # self.order_line._validate_analytic_distribution()

        for order in self:
            if order.partner_id in order.message_partner_ids:
                continue
            order.message_subscribe([order.partner_id.id])

        self.write(self._prepare_confirmation_values())

        # Context key 'default_name' is sometimes propagated up to here.
        # We don't need it and it creates issues in the creation of linked records.
        context = self._context.copy()
        context.pop('default_name', None)

        self.with_context(context)._action_confirm()
        for order in self:
            for line in order.order_line:
                if order.start_date and line.enrollee_id:
                    param=[]
                    sql= ""					
                    if order.policy_start:
                        param=[order.start_date,order.start_date,order.end_date]
                        sql="update enrollee set policy_start_date = %s,policy_cycle_date= %s,end_date=%s,active=True where id = " + str(line.enrollee_id.id)
                    else:
                        param=[order.start_date,order.end_date]
                        sql="update enrollee set policy_cycle_date = %s,end_date=%s,active=True where id = " + str(line.enrollee_id.id)
                    yc = self.env.cr.execute(sql,tuple(param))
        if self.env.user.has_group('sale.group_auto_done_setting'):
            self.action_done()

        return True

    def sum_enrollees(self,qry):
        sql="select l.name,count(l.name) from sale_order_line l inner join sale_order s on s.id = l.order_id where s.name = '" + str(self.name) + "' group by l.name"
        self._cr.execute(qry)
        res = self._cr.dictfetchall()
        return res
    
    @api.depends('order_line.price_subtotal', 'order_line.price_tax', 'order_line.price_total', 'order_line.duration')
    def _compute_amounts(self):
        """Compute the total amounts of the SO."""
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type)
            order.amount_untaxed = sum(order_lines.mapped('price_subtotal'))
            order.amount_tax = sum(order_lines.mapped('price_tax'))
            order.amount_total = order.amount_untaxed + order.amount_tax
                   
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    line_date = fields.Datetime(related='order_id.date_order', string='Date')
    duration = fields.Integer(string = 'Duration(Mth)')
    provider_id = fields.Many2one('res.partner', string='HCP', domain=['&',('supplier','=',True),('hcp','=',True)])
    enrollee_id = fields.Many2one('enrollee', string='Enrollee')
    start_date = fields.Date(related='order_id.start_date', string ='Start Date')
    end_date = fields.Date(related='order_id.end_date', string ='End Date')
    parent_doc_type = fields.Selection(related='order_id.doc_type', string='Document Type')

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_ids','duration')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            #duration = 1
            #if line.order_id.doc_type == 'order':
            #    duration = line.duration
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            tax_results = line.tax_ids.compute_all(
                price,
                line.currency_id,
                line.product_uom_qty,
                product=line.product_id,
                partner=line.order_id.partner_id
            )
            amount_untaxed = tax_results['total_excluded']
            amount_tax = tax_results['total_included'] - tax_results['total_excluded']

            line.update({
                #'product_uom_qty': duration,
                'price_subtotal': amount_untaxed,
                'price_tax': amount_tax,
                'price_total': amount_untaxed + amount_tax,
            })
            
    def _prepare_invoice_line(self, **optional_values):
        """Prepare the values to create the new invoice line for a sales order line.

        :param optional_values: any parameter that should be added to the returned invoice line
        :rtype: dict
        """
        self.ensure_one()
        
        if self.order_id.doc_type == 'order':
            qty=self.qty_to_invoice * self.duration
            
        res = {
            'display_type': self.display_type or 'product',
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom_id.id,
            'quantity': self.product_uom_qty,
            'discount': self.discount,
            'price_unit': self.price_unit,
            'tax_ids': [Command.set(self.tax_ids.ids)],
            'sale_line_ids': [Command.link(self.id)],
            'is_downpayment': self.is_downpayment,
        }
       
        analytic_account_id = False
        if hasattr(self.order_id, 'analytic_account_id') and self.order_id.analytic_account_id:
            analytic_account_id = self.order_id.analytic_account_id.id

      
        if self.analytic_distribution and not self.display_type:
            res['analytic_distribution'] = self.analytic_distribution.copy()
        if analytic_account_id and not self.display_type:
            analytic_account_id = str(analytic_account_id)
        if 'analytic_distribution' in res:
            res['analytic_distribution'][analytic_account_id] = res['analytic_distribution'].get(analytic_account_id, 0) + 100
        else:
            res['analytic_distribution'] = {analytic_account_id: 100}
            if optional_values:
                res.update(optional_values)
            if self.display_type:
                res['account_id'] = False
            return res
    
    def _convert_to_tax_base_line_dict(self):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        qty=self.product_uom_qty * self.duration
        #if self.order_id.doc_type == 'policy':
        #    qty = self.duration
        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.order_id.partner_id,
            currency=self.order_id.currency_id,
            product=self.product_id,
            taxes=self.tax_ids,
            price_unit=self.price_unit,
            quantity=qty,
            discount=self.discount,
            price_subtotal=self.price_subtotal,
        )
