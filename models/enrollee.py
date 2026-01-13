# Copyright 2019 Nacmara
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from logging import getLogger

from odoo import _, api, fields, models,Command
from odoo.exceptions import UserError
from datetime import datetime

_logger = getLogger(__name__)


class Enrollee(models.Model):
    _name = 'enrollee'
    _description = 'Enrollees'
    _rec_name = 'code'

    code = fields.Char(string='Enrollee Code', required=True)
    firstname = fields.Char(string='First Name', required=True)
    othername = fields.Char(string='Middle Name')
    surname = fields.Char(string='Surname',required=True)
    start_date = fields.Date(string ='Start Date')
    end_date = fields.Date(string ='End Date')
    hcp = fields.Many2one('res.partner', string='HCP', domain=[('hcp','=',True)])
    employer = fields.Many2one('res.partner', string='Employer', domain =[('customer_rank','=',1)])
    dob = fields.Date(string ='Date of Birth')
    address = fields.Text(string='Address')
    town = fields.Char(string='Town')
    state = fields.Many2one('res.country.state', string='State')
    country = fields.Many2one('res.country', string='Country')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    marital = fields.Selection([('single', 'Single'),('married','Married'),('divorced','Divorced')], string='Marital')
    gender = fields.Selection([('male', 'Male'),('female','Female')],string='Gender')
    coverage = fields.Selection([('individual', 'Individual'), ('family','Family')], string='Coverage')
    type = fields.Selection([('principal', 'Principal') ,('dependent','Dependent')], string='Plan Type')
    active = fields.Boolean('Active', default=True)
    bloodgroup = fields.Char(string='Blood Group')
    genotype = fields.Char(string='Genotype')
    occupation = fields.Char(string='Occupation')
    comment = fields.Text(string='Comments')
    uncapitated = fields.Boolean('Not Capitated')
    enforce = fields.Boolean('Waive plan limit')
    ref = fields.Char(string='External Reference')
    policy_start_date = fields.Date(string ='Policy Start Date')
    policy_cycle_date = fields.Date(string ='Current Policy Cycle')
    plan = fields.Many2one('product.product', string='Health Plan', domain=[('sale_ok','=',True),('categ_id.name','=','Plans')])
    dependent1=fields.Many2one('enrollee', string='Dependent 1')
    dependent2=fields.Many2one('enrollee', string='Dependent 2')
    dependent3=fields.Many2one('enrollee', string='Dependent 3')
    dependent4=fields.Many2one('enrollee', string='Dependent 4')
    dependent5=fields.Many2one('enrollee', string='Dependent 5')
    extra1=fields.Many2one('enrollee', string='Extra Dep 1')
    extra2=fields.Many2one('enrollee', string='Extra Dep 2')
    extra3=fields.Many2one('enrollee', string='Extra Dep 3')
    extra4=fields.Many2one('enrollee', string='Extra Dep 4')
    extra5=fields.Many2one('enrollee', string='Extra Dep 5')
    password = fields.Char(string='Password')
    picture= fields.Binary(attachment=True, string='Picture')
    lga = fields.Many2one('lga', string='LGA')
    treatment_lines = fields.One2many('purchase.order.line', 'enrollee_id', string= 'Medical History')
    x_m_id = fields.Integer(string="Migration_ID")
    dependents = fields.Integer(string ='Dependents',compute ='_compute_deps',store=True)
    principal_id=fields.Many2one('enrollee', string='Principal')
    
    def name_get(self):
        res=[]
        for emp in self:
            res.append((emp.id, emp.surname + ', ' + emp.firstname + ' - ' + emp.code))   
        return res

    @api.depends('type','dependent1','dependent2','dependent3','dependent4','dependent5','extra1','extra2','extra3','extra4','extra5')
    def _compute_deps(self):
        dep = 0
        for part in self:
            dep = 0
            if part.type == 'principal':
                if part.dependent1:
                    dep+=1
                if part.dependent2 :
                    dep+=1
                if part.dependent3 :
                    dep+=1
                if part.dependent4 :
                    dep+=1
                if part.dependent5 :
                    dep+=1
                if part.extra1 :
                    dep+=1
                if part.extra2 :
                    dep+=1
                if part.extra3 :
                    dep+=1
                if part.extra4 :
                    dep+=1
                if part.extra5:
                    dep+=1
            part.dependents =  dep
                
    #@api.one
    def _set_image(self):
        self._set_image_value(self.picture)

    #@api.one
    def _set_image_value(self, value):
        if isinstance(value, pycompat.text_type):
            value = value.encode('ascii')
        image = tools.image_resize_image_medium(value)
        self.picture = image

    @api.onchange('active')
    def _onchange_active(self):
        if self.active != True:
            self.end_date = datetime.now().date()
        else:
            self.end_date = False
	
    def _get_binary_filesystem(self):
        """ Display the binary from ir.attachment, if already exist """
        res = {}
        attachment_obj = self.pool.get('ir.attachment')

        for record in self:
            res[record.id] = False
            attachment_ids = record.env['ir.attachment'].search([('res_model','=',self._name),('res_id','=',record.id),('name','=',name)])
            #_logger = logging.getLogger(__name__)
            _logger.info('res %s', attachment_ids)
            if attachment_ids:
                img  = record.env['ir.attachment'].browse(attachment_ids)[0].datas
                _logger.info('res %s', img)
                res[record.id] = img
        return res

    def _set_binary_filesystem(self, cr, uid, id, name, value, arg, context=None):
        """ Create or update the binary in ir.attachment when we save the record """
        attachment_obj = self.pool.get('ir.attachment')

        attachment_ids = attachment_obj.search([('res_model','=',self._name),('res_id','=',id),('name','=',name)])
        if value:
            if attachment_ids:
                attachment_obj.write(attachment_ids, {'datas': value})
            else:
                attachment_obj.create({'res_model': self._name, 'res_id': id, 'name': 'Enrollee picture', 'name': name, 'datas': value, 'datas_fname':'picture.jpg'})
        else:
            attachment_obj.unlink(attachment_ids)
    
    @api.onchange('dependent1')
    def _onchange_dependent1(self):
        if self.dependent1:
            self.update_principal(self.id,self.dependent1.id)
        
    @api.onchange('dependent2')
    def _onchange_dependent2(self):
        if self.dependent2:
            self.update_principal(self.id,self.dependent2.id)
             
    @api.onchange('dependent3')
    def _onchange_dependent3(self):
        if self.dependent3:
            self.update_principal(self.id,self.dependent3.id)
        
    @api.onchange('dependent4')
    def _onchange_dependent4(self):
        if self.dependent4:
            self.update_principal(self.id,self.dependent4.id)
       
    @api.onchange('dependent5')
    def _onchange_dependent5(self):
        if self.dependent5:
            self.update_principal(self.id,self.dependent5.id)
            
    @api.onchange('extra1')
    def _onchange_extra1(self):
        if self.extra1:
            self.update_principal(self.id,self.extra1.id)
        
    @api.onchange('extra2')
    def _onchange_extra2(self):
        if self.extra2:
            self.update_principal(self.id,self.extra2.id)
        
    @api.onchange('extra3')
    def _onchange_extra3(self):
        if self.extra3:
            self.update_principal(self.id,self.extra3.id)
        
    @api.onchange('extra4')
    def _onchange_extra4(self):
        if self.extra4:
            self.update_principal(self.id,self.extra4.id)
    
    @api.onchange('extra5')
    def _onchange_extra5(self):
        if self.extra5:
            self.update_principal(self.id,self.extra5.id)
    
    def update_principals(self):
        enrollees = self.env['enrollee'].search([('type','=','principal'),('employer.id','!=',7065)])
        for enrollee in enrollees:
            enrollee._onchange_dependent1()
            enrollee._onchange_dependent2()
            enrollee._onchange_dependent3()
            enrollee._onchange_dependent4()
            enrollee._onchange_dependent5()
            enrollee. _onchange_extra1()
            enrollee._onchange_extra2()
            enrollee._onchange_extra3()
            enrollee._onchange_extra4()
            enrollee._onchange_extra5()
            
    def update_principal(self,pr_id,de_id,has_value = True):
        if has_value:
            query = "update enrollee set principal_id = " + str(pr_id).replace("NewId_","") + " where id = " + str(de_id)
        else:
            query = "update enrollee set principal_id = null  where id = " + str(de_id)
        yc = self.env.cr.execute(query)

class LGA(models.Model):
    _name = 'lga'
    _description = 'Local Govt Areas'


    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code')
    state = fields.Many2one('res.country.state', string='State')
