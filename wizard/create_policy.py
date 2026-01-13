
import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime

class create_policy(models.TransientModel):
    _name= "create.policy"
    _description= "Additional Policy Wizard"

    start_date= fields.Date(string="Start Date")
    end_date= fields.Date(string="End Date")
    quantity=fields.Float(string="Duration/Months")
    customer_id = fields.Many2one('res.partner', string="Customer", domain=[('customer_rank', '=', True)]) 
	
    def generate_policy(self):
        enrollee_ids = self.env['enrollee'].browse(self._context.get('active_ids'))
        full_rep=[]
        for ids in enrollee_ids:
            sql=("select e.id,e.code,p.list_price,hcp,plan,p.name,e.employer from enrollee e inner join product_product t on t.id = e.plan  inner join product_template p on t.product_tmpl_id = p.id where (end_date <= (SELECT DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '2 month' - INTERVAL '1 day') or end_date is null) and e.id = " + str(ids.id))
            yc = self.env.cr.execute(sql)
            for row in self.env.cr.dictfetchall():
                full_rep.append(row)
        employer=0
        line_ids=[]
        for line in full_rep:
            order_line = (0, 0, {
                'name': self.replacer(line['name']),
                'product_id': line['plan'],
                'product_uom_qty': 1,
                'enrollee_id': line['id'],
                'provider_id': line['hcp'],
                'duration':self.quantity,
            })
            if employer == 0:
                employer = line['employer']
            else:
                if employer != line['employer']:
                    raise UserError(_('Multiple employers in selection. Choose only enrollees in one company'))
                #employer = line['employer']
            line_ids.append(order_line)

        order = {
                'partner_id': employer,
                'start_date': self.start_date,			
				'end_date': self.end_date,	
                'date_order':datetime.now().date(),	
                'doc_type' : 'policy'
            }
        order.update({'order_line': line_ids})
        orders = self.env['sale.order'].create(order)
        return True

    def policy_operations(self):
        full_rep=[]
        full_repgrp=[]
        sql=("select e.id,e.code,p.list_price,hcp,plan,p.name from enrollee e inner join product_product t on t.id = e.plan  inner join product_template p on t.product_tmpl_id = p.id where (end_date >= (SELECT DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '2 month' - INTERVAL '1 day') or end_date is null) and e.active=True  and employer = " + str(self.customer_id.id)) + " order by plan,e.code"
        sqlgrp=("select p.name,count(p.name) from enrollee e inner join product_product t on t.id = e.plan  inner join product_template p on t.product_tmpl_id = p.id where (end_date >= (SELECT DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '2 month' - INTERVAL '1 day') or end_date is null) and e.active=True  and employer = " + str(self.customer_id.id)) + " group by p.name order by p.name"		
        yc = self.env.cr.execute(sql)
        for row in self.env.cr.dictfetchall():
            full_rep.append(row)
        zc = self.env.cr.execute(sqlgrp)
        for rows in self.env.cr.dictfetchall():
            full_repgrp.append(rows)
        summary=""
        for sums in full_repgrp:
            #raise UserError(_("%s") % str(sums['name']))
            summary = summary + "["  + self.replacer((sums['name'])) + ":" + str(sums['count']) + "]"
        so_pool = self.pool.get('sale.order')
        order = {
                'partner_id': self.customer_id.id,
                'start_date': self.start_date,			
				'end_date': self.end_date,	
                'date_order':datetime.now().date(),	
                'doc_type' : 'policy',
                'summary': summary
            }
        line_ids=[]
        for line in full_rep:
            order_line = (0, 0, {
                'name': self.replacer(line['name']),
                'product_id': line['plan'],
                'product_uom_qty': 1,
                'enrollee_id': line['id'],
                'provider_id': line['hcp'],
                'duration': self.quantity,
            })
            line_ids.append(order_line)

        order.update({'order_line': line_ids})
        orders = self.env['sale.order'].create(order)
        return True

    def replacer(self,input_string):
        return input_string['en_US']
    