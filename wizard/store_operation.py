# -*- coding: utf-8 -*-
# copyright reserved

from openerp import models, fields, api,_
from openerp.exceptions import UserError
import math
from datetime import datetime
from datetime import datetime, date, time, timedelta

class locationStockOperation(models.TransientModel):
	_name = "location.stock.operation"
	
	stock_location = fields.Many2one('n.warehouse.placed.product','Stock Location')
	new_stock_location = fields.Many2one('n.warehouse.placed.product','New Stock Location')
	product_id = fields.Many2one('product.product', string="Product")
	unit = fields.Many2one('product.uom','Unit',related="product_id.uom_id",readonly=True)
	qty = fields.Float('Avaiable Quantity',compute='_get_product_qty',help='Available Product Quantity Which is not added in any Store Locations')
	storage = fields.Float('Available Capicity',compute='_get_storage_qty',help='Available storage capicity calculate using primary and secondary packaging qty')
	storage_unit = fields.Many2one('product.uom','Unit',related="product_id.uom_id",readonly=True)
	add_qty = fields.Float('Quantity')
	add_unit = fields.Many2one('product.uom','Unit',related="product_id.uom_id",readonly=True)
	
	primary_packaging = fields.Many2one('product.packaging','Packaging')
	secondary_packaging = fields.Many2one('product.packaging','Secondary Packaging')
	packaging_qty = fields.Char('Packaging Qty',compute='_get_packaging_qty')
	release_unit = fields.Many2one('product.uom','Release Unit')
	
	new_storage_capicity = fields.Float('New Storage Capacity')
	new_capicity_unit = fields.Many2one('product.uom','Unit',readonly=True)
	previous_storage_capicity = fields.Float('Previous Storage Capacity')
	pre_capicity_unit = fields.Many2one('product.uom','Unit',readonly=True)
	used_storage = fields.Float('Used Storage')
	used_unit = fields.Many2one('product.uom','Unit',readonly=True)
	
	@api.multi		# For transfer operation
	@api.onchange('new_stock_location')
	def onchange_free_qty(self):
		for rec in self:
			qty=  rec.new_stock_location.Packaging_type.qty if rec.new_stock_location else 0
			free = rec.new_stock_location.pkg_capicity-rec.new_stock_location.packages
			rec.storage= free* qty
	
	@api.multi
	@api.onchange('product_id') # make packaging field empty and add available quantity 
	def onchange_product_qty(self):
	   if self._context.get('add_stock') or self._context.get('update_stock'):
		for rec in self:
		    if rec.product_id:
			qty=rec.product_id.qty_available
			# find total sotre quantity and substract from avilabel product quantity to get quantity available for store
			for line in self.env['n.warehouse.placed.product'].search([('product_id','=',rec.product_id.id),('state','!=','empty')]):
				qty -= line.total_quantity
			for line in self.env['store.multi.product.data'].search([('product_id','=',rec.product_id.id)]):
				qty -= line.total_quantity		
				
			rec.qty=qty
			if self._context.get('add_stock'): # set values to NUll on product onchange
				rec.primary_packaging=False
				rec.secondary_packaging=False
				rec.storage=0.0
			if self._context.get('update_stock'): # update available storage in Update form in packaging unit
				rec.storage=(rec.stock_location.pkg_capicity-rec.stock_location.packages)*rec.stock_location.Packaging_type.qty
			
	#write onchange beacuse it will change the value of storage fields
	@api.multi
	@api.depends('product_id')
	def _get_product_qty(self):
	   if self._context.get('add_stock') or self._context.get('update_stock'):
		for rec in self:
		    if rec.product_id:
			qty=rec.product_id.qty_available
			# find total sotre quantity and substract from avilabel product quantity to get quantity available for store
			#for single product store
			for line in self.env['n.warehouse.placed.product'].search([('product_id','=',rec.product_id.id),('state','!=','empty')]):
				qty -= line.total_quantity		# Substraction
				
			#for Multi product store
			for line in self.env['store.multi.product.data'].search([('product_id','=',rec.product_id.id)]):
				qty -= line.total_quantity
			rec.qty=qty
	   if self._context.get('release_stock'):  # get available quantity for release operation
		for rec in self:
		    if rec.product_id: 
		    	qty=0.0
			for line in self.env['n.warehouse.placed.product'].search([('product_id','=',rec.product_id.id),('state','!=','empty')]):
				qty += line.total_quantity    # addition
			rec.qty=qty
			
	   if self._context.get('transfer_stock'):  # get available quantity for Transfer operation
		for rec in self:
			rec.qty=rec.stock_location.total_quantity
			
	@api.multi			#TO make secondary packaging field empty for proper storage quantity calculation
	@api.onchange('primary_packaging')
	def onchange_primary_packaging(self):
		for rec in self:
			rec.secondary_packaging=False
			
	@api.multi		#TO calculate proper storage quantity
	@api.onchange('secondary_packaging')
	def _get_storage_qty(self):
		for rec in self:
			if self._context.get('add_stock'):
				if rec.primary_packaging and rec.secondary_packaging:
					storage=rec.primary_packaging.qty*rec.secondary_packaging.qty
					rec.storage=storage*rec.stock_location.max_qty
			if self._context.get('update_stock'): # update available storage in Update form in packaging unit
				rec.storage=(rec.stock_location.pkg_capicity-rec.stock_location.packages)*rec.stock_location.Packaging_type.qty
	
	@api.multi  # Get packaging Quantity from entered quantity
	@api.onchange('add_qty')
	def _get_packaging_qty(self):
		for rec in self:
		    if rec.add_qty >0.0 and rec.primary_packaging.qty >0.0:
			packaging_qty = str(rec.add_qty/rec.primary_packaging.qty)+" "+str(rec.secondary_packaging.packg_uom.name)
			rec.packaging_qty=packaging_qty
    		    elif self._context.get('update_stock'):
    		    	rec.packaging_qty = str(rec.add_qty/rec.stock_location.Packaging_type.qty)+" "+str(rec.stock_location.Packaging_type.uom_id.name)
	    	    elif self._context.get('release_stock'):
	    	    	if rec.release_unit and rec.release_unit.id != rec.unit.id:
	    	    		unit_id=self.env['product.packaging'].search([('product_tmpl_id','=',rec.product_id.product_tmpl_id.id),('packg_uom','=',rec.unit.id),('uom_id','=',rec.release_unit.id)])
	    	    		qty= unit_id.qty if unit_id else 1
    		    		rec.packaging_qty = str(rec.add_qty/qty)+" "+str(rec.release_unit.name)
	    		else:
	    			rec.packaging_qty = False

	@api.multi	 # to check release unit and product unit for packaging quantity counting invisibility
	@api.onchange('release_unit')
	def onhcange_release_unit(self):
		for rec in self:
			if rec.release_unit:
				rec.packaging_qty = False
	    		
	@api.multi
	def save(self):
		n_type=''
		body=""
		stock_product_id=False
		if self.add_qty < 0.0:
			raise UserError(_('Please Enter Proper Quantity'))
		if self._context.get('add_stock'):
			n_type='in'
			body+="<ul>New Quantity Added in Store</ul>"
			if self.add_qty >self.qty:
				 raise UserError(_('Entered Quantity is shoud be less than Available Quantity'))
			if self.add_qty >self.storage:
				 raise UserError(_('Entered Quantity is shoud be less than Available Capicty'))
			
			if  self.stock_location.product_type == 'single':
				self.stock_location.product_id=self.product_id
				body+="<li>Product add : "+str(self.product_id.name)+" </li>"
				if self.primary_packaging and self.secondary_packaging:
					capacity=self.secondary_packaging.qty*self.stock_location.max_qty
					self.stock_location.pkg_capicity=capacity
					self.stock_location.pkg_capicity_unit =self.secondary_packaging.packg_uom.id
					body+="<li>Packag Capicity : "+str(capacity)+" "+str(self.secondary_packaging.packg_uom.name)+" </li>"
				self.stock_location.packages = self.add_qty/self.primary_packaging.qty
				self.stock_location.pkg_unit = self.secondary_packaging.packg_uom.id
				body+="<li>No of Packages : "+str(self.add_qty/self.primary_packaging.qty)+" "+str(self.secondary_packaging.packg_uom.name)+" </li>"
				self.stock_location.total_quantity = self.add_qty
				self.stock_location.total_qty_unit = self.add_unit.id
				body+="<li>Quantity Added : "+str(self.add_qty)+" "+str(self.add_unit.name)+" </li>"
				self.stock_location.Packaging_type = self.primary_packaging.id
				body+="<li>Packaging : "+str(self.primary_packaging.name)+" </li>"
				
			elif self.stock_location.product_type == 'multi':
				add_vals={'product_id':self.product_id.id}
				body+="<li>Product add : "+str(self.product_id.name)+" </li>"
				if self.primary_packaging and self.secondary_packaging:
					capacity=self.secondary_packaging.qty*self.stock_location.max_qty
					add_vals.update({'pkg_capicity':capacity})
					add_vals.update({'pkg_capicity_unit':self.secondary_packaging.packg_uom.id})
					body+="<li>Packag Capicity : "+str(capacity)+" "+str(self.secondary_packaging.packg_uom.name)+" </li>"
				add_vals.update({'packages':self.add_qty/self.primary_packaging.qty})
				add_vals.update({'pkg_unit':self.secondary_packaging.packg_uom.id})
				body+="<li>No of Packages : "+str(self.add_qty/self.primary_packaging.qty)+" "+str(self.secondary_packaging.packg_uom.name)+" </li>"
				add_vals.update({'total_quantity':self.add_qty})
				add_vals.update({'total_qty_unit':self.add_unit.id})
				body+="<li>Quantity Added : "+str(self.add_qty)+" "+str(self.add_unit.name)+" </li>"
				add_vals.update({'Packaging_type':self.primary_packaging.id})
				body+="<li>Packaging : "+str(self.primary_packaging.name)+" </li>"
				
				self.stock_location.multi_product_ids=[(0,0,add_vals)]
			self.stock_location.state = 'full' if self.stock_location.pkg_capicity==self.stock_location.packages else 'partial'
			stock_product_id=self.product_id.id
		if self._context.get('update_stock'):
			n_type='in'
			body+="<ul>Quantity Updated in Store"
			if self.add_qty >self.storage:
				 raise UserError(_('Entered Quantity is shoud be less than Available Capicity')) 
			self.stock_location.total_quantity +=self.add_qty
			body+="<li>Quantity : "+str(self.add_qty)+" </li>"
			self.stock_location.packages += (self.add_qty/self.stock_location.Packaging_type.qty)
			body+="<li>Packages : "+str(self.add_qty/self.stock_location.Packaging_type.qty)+" </li></ul>"
			self.stock_location.state = 'full' if self.add_qty==self.storage else 'partial'
			stock_product_id=self.stock_location.product_id.id
		if self._context.get('release_stock'):
			n_type='out'
			stock_product_id=self.stock_location.product_id.id	
			if self.add_qty == self.qty:
				body+="<li> <font color='red'>Make Store Empty</font></li>"
				self.stock_location.state = 'empty'
				self.stock_location.product_id = False
				self.stock_location.qty_unit = False
				self.stock_location.pkg_capicity = False
				self.stock_location.pkg_capicity_unit = False
				self.stock_location.packages = False
				self.stock_location.pkg_unit = False
				self.stock_location.Packaging_type = False
			else:
				body+="<ul>Quantity Release From Store"
				body+="<li>Quantity : "+str(self.add_qty)+" </li>"
				self.stock_location.state = 'partial'
				#if self.release_unit.id != self.unit.id:
    	    			unit_id=self.env['product.packaging'].search([('product_tmpl_id','=',self.product_id.product_tmpl_id.id),('unit_id','=',self.unit.id),('pkgtype','=','primary')],limit=1)
    	    			qty= unit_id.qty if unit_id else 1
				self.stock_location.packages -= (self.add_qty/qty)
				body+="<li>Packages : "+str(self.add_qty/qty)+" </li></ul>"
			self.stock_location.total_quantity -= self.add_qty	
		if self._context.get('transfer_stock'):
			n_type='out'
			stock_product_id=self.stock_location.product_id.id	
			if self.add_qty >self.qty:
				 raise UserError(_('Entered Quantity is shoud be less than Available Quantity')) 
			self.stock_location.total_quantity -= self.add_qty
			
			body1="<ul>New Quantity Added in Store</ul>"
			self.new_stock_location.product_id = self.stock_location.product_id
			body1+="<li>Product add : "+str(self.stock_location.product_id.name)+" </li>"
			self.new_stock_location.total_quantity += self.add_qty
			self.new_stock_location.qty_unit = self.stock_location.qty_unit
			body1+="<li>Quantity Added : "+str(self.add_qty)+" "+str(self.stock_location.qty_unit.name)+" </li>"
			self.new_stock_location.pkg_capicity += self.stock_location.pkg_capicity
			self.new_stock_location.pkg_capicity_unit = self.stock_location.pkg_capicity_unit
			body1+="<li>Packag Capicity : "+str(self.stock_location.pkg_capicity)+" "+str(self.stock_location.pkg_capicity_unit.name)+" </li>"
			self.new_stock_location.pkg_unit = self.stock_location.pkg_unit
			self.new_stock_location.Packaging_type = self.stock_location.Packaging_type
			body1+="<li>Packaging : "+str(self.stock_location.Packaging_type)+" </li>"
			
			if self.add_qty == self.qty:
				body+="<li>Store Quantity is Transfered</li>"
				self.stock_location.state = 'empty'
				self.stock_location.product_id = False
				self.stock_location.qty_unit = False
				self.stock_location.pkg_capicity = False
				self.stock_location.pkg_capicity_unit = False
				self.stock_location.packages = False
				self.stock_location.pkg_unit = False
				self.stock_location.Packaging_type = False
				
				self.new_stock_location.state = 'full'
				self.new_stock_location.packages = self.stock_location.packages
			else:
				self.stock_location.state = 'partial'
				self.new_stock_location.state = 'partial'
				packages=self.add_qty/self.stock_location.Packaging_type.qty
				self.stock_location.packages -= packages
				self.new_stock_location.packages += packages
				
			self.env['location.history'].create({
					'stock_location':self.new_stock_location.id,
					'product_id':stock_product_id,
					'qty':self.add_qty,
					'n_type':'in',
				})
		if body:
			self.stock_location.message_post(body)		
		self.env['location.history'].create({'stock_location':self.stock_location.id,
							'product_id':stock_product_id,
							'qty':self.add_qty,
							'n_type':n_type,
				})
		return 
		
	@api.multi
	# to update the storage Capicity
	def update_capicity(self):
		for rec in self:
			if rec.new_storage_capicity <=0:
				raise UserError(_('Please Enter Proper Value'))
			if rec.new_storage_capicity < rec.used_storage:
				raise UserError(_('Please Enter Highter Value Than Previous Storage Capicity')) 
			max_qty=rec.stock_location.max_qty if rec.stock_location.max_qty else 1
			pkg_capicity = rec.stock_location.pkg_capicity if rec.stock_location.pkg_capicity else 1
			rec.stock_location.pkg_capicity = (pkg_capicity/max_qty) * rec.new_storage_capicity
			rec.stock_location.max_qty = rec.new_storage_capicity
			rec.stock_location.message_post("<ul><li>Storage Capicity Increase :"+str(rec.new_storage_capicity))
		return 
		
