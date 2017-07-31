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
	_order = "n_row,n_shelf,n_case"
	
	@api.multi
	@api.depends('n_qty','n_max_qty')
	def _get_free_qty(self):
		for rec in self:
			if rec.n_max_qty < rec.n_qty:
				raise UserError(_('Entered Store Quantity is shoud be less than Storage Capacity')) 
			rec.n_free_qty=rec.n_max_qty-rec.n_qty
			if rec.n_max_qty-rec.n_qty==0.0:
				rec.state='full'
				
	n_mo_number = fields.Many2one("mrp.production","MO Number")
    	n_po_number = fields.Many2one("purchase.order","PO Number")
    	n_do_number = fields.Many2one("stock.picking","DO Number")
    	n_qc_number = fields.Many2one("stock.picking","QC Number")
    	
	n_warehouse = fields.Many2one('stock.warehouse','Warehouse')
	n_location = fields.Many2one('stock.location','Location')
	n_row = fields.Char('Row')
	n_shelf =fields.Char('Shelf')
	n_case =fields.Char('Case')
	product_id = fields.Many2one('product.product', string="Product")
	state= fields.Selection([('empty','Empty'),('partial','Partial'),('full','FULL'),('maintenance','In Maintenance')],default='empty')
	label_status = fields.Selection([('done','Done'),('warehouse','Warehouse'),
					 ('location','Location'),('row','Row'),
					 ('shelf','Shelf'),('case','Case'),('less_qty','Less Qty')],default='done')
	n_max_qty = fields.Float('Storage Capacity')
	n_qty = fields.Float('Store Qunatity')
	n_free_qty = fields.Float('Free Qunatity',compute="_get_free_qty",store=True)
	
	@api.multi
	def name_get(self):
	    result = []
	    for record in self:
		name = str(record.n_location.name) +'/'+ str(record.n_row) +'/'+ str(record.n_shelf) +'/'+ str(record.n_case)
		result.append((record.id, name))
	    return result
    
    	@api.multi
    	def open_stock_history(self):
    		for rec in self:
    			order_tree = self.env.ref('api_inventory.stock_location_history_action_tree', False)
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
    			order_form = self.env.ref('api_inventory.add_stock_location_operation_form', False)
    			name='Add Stock In Location'
    			context.update({'default_storage':rec.n_free_qty})
    			
	    	if self._context.get('release_stock'):
    			order_form = self.env.ref('api_inventory.remove_stock_location_operation_form', False)
    			name='Remove Stock In Location'
    			context.update({'default_qty':rec.n_qty})
    			
	    	if self._context.get('transfer_stock'):
    			order_form = self.env.ref('api_inventory.transfer_stock_location_operation_form', False)
    			name='Transfer Stock In Location'
    			context.update({'default_qty':rec.n_qty})
    			
		if self._context.get('update_stock'):
    			order_form = self.env.ref('api_inventory.update_stock_location_operation_form', False)
    			name='Update Stock In Location'
    			qty=rec.product_id.qty_available
			for line in self.search([('product_id','=',rec.product_id.id),('state','!=','empty')]):
				qty -= line.n_qty
    			context.update({'default_qty':qty,'default_storage':rec.n_free_qty})
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
			 
	@api.model
	def create(self,vals):
		if vals.get('n_qty') and vals.get('n_max_qty'):
			if vals.get('n_qty') >= vals.get('n_max_qty'):
				vals.update({'state':'full'})
			else:
				vals.update({'state':'partial'})
		return super(StockWarehouseMain,self).create(vals)


	@api.multi
	def change_storage_capicity(self):
    		context = self._context.copy()
		context.update({'default_previous_storage_capicity':self.n_max_qty,'default_stock_location':self.id})
		order_form = self.env.ref('api_inventory.update_storage_capicity_operation_form', False)
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
	
