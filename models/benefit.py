from datetime import datetime
from odoo import models,fields,api,_
import logging

_logger = logging.getLogger(__name__)

class benefit_category (models.Model):# Name class
	_name = 'benefit.category'
	_description = 'Benefit Category'
	name = fields.Char(string="Category")
	x_m_id = fields.Integer(string="Migration_ID")
	
class plan_benefit (models.Model):# Name class
	_name = 'plan.benefit'
	_description = 'Plan Benefits'
	
	name = fields.Char(string="Benefit Name")
	line_id = fields.One2many('benefit.lines', 'plan_benefit_id', string='Lines')
	plan_id = fields.Many2one('product.product',string="Plan")
	employer_ids = fields.One2many('employer.lines', 'plan_benefit_id', string='Customers')
	employer_id = fields.Many2one('res.partner',string="Customer")
	x_m_id = fields.Integer(string="Migration_ID")


class benefit (models.Model):# Name class
	_name = 'benefit'
	_description = 'Benefits'
    
	category_id = fields.Many2one('benefit.category',string="Category")
	name = fields.Char(string="Benefit")
	x_m_id = fields.Integer(string="Migration_ID")

class benefit_lines (models.Model):# Name class
	_name = 'benefit.lines'
	_description = 'Approved Treatment'
    
	plan_benefit_id = fields.Many2one('plan.benefit',string="Plan")
	name = fields.Many2one('benefit', string="Benefit")
	remarks = fields.Char(string="Remarks")
	x_m_id = fields.Integer(string="Migration_ID")
    
class employer_lines (models.Model):# Name class
	_name = 'employer.lines'
	_description = 'Benefits Customers'
    
	plan_benefit_id = fields.Many2one('plan.benefit',string="Plan")
	name = fields.Many2one('res.partner', string="Customer")
	plan_id = fields.Many2one(related="plan_benefit_id.plan_id",string = "Plan")
