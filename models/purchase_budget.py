# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class PurchaseBudget(models.Model):
    _name = 'purchase.budget'
    _description = 'Budget de département'
    _order = 'date_start desc, id desc'

    name = fields.Char(string='Nom', compute='_compute_name', store=True)
    department_id = fields.Many2one(
        'hr.department', string='Département', required=True, index=True)
    company_id = fields.Many2one(
        'res.company', string='Société', required=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', readonly=True)
    date_start = fields.Date(string='Début', required=True)
    date_end = fields.Date(string='Fin', required=True)
    amount = fields.Monetary(string='Montant alloué', required=True)
    committed = fields.Monetary(
        string='Engagé', compute='_compute_amounts')
    remaining = fields.Monetary(
        string='Restant', compute='_compute_amounts')

    @api.depends('department_id.name', 'date_start', 'date_end')
    def _compute_name(self):
        for budget in self:
            budget.name = "%s (%s -> %s)" % (
                budget.department_id.name or '',
                budget.date_start or '',
                budget.date_end or '')

    def _get_committed_amount(self):
        """Somme des totaux des demandes Validées ou Converties de la période.
        sudo() : le restant doit rester exact même si l'utilisateur ne voit
        pas les demandes des autres."""
        self.ensure_one()
        requests = self.env['purchase.request'].sudo().search([
            ('department_id', '=', self.department_id.id),
            ('company_id', '=', self.company_id.id),
            ('state', 'in', ('validated', 'converted')),
            ('date_start', '>=', self.date_start),
            ('date_start', '<=', self.date_end),
        ])
        return sum(requests.mapped('amount_total'))

    def _get_remaining(self):
        self.ensure_one()
        return self.amount - self._get_committed_amount()

    @api.depends('amount', 'department_id', 'company_id', 'date_start', 'date_end')
    def _compute_amounts(self):
        for budget in self:
            if (budget.department_id and budget.company_id
                    and budget.date_start and budget.date_end):
                budget.committed = budget._get_committed_amount()
            else:
                budget.committed = 0.0
            budget.remaining = budget.amount - budget.committed

    @api.model
    def _find_for_request(self, department, company, date):
        """Budget applicable : même département et société, période
        contenant la date (bornes incluses)."""
        return self.sudo().search([
            ('department_id', '=', department.id),
            ('company_id', '=', company.id),
            ('date_start', '<=', date),
            ('date_end', '>=', date),
        ], limit=1)

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for budget in self:
            if budget.date_end < budget.date_start:
                raise ValidationError(_("La date de fin doit être postérieure ou égale à la date de début."))

    @api.constrains('department_id', 'company_id', 'date_start', 'date_end')
    def _check_overlap(self):
        for budget in self:
            overlap = self.search_count([
                ('id', '!=', budget.id),
                ('department_id', '=', budget.department_id.id),
                ('company_id', '=', budget.company_id.id),
                ('date_start', '<=', budget.date_end),
                ('date_end', '>=', budget.date_start),
            ])
            if overlap:
                raise ValidationError(_("Deux budgets d'un même département ne peuvent pas se chevaucher dans le temps."))

    @api.constrains('amount')
    def _check_amount(self):
        for budget in self:
            if budget.amount < 0:
                raise ValidationError(_("Le montant alloué ne peut pas être négatif."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            request = self.env['purchase.request'].browse(vals.get('request_id'))
            if request and request.state != 'draft':
                raise UserError(_("Les lignes d'une demande ne peuvent être modifiées qu'en brouillon."))
        return super().create(vals_list)

    def write(self, vals):
        if any(line.request_id.state != 'draft' for line in self):
            raise UserError(_("Les lignes d'une demande ne peuvent être modifiées qu'en brouillon."))
        return super().write(vals)

    def unlink(self):
        if any(line.request_id.state != 'draft' for line in self):
            raise UserError(_("Les lignes d'une demande ne peuvent être supprimées qu'en brouillon."))
        return super().unlink()            