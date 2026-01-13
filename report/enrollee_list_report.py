# -*- coding: utf-8 -*-
##############################################################################
# iSync 
#
##############################################################################
from datetime import datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError        
  
class enrollee_list_report_print(models.AbstractModel):
    _name = 'report.hmo_management.enrollee_list_template' 

    @api.model 
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name('hmo_management.enrollee_list_template')
        partners = self.env['res.partner'].search_read([('id', '=', docids[0])])
        partner_id = partners[0]
			
        return{
            'doc_ids': docids,
            'doc_model': self.env['res.partner'],
            'docs': partners,
            'print_capitation' : self._print_list,
            'company' : self.env['res.company']._company_default_get('account.invoice'),
        }

    def _print_list(self, partner):
        sql=("select e.code code ,surname,firstname, othername,t.cap_amount,t.name from enrollee e inner join product_product p on p.id = e.plan inner join product_template t on p.product_tmpl_id = t.id where (end_date >= (SELECT DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '2 month' - INTERVAL '1 day') or end_date is null) and e.active=True and hcp=%s  order by e.code")

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
                'cap_amount': res['cap_amount']
            })
        return doc
        
    def replacer(self,input_string):
        return input_string['en_US']
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


