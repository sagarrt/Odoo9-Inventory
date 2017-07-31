# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import api, fields, models, exceptions, _
from openerp.tools.translate import _
from openerp.exceptions import UserError, ValidationError
from openerp import fields
import openerp.addons.decimal_precision as dp
from datetime import datetime
import re
from dateutil.relativedelta import relativedelta

class stockWarehouse(models.Model):
    _inherit = "stock.warehouse"
 
    move_type_id = fields.Many2one('stock.picking.type', 'Quality Check')
    wh_move_stock_loc_id = fields.Many2one('stock.location', 'Store Location',help="this location is used for Move to Stock storage location in warehouse")
    
    @api.model
    def create(self,vals):
    	location_obj=self.env['stock.location']
    	warehouse=super(stockWarehouse,self).create(vals)
    	location_vals={'name': 'Pre Stock Location',
                	'usage': 'internal',
                	'location_id': warehouse.lot_stock_id.location_id.id,
                	'active': True,
                	'company_id' : warehouse.company_id.id,
                	'pre_ck':True}
    	location_id = location_obj.create(location_vals)
    	warehouse.wh_move_stock_loc_id=location_id.id
    	warehouse.lot_stock_id.actual_location = True
    	return warehouse
    
    @api.v7
    def create_sequences_and_picking_types(self,cr,uid,warehouse,context):
    	super(stockWarehouse,self).create_sequences_and_picking_types(cr,uid,warehouse,context)
    	seq_obj = self.pool.get('ir.sequence')
        picking_type_obj = self.pool.get('stock.picking.type')
        #create new sequences
        int_seq_id = seq_obj.search(cr, uid, [('name','=',str(warehouse.name + _(' Sequence internal'))),('prefix','=',str(warehouse.code + '/INT/'))], context=context)
       
        #order the picking types with a sequence allowing to have the following suit for each warehouse: reception, internal, pick, pack, ship. 
        max_sequence = self.pool.get('stock.picking.type').search_read(cr, uid, [], ['sequence'], order='sequence desc')
        max_sequence = max_sequence and max_sequence[0]['sequence'] or 0
    	move_type = picking_type_obj.create(cr,uid,vals={
            'name': _('Move In Locations'),
            'warehouse_id': warehouse.id,
            'code': 'internal',
            'use_create_lots': False,
            'use_existing_lots': True,
            'sequence_id': int_seq_id[0],
            'default_location_src_id': warehouse.qc_type_id.id,
            'default_location_dest_id': warehouse.lot_stock_id.id,
            'sequence': max_sequence + 2,
            'color': warehouse.int_type_id.color},context=context)
    	return super(stockWarehouse, self).write(cr, uid, warehouse.id, vals={'move_type_id':move_type}, context=context)
		
	
