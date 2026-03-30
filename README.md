# 📷 Portfolio Photographe

Portfolio professionnel complet avec front-end public et panneau d'administration.

---

## 🗂️ Structure des fichiers

```
photographer-portfolio/
├── app.py               ← Application Flask principale
├── models.py            ← Modèles de base de données
├── config.py            ← Configuration
├── requirements.txt     ← Dépendances Python
├── .env.example         ← Variables d'environnement (à copier en .env)
├── static/
│   ├── css/
│   │   ├── public.css   ← Style du site public
│   │   └── admin.css    ← Style du panneau admin
│   ├── js/
│   │   ├── public.js    ← JavaScript public
│   │   └── admin.js     ← JavaScript admin
│   └── uploads/         ← Dossier des uploads (créé automatiquement)
│       ├── photos/
│       └── profile/
└── templates/
    ├── base_public.html
    ├── base_admin.html
    ├── public/
    │   ├── index.html
    │   ├── gallery.html
    │   ├── projects.html
    │   ├── project_detail.html
    │   └── contact.html
    └── admin/
        ├── login.html
        ├── dashboard.html
        ├── profile.html
        ├── gallery.html
        ├── projects.html
        ├── experiences.html
        ├── formations.html
        ├── contact_info.html
        └── messages.html
```

---

## 🚀 Installation locale

### 1. Créer l'environnement Python
```bash
cd photographer-portfolio
python -m venv venv
source venv/bin/activate        # Linux / Mac
# OU
venv\Scripts\activate           # Windows
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Configurer l'environnement
```bash
cp .env.example .env
# Éditez .env et changez les valeurs :
# SECRET_KEY=votre-cle-secrete
# ADMIN_USERNAME=admin
# ADMIN_PASSWORD=votre-mot-de-passe
```

### 4. Lancer l'application
```bash
python app.py
```

Accédez à :
- **Site public** → http://localhost:5000
- **Admin** → http://localhost:5000/admin

---

## 🌐 Déploiement sur PythonAnywhere

1. Uploadez tous les fichiers via l'onglet **Files** de PythonAnywhere
2. Dans le **Bash console** :
   ```bash
   pip install -r requirements.txt --user
   python app.py   # pour créer la base de données
   ```
3. Onglet **Web** → Add a new web app → Flask → Python 3.10
4. Modifiez le **WSGI file** :
   ```python
   import sys
   sys.path.insert(0, '/home/VOTRE_USERNAME/photographer-portfolio')
   from app import app as application
   # Initialiser la DB au 1er démarrage :
   from app import init_db
   init_db()
   ```
5. Dans **Static files** :
   - URL: `/static/` → Dossier: `/home/VOTRE_USERNAME/photographer-portfolio/static`
6. Rechargez l'app → le site est en ligne !

---

## 🔐 Connexion admin par défaut

- **URL** : `/admin/login`
- **Identifiant** : `admin`
- **Mot de passe** : `admin123`

> ⚠️ **Changez le mot de passe immédiatement** depuis le tableau de bord après la première connexion !

---

## ✨ Fonctionnalités

### Partie publique
- Page d'accueil avec hero, à propos, projets, expériences, formations
- Galerie photos avec filtres par catégorie et lightbox
- Page projets avec détail de chaque projet
- Formulaire de contact

### Partie admin
| Section | Ce qu'on peut faire |
|---|---|
| **Profil** | Nom, structure, années d'expérience, à propos, photo |
| **Galerie** | Upload multiple de photos, catégorisation, masquer/afficher |
| **Projets** | CRUD complet, couverture, galerie liée |
| **Expériences** | Timeline de parcours professionnel |
| **Formations** | Diplômes et certifications |
| **Coordonnées** | WhatsApp, téléphone, email, Instagram, Facebook, TikTok... |
| **Messages** | Voir, marquer lu, supprimer les messages du formulaire |
