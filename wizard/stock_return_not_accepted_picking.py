# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp.osv import osv, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)
class stock_return_not_accepted_picking_line(osv.osv_memory):
    _name = "stock.return.not.accepted.picking.line"
    _rec_name = 'product_id'

    _columns = {
        'product_id': fields.many2one('product.product', string="Product", required=True),
        'quantity': fields.float("Quantity", digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
        'wizard_id': fields.many2one('stock.return.not.accepted.picking', string="Wizard"),
        'move_id': fields.many2one('stock.move', "Move"),
        'product_not_accepted_ids': fields.one2many(
            'wizard.stock.picking.product.not.accepted',
            'wizard_return_not_accepted_line_id',
            'Quality Review in Products')
    }


class stock_return_not_accepted_picking(osv.osv_memory):
    _name = 'stock.return.not.accepted.picking'
    _description = 'Picking of return not accepted'
    _columns = {
        'product_return_not_accepted_moves': fields.one2many('stock.return.not.accepted.picking.line', 'wizard_id', 'Moves'),
        'original_location_id': fields.many2one('stock.location'),
        'parent_location_id': fields.many2one('stock.location'),
        'location_id': fields.many2one('stock.location', 'Location of Returns not accepted',
            domain="[('return_not_accepted_location', '=', True), ('id', 'child_of', parent_location_id)]",
            required=True)
    }

    def default_get(self, cr, uid, fields, context=None):
        """
         To get default values for the object.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param fields: List of fields for which we want default values
         @param context: A standard dictionary
         @return: A dictionary with default values for all field in ``fields``
        """
        result1 = []
        if context is None:
            context = {}
        if context and context.get('active_ids', False):
            if len(context.get('active_ids')) > 1:
                raise UserError(_("You may only apply returns not accepted of one return picking at a time!"))
        res = super(stock_return_not_accepted_picking, self).default_get(cr, uid, fields, context=context)
        record_id = context and context.get('active_id', False) or False
        uom_obj = self.pool.get('product.uom')
        pick_obj = self.pool.get('stock.picking')
        pick = pick_obj.browse(cr, uid, record_id, context=context)
        quant_obj = self.pool.get("stock.quant")

        if pick:
            if pick.state != 'done':
                raise UserError(_("You may only apply returns not accepted of return pickings that are Done!"))

            for move in pick.move_lines:
                if move.scrapped:
                    continue

                #Sum the quants in that location (they should have been moved by the moves that were included in the returned picking)
                qty = 0
                quant_search = quant_obj.search(cr, uid, [('history_ids', 'in', move.id), ('qty', '>', 0.0), ('location_id', '=', move.location_dest_id.id)], context=context)
                for quant in quant_obj.browse(cr, uid, quant_search, context=context):
                    if not quant.reservation_id:
                        qty += quant.qty
                qty = uom_obj._compute_qty(cr, uid, move.product_id.uom_id.id, qty, move.product_uom.id)
                result1.append((0, 0, {'product_id': move.product_id.id, 'quantity': qty, 'move_id': move.id}))

            if len(result1) == 0:
                raise UserError(_("No products to return (only lines in Done state and not fully returned yet can be returned)!"))

            if 'product_return_not_accepted_moves' in fields:

                ProductQualityReview = self.pool.get('product.quality.review')
                quality_review_items = ProductQualityReview.search(
                    cr, uid, [], context=context)
                quality_review_ids = list()

                for item_id in quality_review_items:
                    quality_review_ids.append(
                        (0, 0, {'quality_review_id': item_id})
                    )

                for record in result1:
                    data = record[2]
                    product_id = data['product_id']
                    product_qty = data['quantity']
                    data['product_not_accepted_ids'] = list()

                    for unit in range(int(product_qty)):
                        data['product_not_accepted_ids'].append(
                            (0, 0, {
                                'product_id': product_id,
                                'product_qty': 1,
                                'quality_review_ids': quality_review_ids,
                                })
                            )

                res.update({'product_return_not_accepted_moves': result1})

            if 'parent_location_id' in fields and pick.location_id.usage == 'internal':
                res.update({'parent_location_id':pick.picking_type_id.warehouse_id and pick.picking_type_id.warehouse_id.view_location_id.id or pick.location_id.location_id.id})
            if 'original_location_id' in fields:
                res.update({'original_location_id': pick.location_id.id})
            stock_location_obj = self.pool.get('stock.location')
            return_not_accepted_location = stock_location_obj.search(
                cr, uid, [
                    ('id', 'child_of', pick.location_dest_id.location_id.id),
                    ('return_not_accepted_location', '=', True)
                    ], context=context)
            if 'location_id' in fields and return_not_accepted_location:
                res.update({'location_id': return_not_accepted_location[0]})
        return res

    def _create_returns_not_accepted(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        record_id = context and context.get('active_id', False) or False
        move_obj = self.pool.get('stock.move')
        pick_obj = self.pool.get('stock.picking')
        uom_obj = self.pool.get('product.uom')
        data_obj = self.pool.get('stock.return.not.accepted.picking.line')
        pick = pick_obj.browse(cr, uid, record_id, context=context)
        data = self.read(cr, uid, ids[0], context=context)
        returned_lines = 0

        #Create new picking for returned products not accepted
        picking_type_internal_id = self.pool.get(
            'ir.model.data').get_object_reference(
                cr, uid, 'stock', 'picking_type_internal')[1]
        new_picking = pick_obj.copy(cr, uid, pick.id, {
            'move_lines': [],
            'picking_type_id': picking_type_internal_id,
            'state': 'draft',
            'origin': pick.name,
            'location_id': pick.location_dest_id.id,
            'location_dest_id': data['location_id'] and data['location_id'][0],
        }, context=context)

        for data_get in data_obj.browse(
            cr, uid, data['product_return_not_accepted_moves'],
            context=context):

            move = data_get.move_id
            if not move:
                raise UserError(_("You have manually created product lines, please delete them to proceed"))
            new_qty = data_get.quantity
            if new_qty:
                # The return of a return not accepted should be linked with the original's destination move if it was not cancelled
                if move.origin_returned_move_id.move_dest_id.id and move.origin_returned_move_id.move_dest_id.state != 'cancel':
                    move_dest_id = move.origin_returned_move_id.move_dest_id.id
                else:
                    move_dest_id = False

                returned_lines += 1
                location_id = data['location_id'] and data['location_id'][0] or move.location_id.id
                move_obj.copy(cr, uid, move.id, {
                    'product_id': data_get.product_id.id,
                    'product_uom_qty': new_qty,
                    'picking_id': new_picking,
                    'state': 'draft',
                    'location_id': move.location_dest_id.id,
                    'location_dest_id': location_id,
                    'picking_type_id': picking_type_internal_id,
                    'warehouse_id': pick.picking_type_id.warehouse_id.id,
                    'origin_returned_not_accepted_move_id': move.id,
                    'procure_method': 'make_to_stock',
                    'move_dest_id': move_dest_id,
                })

        if not returned_lines:
            raise UserError(_("Please specify at least one non-zero quantity."))

        product_not_accepted_ids = list()

        for move_id in data['product_return_not_accepted_moves']:

            move = self.pool.get(
                'stock.return.not.accepted.picking.line').browse(
                    cr, uid, move_id, context=context)

            for product_not_accepted in move.product_not_accepted_ids:

                quality_review_ids = list()

                for quality_review_item in product_not_accepted.quality_review_ids:
                    quality_review_ids.append(
                        (0, 0, {
                            'quality_review_id': \
                                quality_review_item.quality_review_id.id,
                            'meet': quality_review_item.meet,
                            })
                        )

                product_not_accepted_ids.append(
                    (0, 0, {
                        'product_id': product_not_accepted.product_id.id,
                        'product_qty': product_not_accepted.product_qty,
                        'quality_review_ids': quality_review_ids,
                        })
                    )
        _logger.debug('DEBUG PRODUCTS NOT ACCEPTED %s', product_not_accepted_ids)
        _logger.debug('DEBUG PRODUCTS NOT ACCEPTED %s', self)
        _logger.debug('DEBUG PRODUCTS NOT ACCEPTED %s', data)

        self.pool.get('stock.picking').write(
            cr, uid, new_picking, {
                'product_not_accepted_ids': product_not_accepted_ids
                }, context=context)

        pick_obj.action_confirm(cr, uid, [new_picking], context=context)
        pick_obj.action_assign(cr, uid, [new_picking], context=context)
        return new_picking, picking_type_internal_id

    def create_returns_not_accepted(self, cr, uid, ids, context=None):
        """
         Creates return not accepted picking and returns act_window to new picking
        """
        new_picking_id, picking_type_internal_id = self._create_returns_not_accepted(cr, uid, ids, context=context)
        # Override the context to disable all the potential filters that could have been set previously
        ctx = context.copy()
        ctx.update({
            'search_default_picking_type_id': picking_type_internal_id,
            'search_default_draft': False,
            'search_default_assigned': False,
            'search_default_confirmed': False,
            'search_default_ready': False,
            'search_default_late': False,
            'search_default_available': False,
        })
        return {
            'name': _('Picking of returns not accepted'),
            'view_type': 'form',
            'view_mode': 'form,tree,calendar',
            'res_model': 'stock.picking',
            'res_id': new_picking_id,
            'type': 'ir.actions.act_window',
            'context': ctx,
        }


class WizardStockPickingProductNotAccepted(osv.osv_memory):
    _name = 'wizard.stock.picking.product.not.accepted'
    _rec_name = 'product_id'

    _columns = {
        'product_id': fields.many2one(
            'product.product', string="Product", required=True),
        'product_qty': fields.float(
            "Quantity",
            digits_compute=dp.get_precision('Product Unit of Measure'),
            required=True, default=1),
        'wizard_return_not_accepted_line_id': fields.many2one(
            'stock.return.not.accepted.picking.line',
            string='Line of Wizard Return Not Accepted',
            required=True),
        'quality_review_ids': fields.one2many(
            'product.quality.review.wizard.return.not.accepted.rel',
            'product_not_accepted_id',
            string='Quality Review in Products'
        )
        }


class ProductQualityReviewWizardRel(osv.osv_memory):
    _name = 'product.quality.review.wizard.return.not.accepted.rel'
    _rec_name = 'quality_review_id'

    _columns = {
        'product_not_accepted_id': fields.many2one(
            'wizard.stock.picking.product.not.accepted',
            string="Product not accepted",
            required=True),
        'quality_review_id': fields.many2one(
            'product.quality.review',
            string='Quality review item',
            required=True),
        'meet': fields.boolean('Does it meet?')
    }
