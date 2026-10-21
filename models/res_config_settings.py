# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    purchase_request_currency_id = fields.Many2one(
        related='company_id.currency_id')
    purchase_request_threshold = fields.Monetary(
        string='Seuil de validation Direction',
        related='company_id.purchase_request_threshold',
        currency_field='purchase_request_currency_id',
        readonly=False)