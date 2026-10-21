# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PurchaseRequestLine(models.Model):
    _name = 'purchase.request.line'
    _description = "Ligne de demande d'achat"
    _order = 'id'

    request_id = fields.Many2one(
        'purchase.request', string='Demande',
        required=True, ondelete='cascade', index=True)
    product_id = fields.Many2one(
        'product.product', string='Produit', required=True)
    description = fields.Char(string='Description')
    quantity = fields.Float(string='Quantité', default=1.0, required=True)
    uom_id = fields.Many2one('uom.uom', string='Unité')
    price_unit = fields.Monetary(
        string='Prix unitaire estimé', currency_field='currency_id')
    supplier_id = fields.Many2one('res.partner', string='Fournisseur suggéré')
    currency_id = fields.Many2one(
        'res.currency', related='request_id.currency_id',
        store=True, readonly=True)
    subtotal = fields.Monetary(
        string='Sous-total', compute='_compute_subtotal',
        store=True, currency_field='currency_id')

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            product = line.product_id
            if product:
                line.description = product.display_name
                line.uom_id = product.uom_po_id
                line.price_unit = product.standard_price

    @api.constrains('quantity')
    def _check_quantity(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_("La quantité doit être strictement positive."))
