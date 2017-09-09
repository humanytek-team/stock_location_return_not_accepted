# -*- coding: utf-8 -*-
###############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2017 Humanytek (<www.humanytek.com>).
#    Manuel Márquez <manuel@humanytek.com>
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

{
    'name': "Enable locations for stock of products returned but not accepted",
    'description': """
    Adds boolean field "Is a location of returns not accepted ?" to allow
    indicate that the location is for stock of products returned but not
    accepted for any reason.
    """,
    'author': "Humanytek",
    'website': "http://www.humanytek.com",
    'category': 'Stock',
    'version': '0.1.0',
    'depends': ['stock', ],
    'data': [
        'wizard/stock_return_not_accepted_picking_view.xml',
        'views/stock_location_view.xml',
        'views/stock_picking_view.xml',
    ],
    'demo': [
    ],
}
