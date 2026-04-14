# NexusGame — Suite de Tests

> Projet final 2TES3 — Tests Avancés & Automatisation

## Présentation du projet

<!-- Décrivez le contexte du projet et l'API GameStore. -->

---

## Structure du repo

```
NexusGame/
├── app_gamestore.py
├── requirements.txt
├── README.md
├── tests/
│   ├── conftest.py
│   ├── test_unit.py
│   ├── test_integration.py
│   ├── test_ui.py
│   ├── gamestore_collection.json
│   ├── locust_gamestore.py
│   └── pages/
│       ├── home_page.py
│       ├── add_game_modal.py
│       └── game_detail_page.py
├── .github/
│   └── workflows/
│       ├── ci-pipeline.yml     ← Pipeline CI complet
│       └── zap-scan.yml        ← Scan sécurité OWASP ZAP
├── .zap/
│   └── rules.tsv
└── .gitignore
```

---

## 🚀 Pipeline CI sur GitHub Actions

### Architecture du pipeline

Le pipeline CI est complètement automatisé et s'exécute séquentiellement :

```mermaid
graph LR
    A[unitaires] --> B[intégration] --> C[API] --> D[UI] --> E[charge] --> F[sécurité]
    F --> G✅[Pipeline VERT]
    A -.-|échec| H❌[Pipeline ROUGE]
    B -.-|échec| H
    C -.-|échec| H
    D -.-|échec| H
    E -.-|échec| H
    F -.-|échec| H
```

### Jobs et dépendances

| Étape | Job | Condition | Artefacts |
|-------|-----|-----------|-----------|
| 1️⃣ | `unit-tests` | — | `unit-test-report.html` |
| 2️⃣ | `integration-tests` | Unitaires ✓ | `integration-test-report.html` |
| 3️⃣ | `api-tests` | Intégration ✓ | `api-test-report.html` |
| 4️⃣ | `ui-tests` | API ✓ | `ui-test-report.html` + screenshots |
| 5️⃣ | `load-tests` | UI ✓ | `load-test-report.html` |
| 6️⃣ | `security-scan` | Charge ✓ | `security-report/` (HTML/XML/JSON) |
| ✅ | `all-tests-passed` | Tous ✓ | — |

### Pousser sur GitHub

**Documentation complète** : voir [GITHUB_ACTIONS.md](./GITHUB_ACTIONS.md)

Étapes rapides :
```bash
# 1. Créer un dépôt GitHub (https://github.com/new)

# 2. Initialiser et pousser localement
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/<USERNAME>/NexusGame.git
git branch -M main
git push -u origin main

# 3. Vérifier sur GitHub
# Actions → dernier workflow → tous les jobs verts ✓
```

### Accéder aux rapports

**Sur GitHub** :
1. Aller sur Actions
2. Cliquer sur le workflow le plus récent
3. Scroll vers le bas → **Artifacts**
4. Télécharger les rapports par job

**Exemple de structure d'artefacts** :
```
unit-test-report.html
integration-test-report.html
api-test-report.html
ui-test-report.html
ui-screenshots/
load-test-report.html
security-report/report_html.html
security-report/report_xml.xml
security-report/report_json.json
```

---

## 🧪 Lancer les tests

### Installation

```bash
# Installation
pip install -r requirements.txt
playwright install chromium
npm install -g newman newman-reporter-htmlextra
pip install locust

# Démarrer l'API
python app_gamestore.py
```

### Tests locaux

```bash
# Tests unitaires
pytest tests/test_unit.py -v --cov=app_gamestore --cov-report=html

# Tests d'intégration
pytest tests/test_integration.py -v -m integration

# Tests UI
pytest tests/test_ui.py -v --headed

# Collection Newman
newman run tests/gamestore_collection.json --env-var "base_url=http://localhost:5000" --reporters cli,htmlextra

# Tests de charge
locust -f tests/locust_gamestore.py --host=http://localhost:5000 --headless -u 20 -r 2 --run-time 30s
```

---

## Mes choix techniques
## Tests de charge — Locust
locust -f tests/locust_gamestore.py --host=http://localhost:5000
### Scénario
- Utilisateurs simulés : 50
- Spawn rate : 5/s
- Durée : 60 secondes

### Résultats observés

| Endpoint         | Req/s | p95 (ms) | Erreurs |
|------------------|-------|----------|---------|
| GET /games       | 216    | 2100ms    | 0%      |
| GET /games/featured | 48 | 2100ms    | 0%      |
| GET /games/[id]  | 91    | 2000ms     | 1.1%      |
| POST /games      | 45    | 2100ms    | 0%      |

### Seuils définis
- p95 cible : < 3000ms pour tous les endpoints
- Taux d'erreur cible : < 10%

### Observations
- L'API tient correctement jusqu'à 60 utilisateurs simultanés
- L'endpoint le plus lent est POST /games 
### Pyramide de tests adoptée

La pyramide de test que j'ai adoptée est 70% test unitaires + 20% test d'integratrion + 10% E2E UI 
- Pourquoi : Cette repartition maximise la detections de bugs tout en minimisant les couts de developpment. les test unitaires se charges de detecter 70-80% des bugs , les test d'integration Vérifie que les composants communiquent correctement et les test E2E verifie le comportment end to end.

### Pipeline CI vs local