class locationHistory(models.Model):
	_name = "location.history"
	
	stock_location = fields.Many2one('n.warehouse.placed.product','Stock Location')
	product_id = fields.Many2one('product.product', string="Product")
	qty = fields.Float('Quantity')
	operation_name= fields.Char('Operation')
	operation = fields.Selection([('mo','MO'),('po','PO'),('do','DO'),('transfer','Transfer')])
	n_type = fields.Selection([('in','IN'),('out','OUT')],default='in')
	
	n_mo_number = fields.Many2one("mrp.production","MO Number")
    	n_po_number = fields.Many2one("purchase.order","PO Number")
    	n_do_number = fields.Many2one("stock.picking","DO Number")
    	n_qc_number = fields.Many2one("stock.picking","QC Number")
    	
class locationStockOperation(models.TransientModel):
	_name = "location.stock.operation"
	
	stock_location = fields.Many2one('n.warehouse.placed.product','Stock Location')
	new_stock_location = fields.Many2one('n.warehouse.placed.product','New Stock Location')
	product_id = fields.Many2one('product.product', string="Product")
	qty = fields.Float('Avaiable Quantity')
	storage = fields.Float('Available Capicity')
	add_qty = fields.Float('Add Quantity')
	new_storage_capicity = fields.Float('New Storage Capacity')
	previous_storage_capicity = fields.Float('Previous Storage Capacity')
	
	@api.multi
	@api.onchange('new_stock_location')
	def _get_free_qty(self):
		for rec in self:
			rec.storage=rec.new_stock_location.n_free_qty
	
	@api.multi
	@api.onchange('product_id')
	def _get_product_qty(self):
	   if self._context.get('add_stock'):
		for rec in self:
			qty=rec.product_id.qty_available
			for line in self.env['n.warehouse.placed.product'].search([('product_id','=',rec.product_id.id),('state','!=','empty')]):
				qty -= line.n_qty
			rec.qty=qty	
			
	@api.multi
	def save(self):
		n_type=''
		if self._context.get('add_stock'):
			n_type='in'
			if self.add_qty >self.qty:
				 raise UserError(_('Entered Quantity is shoud be less than Available Storage Capicty')) 
			self.stock_location.product_id=self.product_id
			self.stock_location.n_qty=self.add_qty
			self.stock_location.state = 'full' if self.add_qty==self.qty else 'partial'
			
		if self._context.get('update_stock'):
			n_type='in'
			if self.add_qty >self.qty:
				 raise UserError(_('Entered Quantity is shoud be less than Available Storage Capicty')) 
			self.stock_location.n_qty+=self.add_qty
			self.stock_location.state = 'full' if self.stock_location.n_qty==self.stock_location.n_max_qty else 'partial'
			
		if self._context.get('release_stock'):
			n_type='out'
			if self.stock_location.n_qty==self.add_qty:
				self.stock_location.product_id=False
				self.stock_location.n_qty=0.0
				self.stock_location.state ='empty'
			else:
				self.stock_location.n_qty-=self.add_qty
				self.stock_location.state ='partial'
				
		if self._context.get('transfer_stock'):
			n_type='out'
			if self.stock_location.n_qty==self.add_qty:
				self.stock_location.product_id=False
				self.stock_location.n_qty=0.0
				self.stock_location.state = 'empty'
			else:
				self.stock_location.n_qty-=self.add_qty
				self.stock_location.state='partial'
			self.new_stock_location.product_id=self.product_id
			self.new_stock_location.n_qty=self.add_qty
			self.new_stock_location.state='full' if self.new_stock_location.n_free_qty == self.add_qty else 'partial'
			self.env['location.history'].create({
					'stock_location':self.new_stock_location.id,
					'product_id':self.stock_location.product_id.id,
					'qty':self.add_qty,
					'n_type':'in',
				})
				
		self.env['location.history'].create({
					'stock_location':self.stock_location.id,
					'product_id':self.stock_location.product_id.id,
					'qty':self.add_qty,
					'n_type':n_type,
				})
		return 
		
	@api.multi
	def update_capicity(self):
		for rec in self:
			if rec.stock_location.n_qty > rec.new_storage_capicity:
				raise UserError(_('Current cell Contain Store Qty is more Your New Storage Capicity')) 
			rec.stock_location.n_max_qty = rec.new_storage_capicity	
			rec.stock_location.message_post("<ul><li>Storage Capicity Increase :"+str(rec.new_storage_capicity))
		return 
		
