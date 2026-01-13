from datetime import datetime
from odoo import models,fields,api,_
import logging

_logger = logging.getLogger(__name__)

class capitation_report (models.Model):# Name class
	_name = 'capitation.report'
	_description = 'Capitation Report'
	
	def name_get(self):
		res=[]

		for emp in self:
			res.append((emp.id, emp.enrollee_code))    
		return res

	enrollee_code = fields.Char(string="Enrollee Code")
	surname = fields.Char(string="Surname")
	firstname = fields.Char(string="First Name")
	capitation_date = fields.Date(string ="Date")
	hcp = fields.Char(string="Provider")
	plan = fields.Char(string='Health Plan')
	amount = fields.Float(string="Amount")
	employer = fields.Char(string='Employer')
	



