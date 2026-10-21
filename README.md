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
- **H1** : Version d'Odoo (18 ou 19) | Odoo 18.0 Community | Documentation plus abondante ; la 19 renomme plusieurs champs (product_uom, groups_id) |

- **H2** :  Demandeur par défaut (le sujet dit « employé connecté ») | Le demandeur est l'utilisateur connecté ; son département est déduit de sa fiche employé liée et reste modifiable | Sans fiche employé, le département reste vide et la soumission est bloquée (H7) |

- **H3** : « Prix d'achat du produit » et unité des lignes | Prix estimé = coût du produit (standard_price) ; unité = unité d'achat du produit (uom_po_id) | Un produit sans coût donne un prix à 0, modifiable à la main |

- **H4** : | Qui voit quoi | L'acheteur voit les demandes Validées et Converties ; un manager voit aussi ses propres demandes | Une autre politique se règle dans security_rules.xml |

- **H5** : | Quel budget s'applique à une demande | Celui du même département et de la même société dont la période contient la date de la demande (bornes incluses) | Une demande hors de toute période n'a pas de budget : sa soumission est bloquée |

- **H6** : | Unicité des budgets | Pas de chevauchement par département et par société | Deux sociétés peuvent avoir des budgets aux mêmes dates pour un même département |

## Limites et suite
*(Sera complété au fil de l'eau)*