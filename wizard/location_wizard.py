# -*- coding: utf-8 -*-
# copyright reserved

from openerp import models, fields, api,_
from openerp.exceptions import UserError
import math
from datetime import datetime
from datetime import datetime, date, time, timedelta

class StockStoreLocationWizard(models.TransientModel):
    """This wizard is used to preset the free store location for a given
    lots and batches.  """
    
    _name = 'stock.store.location.wizard'

    picking = fields.Many2one('stock.picking', string='Picking')
    product_id = fields.Many2one('product.product', string='Product')
    back_order_id = fields.Many2one('stock.backorder.confirmation', string='Picking')
    immediate_tra = fields.Many2one('stock.immediate.transfer', string='Picking')
    locations = fields.One2many('stock.store.location.wizard.line','wizard_id','Store Locations')
    backorder = fields.Boolean('',default=False)
    #no_of_batch=fields.Float('No of Batches', compute='total_batches')
    #per_batch_qty=fields.Float('Each Batch Qty')
    #hide_button=fields.Boolean('Hide create Batch Button ')
     
    #@api.multi
    #@api.depends('per_batch_qty')
    #def total_batches(self):
        #for record in self:
            #if record.per_batch_qty:
               #qty=sum(line.product_qty if line.product_qty else line.qty_done for line in record.picking.#pack_operation_product_ids)
               #record.no_of_batch=math.ceil(qty/record.per_batch_qty)
                  
    #@api.multi
    #def issue_incomingbatch(self):
    #    for record in self:
    #        if not record.per_batch_qty:
    #           raise UserError(_("Please Fill the Required Per Batch Qty. for Batch Numbers Issue....."))
    #        else:
    #           pr_no=record.picking.name
    #           b_list=[]
    #           body='<b>New Batch Numbers Issue For Incoming:</b>'
    #           body +='<ul><li> Incoming No. : '+str(record.picking.name) +'</li></ul>'
    #           body +='<ul><li> Issued By   : '+str(self.env.user.name) +'</li></ul>' 
    #           body +='<ul><li> Issued Time : '+str(datetime.now() + timedelta(hours=4))+'</li></ul>' 
    #           body +='<ul><li> Batch Numbers: '
    #           for line in record.picking.pack_operation_product_ids:
    #               lot=self.env['stock.production.lot'].create({'product_id':line.product_id.id,
     #                                                   'picking_id':record.picking.id})
    #               req=batch_qty=0.0
    #               req=sum(line.product_qty if line.product_qty else line.qty_done for line in record.picking.pack_operation_product_ids)
    #               for x in range(0, int(record.no_of_batch)): 
    #                   qty=0.0
    #                   if req >  record.per_batch_qty:
    #                      qty= record.per_batch_qty
    #                   else:
    #                      qty=req
    #                   code = self.env['ir.sequence'].next_by_code('mrp.order.batch.number') or 'New'
    #                   final_code= str(pr_no)+'-'+str(code)
    #                   batch=self.env['mrp.order.batch.number'].create({'name':final_code,
    #                                   'picking_id':record.picking.id,'lot_id':lot.id,
    #                                 	'uom_id':line.product_uom_id.id,
    #                                    'product_qty':qty,'product_id':line.product_id.id})
    #                   req -=record.per_batch_qty
    #                   body +=str(batch.name)+','
    #               record.hide_button=True
    #               body +='</li></ul>' 
     #              record.picking.message_post(body=body) 
    #               return {
	#		'type': "ir.actions.do_nothing",
		    #}

    @api.multi
    def process(self):
    	self.ensure_one()
    	for line in self.locations:
    	   product_id=False
    	   Sale_line_id =False
    	   mo_number=self.env['mrp.production'].search([('name','=',self.picking.origin)])
    	   for operation in self.picking.pack_operation_product_ids:
    	   	product_id= operation.product_id if operation.product_id else False
    	   	Sale_line_id= operation.n_sale_order_line if operation.n_sale_order_line else False
    	   if line.select_store and line.batch_ids:
    	   	batches_id=[]
    	   	body=''
    	   	if line.batch_ids==[]:
    	   		raise exceptions.Warning(_("Please add Batches in store location {}/{}/{} ",format(line.locations.row,line.locations.column,line.locations.depth)))		
    	   	for rec in line.batch_ids:
    	   		if rec.id in batches_id:
				raise exceptions.Warning(_("Your batch {} appered in Multiple store locations",format(rec.name)))		
   			else:
   				batches_id.append(rec.id)
    	   	qty=total_qty=0
    	   	unit=False
    	   	for res in line.batch_ids:
			qty = res.approve_qty if res.approve_qty else res.product_qty
                        total_qty +=qty
			unit=res.uom_id
    			store_data=self.env['picking.lot.store.location'].create({'picking_id':self.picking.id,
    							'store_id':line.locations.id,'quantity':qty,
    							'lot_number':res.lot_id.id,'batch_number':res.id,
    							})
		body+="<ul>New Quantity Added in Store</ul>"
		line.locations.product_id=product_id.id
		body+="<li>Product add : "+str(product_id.name)+" </li>"
		line.locations.pkg_capicity=self.picking.pallet_size
		line.locations.pkg_capicity_unit =self.picking.pallet_qty_unit.id
		body+="<li>Package Capicity : "+str(self.picking.pallet_size)+" "+str(self.picking.pallet_qty_unit.name)+" </li>"
		line.locations.packages = self.picking.pallet_size
		line.locations.pkg_unit = self.picking.pallet_qty_unit.id
		body+="<li>No of Packages : "+str(self.picking.pallet_size)+" "+str(self.picking.pallet_qty_unit.name)+" </li>"
		line.locations.total_quantity = total_qty 
		line.locations.qty_unit = unit.id if unit else False
		body+="<li>Quantity Added : "+str(qty)+" "+str(unit.name if unit else '')+" </li>"
		line.locations.Packaging_type = self.picking.packaging.id
		body+="<li>Packaging : "+str(self.picking.packaging.name)+" </li>"
		line.locations.state = 'full'
		line.locations.message_post(body)
		line.locations.mo_number=mo_number.id if mo_number else False
		if Sale_line_id:
			line.sale_reserve_ids=[(0,0,{'store_id':line.locations.id,'sale_line_id':Sale_line_id.id,
					    'sale_id':Sale_line_id.order_id.id,'product_qty':qty,'uom_id':unit.id if unit else False})]
    	if self.back_order_id:
    		self.back_order_id._process(cancel_backorder=self.backorder)
    		self.picking.do_transfer()
	elif self.immediate_tra:
		self.picking.do_transfer()
	elif self.picking:
		self.picking.do_transfer()
		
    @api.multi
    def store_validate(self):
	for rec in self:
		flag=False
		for line in rec.locations:
			batches=[ res.id for res in line.batch_ids]
			for loc in line.locations_ids:
				for batch in loc.batches_ids:
					if batch.id in batches:
						batch.unlink()
				qty=0
				for op in rec.picking.pack_operation_product_ids:
					if loc.product_id.id == op.product_id.id:
						qty=op.qty_done 
						break
						
				loc.total_quantity -= qty
				if loc.total_quantity <=0:
					loc.state = 'empty'
					loc.product_id = False
					loc.qty_unit = False
					loc.pkg_capicity = False
					loc.pkg_capicity_unit = False
					loc.packages = False
					loc.pkg_unit = False
					loc.Packaging_type = False
					break
					flag=True
			if flag:
				break
		if flag:
			break
    	return self.picking.action_first_validation_data()
    	