**En CI (GitHub Actions)** :
-  **Tous les tests** s'exécutent automatiquement à chaque push/PR
-  **Tests unitaires** (50+ tests, BDD fraîche à chaque)
-  **Tests d'intégration** (serveur réel, concurrence, threading)
-  **Tests API** (13 requêtes Newman chaînées avec variables)
-  **Tests UI** (3 parcours utilisateur + screenshots en cas d'échec)
-  **Tests de charge** (50 utilisateurs simultanés, 60s, Locust)
-  **Scan de sécurité** (OWASP ZAP baseline)
-  **Artefacts** (rapports HTML/XML/JSON, téléchargeables 90 jours)
-  **Immuable** : même environnement pour tous (Ubuntu 22.04)

**En local (développement)** :
-  **Tests rapides** : unitaires uniquement (30s) pour feedback immédiat
-  **Débogage** : erreurs visibles en direct, logs détaillés
-  **Itération rapide** : pytest --watch ou modifications en live
-  **Tests manuels** : UI avec `--headed` pour voir le navigateur
-  **Flexibilité** : modifier les seuils, ignorer certains tests

**Pourquoi cette séparation ?**
CI = **validation finale** (qualité garantie), Local = **développement rapide** (feedback immédiat). La CI est stricte et exhaustive, le local permet l'expérimentation.

### Mes choix libres

Au de la les tests obligatoires (unitaires, intégration, API, UI, charge, sécurité), voici les choix que j'ai choisi :

####  **Test d'intégration Threading & Concurrence**
- **Ce qu'il teste** : Scénario réaliste où plusieurs utilisateurs créent/suppriment des jeux simultanément
- **Pourquoi** : Les bugs de concurrence (race conditions, deadlocks) ne sont détectables que sous charge réelle
- **Fichier** : `tests/test_integration.py` → `test_concurrent_game_creation`
- **Bénéfice** : Valide que SQLite + Flask gèrent correctement les requêtes concurrentes

####  **Test Locust : Scénario multi-tâche réaliste**
- **Ce qu'il teste** : 7 scénarios critiques pondérés par probabilité réelle :
  - **Consulter catalogue** (5x) : liste complète des jeux
  - **Filtrer par genre** (3x) : genre aléatoire parmi 6 options
  - **Consulter jeu individuel** (2x) : ID aléatoire 1-20
  - **Health check** (2x) : vérifier la disponibilité
  - **Consulter stats** (1x) : endpoint lourd en calcul
  - **Consulter featured** (1x) : endpoint optimisé (jeux top-rated)
  - **Créer puis supprimer un jeu** (1x) : scénario admin
- **Pourquoi** : Simule un trafic réaliste, pas juste des GET /health
- **Fichier** : `tests/locust_gamestore.py` → `GameStoreUser`
- **Bénéfice** : Identifie les endpoints lents (POST /games est slowest) et les goulots

####  **Test UI : 3 parcours utilisateur complets (Page Object Model)**
- **Ce qu'il teste** : Comportement end-to-end réel via Playwright
  1. **Navigation** : page accueil → clic jeu → vérif détail → retour
  2. **Ajout** : modal → formulaire → soumission → vérif liste
  3. **Recherche/Filtre** : barre search → filtre genre → vérif résultats
- **Pourquoi** : POM rend les tests maintenables ; très peu de changements de sélecteurs
- **Fichier** : `tests/test_ui.py` → `TestParcoursUtilisateur`
- **Bénéfice** : Détermine si l'app reste utilisable; captures d'écran en cas d'échec

####  **Collection Newman/Postman : 13 requêtes chaînées**
- **Ce qu'il teste** : Chaînage de variables (ID créé d'une réponse → utilisé dans la suivante)
  - Health check, listing, création, modification, suppression, recherche, stats
  - Cas d'erreur : 409 (dupliqué), 400 (invalide), 404 (introuvable)
- **Pourquoi** : Newman s'exécute en CLI (idéal pour CI) ; assertions complexes en JavaScript
- **Fichier** : `tests/gamestore_collection.json`
- **Bénéfice** : Valide le comportement API exact ; rapport HTML lisible par non-techniciens

####  **Scan OWASP ZAP : Baseline de sécurité**
- **Ce qu'il teste** : Cherche les vulnérabilités courantes (injection, XSS, CSRF, etc.)
  - Cookies sans HttpOnly/Secure
  - Lack of X-Frame-Options (clickjacking)
  - Révélation d'informations via headers
- **Pourquoi** : Baseline ZAP est léger (2-3 min), détecte 80% des vulns courant
- **Fichier** : `.github/workflows/zap-scan.yml` → job `security-scan`
- **Bénéfice** : Prévient les failles OWASP Top 10 simples

####  **Pyramide de tests : 70/20/10**
- **Implementation** :
  - 70% : `test_unit.py` → 50+ tests unitaires (logique métier)
  - 20% : `test_integration.py` + Locust → interaction composants
  - 10% : `test_ui.py` → parcours utilisateur E2E
- **Justification** : Maximise détection de bugs / coûts. Unitaires trouvent 70-80% des bugs ; intégration vérifie communication ; UI valide le comportement réel

---

## Investigation de l'API

<!-- Ce que vous avez observé en testant l'API.
     Comportements inattendus, hypothèses, ce que vos tests révèlent. -->

---

## Pipeline CI/CD

<!-- État de votre pipeline sur GitHub Actions. -->

---

## Ce que j'ai appris

<!-- Optionnel. -->
