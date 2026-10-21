# Demandes d'achat internes (purchase_request_budget)

## Installation
- Version d'Odoo : Odoo 18.0 Community
- Dépendances : base, mail, hr, purchase, product
- Commande d'installation : `python odoo/odoo-bin --addons-path=odoo/addons,custom_addons,omias-test -d pr_dev -i purchase_request_budget`

## Présentation

Le module remplace les demandes d'achat par e-mail et papier par un circuit unique, tracé et contrôlé.

Parcours d'un utilisateur :

1. **Demandeur** : crée une demande (motif obligatoire, lignes produit/quantité/prix/fournisseur). La référence `DA/AAAA/NNNN` est générée. Il la **soumet**.
2. **Contrôle budgétaire** à la soumission : la demande est bloquée s'il n'y a ni ligne, ni budget pour la période, ni manager, ou si le total dépasse le restant (le message donne les deux montants).
3. **Manager** du département : reçoit une activité « À valider », valide ou refuse (avec motif). Il ne valide jamais sa propre demande.
4. **Direction** : n'intervient que si le total est strictement supérieur au seuil de la société. Elle valide ou refuse.
5. **Refus** : motif obligatoire (assistant), publié dans le chatter, demandeur notifié ; il peut remettre en brouillon et resoumettre.
6. **Acheteur** : sur une demande Validée, génère une demande de prix par fournisseur ; la demande passe à Convertie.

Menus : Achats › Demandes internes › Mes demandes, Demandes à valider, Toutes les demandes, Budgets. Seuil : Achats › Configuration › Paramètres.

Comptes de démo (mot de passe = identifiant) : `marie`, `awa` (Demandeurs), `manager_it`, `manager_mkt`, `manager_fin` (Managers), `direction`, `acheteur`.

## Choix techniques

- **Total stocké** (`@api.depends` + `store=True`) : triable, filtrable et suivi dans le chatter.

- **Assistant de refus** (`TransientModel`) : force la saisie du motif avant l'action.

- **Groupes hiérarchiques** (`implied_ids`) : un seul groupe par personne, aucun droit oublié.

- **Règles d'enregistrement** : règles de groupe en OU, règle multi-société en ET ; les droits d'accès (CSV) disent quelle action, les règles disent quelles lignes.

- **`sudo()` dans le calcul du budget** : le restant reste exact même si l'utilisateur ne voit pas toutes les demandes.

- **Protection côté serveur** (`write`, `unlink`, contrôles dans les méthodes) en plus de l'écran : l'écran seul ne protège pas.

- **Contrôle budgétaire refait à la validation finale** (H10).

- **Départements stockés et modifiables** (`compute` + `store=True` + `readonly=False`).

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

- **H11** : | Sort du motif après remise en brouillon | Le motif est conservé (visible dans le chatter) ; seul le demandeur remet en brouillon | L'historique des refus reste traçable ; une limite de refus pourrait être ajoutée plus tard |


- **H12** : | Que veut dire « modifiable » | Les champs métier (demandeur, motif, département, dates, lignes) ne sont modifiables qu'en brouillon ; les changements d'état passent par les boutons | Les messages du chatter restent possibles à tout état |

- **H13** : | Contenu des lignes de demande de prix | Prix et unité repris de la ligne de demande ; fournisseur = partenaire suggéré ; devise de la société | Les prix restent modifiables par l'acheteur avant l'envoi au fournisseur |

- **H14** : | Comptes et période des données de démonstration | Mot de passe = identifiant (marie, awa, manager_it, manager_mkt, manager_fin, direction, acheteur) ; budgets sur l'année en cours ; seuil de la société à 1000 | Les données de démo ne servent qu'à tester ; elles ne se chargent pas en production |


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

- Pas de rapport PDF « Bon de demande d'achat » (je l'ajouterais avec un rapport QWeb et l'historique des validations).
- Pas d'assistant de choix du fournisseur pour les lignes qui n'en ont pas (aujourd'hui la génération est bloquée).
- Pas de tests automatiques : je commencerais par des tests sur le contrôle budgétaire et le seuil.
- Interface en français uniquement (pas de fichiers de traduction).
- Deux demandes soumises simultanément ne se réservent pas le budget : seul le contrôle final (validation) les départage.
- Le délai de 3 jours de l'action planifiée est codé en dur (pas encore paramétrable).