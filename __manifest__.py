# -*- coding: utf-8 -*-
{
    'name': "Demandes d'achat internes",

    'summary': "Demandes d'achat internes avec validation selon le montant, contrôle budgétaire par département et génération des demandes de prix",

    'description': """
Cette application permet la gestion complète des demandes d'achat internes d'une entreprise
multi-départements, de l'expression du besoin jusqu'à la demande de prix fournisseur.
    """,

    'author': "MUPUNU InformatiX",
    'website': "https://evers-dev-folio.vercel.app/",
    
    'application': True,

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Inventory/Purchase',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'hr', 'purchase', 'product'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/security_rules.xml',
        'data/purchase_request_sequence.xml',
        'data/purchase_request_cron.xml',
        'views/purchase_request_views.xml',
        'views/purchase_budget_views.xml',
        'wizard/purchase_request_refuse_wizard_views.xml',
        'views/res_config_settings_views.xml',
        'views/purchase_order_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

