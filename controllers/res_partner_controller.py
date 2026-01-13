from odoo import http 
from odoo.http import request
import json
from json import dumps

#http://localhost:8069/web/session/authenticate 
#single call /api/post_partner/?id=2

class PartnereController(http.Controller):
    @http.route('/api/post_partners',type='json', auth="user", methods=['POST'], csrf=False)
    def post_partners(self, **kwargs):
        cnt = 0
        str1 = str(kwargs).replace("\'", "\"")
        x_import = json.loads(str1)
        partners = x_import['data']
        #return partners
        for partner in partners:
            exist = request.env['res.partner'].sudo().search([('ref','=',partner['id'])],limit=1)
            if exist:
                if partner['write_date'] > exist.last_updated:
                    #update provider
                    exist.name = partner['name']
            else:
                #create partner 
                cat = self.env['res.partner.category'].search([('name', '=', 'provider')],limit=1)
                partner['category_id'] = cats,
                good_request=request.env['res.partner'].sudo().create(partner)
                cnt += 1
        if cnt > 1:
            return json.dumps("create success")
        else:
            return "something happened"
    
    