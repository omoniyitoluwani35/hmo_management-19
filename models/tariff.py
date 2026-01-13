from logging import getLogger

from odoo import _, api, fields, models
from odoo.exceptions import UserError

class tariff (models.Model):# Name class
	_name = 'tariff'
	_description = 'Tariffs'
	
	name = fields.Char(string='Tariff Name', required=True)
	active =  fields.Boolean('Active', default=True)
	code  = fields.Char(string='Code')
	tariff_line = fields.One2many('tariff.lines', 'tariff_id', string="Products", copy=True)
	x_m_id = fields.Integer(string='Migration_ID')
	product_ids = fields.Many2many('product.product', string='Allowed Products', compute='_compute_product_ids', store=True, help="Automatically populated from Tariff Lines for fast lookup." )
	state = fields.Selection([
		('draft', 'Draft'),
		('confirm', 'Confirmed'),
	], string="State", default='draft', copy=False)


	#@api.depends('tariff_lines.product_id')
	#def _compute_product_ids(self):
	#	for tariff in self:
	#		tariff.product_ids = tariff.tariff_lines.mapped('product_id')

	@api.depends('tariff_line.product_id')
	def _compute_product_ids(self):
		Product = self.env['product.product']
		for tariff in self:
			# Collect product templates from tariff lines
			template_ids = tariff.tariff_line.mapped('product_id')
			if template_ids:
				# Get all product variants belonging to those templates
				products = Product.search([('product_tmpl_id', 'in', template_ids.ids)])
				tariff.product_ids = products
			else:
				tariff.product_ids = False

	def set_tariff_products(self):
		tfs = self.env['tariff'].search([])
		for tf in tfs:
			tf._compute_product_ids()

	def action_confirm(self):
		for rec in self:
			rec.set_tariff_products()
			rec.write({'state':'confirm'})

	def action_draft(self):
		for rec in self:
			rec.product_ids = False
			rec.write({'state':'draft'})

	def name_get(self):
		res=[]
		for emp in self:
			res.append((emp.id, emp.name + ', ' + emp.code))    
		return res
		
class tariff_line (models.Model):# Name class
	_name = 'tariff.lines'
	_description = 'Tariffs Lines'
	
	name = fields.Char(string="Details", required=True)
	product_id = fields.Many2one('product.template', string="Product", domain ="[('purchase_ok','=',True)]")
	tariff_id = fields.Many2one('tariff', string="Tariff")
	price = fields.Float(string="Price", digits=(16, 2))
	comment = fields.Char(string="Comment")
	x_m_id = fields.Integer(string="Migration_ID")

	def on_product_change(self, product_ids, tariff_ids, list_price, context=None):
		tariff = list_price
		if product_ids and tariff_ids:
			sql=("select price from tariff_lines where tariff_id =" + str(tariff_ids) + " and product_id = (select product_template.id from product_template inner join product_product on product_product.product_tmpl_id = product_template.id where product_product.id = " + str(product_ids) + ")")
			rc = self.env.cr.execute(sql)
			for row in self.env.cr.dictfetchall():
				tariff=row['price']
		return tariff
		
	def name_get(self):
		res=[]

		for emp in self:
			res.append((emp.id, emp.product_id.name ))    
		return res
	