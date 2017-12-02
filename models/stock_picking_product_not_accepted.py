# -*- coding: utf-8 -*-
# Copyright 2017 Humanytek - Manuel Marquez <manuel@humanytek.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import fields, models
import openerp.addons.decimal_precision as dp


class StockPickingProductNotAccepted(models.Model):
    _name = 'stock.picking.product.not.accepted'
    _rec_name = 'product_id'

    product_id = fields.Many2one(
        'product.product', string="Product", required=True)
    product_qty = fields.Float(
        "Quantity",
        digits_compute=dp.get_precision('Product Unit of Measure'),
        required=True, default=1)
    picking_id = fields.Many2one(
        'stock.picking', string='Picking', required=True)    
