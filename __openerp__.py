 # -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.
#
##############################################################################
{
    'name': 'Inventory Location Management', 
    'version': '1.0',
    'category': 'inventory',
    'sequence': 1015,
    'summary': 'Stock Location management',
    'description': ''' Manage Inventory location product qty \n .
                      add product in Row(X), Shelf(Y) and case(Z) \n
                      Do proper Setting Before using this module \n
                      Make At least 2 Step in Warehouse reception steps,it will add push rule in manufacturing and warehouse receipt routes \n
                      This all are should be internal transfer routes \n
                      Add Primary and Secondary Packaging in Product for add product qty in store\n
                      Primary and secondary packaging are related to each other \n
                      Ex-: Primary (30 Pcs/Carton) then secondary shoud be (20 carton/Pallet)
                      like second unit of primary should be in secondary first unit''',
    #'author': '',
   # 'website': 'http://abc.com',
    'depends': ['base','web','stock','product','purchase','mrp'],
    'data': [
                #'security/ir.model.access.csv',
                'data/series_data.xml',
                "data/stock_data.xml",
                'views/warehouse.xml',
                'views/product_location.xml',
                'views/stock_location.xml',
                'views/stock_picking_view.xml',
                'wizard/location_wizard.xml',
                'wizard/store_operation_view.xml',
                ],
    'demo': [],
    'test': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

