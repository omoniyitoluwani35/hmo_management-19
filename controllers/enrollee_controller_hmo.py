from odoo import http 
from odoo.http import request
import json
from json import dumps

#http://localhost:8069/web/session/authenticate 
#single call /api/post_partner/?id=2

class EnrolleeController(http.Controller):
    @http.route('/api/post_enrollees',type='json', auth="user", methods=['POST'], csrf=False)
    def post_partners(self, **kwargs):
        cnt = 0
        str1 = str(kwargs).replace("\'", "\"")
        x_import = json.loads(str1)
        enrollees = x_import['data']
        #return partners
        for enrollee in enrollees:
            exist = request.env['enrollee'].sudo().search([('code','=',enrollee['code'])],limit=1)
            if exist:
                hcp = request.env['res.partner'].sudo().search([('ref','=',enrollee['hcp'])],limit=1)
                if enrollee['write_date'] > exist.last_updated:
                    #update enrollee
                    exist.surname = enrollee['surname']
                    exist.othername = enrollee['othername']
                    exist.firstname = enrollee['firstname']
                    if hcp:
                        exist.hcp = hcp.id
            else:
                #create enrollee
                good_request=request.env['enrollee'].sudo().create(enrollee)
                cnt += 1
        if cnt > 1:
            return json.dumps("create success")
        else:
            return "something happened"
    
    