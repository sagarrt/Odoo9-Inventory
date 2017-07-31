# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import api, fields, models, _
from openerp.tools.translate import _
from openerp.exceptions import UserError, ValidationError
from openerp import fields
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
from dateutil.relativedelta import relativedelta


class stockLocation(models.Model):
	_inherit = "stock.location"

	pre_ck = fields.Boolean('Pre Stock Location',help="by checking this, Current location is refered as Pre Stock Location . It is used to store product in Stock in ROW,Columns and Case. It shoud be only one location per warehouse")
	actual_location = fields.Boolean("Is Store Location",help='if check this then the Current Location is used for store the products in Row,Shelf,Case', default=False)
	
	row = fields.Integer('No of Row')
	row_name = fields.Many2one("location.series.name","Row Series")
	shelf = fields.Integer('No of Shelf')
	shelf_name = fields.Many2one("location.series.name","Shelf Series")
	case = fields.Integer('No of Case')
	case_name = fields.Many2one("location.series.name","Case Series")
	readonly_bool = fields.Selection([('row','Row'),('rs','Row Shelf'),('rsc','Row Shelf Case')],"Series bool")
	case_name = fields.Many2one("location.series.name","Case Series")
	storage_capacity = fields.Integer('Capacity',help="Sotrage capicity of each Cell , In Pallets.",default=1)
	uom_id = fields.Many2one('product.uom',"Unit")
	storage_locations = fields.Html('Location View')
				
	@api.multi
	def calculate_structure(self):
		for rec in self:
			flag='rsc'
			view =''
			for row in range(rec.row):
				view +='<table style="width:100%" border="1">'
				n_row=0
				if rec.row_name.str_id == 'ASL':
					n_row=chr(ord('a')+row)
				elif rec.row_name.str_id == 'ACL':
					n_row=chr(ord('A')+row)
				elif rec.row_name.str_id == 'NUM':
					n_row=row+1
				elif rec.row_name.str_id == 'ROM':
					n_row=self.int_to_roman(row+1)
				flag='row'
				for shelf in range(rec.shelf):
					view +='<tr>'
					n_shelf=0
					if rec.shelf_name.str_id == 'ASL':
						n_shelf=chr(ord('a')+shelf)
					elif rec.shelf_name.str_id == 'ACL':
						n_shelf=chr(ord('A')+shelf)
					elif rec.shelf_name.str_id == 'NUM':
						n_shelf=shelf+1
					elif rec.shelf_name.str_id == 'ROM':
						n_shelf=self.int_to_roman(shelf+1)
					flag='rs'
					for case in range(rec.case):
						view +='<td>'
						n_case=0
						if rec.case_name.str_id == 'ASL':
							n_case=chr(ord('a')+case)
						elif rec.case_name.str_id == 'ACL':
							n_case=chr(ord('A')+case)
						elif rec.case_name.str_id == 'NUM':
							n_case=case+1
						elif rec.case_name.str_id == 'ROM':
							n_case=self.int_to_roman(case+1)
						view +=str(n_row)+str(n_shelf)+str(n_case)
						search_id=self.env['n.warehouse.placed.product'].search([
								('n_location','=',rec.id),
								('n_row','=',str(n_row)),
								('n_shelf','=',str(n_shelf)),
								('n_case','=',str(n_case)),
								('n_max_qty','=',rec.storage_capacity)])
								
						if not search_id:
							self.env['n.warehouse.placed.product'].create({
								'n_warehouse':False,
								'n_location':str(rec.id),
								'n_row':str(n_row),
								'n_shelf':str(n_shelf),
								'n_case':str(n_case),
								'n_max_qty':rec.storage_capacity,
								})
						flag='rsc'
						view +='</td>'
					view +='</tr>'
				view +='</table> <p><p>'
			rec.storage_locations=view
			print "---",view
			rec.readonly_bool=flag
		
	def int_to_roman(self,input):
		ints = (1000, 900,  500, 400, 100,  90, 50,  40, 10,  9,   5,  4,   1)
		nums = ('M',  'CM', 'D', 'CD','C', 'XC','L','XL','X','IX','V','IV','I')
		result = ""
		for i in range(len(ints)):
		      count = int(input / ints[i])
		      result += nums[i] * count
		      input -= ints[i] * count
		return result 
		
	@api.multi  
	def change_series(self):
		context = self._context.copy()
		order_form = self.env.ref('api_inventory.change_series_form', False)
		if self._context.get('row'):
    			name='Change Row Series'
    			context.update({'default_previous_series':self.row_name.id})
    		if self._context.get('shelf'):
    			name='Change Shelf Series'
    			context.update({'default_previous_series':self.shelf_name.id})
		if self._context.get('row'):
    			name='Change Case Series'
    			context.update({'default_previous_series':self.case_name.id})	
    		if name and order_form:	
			return {
			    'name':name,
			    'type': 'ir.actions.act_window',
			    'view_type': 'form',
			    'view_mode': 'form',
			    'res_model': 'change.series',
			    'views': [(order_form.id, 'form')],
			    'view_id': order_form.id,
			    'context':context,
			    'target': 'new',
			 }
				 
class locationSeriesName(models.Model):
	_name = "location.series.name"

	name = fields.Char(string="Name")
	str_id	= fields.Char(string="Code")
	value = fields.Char('Value')
	
class changeSeries(models.TransientModel):
	_name = "change.series"
	
	previous_series = fields.Many2one("location.series.name","Pervious Series")
	new_series = fields.Many2one("location.series.name","New Series")
	
