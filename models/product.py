# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from logging import getLogger

_logger = getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_drug = fields.Boolean(string='Is Drug/Service', default=True)
    cap_amount = fields.Float(string = 'Capitation Amount')
    is_nhis = fields.Boolean(string = 'Is NHIS')
    plan_limit = fields.Float(string = 'Plan Limit')
    benefit_id = fields.Many2one('plan.benefit',string = 'Plan Benefits')
    stockable = fields.Boolean(string = 'Inventory Item')
    investigation = fields.Boolean(string = 'Investigation')
    x_m_id = fields.Integer(string="Migration_ID")


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def _apply_tariff_filter(self, args):
        
        partner_id =  self._context.get('partner_id')
        partner = self.env['res.partner'].search([('id','=',partner_id)], limit=1)
        tariff_id = partner.tariff_id
        _logger.info(_("hello %s")% self._context)
        # If no tariff provided, do normal name_search (no additional restriction).
        if not tariff_id:
            return args

        # If tariff exists, filter results by product templates referenced by tariff lines.
        tariff = self.env['tariff'].browse(tariff_id)
        if not tariff:
            _logger.info("hallos")
            return args

        # Get template ids from tariff lines (fast, small list of templates)
        template_ids = tariff_id.tariff_line.mapped('product_id.id')
        _logger.info("hola")
        if not template_ids:
            args += [('id', '=', 0)]
        else:
            args += [('product_tmpl_id', 'in', template_ids)]

        return args

    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        args = self._apply_tariff_filter(domain or [])
        return super().name_search(name=name, domain=domain, operator=operator, limit=limit)

    @api.model
    def search_count(self, domain=None, offset=0, limit=None, order=None, count=False):
        args = self._apply_tariff_filter(domain or [])
        return super().search_count(domain, offset=offset, limit=limit, order=order, count=count)