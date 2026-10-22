# Demandes d'achat internes (purchase_request_budget)

## Installation

- **Version d'Odoo** : Odoo 18.0 Community Edition
- **Version Python** : Python 3.12 (ou version compatible 3.10+)
- **Base de données** : PostgreSQL 16 (ou supérieur)
- **Dépendances Odoo** : `base`, `mail`, `hr`, `purchase`, `product`
- **Commande d'installation** :
  ```bash
  python odoo/odoo-bin --addons-path=odoo/addons,custom_addons,omias-test -d pr_dev -i purchase_request_budget
  ```

---

## Présentation

Ce module remplace la gestion informelle des demandes d'achat (e-mails, formulaires papier) par un circuit unique, centralisé, tracé et soumis à un contrôle budgétaire strict.

### Parcours utilisateur étape par étape :

1. **Création et Soumission (Demandeur)** :
   - L'employé crée une demande en saisissant le motif (obligatoire) et ses lignes d'articles (produit, quantité, prix estimé, fournisseur suggéré).
   - Une référence unique et séquentielle est attribuée (`DA/AAAA/NNNN`).
   - Le demandeur soumet sa demande.
2. **Contrôle budgétaire** :
   - Contrôle automatique à la soumission : la demande requiert au moins une ligne, un budget configuré pour la période et le département, ainsi qu'un manager assigné.
   - Le montant restant disponible du département est calculé et affiché en temps réel.
3. **Validation Hiérarchique (Manager)** :
   - Le manager du département reçoit une activité Odoo « À valider ».
   - Un manager ne peut en aucun cas valider sa propre demande (elle est alors escaladée à la Direction).
   - Il valide ou refuse la demande en justifiant obligatoirement sa décision.
4. **Validation Direction (Arbitrage / Dépassement)** :
   - La Direction intervient lorsque le montant demandé est supérieur ou égal au montant restant du budget du département, ou en cas de dépassement du seuil société.
   - La Direction peut approuver ou refuser la demande.
5. **Gestion du Refus** :
   - En cas de refus (manager ou direction), la saisie d'un motif est obligatoire via un assistant dédié (`TransientModel`).
   - Le motif est historisé dans le chatter et le demandeur est notifié. Ce dernier peut modifier et remettre sa demande en brouillon pour la resoumettre.
6. **Conversion en Demandes de Prix (Acheteur)** :
   - Une fois la demande passée à l'état **Validée**, l'acheteur peut déclencher la génération des demandes de prix (RFQ).
   - Le module regroupe automatiquement les articles par fournisseur suggéré et crée les bons de commande correspondants.
   - La demande d'achat passe alors à l'état définitif **Convertie**.

### Menus et Accès :
- **Demandes d'achat** : *Achats › Demandes internes › Mes demandes / Demandes à valider / Toutes les demandes*
- **Gestion des budgets** : *Achats › Demandes internes › Budgets*
- **Configuration du seuil** : *Achats › Configuration › Paramètres*

### Comptes d'utilisateurs et rôles (configurés en base de données) :

| Identifiant (Login) | Nom affiché | Département | Rôle / Profil |
|---|---|---|---|
| `saiyan` | Broly | Comptabilité | **Demandeur** |
| `kastuki@example.com` | Kastuki Bakugo | Informatique | **Demandeur** |
| `kesuke@example.com` | Kesuke Urahara | Informatique | **Manager** *(Manager du Dept. Informatique)* |
| `Kiojin` | Eren Jager | — | **Direction** |
| `Jujustu` | Sugu Geto | — | **Direction** |
| `Uchiwa` | Madara Uchiwa | Informatique | **Demandeur** + **Acheteur** |
| `bayers@gmail.com` | Bayers | — | **Acheteur** |
| `fourni@gmail.com` | founi | — | **Fournisseur suggéré** *(Contact / Partenaire pour les lignes)* |
| `admin` | evers Dev Mbini Admin | Management | **Administrateur** *(Direction + Responsable Achats)* |

---

## Choix techniques

- **Total calculé et stocké** (`@api.depends` + `store=True`) : permet le tri, la recherche, le filtrage avancé et le suivi des variations dans le chatter (`tracking=True`).
- **Assistant de refus (`TransientModel`)** : garantit l'obligation de saisie d'un motif explicite avant tout rejet, évitant les annulations silencieuses.
- **Groupes de sécurité hiérarchiques (`implied_ids`)** : attribution simplifiée d'un seul rôle par utilisateur sans risque d'omettre des droits sous-jacents.
- **Règles d'enregistrement multi-société et par rôle** : séparation stricte des données entre départements et filiales tout en garantissant aux acheteurs et à la direction la visibilité requise.
- **Calcul sécurisé du budget disponible via `sudo()`** : assure l'exactitude du solde restant calculé en agrégeant toutes les demandes engagées de la période, même si l'utilisateur connecté n'a pas accès aux demandes des autres départements.
- **Verrouillage des champs côté serveur (`write`, `unlink`)** : les demandes ne sont modifiables ou supprimables qu'à l'état brouillon. Les sécurités sont appliquées au niveau ORM (Python) et ne reposent pas uniquement sur les attributs de vue (XML).
- **Double vérification budgétaire** : le contrôle est exécuté lors de la soumission puis revérifié à la validation finale afin de prévenir les dépassements en cas de validations concurrentes.

