from datetime import timedelta

from odoo import _, api, fields, models


class PurchaseRequestCron(models.Model):
    _inherit = 'purchase.request'

    @api.model
    def _cron_remind_pending(self):
        """Rappel quotidien : demandes en attente de validation depuis plus de 3 jours."""
        limit = fields.Datetime.now() - timedelta(days=3)
        requests = self.search([
            ('state', 'in', ('submitted', 'waiting_direction')),
            ('write_date', '<', limit),
        ])
        summary = _('Rappel : demande en attente de validation')
        for request in requests:
            if request.state == 'waiting_direction':
                users = request._get_direction_users()
            else:
                users = request.department_id.manager_id.user_id
            for user in users:
                already = request.activity_ids.filtered(
                    lambda a: a.user_id == user and a.summary == summary)
                if not already:
                    request.activity_schedule(
                        'mail.mail_activity_data_todo',
                        user_id=user.id, summary=summary)
        return True
