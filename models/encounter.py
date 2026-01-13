from datetime import datetime
from odoo import models,fields,api,_
import logging

_logger = logging.getLogger(__name__)

class encounter (models.Model):# Name class
	_name = 'encounter'
	_description = 'Encounter'
	
	def name_get(self):
		res=[]

		for emp in self:
			res.append((emp.id, emp.enrollee.code + ' - ' + emp.hcp.name))    
		return res

	enrollee = fields.Many2one('enrollee', string="Enrollee")
	encounter_date = fields.Date(string ="Encounter Date")
	hcp = fields.Many2one('res.partner', string="HCP", domain="[('hcp','=',True)]")
	employer = fields.Many2one('res.partner', string="Employer", domain ="[('customer_rank','=',1)]")
	comment = fields.Text(string="Comments")
	diagnosis=fields.Many2one('icd', string="Diagnosis")
	remark = fields.Text(string="Remarks")
	diagnosis_detail = fields.Char(string="Diagnosis Detail")
	treatment = fields.Selection([('minor','Minor'),('inter','Intermediate'),('major','Major')], string='Treatment')
	result = fields.Selection( [('refer','Referred'),('partial','Partial Recovery'),('full','Full Recovery'),('death','Death')]	, string='Treatment Result')
	investigation=fields.Many2one('product.template', string="Investigations", domain ="[('investigation','=',True)]")
	user_id=fields.Many2one('res.users',String="User")
	x_m_id = fields.Integer(string="Migration_ID")



