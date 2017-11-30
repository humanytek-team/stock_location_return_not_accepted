# -*- coding: utf-8 -*-
# Copyright 2017 Humanytek - Manuel Marquez <manuel@humanytek.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import fields, models


class ProductQualityReview(models.Model):
    _name = 'product.quality.review'

    name = fields.Char('Name')
    active = fields.Boolean('Active', default=True)
