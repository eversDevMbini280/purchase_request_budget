# Demandes d'achat internes (purchase_request_budget)

## Installation
- Version d'Odoo : Odoo 18.0 Community
- Dépendances : base, mail, hr, purchase, product
- Commande d'installation : `python odoo/odoo-bin --addons-path=odoo/addons,custom_addons,omias-test -d pr_dev -i purchase_request_budget`

## Présentation
*(Sera complété au fil de l'eau)*

## Choix techniques
*(Sera complété au fil de l'eau)*

## Hypothèses
- **H1** : Version Odoo 18.0 Community choisie pour l'abondance de sa documentation.

- **H2** : La création du modèle purchase.request dans models.py couplée à la séquence ir.sequence (purchase.request) garantit la génération automatique d'une référence unique sous le format DA/2026/XXXX lors de l'appel de la méthode create

## Limites et suite
*(Sera complété au fil de l'eau)*