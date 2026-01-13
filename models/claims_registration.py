# Copyright 2019 Nacmara
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from logging import getLogger

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = getLogger(__name__)


class ClaimsRegistration(models.Model):
    _name = "claims.registration"
    _order = "receipt_date desc,id desc"
    _description = "Claims Registration"

    name = fields.Char('Period', required=True)
    hcp_id = fields.Many2one('res.partner', string='HCP',domain=[('hcp','=',True)],required=True)
    user_id = fields.Many2one('res.users', string='Registration Officer')
    receipt_date = fields.Date(string ='Receipt Date')
    bill_total = fields.Float(string ='Bill Total')
    x_m_id = fields.Integer(string="Migration_ID")
    lines = fields.One2many('purchase.order','claim_reg_id',string='Claims')
    def name_get(self):
        res=[]
        for emp in self.sudo():
            res.append((emp.id, emp.hcp_id.name + " - " + emp.name)) 
        return res

