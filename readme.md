# 📊 E-commerce Sentiment Analysis & Alerting System

Une solution complète d'analyse de sentiment pour avis clients, déployée en production. Ce projet démontre une architecture **hybride** optimisée pour réduire les coûts d'inférence, couplée à un système d'alerte et de monitoring en temps réel pour les équipes métier.

🔗 **[Voir l'Interface E-commerce ](https://varde11-ecommerce.hf.space)**

🔗 **[Voir l'Interface Admin & Monitoring ](https://varde11-console-sentiment.hf.space)**


---

##  Architecture & Points Forts

Ce projet n'est pas un simple notebook de Data Science, c'est une application micro-services orchestrée et pensée pour un usage réel (Scale & Cost Optimization).

### 1. Stratégie de Modèle "Cascade" (Cost Optimization)
Pour optimiser la latence et les ressources CPU, j'ai implémenté une logique de filtrage intelligent :
* **Niveau 1 (Rapide) :** Un modèle `TF-IDF + Logistic Regression` traite 100% des requêtes. Il est ultra-rapide et gère les cas évidents.
* **Niveau 2 (Précis) :** Si le premier modèle n'est pas certain de sa réponse, la requête est passée à un modèle Deep Learning **XLM-RoBERTa** (Fine-tuné).
* **Niveau 3 (Human-in-the-loop) :** Si l'IA n'est toujours pas certaine, le label `uncertain` est attribué. Un humain peut alors valider ou corriger l'étiquette depuis la console administrateur pour ré-entraîner ou garantir la qualité des données.

### 2. Monitoring & Détection d'Incidents
L'interface administrateur embarque un système d'alerte métier :
* Détection automatique des pics d'avis négatifs (Volume Spikes).
* Détection de mots-clés critiques (Ex: "arnaque", "dangereux", "cassé").
* File d'attente priorisée (Review Queue) pour que l'équipe sache exactement quel produit nécessite une intervention immédiate (P0, P1, P2).

### 3. Architecture DevOps
* **Backend :** FastAPI (Expose les modèles, interagit avec la BDD et gère la logique métier).
* **Frontends :** Streamlit (Deux interfaces distinctes : un faux site e-commerce et un dashboard administrateur).
* **Database :** PostgreSQL pour la persistance des prédictions, clients et historiques.
* **CI/CD :** Pipeline GitHub Actions qui teste le code, construit les images Docker multi-services, et les pousse sur Docker Hub automatiquement.
* **Déploiement :** Dockerisés et hébergés de manière indépendante sur **Hugging Face Spaces**.

---

## Tech Stack

| Catégorie | Technologies |
| :--- | :--- |
| **Langage** | Python 3.11 |
| **ML / DL** | Scikit-learn, Hugging Face Transformers, PyTorch |
| **Backend** | FastAPI, SQLAlchemy, Pydantic, Uvicorn |
| **Frontend** | Streamlit, Pandas |
| **Database** | PostgreSQL 15 |
| **Infrastructure** | Docker, Docker Compose |
| **CI/CD** | GitHub Actions, Docker Hub |

---

##  Installation & Lancement Local

Si vous souhaitez faire tourner le projet complet sur votre machine (Backend + DB + Les 2 UIs) :

### Prérequis
* Docker & Docker Compose installés.
* Git installé.

### 1. Cloner le projet

```bash
git clone [https://github.com/varde11/sentimentProjet.git](https://github.com/varde11/sentimentProjet.git)
cd sentimentProjet




Configuration du dossier .env

POSTGRES_USER=user
POSTGRES_PASSWORD=password
DATABASE_URL=postgresql://user:password@db:5432/sentiment_db
BASE_URL=http://localhost:8000
API_URL=http://localhost:8000


Lancement de docker compose

docker compose up -d --build
