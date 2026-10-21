# -*- coding: utf-8 -*-

from odoo import fields, models


class PurchaseRequestRefuseWizard(models.TransientModel):
    _name = 'purchase.request.refuse.wizard'
    _description = "Assistant de refus d'une demande d'achat"

    request_id = fields.Many2one(
        'purchase.request', string='Demande', required=True)
    reason = fields.Text(string='Motif du refus', required=True)

    def action_confirm(self):
        self.ensure_one()
        self.request_id._refuse(self.reason)
        return {'type': 'ir.actions.act_window_close'}
    
