# -*- coding: utf-8 -*-
##############################################################################
# iSync 
#
##############################################################################
from datetime import datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError        
  
class cap_alone_report_print(models.AbstractModel):
    _name = 'report.hmo_management.cap_alone_report_template' 
    _auto = False
    #_template = 'capitation_alone_print.cap_alone_report_template'

    @api.model 
    def _get_report_values(self, docids, data=None):
        partners = self.env['res.partner'].search_read([('id', '=', docids[0])])
        partner_id = partners[0]
        #raise UserError(_('Cap geater than zero %s') % (partner_id['id'],))
			
        return{
            'doc_ids': docids,
            'doc_model': self.env['res.partner'],
            'docs': partners,
            'print_capitation' : self._print_capitation,
            'sum_capitation' : self._sum_capitation,
            'company' : self.env['res.company']._company_default_get('account.invoice'),
            '_name': 'Test'
        }

    def _print_capitation(self, partner):
        sql=("select e.code code ,surname,firstname, othername,t.cap_amount,t.name,e.uncapitated,o.name employer from enrollee e inner join res_partner o on e.employer=o.id inner join product_product p on p.id = e.plan inner join product_template t on p.product_tmpl_id = t.id where (end_date >= (SELECT DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '2 month' - INTERVAL '1 day') or end_date is null) and e.active=True and (e.uncapitated=False or e.uncapitated is null) and e.hcp=%s  order by e.code")
        if partner['nhis']==True:
            if partner['nhis_capitation_amount'] > 0:
                sql=("select e.code,surname,firstname, othername,h.nhis_capitation_amount,t.name,e.uncapitated,o.name employer from enrollee e inner join res_partner o on e.employer=o.id e inner join product_product p on p.id = e.plan inner join product_template t on p.product_tmpl_id = t.id inner join res_partner h on h.id = e.hcp where (end_date >= (SELECT DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '2 month' - INTERVAL '1 day') or end_date is null) and e.active=True and (e.uncapitated=False or e.uncapitated is null) and e.hcp=%s order by e.code")
        else:
            if partner['cap_amount'] > 0 :
                sql=("select e.code,surname,firstname, othername,h.cap_amount,t.name,e.uncapitated,o.name employer from enrollee e inner join res_partner o on e.employer=o.id inner join product_product p on p.id = e.plan inner join product_template t on p.product_tmpl_id = t.id inner join res_partner h on h.id = e.hcp where (end_date >= (SELECT DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '2 month' - INTERVAL '1 day') or end_date is null) and e.active=True and (e.uncapitated=False or e.uncapitated is null) and e.hcp=%s order by e.code")
                #

        param=[partner['id']]
        self._cr.execute(sql, tuple(param))
        _res = self._cr.dictfetchall()
        doc =[]
        for res in _res:
            #raise UserError(_('Cap geater than zero %s') % (res['code'],))
            doc.append({
                'code': res['code'],
                'surname': res['surname'],
                'firstname': res['firstname'],
                'othername': res['othername'],
                'name': self.replacer(res['name']),
                'uncapitated': res['uncapitated'],
                'cap_amount': res['cap_amount'],
                'employer': res['employer'],
               
            })
        return doc
    
    def _sum_capitation(self, partner_id):
        #partners = self.env['res.partner'].search_read([('id', '=', docids[0])])
        #partner_id = partners[0]
        #raise UserError(_('Cap geater than zero %s') % (partner_id['id'],))

        sql=("select coalesce(sum(t.cap_amount),0) as caps from enrollee e inner join product_product p on p.id = e.plan inner join product_template t on t.id = p.product_tmpl_id inner join res_partner r on r.id = e.hcp where (end_date >= (SELECT DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '2 month' - INTERVAL '1 day') or end_date is null) and e.active=True and e.hcp=%s and  (e.uncapitated=False or e.uncapitated is null) and r.capitated=True")
        if partner_id['nhis']:
            if partner_id['nhis_capitation_amount'] > 0 :
                sql=("select coalesce(sum(h.nhis_capitation_amount),0) as caps from enrollee e inner join res_partner  h on h.id = e.hcp  where (end_date >= (SELECT DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '2 month' - INTERVAL '1 day') or end_date is null) and e.active=True and e.hcp=%s and  (e.uncapitated=False or e.uncapitated is null) and h.capitated=True")
        else:
            if partner_id['cap_amount'] > 0:
                sql=("select coalesce(sum(h.cap_amount),0) as caps from enrollee e inner join res_partner  h on h.id = e.hcp  where (end_date >= (SELECT DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '2 month' - INTERVAL '1 day') or end_date is null) and e.active=True and e.hcp=%s and  (e.uncapitated=False or e.uncapitated is null) and h.capitated=True")
        param=[partner_id['id']]
        self._cr.execute(sql, tuple(param))
        _res = self._cr.dictfetchall()
        return _res
    
    def replacer(self,input_string):
        return input_string['en_US']

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


