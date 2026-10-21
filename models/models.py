# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _description = 'Demande d\'achat'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Numéro de demande',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    origin = fields.Char(
        string='Document d\'origine',
        help="Référence du document d'origine (ex: projet, autre document)."
    )
    date_start = fields.Date(
        string='Date de création',
        required=True,
        default=fields.Date.context_today
    )
    requested_by = fields.Many2one(
        'res.users',
        string='Demandeur',
        required=True,
        default=lambda self: self.env.user,
        tracking=True
    )
    description = fields.Text(
        string='Description / Justification',
        required=True
    )
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('to_approve', 'À approuver'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
        ('done', 'Traité')
    ], string='Statut', default='draft', tracking=True, index=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('purchase.request') or _('New')
        return super().create(vals_list)