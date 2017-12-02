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
    quality_review_ids = fields.One2many(
        'product.quality.review.product.not.accepted.rel',
        'product_not_accepted_id',
        string='Quality Review in Products'
    )


class ProductQualityReviewRel(models.Model):
    _name = 'product.quality.review.product.not.accepted.rel'
    _rec_name = 'quality_review_id'

    product_not_accepted_id = fields.Many2one(
        'stock.picking.product.not.accepted',
        string="Product not accepted",
        required=True)
    quality_review_id = fields.Many2one(
        'product.quality.review',
        string='Quality review item',
        required=True)
    meet = fields.Boolean('Does it meet?')
