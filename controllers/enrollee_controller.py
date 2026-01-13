from odoo import http 
from odoo.http import request
import json
from json import dumps

#http://localhost:8069/web/session/authenticate 
#single call /api/post_partner/?id=2

class EnrolleeController(http.Controller):
    @http.route('/api/post_enrollees',type='json', auth="user", methods=['POST'], csrf=False)
    def post_enrollees(self, **kwargs):
        cnt = 0
        str1 = str(kwargs).replace("\'", "\"")
        x_import = json.loads(str1)
        enrollees = x_import['data']
        #return partners
        for enrollee in enrollees:
            exist = request.env['enrollee'].sudo().search([('code','=',enrollee['code'])],limit=1)
            plan = request.env['product.template'].sudo().search([('default_code','=',enrollee['plan'])],limit=1)
            if exist:
                hcp = request.env['res.partner'].sudo().search([('ref','=',enrollee['hcp'])],limit=1)
                if enrollee: #['write_date'] > exist.last_updated:
                    #update enrollee
                    exist.surname = enrollee['surname']
                    if enrollee['othername']:
                        exist.othername = enrollee['othername']
                    exist.firstname = enrollee['firstname']
                    exist.plan_id = plan.id
                    if hcp:
                        exist.hcp = hcp.id
            else:
                #create enrollee
                if enrollee['othername'] != 'null':
                    othername = enrollee['othername']
                else:
                    othername = False
                hcp = request.env['res.partner'].sudo().search([('ref','=',enrollee['hcp'])],limit=1)
                if hcp:
                    hcp_id = hcp.id
                else:
                    hcp_id = False
                json_data = {'surname' : enrollee['surname'],'firstname' : enrollee['firstname'],'othername' : othername,'code' : enrollee['code'],'hcp':hcp_id, 'plan_id':plan.id}
                good_request=request.env['enrollee'].sudo().create(json_data)
                cnt += 1
        if cnt > 0:
            return json.dumps("{'message':'create success'}")
        else:
            return json.dumps("{'message':'something happened'}")
    
    