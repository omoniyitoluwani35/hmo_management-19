# Copyright 2019 Nacmara
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from logging import getLogger

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = getLogger(__name__)


class ICD(models.Model):
    _name = "icd"
    _description = "ICD Classification"

    name = fields.Char(string ='Classification')
    band = fields.Char(string ='Dx Band')
    active = fields.Boolean(string='Active',default=True)
    x_m_id = fields.Integer(string="Migration_ID")
 

