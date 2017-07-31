# -*- coding: utf-8 -*-
# copyright reserved

from openerp import models, fields, api

class StockStoreLocationWizard(models.TransientModel):
    """This wizard is used to preset the test for a given
    inspection. This will fill in the 'test' field, but will
    also fill in all lines of the inspection with the corresponding lines of
    the template.
    """
    _name = 'stock.store.location.wizard'

    picking = fields.Many2one('stock.picking', string='Picking')
    back_order_id = fields.Many2one('stock.backorder.confirmation', string='Picking')
    immediate_tra = fields.Many2one('stock.picking', string='Picking')
    locations = fields.One2many('stock.store.location.wizard.line','wizard_id','Store Locations')
    backorder = fields.Boolean('',default=False)
    
    @api.multi
    def process(self):
    	self.ensure_one()
    	print "-------------------------",self.back_order_id,'//////',self.immediate_tra
    	if self.back_order_id:
    		self.back_order_id._process(cancel_backorder=self.backorder)
	elif self.immediate_tra:
		print "--------------------"
		self.picking.do_transfer()
    	
    	
class StockStoreLocationWizardLine(models.TransientModel):
    """This wizard is used to preset the test for a given
    inspection. This will fill in the 'test' field, but will
    also fill in all lines of the inspection with the corresponding lines of
    the template.
    """
    _name = 'stock.store.location.wizard.line'

    select_store = fields.Boolean('Store Select')
    wizard_id = fields.Many2one('stock.store.location.wizard', string='Wizard')
    locations = fields.Many2one('n.warehouse.placed.product','Store Location')
    n_max_qty = fields.Float('Storage Capacity',related='locations.n_max_qty')
    n_free_qty = fields.Float('Free Storage',related='locations.n_free_qty')

class stock_immediate_transfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    @api.multi
    def process(self):
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
		free_ids=self.env['n.warehouse.placed.product'].search([('n_free_qty','>',0)])
		for line in free_ids:
			data.append((0,0,{'locations':line.id}))
		res_id=self.env['stock.store.location.wizard'].create({'immediate_tra':self.id,
									'picking':self.pick_id.id,'locations':data})
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
        self.pick_id.do_transfer()

    
class stock_backorder_confirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'
    
    @api.multi
    def process(self):
        self.ensure_one()
        if self.pick_id.picking_type_id.code=='internal' and self.pick_id.picking_type_id.default_location_src_id.pre_ck:
		data=[]
		free_ids=self.env['n.warehouse.placed.product'].search([('n_free_qty','>',0)])
		for line in free_ids:
			data.append((0,0,{'locations':line.id}))
		res_id=self.env['stock.store.location.wizard'].create({'back_order_id':self.id,
									'picking':self.pick_id.id,'locations':data})
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
        self._process()

    @api.multi
    def process_cancel_backorder(self):
        self.ensure_one()
        if self.pick_id.picking_type_id.code=='internal' and self.pick_id.picking_type_id.default_location_src_id.pre_ck:
		data=[]
		free_ids=self.env['n.warehouse.placed.product'].search([('n_free_qty','>',0)])
		for line in free_ids:
			data.append((0,0,{'locations':line.id}))
		res_id=self.env['stock.store.location.wizard'].create({'back_order_id':self.id,'backorder':True,
									'picking':self.pick_id.id,'locations':data})
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

