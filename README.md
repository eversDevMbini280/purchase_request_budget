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

- **H7** : | Département ou manager manquant à la soumission | La soumission est bloquée avec un message clair | Un département sans manager lié à un utilisateur ne peut pas soumettre tant qu'il n'est pas configuré |

- **H8** : | Valeur par défaut du seuil | 0 : tant qu'il n'est pas réglé, toute demande de total positif passe par la Direction | C'est le comportement le plus prudent ; la démo règle un seuil réaliste |

- **H9** : | Qui valide la demande d'un manager (il ne valide jamais la sienne) | Un utilisateur Direction autre que le demandeur la valide au niveau 1 | La Direction est le seul niveau supérieur ; sans utilisateur Direction, la soumission est bloquée |

- **H10** : | Le contrôle budgétaire est-il refait à la validation ? | Oui, à la validation finale (manager sous le seuil, ou Direction) | Deux demandes soumises ensemble ne peuvent pas dépasser le budget à elles deux |






# Comparaison de chaque hypothèse de la roadmap avec les réponses d’OMIAS.


#	Hypothèse	Verdict	Ce que ça change
H1	Version Odoo 18	Inchangée (ton choix)	Ajoute les versions exactes de Python et PostgreSQL au README, comme OMIAS le demande
H2	Demandeur = utilisateur connecté, département déduit de sa fiche employé	Inchangée (ton choix)	OMIAS ne l’a pas traitée : elle reste ton hypothèse, pas une réponse confirmée
H3	Prix = coût du produit	Confirmée	Rien
H4	L’acheteur voit les demandes Validées et Converties	Confirmée	Rien. « Un manager voit aussi les siennes » n’a pas été abordée : elle reste ton choix
H5	Budget applicable (même département et société, bornes incluses)	Confirmée et complétée	Les sous-départements ne comptent pas dans le budget du parent
H6	Chevauchement par département et société	Confirmée et complétée	Multi-société géré, une seule devise par société, pas de conversion
H7	Département ou manager manquant : soumission bloquée	Confirmée	Rien
H8	Seuil par défaut à 0	Confirmée	Ajoute au README qu’avec un seuil à 0, toute demande passe par la Direction
H9	Un manager est validé par la Direction	Étendue (le code change)	Le cas « le demandeur est un utilisateur Direction » est maintenant tranché : un autre utilisateur Direction valide. Utilise les deux méthodes corrigées de mon dernier message
H10	Contrôle budgétaire refait à la validation	Confirmée	Rien
H11	Motif conservé, seul le demandeur remet en brouillon	Confirmée et précisée	Refus au niveau 1 : manager ou Direction ; au niveau 2 : Direction seule
H12	« Modifiable » = champs métier en brouillon	Inchangée (ton choix)	Pas abordée par OMIAS
H13	Contenu des demandes de prix	Confirmée et complétée	N’importe quel contact comme fournisseur ; « Convertie » est définitif ; seuls les acheteurs génèrent
H14	Action planifiée : rappel après 3 jours	Supprimée	OMIAS n’en attend aucune : c’est un bonus. Si tu ne la fais pas, retire H14 et mets-la dans « Limites et suite »
H15	Démo : un utilisateur par profil, mot de passe = identifiant	Confirmée	Les identifiants doivent figurer dans le README
H16	Date d’envoi	Modifiée	Le sujet dit vendredi, OMIAS accepte jeudi soir au plus tard : à écrire dans le README, puisque la réponse diffère de « vendredi »

## Limites et suite
*(Sera complété au fil de l'eau)*