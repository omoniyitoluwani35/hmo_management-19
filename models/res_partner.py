# -*- coding: utf-8 -*-
from odoo import fields, api, models, _
from odoo.exceptions import UserError
import requests
import json

class ResPartner(models.Model):
    _inherit = 'res.partner'

    tariff_id = fields.Many2one('tariff', string='Tariff')
    x_m_id = fields.Integer(string="Migration_ID")
    hcp = fields.Boolean(string='Is HCP')
    capitated = fields.Boolean(string='Capitated', help='Is this a capitated provider?')
    nhis_ref = fields.Char(string='NHIS Ref')
    nhis = fields.Boolean(string='Is NHIS')
    cap_amount = fields.Monetary(string='Capitation Amount')
    nhis_cap_amount = fields.Monetary(string='NHIS Capitation Amount')
    uploaded = fields.Boolean(string='Uploaded to Portal', default=False)
    analytic_count = fields.Integer(string='Analytic Accounts', compute='_compute_analytics')

    @api.depends('name')
    def _compute_analytics(self):
        for partner in self:
            # Using search_count for performance
            partner.analytic_count = self.env['account.analytic.account'].search_count([
                ('partner_id', '=', partner.id)
            ])

    def _compute_display_name(self):
        
        super()._compute_display_name()
        for partner in self:
            if partner.nhis_ref:
                partner.display_name = f"{partner.display_name} ({partner.nhis_ref})"

    def action_view_analytics(self):
        self.ensure_one()
    
        action = self.env["ir.actions.actions"]._for_xml_id('analytic.action_account_analytic_account_form')
        anals = self.env['account.analytic.account'].search([('partner_id', '=', self.id)])
        
        if len(anals) > 1:
            action['domain'] = [('id', 'in', anals.ids)]
        elif len(anals) == 1:
            action['views'] = [(self.env.ref('analytic.view_account_analytic_account_form').id, 'form')]
            action['res_id'] = anals.id
        
        action["context"] = {'default_partner_id': self.id}
        return action

    def upload(self):
        # Filter for HCPs not yet uploaded
        partners = self.search([('hcp', '=', True), ('uploaded', '!=', True)])
        url = 'https://www.w3schools.com/python/demopage.php'
        
        for partner in partners:           
            try:
                # Direct JSON posting is cleaner in requests
                payload = {'name': partner.name}
                response = requests.post(url, json=payload, timeout=5)
                if response.status_code == 200:
                    partner.uploaded = True
            except Exception as e:
                continue

class ResCompany(models.Model):
    _inherit = 'res.company'

    signature = fields.Binary(string='Authorized Signature', attachment=True)