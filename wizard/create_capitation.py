
import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime

class create_capitation(models.TransientModel):
    _name= "create.capitation"
    _description= "Capitation Creation Multi Wizard"

    is_nhis_cap = fields.Boolean(string="Is NHIS")
	
    def generate_capitation(self):
        enrollee_ids = self.env['enrollee'].browse(self._context.get('active_ids'))
        full_rep=[]
        line_id = []
        line_ids = []
        acct_ids = []
        for ens in enrollee_ids:
            line_id.append(ens.id)
        total=0.0
        cap_acct_id = nhis_acct_id = payable_acct_id = bank_id = 0
        
        cap_acct_id = self.env['account.account'].search([('tag_ids.name', '=', 'capitation')],limit=1)
        nhis_acct_id = self.env['account.account'].search([('tag_ids.name', '=', 'capitation')],limit=1)
        bank_id = self.env['account.account'].search([('tag_ids.name', '=', 'bank')],limit=1)
        payable_acct_id = self.env['account.account'].search([('tag_ids.name', '=', 'payable')],limit=1)
        
        sql_enrol= "select e.hcp,h.nhis, h.name, coalesce(sum(case when h.cap_amount IS NULL or h.cap_amount = 0 then t.cap_amount else h.cap_amount end),0) as capitation from enrollee e inner join product_product p on p.id = e.plan inner join product_template t on t.id = p.product_tmpl_id inner join res_partner h on e.hcp=h.id where e.id in " + str(tuple(line_id)) + " and h.capitated = true group by e.hcp,h.cap_amount, t.cap_amount,h.nhis,h.name"
        yc = self.env.cr.execute(sql_enrol)
        for row in self.env.cr.dictfetchall():
            full_rep.append(row)	
        for line in full_rep:
            total += line['capitation']
       
        move = {
            'narration': "Capitation payments",
            'journal_id': 1,
            'date': datetime.now().date(),		
            'name': "Capitation payments",
            'move_type':"entry"
        }        
        
        if total > 0:
            for line in full_rep:
                acct = nhis_acct_id.id
                is_nhis = True
                is_capitated = False   
                narra="NHIS Capitation payments "		
                if line['nhis'] == False:
                    #is_nhis = False
                    #is_capitated = line['x_capitated']
                    acct = cap_acct_id.id
                    narra="Capitation payments "
                move_line = (0, 0, {
                    'name': narra + line['name'],
                    'account_id': acct,
                    'date':datetime.now().date(),
                    'date_maturity':datetime.now().date(),
                    'debit': line['capitation'],
                    'credit': 0.0,
                    'journal_id': 1,
                    'partner_id': line['hcp'],
                })
                line_ids.append(move_line)
                #total= total + amt
            
                move_line2 = (0, 0, {
                    'name': "Capitation payments ",
                    'account_id': payable_acct_id.id,
                    'date':datetime.now().date(),
                    'date_maturity':datetime.now().date(),
                    'debit': 0.0,
                    'credit': line['capitation'],
                    'journal_id': 1,
                    'partner_id': line['hcp'],
                })
                line_ids.append(move_line2) 
            move_line3 = (0, 0, {
                'name': "Capitation payments ",
                'account_id': payable_acct_id.id,
                'date':datetime.now().date(),
                'date_maturity':datetime.now().date(),
                'debit': total,
                'credit':0.0,
                'journal_id': 1,
            })
            line_ids.append(move_line3)
            
            move_line4 = (0, 0, {
                'name': "Capitation payments ",
                'date':datetime.now().date(),
                'date_maturity':datetime.now().date(),
                'debit': 0.0,
                'credit':total,
                'journal_id': 1,
                'account_id': bank_id.id,
            })
            line_ids.append(move_line4)
            move.update({'line_ids': line_ids})
            move.update({'amount_total': total})
            moves = self.env['account.move'].create(move)
        return True
    