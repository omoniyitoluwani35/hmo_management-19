from odoo import http 
from odoo.http import request
import json
from json import dumps

#http://localhost:8069/web/session/authenticate 

class Product(http.Controller):
    @http.route('/api/post_products',type='json', auth="user", methods=['POST'], csrf=False)
    def post_products(self, **kwargs):
        cnt = 0
        str1 = str(kwargs).replace("\'", "\"")
        x_import = json.loads(str1)
        products = x_import['data']
        for product in products:
            e_product = request.env['product.template'].sudo().search([('default_code','=',product['default_code'])],limit=1)
            if product['product_type'] == 'plan':
                cat = request.env['product.category'].sudo().search([('name','=','Plans')],limit=1)
            else:
                cat = request.env['product.category'].sudo().search([('name','=','Services')],limit=1)
            if e_product:
                e_product.name = product['name']
            else:
                product['detailed_type'] = 'service'
                product['taxes_id'] = None
                product['categ_id'] = cat.id
                good_request=request.env['product.template'].sudo().create(product)
                cnt += 1
        if cnt > 1:
            return json.dumps("create success")
        else:
            return "something happened"