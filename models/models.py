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
    requested_by = fields.Many2one(
        'res.users',
        string='Demandeur',
        required=True,
        default=lambda self: self.env.user,
        tracking=True
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Département',
        compute='_compute_department_id',
        store=True,
        readonly=False,
        tracking=True
    )
    date_start = fields.Date(
        string='Date de la demande',
        required=True,
        default=fields.Date.context_today
    )
    date_required = fields.Date(
        string='Date souhaitée'
    )
    description = fields.Text(
        string='Motif de la demande',
        required=True,
        tracking=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        required=True,
        default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        related='company_id.currency_id',
        store=True,
        readonly=True
    )
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumise'),
        ('waiting_direction', 'Attente Direction'),
        ('validated', 'Validée'),
        ('refused', 'Refusée'),
        ('converted', 'Convertie'),
    ], string='Statut', default='draft', tracking=True, index=True)
    line_ids = fields.One2many(
        'purchase.request.line', 'request_id', string='Lignes', copy=True)
    amount_total = fields.Monetary(
        string='Total', compute='_compute_amount_total', store=True,
        currency_field='currency_id', tracking=True)

    @api.depends('line_ids.subtotal')
    def _compute_amount_total(self):
        for request in self:
            request.amount_total = sum(request.line_ids.mapped('subtotal'))

    @api.depends('requested_by')
    def _compute_department_id(self):
        for request in self:
            employee = request.requested_by.sudo().employee_id
            request.department_id = employee.department_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('purchase.request') or _('New')
        return super().create(vals_list)