from datetime import datetime
from odoo import models,fields,api,_
import logging

_logger = logging.getLogger(__name__)

class visitation (models.Model):# Name class
	_name = 'visitation'
	_description = 'Hospital Visitation'
	
	def name_get(self):
		res=[]

		for emp in self:
			res.append((emp.id, emp.name.name + ' - ' + emp.hcp.name))    
		return res

	name = fields.Many2one('enrollee', string="Enrollee")
	admission_date = fields.Date(string ="Admission Date")
	discharge_date = fields.Date(string ="Discharge Date")
	visit_date = fields.Date(string ="Visitation Date")
	hcp = fields.Many2one('res.partner', string="HCP", domain="[('hcp','=',True)]")
	employer = fields.Many2one('res.partner', string="Employer", domain ="[('customer_rank','=',1)]")
	auth_code = fields.Many2one('purchase.order', string="Approval Code", domain ="[('claim_type','=','claim')]")
	active = fields.Boolean("Closed", default=True)
	complaint = fields.Text(string="Presenting Complaint")
	finding = fields.Text(string="Examination Finding")
	result = fields.Text(string="Investigation Results")
	comment = fields.Text(string="Comments")
	diagnosis=fields.Many2one('icd', string="Diagnosis")
	contact = fields.Char(string="Hospital Contact")
	plan_id = fields.One2many('treatment.plan', 'visitation_id', string='Treatment Plan Lines')
	approved_id = fields.One2many('treatment.approved', 'visitation_id', string='Approved Treatment Lines')
	x_m_id = fields.Integer(string="Migration_ID")


class treatment_plan (models.Model):# Name class
	_name = 'treatment.plan'
	_description = 'Treatment Plan'
	name = fields.Many2one('product.product',string="Treatment", domain="[('is_drug','=',True)]")
	visitation_id = fields.Many2one('visitation', string="Lines")
	x_m_id = fields.Integer(string="Migration_ID")

class treatment_approved (models.Model):# Name class
	_name = 'treatment.approved'
	_description = 'Approved Treatment'
	name = fields.Many2one('product.product',string="Treatment", domain="[('is_drug','=',True)]")
	visitation_id = fields.Many2one('visitation', string="Lines")
	x_m_id = fields.Integer(string="Migration_ID")
