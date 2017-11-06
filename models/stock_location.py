# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import api, fields, models, _
from openerp.tools.translate import _
from openerp.exceptions import UserError, ValidationError
from openerp import fields
from urlparse import urljoin
from urllib import urlencode
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
from dateutil.relativedelta import relativedelta
import logging
import math
from openerp.exceptions import UserError
import sys
_logger = logging.getLogger(__name__)

class stockLocation(models.Model):
	_inherit = "stock.location"

	pre_ck = fields.Boolean('Pre Stock Location',help="by checking this, Current location is refered as Pre Stock Location . It is used to store product in Stock in ROW,Columns and Depth. It shoud be only one location per warehouse")
	actual_location = fields.Boolean("Is Store Location",help='if check this then the Current Location is used for store the products in Row,Columns,Depth', default=False)
	
	location_view=fields.One2many('stock.location.view','location_id','Location View')
	storage_locations = fields.Html('Location View',compute="_create_html_view")
	
	@api.multi
	def _create_html_view(self):
		for rec in self:
			pass
			
class stockLocationview(models.Model):
	_name = "stock.location.view"

	@api.model
    	def default_get(self, fields):
		res = {}
		active_id = self._context.get('active_id')
		if active_id:
		    res = {'location_id': active_id}
		return res
        
	name=fields.Char('Name',required=1)
	location_id=fields.Many2one('stock.location','Location Name',ondelete='cascade')
	row = fields.Integer('No of Row(X)')
	row_name = fields.Many2one("location.series.name","Row Series")
	column = fields.Integer('No of Column(Y)')
	column_name = fields.Many2one("location.series.name","Column Series")
	depth = fields.Integer('No of Depth(Z)')
	depth_name = fields.Many2one("location.series.name","Depth Series")
	readonly_bool = fields.Selection([('row','Row'),('rc','Row Column'),('rcd','Row Column Depth')],"Series bool")
	storage_capacity = fields.Integer('Capacity',help="Sotrage capicity of each Cell , In Pallets.",default=1)
	uom_id = fields.Many2one('product.uom',"Unit")
	product_type = fields.Selection([('single','Single Product'),('multi','Multi Product')],'Product Type')
	storage_locations = fields.Html('Location View',compute="_create_html_view")

	@api.model
	def create(self,vals):
		ids=super(stockLocationview, self).create(vals)
		ids.calculate_structure()
		return ids
	
	@api.multi
	def write(self,vals):
		super(stockLocationview, self).write(vals)
		if not vals.get('readonly_bool'):
			self.calculate_structure()
		return True

	@api.multi
	def unlink(self):
		for rec in self:
			search_id=self.env['n.warehouse.placed.product'].search([('location_view','=',rec.id),
								('product_id','!=',False)])
			if search_id:
				raise UserError("You can't delete this record, storage location which are related to this are not empty,if you want to delete this record empty that location first ")
		return super(stockLocationview, self).unlink()
		
	@api.multi
	def calculate_structure(self):
		error_string=''
		try:
		    for rec in self:
			if rec.row_name.str_id == rec.column_name.str_id or rec.column_name.str_id == rec.depth_name.str_id or rec.depth_name.str_id == rec.row_name.str_id:
				error_string='Please select difference series for Storage Name'
				raise
			flag='rsc'
			warehouse=self.env['stock.warehouse'].search([('lot_stock_id','=',rec.location_id.id)],limit=1)
			for row in range(rec.row):
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
				for column in range(rec.column):
					n_column=0
					if rec.column_name.str_id == 'ASL':
						n_column=chr(ord('a')+column)
					elif rec.column_name.str_id == 'ACL':
						n_column=chr(ord('A')+column)
					elif rec.column_name.str_id == 'NUM':
						n_column=column+1
					elif rec.column_name.str_id == 'ROM':
						n_column=self.int_to_roman(column+1)
					flag='rc'
					for depth in range(rec.depth):
						n_depth=0
						if rec.depth_name.str_id == 'ASL':
							n_depth=chr(ord('a')+depth)
						elif rec.depth_name.str_id == 'ACL':
							n_depth=chr(ord('A')+depth)
						elif rec.depth_name.str_id == 'NUM':
							n_depth=depth+1
						elif rec.depth_name.str_id == 'ROM':
							n_depth=self.int_to_roman(depth+1)
						search_id=self.env['n.warehouse.placed.product'].search([
								('warehouse','=',warehouse.id),
								('location','=',rec.location_id.id),
								('location_view','=',rec.id),
								('row','=',str(n_row)),
								('column','=',str(n_column)),
								('depth','=',str(n_depth)),
								])
								
						if not search_id:
							self.env['n.warehouse.placed.product'].create({
								'warehouse':warehouse.id,
								'location':str(rec.location_id.id),
								'location_view':str(rec.id),
								'row':str(n_row),
								'column':str(n_column),
								'depth':str(n_depth),
								'product_type':rec.product_type,
								'max_qty':rec.storage_capacity,
								'qty_unit':rec.uom_id.id,
								})
						flag='rcd'
			rec.readonly_bool=flag
		except Exception as err:
			if error_string:
	   			raise UserError(error_string)
   			else:
	    			exc_type, exc_obj, exc_tb = sys.exc_info()
		    		_logger.error("API-EXCEPTION..Exception in Create Storage Location {} {}".format(err,exc_tb.tb_lineno))
		    		raise UserError("API-EXCEPTION..Exception in Create Storage Location {} {}".format(err,exc_tb.tb_lineno))
				
	def int_to_roman(self,input):
		ints = (1000, 900,  500, 400, 100,  90, 50,  40, 10,  9,   5,  4,   1)
		nums = ('M',  'CM', 'D', 'CD','C', 'XC','L','XL','X','IX','V','IV','I')
		result = ""
		for i in range(len(ints)):
		      count = int(input / ints[i])
		      result += nums[i] * count
		      input -= ints[i] * count
		return result 
	
	#not in use >>>>start	
	@api.multi  
	def change_series(self):
		context = self._context.copy()
		order_form = self.env.ref('api_inventory.change_series_form', False)
		name=''
		context.update({'default_location_id':self.id})
		if self._context.get('row'):
    			name='Change Row Series'
    			context.update({'default_previous_series':self.row_name.id,'default_ntype':'row'})
    		if self._context.get('column'):
    			name='Change Column Series'
    			context.update({'default_previous_series':self.column_name.id,'default_ntype':'column'})
		if self._context.get('depth'):
    			name='Change Depth Series'
    			context.update({'default_previous_series':self.depth_name.id,'default_ntype':'depth'})	
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
	 #<<<end

	@api.multi
	def _create_html_view(self):
		for rec in self:
		    view =''
		    warehouse=self.env['stock.warehouse'].search([('lot_stock_id','=',rec.location_id.id)],limit=1)
		    loc_id=self.env['n.warehouse.placed.product'].search([('warehouse','=',warehouse.id),
									  ('location','=',rec.location_id.id)])
		    if loc_id and rec.row and rec.column and rec.depth:
		    	for depth in range(rec.depth):
		    		view +='<table style="width:100%" border="1">'
				n_depth=0
				if rec.depth_name.str_id == 'ASL':
					n_depth=chr(ord('a')+depth)
				elif rec.depth_name.str_id == 'ACL':
					n_depth=chr(ord('A')+depth)
				elif rec.depth_name.str_id == 'NUM':
					n_depth=depth+1
				elif rec.depth_name.str_id == 'ROM':
					n_depth=self.int_to_roman(depth+1)
				for row in range(rec.row):
					view +='<tr>'
					n_row=0
					if rec.row_name.str_id == 'ASL':
						n_row=chr(ord('a')+row)
					elif rec.row_name.str_id == 'ACL':
						n_row=chr(ord('A')+row)
					elif rec.row_name.str_id == 'NUM':
						n_row=row+1
					elif rec.row_name.str_id == 'ROM':
						n_row=self.int_to_roman(row+1)
					for column in range(rec.column):
						n_column=0
						if rec.column_name.str_id == 'ASL':
							n_column=chr(ord('a')+column)
						elif rec.column_name.str_id == 'ACL':
							n_column=chr(ord('A')+column)
						elif rec.column_name.str_id == 'NUM':
							n_column=column+1
						elif rec.column_name.str_id == 'ROM':
							n_column=self.int_to_roman(column+1)
					
						search_id=self.env['n.warehouse.placed.product'].search([
								('warehouse','=',warehouse.id),
								('location','=',rec.location_id.id),
								('location_view','=',rec.id),
								('row','=',str(n_row)),
								('column','=',str(n_column)),
								('depth','=',str(n_depth)),])
								
						per=100.0/rec.column
						if search_id:
							base_url = self.env['ir.config_parameter'].get_param('web.base.url')
					                query = {'db': self._cr.dbname}
					                fragment = {
								'model': 'n.warehouse.placed.product',
								'view_type': 'form',
                      						'target': 'new',
								'id': search_id.id,
								}
						        url = urljoin(base_url, "/web?%s#%s" % (urlencode(query), urlencode(fragment)))
						        
							if search_id.product_id	:
								view +='<td width="'+str(per)+'%" style="background-color:green;" > <font color="white">'
								text_link = _("""<a href="%s">%s</a> """) % (url,str(n_row)+str(n_column)+str(n_depth))
								view +='<li >'+str(text_link)+'</li>'
								if search_id.product_id:
									view +='<ul><li>'+str(search_id.product_id.name)+'</li>'
								if search_id.total_quantity:
									view +='<li>'+str(search_id.total_quantity)+str(search_id.qty_unit.name)+'</li>'
								if search_id.Packaging_type:
									view +='<li>'+str(search_id.Packaging_type.name)+'</li></ul></font>'
							else:
								view +='<td width="'+str(per)+'%">'
								text_link = _("""<a href="%s">%s</a> """) % (url,str(n_row)+str(n_column)+str(n_depth))
								view +='<li >'+str(text_link)+'</li>'
						else:
							view +='<td width="33%">'
						view +='</td>'
					view +='</tr>'
				view +='</table> <p><p><hr width="100%"> '
		    rec.storage_locations=view

class locationSeriesName(models.Model):
	_name = "location.series.name"

	name = fields.Char(string="Name")
	str_id	= fields.Char(string="Code")
	value = fields.Char('Value')
	
class changeSeries(models.TransientModel):
	_name = "change.series"
	
	previous_series = fields.Many2one("location.series.name","Pervious Series")
	new_series = fields.Many2one("location.series.name","New Series")
	location_id = fields.Many2one("stock.location","Location")
	ntype = fields.Selection([('row','Row'),('column','Column'),('depth','Depth')],"Type")
	
	@api.multi
	def update_series(self):
		for rec in self:
			if rec.ntype == 'row':
				rec.location_id.row_name=rec.new_series.id
			if rec.ntype == 'column':
				rec.location_id.column_name=rec.new_series.id
			if rec.ntype == 'depth':
				rec.location_id.depth_name=rec.new_series.id
				
