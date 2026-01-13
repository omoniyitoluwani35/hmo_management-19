# Copyright 2019 Nacmara
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from logging import getLogger

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = getLogger(__name__)


class ClaimsDiagnosis(models.Model):
    _name = "claims.diagnosis"
    _description = "Claims Diagnosis"

    name = fields.Selection([('diag','Diagnosis'),('inv','Investigation'),('proc','Procedure')], string = 'Type', required=True)
    claim_id = fields.Many2one('purchase.order', string='Claim')
    enrollee_id = fields.Many2one('enrollee', string='Enrollee')
    diagnosis_date = fields.Date(string ='Date')
    details = fields.Char(string ='Details')
    diagnosis = fields.Char(string ='Diagnosis')
    hcp_id = fields.Many2one('res.partner', string='HCP',domain=[('hcp','=',True)])
    icd_id = fields.Many2one('icd', string='Diagnosis')
    active = fields.Boolean (string = 'Active',default = True)
    x_m_id = fields.Integer(string="Migration_ID")
