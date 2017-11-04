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


class StockWarehouseMain(models.Model):
	_name = "n.warehouse.placed.product"
	_inherit = 'mail.thread'
	_order = "row,column,depth"
	
	@api.multi
	@api.depends('pkg_capicity','packages')
	def _get_free_qty(self):
		for rec in self:
			rec.n_free_qty=rec.pkg_capicity - rec.packages
				
	mo_number = fields.Many2one("mrp.production","MO Number")
    	po_number = fields.Many2one("purchase.order","PO Number")
    	
	warehouse = fields.Many2one('stock.warehouse','Warehouse')
	location = fields.Many2one('stock.location','Location')
	location_view = fields.Many2one('stock.location.view','Location',ondelete='cascade')
	row = fields.Char('Row')
	column =fields.Char('Column')
	depth =fields.Char('Depth')
	product_id = fields.Many2one('product.product', string="Product")
	state= fields.Selection([('empty','Empty'),('partial','Partial'),('full','FULL'),('maintenance','In Maintenance')],default='empty')
	label_status = fields.Selection([('done','Done'),('warehouse','Warehouse'),
					 ('location','Location'),('row','Row'),
					 ('column','Column'),('depth','Depth'),('less_qty','Less Qty')],default='done')
	max_qty = fields.Float('Storage Capacity',default=0.0)
	pkg_capicity = fields.Float('Packages Capacity',default=0.0,help="maximum capacity of storage in packets, Caucluation based on product packaging")
	pkg_capicity_unit = fields.Many2one("product.uom",'Unit')
	free_qty = fields.Float('Free Quantity',compute="_get_free_qty")
	
	Packaging_type = fields.Many2one('product.packaging' ,string="Packaging",copy=True)
	packages = fields.Float('No of Packages',default=0.0,help="Total No. of packets currently in Storage")
	pkg_unit = fields.Many2one("product.uom",'Unit')
	
	total_quantity = fields.Float('Total Store Quantity',default=0.0, help="total quantity in product units")
	qty_unit = fields.Many2one("product.uom",'Unit')
	
	@api.multi
	def name_get(self):
	    result = []
	    for record in self:
		name = str(record.location.name)+'-'+str(record.location_view.name) +'/'+ str(record.row) +'/'+ str(record.column) +'/'+ str(record.depth)
		result.append((record.id, name))
	    return result
    
    	@api.multi
    	def open_stock_history(self):
    		for rec in self:
    			order_tree = self.env.ref('Odoo9-Inventory.stock_location_history_action_tree', False)
			return {
			    'name':'History Location Product',
			    'type': 'ir.actions.act_window',
			    'view_type': 'form',
			    'view_mode': 'tree',
			    'res_model': 'location.history',
			    'views': [(order_tree.id, 'tree')],
			    'view_id': order_tree.id,
			    'domain':[('stock_location','=',rec.id)],
			    'target': 'new',
			 }

    	@api.multi
    	def stock_operation(self):
    	   for rec in self:
    		order_form=name=''
    		context = self._context.copy()
		context.update({'default_product_id':rec.product_id.id,'default_stock_location':rec.id})
	    	if self._context.get('add_stock'):
    			order_form = self.env.ref('Odoo9-Inventory.add_stock_location_operation_form', False)
    			name='Add Quantity In Store'
    			context.update({'default_storage':0})
    			
	    	if self._context.get('release_stock'):
    			order_form = self.env.ref('Odoo9-Inventory.remove_stock_location_operation_form', False)
    			name='Remove Quantity From Store'
    			context.update({'default_qty':rec.total_quantity})
    			
	    	if self._context.get('transfer_stock'):
    			order_form = self.env.ref('Odoo9-Inventory.transfer_stock_location_operation_form', False)
    			name='Transfer Quantity In Store To Store'
    			#context.update({'default_qty':rec.n_qty})
    			
		if self._context.get('update_stock'):
    			order_form = self.env.ref('Odoo9-Inventory.update_stock_location_operation_form', False)
    			name='Update Quantity In Store'
    		if name and order_form:	
			return {
			    'name':name,
			    'type': 'ir.actions.act_window',
			    'view_type': 'form',
			    'view_mode': 'form',
			    'res_model': 'location.stock.operation',
			    'views': [(order_form.id, 'form')],
			    'view_id': order_form.id,
			    'context':context,
			    'target': 'new',
			 }
			 
	#@api.model
	#def create(self,vals):
	#	if vals.get('n_qty') and vals.get('max_qty'):
	#		if vals.get('n_qty') >= vals.get('max_qty'):
	#			vals.update({'state':'full'})
	#		else:
	#			vals.update({'state':'partial'})
	#	return super(StockWarehouseMain,self).create(vals)

	@api.multi
	def change_storage_capicity(self):
    		context = self._context.copy()
    		unit=self.env['product.uom'].search([('name','=ilike','pallet')],limit=1)
    		packages = (self.pkg_capicity if self.pkg_capicity else 1) / (self.max_qty if self.max_qty else 1)
		context.update({'default_previous_storage_capicity':self.max_qty,
				'default_pre_capicity_unit':unit.id,
				'default_used_storage':float(self.packages)/packages,
				'default_stock_location':self.id,
				'default_new_capicity_unit':unit.id,
				'default_used_unit':unit.id})
		order_form = self.env.ref('Odoo9-Inventory.update_storage_capicity_operation_form', False)
		return {
			    'name':"Update Storage Capicity",
			    'type': 'ir.actions.act_window',
			    'view_type': 'form',
			    'view_mode': 'form',
			    'res_model': 'location.stock.operation',
			    'views': [(order_form.id, 'form')],
			    'view_id': order_form.id,
			    'context':context,
			    'target': 'new',
			 }

	@api.model
    	def name_search(self, name, args=None, operator='ilike',limit=100):
		if self._context.get('outgoing_wizard'):
        		if self._context.get('product_id'):
        			batch=[]
        			if self._context.get('store_id'):
	        			store=self._context.get('store_id')[0][2] if self._context.get('store_id')[0] else []
                		material=self.search([('product_id','=',self._context.get('product_id'))])
				wizard=self.env['stock.store.location.wizard'].search([('id','=',self._context.get('wizard_id'))])
                		return [(rec.id,str(rec.location.name)+'-'+str(rec.location_view.name) +'/'+ str(rec.row) +'/'+ str(rec.column) +'/'+ str(rec.depth)) for rec in material if rec.id not in store ]
        		return []
        	return super(StockWarehouseMain,self).name_search(name, args, operator=operator,limit=limit)	
        	
class locationHistory(models.Model):
	_name = "location.history"
	
	stock_location = fields.Many2one('n.warehouse.placed.product','Stock Location')
	product_id = fields.Many2one('product.product', string="Product")
	qty = fields.Float('Quantity')
	operation_name= fields.Char('Operation')
	operation = fields.Selection([('mo','MO'),('po','PO'),('do','DO'),('transfer','Transfer')])
	ntype = fields.Selection([('in','IN'),('out','OUT')],default='in')
	
	mo_number = fields.Many2one("mrp.production","MO Number")
    	po_number = fields.Many2one("purchase.order","PO Number")
    	do_number = fields.Many2one("stock.picking","DO Number")
    	qc_number = fields.Many2one("stock.picking","QC Number")
    	

