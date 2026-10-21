# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    purchase_request_threshold = fields.Monetary(
        string='Seuil de validation Direction',
        currency_field='currency_id',
        default=0.0,
        help="Au-dessus (strictement) de ce total, la Direction doit aussi valider.")