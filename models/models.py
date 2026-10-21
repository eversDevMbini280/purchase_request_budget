# -*- coding: utf-8 -*-

from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang
from collections import defaultdict



class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _description = 'Demande d\'achat'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _LOCKED_FIELDS = (
        'requested_by', 'description', 'department_id', 'date_start',
        'date_required', 'origin', 'company_id', 'line_ids')

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

    budget_remaining = fields.Monetary(
        string='Restant du budget', compute='_compute_budget_remaining',
        currency_field='currency_id')

    def _get_budget(self):
        self.ensure_one()
        if not self.department_id or not self.date_start:
            return self.env['purchase.budget']
        return self.env['purchase.budget']._find_for_request(
            self.department_id, self.company_id, self.date_start)

    @api.depends('department_id', 'company_id', 'date_start', 'amount_total', 'state')
    def _compute_budget_remaining(self):
        for request in self:
            budget = request._get_budget()
            request.budget_remaining = budget._get_remaining() if budget else 0.0

    def _check_budget(self):
        """Bloque si aucun budget n'existe ou si le total dépasse le restant."""
        self.ensure_one()
        budget = self._get_budget()
        if not budget:
            raise UserError(_(
                "Aucun budget n'existe pour le département « %(dept)s » à la date du %(date)s.",
                dept=self.department_id.display_name, date=self.date_start))
        remaining = budget._get_remaining()
        if self.amount_total > remaining:
            raise UserError(_(
                "Le total de la demande (%(total)s) dépasse le montant restant du budget (%(remaining)s).",
                total=formatLang(self.env, self.amount_total, currency_obj=self.currency_id),
                remaining=formatLang(self.env, remaining, currency_obj=self.currency_id)))

    def _get_direction_users(self):
        return self.env.ref('purchase_request_budget.group_request_direction').users

    def _get_approvers(self):
        """Qui doit valider : le manager du département ; la Direction si le
        demandeur est lui-même le manager, ou si la demande attend la Direction."""
        self.ensure_one()
        directors = self._get_direction_users() - self.requested_by
        if self.state == 'waiting_direction':
            return directors
        manager = self.department_id.manager_id.user_id
        if manager and manager != self.requested_by:
            return manager
        return directors

    def action_submit(self):
        for request in self:
            if request.state != 'draft':
                raise UserError(_("Seule une demande en brouillon peut être soumise."))
            if request.requested_by != self.env.user:
                raise UserError(_("Seul le demandeur peut soumettre sa demande."))
            if not request.line_ids:
                raise UserError(_("Impossible de soumettre une demande sans ligne."))
            if not request.department_id.manager_id.user_id:
                raise UserError(_("Le département de la demande n'a pas de manager (avec un utilisateur lié) : soumission impossible."))
            request._check_budget()
            approvers = request._get_approvers()
            if not approvers:
                raise UserError(_("Aucun valideur disponible pour cette demande."))
            request.state = 'submitted'
            for approver in approvers:
                request.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=approver.id,
                    summary=_("À valider"),
                    note=_("La demande %s est à valider.", request.name))

    def _check_approver(self):
        """L'utilisateur courant peut-il traiter la demande à son niveau actuel ?"""
        self.ensure_one()
        user = self.env.user
        if self.requested_by == user:
            raise UserError(_("Vous ne pouvez pas valider ou refuser votre propre demande."))
        is_direction = user.has_group('purchase_request_budget.group_request_direction')
        if self.state == 'submitted':
            if not (is_direction or user == self.department_id.manager_id.user_id):
                raise UserError(_("Seul le manager du département (ou la Direction) peut traiter cette demande."))
        elif self.state == 'waiting_direction':
            if not is_direction:
                raise UserError(_("Seule la Direction peut traiter cette demande."))

    def _close_activities(self):
        self.sudo().activity_feedback(['mail.mail_activity_data_todo'])

    def action_manager_approve(self):
        for request in self:
            if request.state != 'submitted':
                raise UserError(_("Cette demande n'attend pas la validation du manager."))
            request._check_approver()
            request._close_activities()
            # Strictement supérieur au seuil : la Direction doit aussi valider
            if request.amount_total > request.company_id.purchase_request_threshold:
                directors = request._get_direction_users() - request.requested_by
                if not directors:
                    raise UserError(_("Le total dépasse le seuil mais aucun utilisateur Direction n'est disponible."))
                request.state = 'waiting_direction'
                for director in directors:
                    request.activity_schedule(
                        'mail.mail_activity_data_todo',
                        user_id=director.id,
                        summary=_("À valider (Direction)"),
                        note=_("La demande %s dépasse le seuil : validation Direction requise.", request.name))
            else:
                request._check_budget()
                request.state = 'validated'

    def action_direction_approve(self):
        for request in self:
            if request.state != 'waiting_direction':
                raise UserError(_("Cette demande n'attend pas la validation de la Direction."))
            request._check_approver()
            request._close_activities()
            request._check_budget()
            request.state = 'validated'

    refusal_reason = fields.Text(
        string='Motif du refus', readonly=True, copy=False, tracking=True)

    purchase_order_ids = fields.One2many(
        'purchase.order', 'purchase_request_id', string='Demandes de prix',
        groups='purchase.group_purchase_user')
    purchase_order_count = fields.Integer(
        string='Nombre de demandes de prix',
        compute='_compute_purchase_order_count',
        groups='purchase.group_purchase_user')

    @api.depends('purchase_order_ids')
    def _compute_purchase_order_count(self):
        for request in self:
            request.purchase_order_count = len(request.purchase_order_ids)

    def action_view_purchase_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Demandes de prix"),
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('purchase_request_id', '=', self.id)],
            'context': {'create': False},
        }

    def action_create_rfqs(self):
        self.ensure_one()
        if self.state != 'validated':
            raise UserError(_("Seule une demande validée peut être convertie en demandes de prix."))
        if not self.env.user.has_group('purchase.group_purchase_user'):
            raise UserError(_("Seul un acheteur peut générer les demandes de prix."))
        missing = self.line_ids.filtered(lambda line: not line.supplier_id)
        if missing:
            names = "\n".join(
                "- %s" % (line.description or line.product_id.display_name)
                for line in missing)
            raise UserError(_("Ces lignes n'ont pas de fournisseur suggéré :\n%s", names))
        by_supplier = defaultdict(lambda: self.env['purchase.request.line'])
        for line in self.line_ids:
            by_supplier[line.supplier_id] |= line
        planned = (fields.Datetime.to_datetime(self.date_required)
                   if self.date_required else fields.Datetime.now())
        for supplier, lines in by_supplier.items():
            self.env['purchase.order'].create({
                'partner_id': supplier.id,
                'company_id': self.company_id.id,
                'currency_id': self.currency_id.id,
                'origin': self.name,
                'purchase_request_id': self.id,
                'order_line': [Command.create({
                    'product_id': line.product_id.id,
                    'name': line.description or line.product_id.display_name,
                    'product_qty': line.quantity,
                    'product_uom': (line.uom_id or line.product_id.uom_po_id).id,
                    'price_unit': line.price_unit,
                    'date_planned': planned,
                }) for line in lines],
            })
        self.sudo().write({'state': 'converted'})
        return self.action_view_purchase_orders()

    def action_refuse(self):
        """Ouvre l'assistant : le motif est obligatoire avant toute action."""
        self.ensure_one()
        if self.state not in ('submitted', 'waiting_direction'):
            raise UserError(_("Cette demande ne peut plus être refusée."))
        self._check_approver()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Refuser la demande"),
            'res_model': 'purchase.request.refuse.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.id},
        }

    def _refuse(self, reason):
        for request in self:
            if request.state not in ('submitted', 'waiting_direction'):
                raise UserError(_("Cette demande ne peut plus être refusée."))
            request._check_approver()
            request.write({'refusal_reason': reason, 'state': 'refused'})
            request._close_activities()
            request.message_post(
                body=_("Demande refusée. Motif : %s", reason),
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                partner_ids=request.requested_by.partner_id.ids)

    def action_reset_draft(self):
        for request in self:
            if request.state != 'refused':
                raise UserError(_("Seule une demande refusée peut être remise en brouillon."))
            if request.requested_by != self.env.user:
                raise UserError(_("Seul le demandeur peut remettre la demande en brouillon."))
            request.state = 'draft'        

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

    def write(self, vals):
        if set(self._LOCKED_FIELDS) & set(vals):
            for request in self:
                if request.state != 'draft':
                    raise UserError(_(
                        "La demande %s n'est plus en brouillon : elle ne peut plus être modifiée.",
                        request.name))
        return super().write(vals)

    def unlink(self):
        for request in self:
            if request.state not in ('draft', 'refused'):
                raise UserError(_(
                    "Seules les demandes en brouillon ou refusées peuvent être supprimées."))
        return super().unlink()
