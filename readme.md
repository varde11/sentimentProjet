Une solution complète d'analyse de sentiment pour avis clients, déployée en production. Ce projet démontre une architecture **hybride** optimisée pour réduire les coûts d'inférence tout en maintenant une haute précision grâce au Deep Learning.

🔗 **[Voir la Démo Live (Streamlit)](https://varde11-sentiment-frontend.streamlit.app/)**
🔗 **[Voir l'API (Swagger UI)](https://varde11-sentiment-backend.hf.space/docs)**

---

## 🏗️ Architecture & Points Forts

Ce projet n'est pas un simple notebook, c'est une application micro-services orchestrée.

### 1. Stratégie de Modèle "Cascade" (Cost Optimization)
Pour optimiser la latence et les ressources CPU, j'ai implémenté une logique de filtrage :
* **Niveau 1 (Rapide) :** Un modèle `TF-IDF + Logistic Regression` traite 100% des requêtes. Il est ultra-rapide et gère les cas simples.

* **Niveau 2 (Précis) :** Si le premier modèle n'est pas certain de sa réponse, le label, la requête est passée à un modèle Deep Learning **XLM-RoBERTa** (Fine-tuné), si même lui n'est pas certain, alors le label 'uncertain' est attribué au commentaire.

* **Résultat :** Une API rapide qui ne consomme des ressources lourdes que lorsque c'est nécessaire.



### 3. Architecture DevOps
* **Backend :** FastAPI (Expose les modèles et gère la logique métier).
* **Frontend :** Streamlit (Interface utilisateur pour les clients et l'administration).
* **Database :** PostgreSQL (Hébergé sur Neon.tech) pour la persistance des clients, produits et historiques.
* **CI/CD :** Pipeline GitHub Actions qui teste le code (`pytest`), construit les images Docker multi-services, et les pousse sur DockerHub automatiquement.
* **Déploiement :** Docker (Hugging Face Spaces pour le backend, Streamlit Cloud pour le frontend).

---

## 🛠️ Tech Stack

| Catégorie | Technologies |
| :--- | :--- |
| **Langage** | Python 3.11 |
| **ML / DL** | Scikit-learn, Hugging Face Transformers, PyTorch |
| **Backend** | FastAPI, SQLAlchemy, Pydantic, Uvicorn |
| **Frontend** | Streamlit, Pandas |
| **Database** | PostgreSQL 15 (Neon Tech) |
| **Infrastructure** | Docker, Docker Compose |
| **CI/CD** | GitHub Actions, Docker Hub |

---

## 🚀 Installation & Lancement Local

Si vous souhaitez faire tourner le projet sur votre machine :

### Prérequis
* Docker & Docker Compose installés.
* Git installé.

### 1. Cloner le projet

```bash
git clone [cliquez ici](https://github.com/varde11/https://github.com/varde11/sentimentProjet)
cd https://github.com/varde11/sentimentProjet

```
Ensuire, vous devez créer un dossier .env pour les variables d'environnement dans laquel vous pouvez mettre:

POSTGRES_USER = user
POSTGRES_PASSWORD = password
DATABASE_URL = postgresql://user:password@db:5432/sentiment_db
BASE_URL=http://localhost:8000

Lancer la commande ```bash docker-compose up --build``` ; et voilà!!!

Si vous renconctrez un problème, vous pouvez me joindre à l'adresse suivant :
[electronvannel@gmail.com](electronvannel@gmail.com)