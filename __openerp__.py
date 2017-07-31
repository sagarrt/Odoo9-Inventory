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
    'name': 'API Inventory Location Management', 
    'version': '1.0',
    'category': 'inventory',
    'sequence': 1015,
    'summary': 'Stock Location management',
    'description': ''' Manage Inventory location product qty .
                      <li> add product in Row, Shelf and case</li>
                      <li> Do proper Setting Before using this module</li>
                      <li> Make At least 2 Step route for manufcturing,Bye,and Received Prodcuts</li>
                      <li> This all are should be internal transfer routes</li>''',
    #'author': '',
   # 'website': 'http://abc.com',
    'depends': ['stock','product'],
    'data': [
                'security/ir.model.access.csv',
                'data/series_data.xml',
                "data/stock_data.xml",
                'views/warehouse.xml',
                'views/product_location.xml',
                'views/stock_location.xml',
                'views/stock_picking_view.xml',
                'wizard/location_wizard.xml'],
    'demo': [],
    'test': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

