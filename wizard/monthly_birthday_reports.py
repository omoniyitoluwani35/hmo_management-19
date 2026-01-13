
import xlwt
from io import StringIO
import io
import base64
import time
import datetime
from datetime import datetime
from datetime import timedelta

from odoo import api, fields, models

class monthly_birthday(models.TransientModel):
    _name= "monthly.birthday.reports"
    _description= "Retrieve birthdays for the month"

    day_of_month = fields.Date(string='Choose any date of the month', required=True)
    status = fields.Selection([
        ('all', 'All'),
        ('private', 'Private'),
        ('nhis', 'NHIS'),
        ], string='Type', copy=False)
    
    #@api.multi
    def monthly_birthday_reports(self,context=None):
 
        sql_date="select surname, firstname, othername,code, phone, dob from enrollee where (extract(month from dob) =  extract(month from TIMESTAMP '" + str(self.day_of_month) + "')) and (extract(day from dob) =  extract(day from TIMESTAMP '" + str(self.day_of_month) + "')) and active = true " 
        
        if self.status == 'all':
            self.env.cr.execute(sql_date)
            res = self.env.cr.dictfetchall()
            return self._print_report_excel(res)
        elif self.status == 'private':
            self.env.cr.execute(sql_date + " and employer <> 7875")
            res = self.env.cr.dictfetchall()	
            return self._print_report_excel(res)
        else:
            self.env.cr.execute(sql_date + " and employer = 7875")
            res = self.env.cr.dictfetchall()	
            return self._print_report_excel(res)

    #@api.multi
    def _print_report_excel(self, datas):
        workbook = xlwt.Workbook()
        title_style_comp = xlwt.easyxf('align: horiz center ; font: name Times New Roman,bold off, italic off, height 450')
        title_style_comp_left = xlwt.easyxf('align: horiz left ; font: name Times New Roman,bold off, italic off, height 450')
        title_style = xlwt.easyxf('align: horiz center ;font: name Times New Roman,bold off, italic off, height 350')
        title_style2 = xlwt.easyxf('font: name Times New Roman, height 200')
        title_style1 = xlwt.easyxf('font: name Times New Roman,bold off, italic off, height 190; borders: top double, bottom double, left double, right double;')
        title_style1_table_head = xlwt.easyxf('font: name Times New Roman,bold on, italic off, height 200; borders: top double, bottom double, left double, right double;')
        title_style1_table_head1 = xlwt.easyxf('font: name Times New Roman,bold on, italic off, height 200')
        title_style1_consultant = xlwt.easyxf('font: name Times New Roman,bold on, italic off, height 200; borders: top double, bottom double, left double, right double;')
        title_style1_table_head_center = xlwt.easyxf('align: horiz center ; font: name Times New Roman,bold on, italic off, height 190; borders: top thick, bottom thick, left thick, right thick;')

        title_style1_table_data = xlwt.easyxf('align: horiz right ;font: name Times New Roman,bold on, italic off, height 190',num_format_str='#,##0.00')
        title_style1_table_data_sub = xlwt.easyxf('font: name Times New Roman,bold off, italic off, height 190')
        title_style1_table_data_sub = xlwt.easyxf('font: name Times New Roman,bold off, italic off, height 190', num_format_str='dd/MM/yyyy')
        #title_style1_table_data_sub.num_format_str = '#,##.00'
        title_style1_table_data_sub_amount = xlwt.easyxf('align: horiz right ;font: name Times New Roman,bold off, italic off, height 190',num_format_str='#,##0.00')
        title_style1_table_data_sub_balance = xlwt.easyxf('align: horiz right ;font: name Times New Roman,bold off, italic off, height 190',num_format_str='#,##0.00')
        #gl_report_obj = self.env['report.account_extra_reports.report_partnerledger']
        
        sheet_name = 'Enrollee Birthdays'
        sheet = workbook.add_sheet(sheet_name)
        
        sheet.write_merge(0, 1, 0, 6, 'Monthly Birthdays Report', title_style_comp_left)
        sheet.write(0, 8, 'Printing Date: '+datetime.now().strftime('%Y-%m-%d'), title_style1_table_head1)
        
        comp_id = self.env.user.company_id
        currency_id = comp_id.currency_id
        sheet.write(3, 0, 'Company',title_style1_table_head1)
        sheet.write(4, 0, comp_id.name, title_style1_table_data_sub)
        
       
        
        sheet.write(8, 0, 'Surname',title_style1_table_head)
        sheet.write(8, 1, 'Firstname',title_style1_table_head)
        sheet.write(8, 2, 'Othername',title_style1_table_head)
        sheet.write(8, 3, 'Code',title_style1_table_head)
        sheet.write(8, 4, 'Phone No',title_style1_table_head)
        sheet.write(8, 5, 'DoB',title_style1_table_head)
       
        
        roww = 9        
        row_data = roww+1
        for line in datas:
            sheet.write(row_data, 0, line['surname'], title_style1_table_data_sub)
            column = sheet.col(0)
            column.width = 256 * 25
            sheet.write(row_data, 1, line['firstname'], title_style1_table_data_sub)
            sheet.write(row_data, 2, line['othername'], title_style1_table_data_sub)
            sheet.write(row_data, 3, line['code'], title_style1_table_data_sub)
            sheet.write(row_data, 4, line['phone'], title_style1_table_data_sub)
            sheet.write(row_data, 5, line['dob'], title_style1_table_data_sub)

            row_data = row_data + 1
        roww = row_data + 3

        stream =  io.BytesIO() #StringIO()
        workbook.save(stream)
        attach_id = self.env['monthly.birthday.report.output.wizard'].create({'name':'Monthly_Birthdays.xls', 'xls_output': base64.encodestring(stream.getvalue())})
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'monthly.birthday.report.output.wizard',
            'res_id':attach_id.id,
            'type': 'ir.actions.act_window',
            'target':'new'
        }

    class MonthlyBirthdayReportOutputWizard(models.Model):
        _name = 'monthly.birthday.report.output.wizard'
        _description = 'Wizard to store the Excel output'

        xls_output = fields.Binary(string='Excel Output',readonly=True)
        name = fields.Char(
            string='File Name',
            help='Save report as .xls format',
            default='Monthly_Birthdays.xls',
        )
