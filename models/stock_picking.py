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
import math

class stockPickig(models.Model):
	_inherit = "stock.picking"

	@api.multi
	def _get_packaging_count(self):
		for rec in self:
			quantity = 0
			pack_qty=rec.packaging.qty if rec.packaging else 1
			if rec.pack_operation_product_ids:
				for line in rec.pack_operation_product_ids:
					quantity += line.qty_done if line.qty_done else line.product_qty	
			else:
				for line in rec.move_lines_related:
					quantity += line.product_uom_qty
			rec.packaging_count=int(quantity)/int(pack_qty)

	@api.multi
	def _get_pallet_count(self):
		for rec in self:
			quantity = rec.packaging_count if rec.packaging_count else 1
			pack_qty=rec.pallet_size if rec.pallet_size else 1
			rec.total_no_pallets=math.ceil(float(quantity)/pack_qty)
	
	@api.onchange('packaging','packaging_unit','pallet_qty_unit')
	def get_uom_id(self):
		if self.packaging:
			self.packaging_unit=self.packaging.n_uom_id.id
			self.pallet_qty_unit=self.packaging.n_uom_id.id
			
	packaging = fields.Many2one('product.packaging' ,string="Packaging",copy=True)
	packaging_count = fields.Integer(string="Packaging",compute='_get_packaging_count')
	packaging_unit = fields.Many2one('product.uom',string="No of Packages")
	
	pallet_size = fields.Float("Qty/Pallet")
	pallet_qty_unit = fields.Many2one('product.uom',string="No of Packages")
	pallet_type = fields.Many2one('product.product',"Pallet Type")
     	total_no_pallets=fields.Float('Total Pallets',compute='_get_pallet_count')
     	