class StockStoreLocationWizardLine(models.TransientModel):
    """This is a temporary table to get and store the Lot in store location 
    """
    _name = 'stock.store.location.wizard.line'

    select_store = fields.Boolean('Store Select')
    wizard_id = fields.Many2one('stock.store.location.wizard', string='Wizard')
    locations = fields.Many2one('n.warehouse.placed.product','Store Location')
    max_qty = fields.Float('Storage Capacity')
    qty_unit = fields.Many2one('product.uom','Unit')
    lot_ids = fields.Many2many('stock.production.lot','lot_store_inventory_wizard','lot_id','wizard_id','Lot No')
    #batch_ids = fields.Many2many('mrp.order.batch.number','batch_store_inventory_wizard','batch_id','wizard_id','Batch No.')
    locations_ids = fields.Many2many('n.warehouse.placed.product','warehouse_store_inventory_wizard_rel',
    				     'wiz_id','loc_id','Store Names')
    product_id = fields.Many2one('product.product', string='Product')
    #n_free_qty = fields.Float('Free Storage')
    #quantity = fields.Float('Store Quantity')

class stock_immediate_transfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    @api.multi
    def process(self):
        context = self._context.copy() 
        self.ensure_one()
        # If still in draft => confirm and assign
        if self.pick_id.state == 'draft':
            self.pick_id.action_confirm()
            if self.pick_id.state != 'assigned':
                self.pick_id.action_assign()
                if self.pick_id.state != 'assigned':
                    raise UserError(_("Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
        for pack in self.pick_id.pack_operation_ids:
            if pack.product_qty > 0:
                pack.write({'qty_done': pack.product_qty})
            else:
                pack.unlink()
                
        if self.pick_id.picking_type_id.code=='internal' and self.pick_id.picking_type_id.default_location_src_id.pre_ck:        
		data=[]
		free_ids=self.env['n.warehouse.placed.product'].search([('product_id','=',False)])
		pallet_id=self.env['product.uom'].search([('name','=ilike','Pallet')],limit=1)
		wizard_id=self.env['stock.store.location.wizard'].search([('picking','=',self.pick_id.id)])
		wizard_id.unlink()
		purchase=self.env['purchase.order'].search([('name','=',self.pick_id.origin)],limit=1)
		data=self.env['stock.backorder.confirmation']._get_bacthes(free_ids,self.pick_id)
                context.update({'incoming':True if purchase else False, 
                                'location':True if data else False})
		vals={'immediate_tra':self.id,'picking':self.pick_id.id,'locations':data}
		res_id=self.env['stock.store.location.wizard'].create(vals)
		form_id = self.env.ref('api_inventory.store_locations_form_view_wizard')
		return {
			'name' :'Select Store Location',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'stock.store.location.wizard',
			'views': [(form_id.id, 'form')],
			'view_id': form_id.id,
			'target': 'new',
                        'context':context,
			'res_id':res_id.id,
		    }
        self.pick_id.do_transfer()

    
class stock_backorder_confirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'
    
    @api.multi
    def process(self):
        self.ensure_one()
        if self.pick_id.picking_type_id.code=='internal' and self.pick_id.picking_type_id.default_location_src_id.pre_ck:
		free_ids=self.env['n.warehouse.placed.product'].search([('product_id','=',False)])
		wizard_id=self.env['stock.store.location.wizard'].search([('picking','=',self.pick_id.id)])
		wizard_id.unlink()
		
		data=self._get_bacthes(free_ids,self.pick_id)
		vals={'back_order_id':self.id,'picking':self.pick_id.id,'locations':data}
		res_id=self.env['stock.store.location.wizard'].create(vals)
		form_id = self.env.ref('api_inventory.store_locations_form_view_wizard')
		return {
			'name' :'Select Store Location',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'stock.store.location.wizard',
			'views': [(form_id.id, 'form')],
			'view_id': form_id.id,
			'target': 'new',
			'res_id':res_id.id,
			#'flags': {'form': {'action_buttons': False, 'options': {'mode': 'edit'}}}
		    }
        self._process()

    @api.multi
    def process_cancel_backorder(self):
        self.ensure_one()
        if self.pick_id.picking_type_id.code=='internal' and self.pick_id.picking_type_id.default_location_src_id.pre_ck:
		data=[]
		free_ids=self.env['n.warehouse.placed.product'].search([('product_id','=',False)])
		wizard_id=self.env['stock.store.location.wizard'].search([('picking','=',self.pick_id.id)])
		wizard_id.unlink()
		
		data=self._get_bacthes(free_ids,self.pick_id)
		vals={'back_order_id':self.id,'picking':self.pick_id.id,'locations':data,'backorder':True,}
		res_id=self.env['stock.store.location.wizard'].create(vals)
		form_id = self.env.ref('api_inventory.store_locations_form_view_wizard')
		return {
			'name' :'Select Store Location',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'stock.store.location.wizard',
			'views': [(form_id.id, 'form')],
			'view_id': form_id.id,
			'target': 'new',
			'res_id':res_id.id,
			#'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}}
		    }
        self._process(cancel_backorder=True)

    @api.model
    def _get_bacthes(self,free_ids,pick_id):
    	''' This method is used to get batches for store location in wizard on validation in move to store picking '''
    	data=[]
    	completed_ids=[]
    	mrp_id=self.env['mrp.production'].search([('name','=',pick_id.origin)],limit=1)
    	pallet_id=self.env['product.uom'].search([('name','=ilike','Pallet')],limit=1)
    	c=1
	for line in free_ids:
		batches=[]
		lots=[]
		qty=0
		#if mrp_id:
		#	bacthes_ids=self.env['mrp.order.batch.number'].search([('production_id','=',mrp_id.id),('lot_id','!=',False),('approve_qty','>',0),('product_qty','>',0),('id','not in',tuple(completed_ids))])
		#	for batch in bacthes_ids:
		#		batches.append(batch.id)
		#		completed_ids.append(batch.id)
		#		lots.append(batch.lot_id.id)
		#		qty+=batch.approve_qty
		#		if qty >= pick_id.packaging.qty:
		#			break
					
		batches=list(set(batches))
		lots=list(set(lots))
		if c<=pick_id.total_no_pallets:
			data.append((0,0,{'locations':line.id,'max_qty':line.max_qty,'qty_unit':pallet_id.id,
			'select_store':True,'lot_ids':[(6,0,lots)],'batch_ids':[(6,0,batches)]}))
		c +=1
	return data
    	
