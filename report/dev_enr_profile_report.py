# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd. (<http://devintellecs.com>).
#
##############################################################################
from datetime import datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError    
import json
    
class dev_enr_profile_report_print(models.AbstractModel):
    _name = 'report.hmo_management.dev_enr_profile_report_template' 

    @api.model 
    def _get_report_values(self, docids, data=None):
        #doc = self._get_details
        enrollees = self.env['enrollee'].search_read([('id', 'in', docids)])
        return{
            'doc_ids': docids,
            'doc_model': self.env['enrollee'],
            'docs': enrollees ,
            'company' : self.env['res.company']._company_default_get('account.invoice'),
            'print_id' : self._get_details,
            'get_logo' : self._get_logo,
            'get_enrollee_pic' : self._get_enrollee_pic
        }
    
    def _get_logo(self,id_no):
        logo = (self.env["res.partner"].search([("id", "=", id_no)])).image_1920
        #raise UserError(_('Cap greater than zero %s') % (id_no,))
        return logo
		
    def _get_enrollee_pic(self,id_no):
        logo = (self.env["enrollee"].search([("id", "=", id_no)])).picture
        #raise UserError(_('Cap greater than zero %s') % (id_no,))
        return logo

    def _get_details(self, partner):
        sql=("select e.id as dd, e.code, surname,firstname, othername,address, s.name as the_state,h.name as hcp, street, employer,t.name plan from enrollee e inner join res_partner h on h.id = e.hcp inner join res_country_state s on s.id = e.state inner join product_product p on p.id = plan inner join product_template t on p.product_tmpl_id = t.id  and e.id=%s ")
      
        param=[partner['id']]
        self._cr.execute(sql, tuple(param))
        _res = self._cr.dictfetchall()
        doc =[]
        for res in _res:
            #raise UserError(_('Cap geater than zero %s') % (res['code'],))
            has_image = enrollee_pic = 'false'
            partners = (self.env['res.partner'].search([('id', '=', res['employer'])])).image_1920
            if partners:
                has_image = 'true'
            enrols = (self.env['enrollee'].search([('id', '=', res['dd'])])).picture
            if enrols:
                enrollee_pic = 'true'
            p1 = str(res['plan']).replace("'",'"')
            p = json.loads(p1)
            #raise UserError(_('Plano %s') % (p1),)
            doc.append({
                'code': res['code'],
                'surname': res['surname'],
                'firstname': res['firstname'],
                'othername': res['othername'],
                'hcp': res['hcp'],
                'hcp_address': res['street'],
                'address': res['address'],
                'plan' : p['en_US'],
                'id' : res['dd'],
                'state' : res['the_state'],
                'employer' : res['employer'],
                'has_image' : has_image,
                'enrollee_pic': enrollee_pic,
                'has_rep': 'yes'				
            })
        return doc
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