---

## Hypothèses

Les points non détaillés dans le cahier des charges initial ont été arbitrés et structurés selon les hypothèses suivantes :

| Réf. | Sujet non précisé | Décision retenue | Justification |
|:---:|---|---|---|
| **H1** | Version d'Odoo | Odoo 18.0 Community | Version stable moderne assurant une compatibilité pérenne des API (`product_uom`, vues standard). |
| **H2** | Demandeur et Département | Demandeur = utilisateur connecté ; département déduit de la fiche employé (`hr.employee`) | Automatise la saisie tout en laissant le département modifiable si besoin. La soumission est bloquée si aucun manager n'est rattaché. |
| **H3** | Prix unitaire estimé et unité | Prix = coût du produit (`standard_price`) ; unité = unité d'achat (`uom_po_id`) | Utilisation des référentiels standards Odoo. Si aucun coût n'est renseigné, la valeur est à 0 et doit être complétée. |
| **H4** | Visibilité des enregistrements | L'acheteur voit les demandes Validées et Converties ; chaque manager voit son département et ses propres demandes ; la direction voit tout | Respect du principe de moindre privilège tout en permettant aux acheteurs d'opérer la conversion. |
| **H5** | Budget applicable | Budget de la même société et du même département dont la période englobe la date de la demande | Les sous-départements ne sont pas consolidés dans le parent pour garantir une étanchéité budgétaire stricte. |
| **H6** | Unicité des périodes | Interdiction de chevauchement de dates pour un même département sur une même société | Prévention des doublons d'allocation budgétaire. Gestion native du multi-société avec une devise unique par société. |
| **H7** | Manager manquant | Blocage à la soumission avec message explicite | Empêche le dépôt de demandes orphelines sans valideur assigné. |
| **H8** | Seuil d'intervention Direction | Déclenché lorsque la demande est supérieure ou égale au budget restant, ou supérieure au seuil société | Garantit qu'aucun dépassement de budget ne peut être validé sans l'aval formel de la Direction. |
| **H9** | Auto-validation interdite | Si le demandeur est manager, validation niveau 1 par la Direction ; si le demandeur est Direction, un autre utilisateur Direction valide | Respect du principe fondamental de séparation des pouvoirs (on ne valide jamais sa propre demande). |
| **H10** | Contrôle budgétaire à la validation | Nouveau contrôle du disponible lors de l'approbation finale | Évite le dépassement si deux demandes ont été soumises en parallèle sur une même enveloppe résiduelle. |
| **H11** | Historique après refus | Le motif de refus reste consigné dans le chatter ; seul le demandeur peut remettre en brouillon | Traçabilité complète de l'historique et des échanges. |
| **H12** | Verrouillage des modifications | Champs métier modifiables uniquement à l'état brouillon | Intégrité des données dès lors que la demande entre dans le circuit de validation. |
| **H13** | Génération des RFQ | Tout contact peut être suggéré ; regroupement automatique par fournisseur ; statut « Convertie » définitif | Permet la création optimisée d'un bon de commande par fournisseur. Seul un acheteur peut effectuer l'action. |
| **H14** | Comptes de test et validation | Comptes réels configurés en base avec départements et rôles dédiés | Permet de tester l'intégralité du circuit (création, validation manager, arbitrage direction, conversion acheteur) avec les permissions idoines. |

---

## Limites et suite

Ce qui pourrait être apporté ou enrichi avec davantage de temps :

- **Rapport imprimable (PDF)** : Création d'un rapport QWeb « Bon de demande d'achat » incluant le tableau des articles, le visa du manager et l'approbation de la Direction.
- **Sélection assistée de fournisseur** : Intégration d'un assistant guidé lors de la conversion pour attribuer un fournisseur aux lignes qui n'en ont pas (actuellement bloquées à la conversion).
- **Couverture de tests unitaires automatisés** : Ajout d'une suite de tests Odoo (`odoo/tests`) validant automatiquement les transitions d'états, le calcul du solde restant et les cas limites de validation Direction.
- **Réservation temporaire de budget** : Système d'engagement préventif dès la soumission pour réserver les fonds avant validation finale face aux accès concurrents.
- **Paramétrage des relances** : Possibilité de configurer dynamiquement le délai des rappels automatiques (actuellement fixé à 3 jours par l'action planifiée).
- **Internationalisation (i18n)** : Export et traduction des termes de l'interface en anglais via les fichiers `.pot` / `.po`.