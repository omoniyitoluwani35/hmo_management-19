
import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime

class enrollee_operations(models.TransientModel):
    _name= "enrollee.operations"
    _description= "Enrollee operations wizard"

    action = fields.Selection([
        ('plan', 'Change Plan'),
        ('status', 'Activate/Deactivate Enrollees'),
        ('cap_amount', 'Update NHIS Capitation Amount'),
        ('capitation', 'Activate/Deactivate Capitation on Plan'),
        ('employer_capitation', 'Activate/Deactivate Capitation on Employer'),		
        ('list', 'Generate Private Capitation Payment Schedule'),
        ('nhis', 'Generate NHIS Capitation Payment Schedule'),
        ], string='Perform Operation', select=True, copy=False)
    customer_id= fields.Many2one('res.partner', string="Customer", domain=[('customer_rank', '=', 1)])
    provider_id= fields.Many2one('res.partner', string="Provider", domain=[('hcp', '=', True)])
    plan_id= fields.Many2one('product.product', string="Plan", domain=[('sale_ok','=', True)])
    active= fields.Boolean(string="Activate Plan")
    cap_activate= fields.Boolean(string="Deactivate Capitation on Plan")
    caps_amount = fields.Float(string="NHIS Capitation Amount")
   	
    def enrollee_operations(self):
        sql_plan=("update enrollee set plan = " + str(self.plan_id.id) + " where employer = " + str(self.customer_id.id)) + " and active = true"
        sql_status=("update enrollee set active = " + str(self.active))
        sql_capitate=("update enrollee set uncapitated = " + str(self.cap_activate) + " where plan = " + str(self.plan_id.id))
        sql_employer=("update enrollee set uncapitated = " + str(self.cap_activate) + " where employer = " + str(self.customer_id.id))
        sql_nhis_amt = ("update res_partner set nhis_capitation_amount = " + str(self.caps_amount) + " where nhis = true")
        if self.action == 'plan':
            yc = self.env.cr.execute(sql_plan)
        elif self.action == 'status':
            sql_plus= " and active = true"
            sql_where = " where employer = " + str(self.customer_id.id)
            sql_act = ",end_date=NULL "
            if self.active == False:
                sql_act = ",end_date=current_timestamp "
                sql_status = sql_status + sql_act + sql_where + sql_plus
            else:
                sql_status = sql_status + sql_act + sql_where
            yc = self.env.cr.execute(sql_status)
        elif self.action == 'capitation':
            yc = self.env.cr.execute(sql_capitate)
        elif self.action == 'employer_capitation':
            yc = self.env.cr.execute(sql_employer)
        elif self.action == 'cap_amount':
            yc = self.env.cr.execute(sql_nhis_amt)				
        else:	
            #cap_pool = self.pool.get('report.capitation_print.cap_report_template')
            partner_pool = self.env['res.partner'].search([])
            move = {
                'narration': "Capitation payments",
                'journal_id': 1,
                'date': datetime.now().date(),		
				'name': "Capitation payments",
                'move_type':"entry"
            }
            line_ids=[]
            acct_ids = []
            total=0.0    
			
            cap_acct_id = nhis_acct_id = payable_acct_id = bank_id = 0
            cap_acct_id = self.env['account.account'].search([('tag_ids.name', '=', 'capitation')],limit=1)
            nhis_acct_id = self.env['account.account'].search([('tag_ids.name', '=', 'capitation')],limit=1)
            bank_id = self.env['account.account'].search([('tag_ids.name', '=', 'bank')],limit=1)
            payable_acct_id = self.env['account.account'].search([('tag_ids.name', '=', 'payable')],limit=1)

            for partner in partner_pool:
                acct = cap_acct_id.id
                is_nhis = True
                is_capitated = False      
                if self.action == 'list':
                    is_nhis = False
                    is_capitated = partner.capitated
                    acct = nhis_acct_id.id
                if partner.supplier_rank >= 1 and partner.hcp == True and partner.nhis == is_nhis and partner.capitated == is_capitated:
                    amount = self.env['report.hmo_management.cap_alone_report_template']._sum_capitation(partner)
                    amt1=amount[0]
                    amt=amt1['caps']
                    cap_rep = self.env['report.hmo_management.cap_alone_report_template']._print_capitation(partner)
                    for caps in cap_rep:
                        capits = {
                            'enrollee_code': caps['code'],
                            'surname': caps['surname'],
                            'firstname': caps['firstname'],
                            'hcp': partner.name,
                            'capitation_date': datetime.now().date(),		
				            'plan': caps['name'],
                            'amount': caps['cap_amount'],
                            'employer': caps['employer'],	
                        }
                        capitations = self.env['capitation.report'].create(capits)
                    #raise UserError(_('Please define income account for this product: "%s"') % (amt['caps']))
                    if amt > 0:
                        move_line = (0, 0, {
                            'name': "Capitation payment " + partner.name,
                            'account_id': acct,
                            'date':datetime.now().date(),
                            'date_maturity':datetime.now().date(),
                            'debit': amt,
                            'credit': 0.0,
                            'journal_id': 1,
                            'partner_id': partner.id,
                        })
                        line_ids.append(move_line)
                        total= total + amt
            
                        move_line2 = (0, 0, {
                            'name': "Capitation payments ",
                            'account_id': payable_acct_id.id,
                            'date':datetime.now().date(),
                            'date_maturity':datetime.now().date(),
                            'debit': 0.0,
                            'credit': amt,
                            'journal_id': 1,
                            'partner_id': partner.id,
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

