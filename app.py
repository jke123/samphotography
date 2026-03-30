import os
import uuid
import base64
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, Admin, SiteConfig, Experience, Formation, Project, Photo, ContactInfo, Message

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "admin_login"
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "warning"

IMGBB_API_KEY = os.getenv("IMGBB_API_KEY", "")

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]


def save_image(file, folder=None, folder_name="photos"):
    """
    Upload l'image originale vers ImgBB (sans compression, qualité intacte).
    Fallback local si IMGBB_API_KEY absent.
    """
    if not file or not file.filename or not allowed_file(file.filename):
        return None

    file.seek(0)
    img_bytes = file.read()

    # ── ImgBB upload (image originale, qualité 100%) ──
    if IMGBB_API_KEY:
        try:
            encoded = base64.b64encode(img_bytes).decode("utf-8")
            response = requests.post(
                "https://api.imgbb.com/1/upload",
                data={
                    "key": IMGBB_API_KEY,
                    "image": encoded,
                    "name": f"portfolio_{uuid.uuid4().hex[:8]}",
                },
                timeout=120
            )
            data = response.json()
            if data.get("success"):
                return data["data"]["url"]
            else:
                app.logger.error(f"ImgBB error: {data}")
                return None
        except Exception as e:
            app.logger.error(f"ImgBB upload error: {e}")
            return None

    # ── Fallback local ──
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, filename), "wb") as f:
        f.write(img_bytes)
    return filename


def image_url(value, subfolder="photos"):
    """Retourne l'URL complète d'une image (ImgBB ou locale)."""
    if not value:
        return ""
    if value.startswith("http"):
        return value
    return url_for("static", filename=f"uploads/{subfolder}/{value}")


app.jinja_env.globals["image_url"] = image_url


def get_config(key, default=""):
    row = SiteConfig.query.filter_by(key=key).first()
    return row.value if row else default


def set_config(key, value):
    row = SiteConfig.query.filter_by(key=key).first()
    if row:
        row.value = value
    else:
        db.session.add(SiteConfig(key=key, value=value))
    db.session.commit()


def get_all_config():
    rows = SiteConfig.query.all()
    return {r.key: r.value for r in rows}


def unread_count():
    return Message.query.filter_by(is_read=False).count()


# ─────────────────────────────────────────────
#  PUBLIC ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def index():
    cfg = get_all_config()
    projects = Project.query.filter_by(visible=True).order_by(Project.order.asc()).limit(6).all()
    experiences = Experience.query.filter_by(visible=True).order_by(Experience.order.asc()).all()
    formations = Formation.query.filter_by(visible=True).order_by(Formation.order.asc()).all()
    contacts = ContactInfo.query.filter_by(visible=True).order_by(ContactInfo.order.asc()).all()
    return render_template("public/index.html", cfg=cfg, projects=projects,
                           experiences=experiences, formations=formations, contacts=contacts)


@app.route("/gallery")
def gallery():
    cfg = get_all_config()
    category = request.args.get("cat", "all")
    if category == "all":
        photos = Photo.query.filter_by(visible=True).order_by(Photo.order.asc(), Photo.created_at.desc()).all()
    else:
        photos = Photo.query.filter_by(visible=True, category=category).order_by(Photo.order.asc(), Photo.created_at.desc()).all()
    categories = db.session.query(Photo.category).filter_by(visible=True).distinct().all()
    categories = [c[0] for c in categories]
    contacts = ContactInfo.query.filter_by(visible=True).order_by(ContactInfo.order.asc()).all()
    return render_template("public/gallery.html", cfg=cfg, photos=photos,
                           categories=categories, current_cat=category, contacts=contacts)


@app.route("/projects")
def projects():
    cfg = get_all_config()
    all_projects = Project.query.filter_by(visible=True).order_by(Project.order.asc()).all()
    contacts = ContactInfo.query.filter_by(visible=True).order_by(ContactInfo.order.asc()).all()
    return render_template("public/projects.html", cfg=cfg, projects=all_projects, contacts=contacts)


@app.route("/project/<int:pid>")
def project_detail(pid):
    cfg = get_all_config()
    project = Project.query.get_or_404(pid)
    if not project.visible:
        return redirect(url_for("projects"))
    photos = Photo.query.filter_by(project_id=pid, visible=True).order_by(Photo.order.asc()).all()
    contacts = ContactInfo.query.filter_by(visible=True).order_by(ContactInfo.order.asc()).all()
    return render_template("public/project_detail.html", cfg=cfg, project=project, photos=photos, contacts=contacts)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    cfg = get_all_config()
    contacts = ContactInfo.query.filter_by(visible=True).order_by(ContactInfo.order.asc()).all()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        subject = request.form.get("subject", "").strip()
        body = request.form.get("body", "").strip()
        if not name or not body:
            flash("Le nom et le message sont obligatoires.", "danger")
        else:
            msg = Message(name=name, email=email, phone=phone, subject=subject, body=body)
            db.session.add(msg)
            db.session.commit()
            flash("Votre message a bien été envoyé. Merci !", "success")
            return redirect(url_for("contact"))
    return render_template("public/contact.html", cfg=cfg, contacts=contacts)


# ─────────────────────────────────────────────
#  ADMIN ROUTES
# ─────────────────────────────────────────────

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            login_user(admin)
            return redirect(url_for("admin_dashboard"))
        flash("Identifiants incorrects.", "danger")
    return render_template("admin/login.html")


@app.route("/admin/logout")
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for("admin_login"))


@app.route("/admin/")
@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    stats = {
        "photos": Photo.query.count(),
        "projects": Project.query.count(),
        "messages": Message.query.count(),
        "unread": unread_count(),
        "experiences": Experience.query.count(),
        "formations": Formation.query.count(),
    }
    recent_messages = Message.query.order_by(Message.created_at.desc()).limit(5).all()
    return render_template("admin/dashboard.html", stats=stats,
                           recent_messages=recent_messages, unread=unread_count())


@app.route("/admin/profile", methods=["GET", "POST"])
@login_required
def admin_profile():
    if request.method == "POST":
        fields = ["photographer_name", "structure_name", "years_experience",
                  "about_short", "about_full", "specialties"]
        for f in fields:
            set_config(f, request.form.get(f, ""))
        profile_file = request.files.get("profile_photo")
        if profile_file and profile_file.filename:
            url = save_image(profile_file, app.config["PROFILE_FOLDER"], "profile")
            if url:
                set_config("profile_photo", url)
        flash("Profil mis à jour avec succès.", "success")
        return redirect(url_for("admin_profile"))
    cfg = get_all_config()
    return render_template("admin/profile.html", cfg=cfg, unread=unread_count())


@app.route("/admin/experiences")
@login_required
def admin_experiences():
    experiences = Experience.query.order_by(Experience.order.asc()).all()
    return render_template("admin/experiences.html", experiences=experiences, unread=unread_count())


@app.route("/admin/experiences/add", methods=["POST"])
@login_required
def admin_exp_add():
    exp = Experience(
        title=request.form.get("title", ""),
        company=request.form.get("company", ""),
        description=request.form.get("description", ""),
        year_start=request.form.get("year_start", ""),
        year_end=request.form.get("year_end", ""),
        order=int(request.form.get("order", 0)),
        visible=bool(request.form.get("visible"))
    )
    db.session.add(exp)
    db.session.commit()
    flash("Expérience ajoutée.", "success")
    return redirect(url_for("admin_experiences"))


@app.route("/admin/experiences/edit/<int:eid>", methods=["POST"])
@login_required
def admin_exp_edit(eid):
    exp = Experience.query.get_or_404(eid)
    exp.title = request.form.get("title", exp.title)
    exp.company = request.form.get("company", exp.company)
    exp.description = request.form.get("description", exp.description)
    exp.year_start = request.form.get("year_start", exp.year_start)
    exp.year_end = request.form.get("year_end", exp.year_end)
    exp.order = int(request.form.get("order", exp.order))
    exp.visible = bool(request.form.get("visible"))
    db.session.commit()
    flash("Expérience mise à jour.", "success")
    return redirect(url_for("admin_experiences"))


@app.route("/admin/experiences/delete/<int:eid>")
@login_required
def admin_exp_delete(eid):
    db.session.delete(Experience.query.get_or_404(eid))
    db.session.commit()
    flash("Expérience supprimée.", "success")
    return redirect(url_for("admin_experiences"))


@app.route("/admin/formations")
@login_required
def admin_formations():
    formations = Formation.query.order_by(Formation.order.asc()).all()
    return render_template("admin/formations.html", formations=formations, unread=unread_count())


@app.route("/admin/formations/add", methods=["POST"])
@login_required
def admin_form_add():
    form = Formation(
        title=request.form.get("title", ""),
        institution=request.form.get("institution", ""),
        year=request.form.get("year", ""),
        description=request.form.get("description", ""),
        order=int(request.form.get("order", 0)),
        visible=bool(request.form.get("visible"))
    )
    db.session.add(form)
    db.session.commit()
    flash("Formation ajoutée.", "success")
    return redirect(url_for("admin_formations"))


@app.route("/admin/formations/edit/<int:fid>", methods=["POST"])
@login_required
def admin_form_edit(fid):
    formation = Formation.query.get_or_404(fid)
    formation.title = request.form.get("title", formation.title)
    formation.institution = request.form.get("institution", formation.institution)
    formation.year = request.form.get("year", formation.year)
    formation.description = request.form.get("description", formation.description)
    formation.order = int(request.form.get("order", formation.order))
    formation.visible = bool(request.form.get("visible"))
    db.session.commit()
    flash("Formation mise à jour.", "success")
    return redirect(url_for("admin_formations"))


@app.route("/admin/formations/delete/<int:fid>")
@login_required
def admin_form_delete(fid):
    db.session.delete(Formation.query.get_or_404(fid))
    db.session.commit()
    flash("Formation supprimée.", "success")
    return redirect(url_for("admin_formations"))


CATEGORIES = [
    ("shoot", "Séance Photo"),
    ("mariage", "Mariage"),
    ("enterrement", "Enterrement"),
    ("evenement", "Événement"),
    ("portrait", "Portrait"),
    ("autre", "Autre"),
]


@app.route("/admin/gallery")
@login_required
def admin_gallery():
    photos = Photo.query.order_by(Photo.created_at.desc()).all()
    return render_template("admin/gallery.html", photos=photos, categories=CATEGORIES, unread=unread_count())


@app.route("/admin/gallery/add", methods=["POST"])
@login_required
def admin_photo_add():
    files = request.files.getlist("photos")
    category = request.form.get("category", "autre")
    title = request.form.get("title", "")
    description = request.form.get("description", "")
    project_id = request.form.get("project_id") or None
    count = 0
    for f in files:
        if f and f.filename:
            file_url = save_image(f, app.config["PHOTOS_FOLDER"], "photos")
            if file_url:
                photo = Photo(filename=file_url, title=title, description=description,
                              category=category, project_id=project_id)
                db.session.add(photo)
                count += 1
    db.session.commit()
    flash(f"{count} photo(s) ajoutée(s).", "success")
    return redirect(url_for("admin_gallery"))


@app.route("/admin/gallery/delete/<int:pid>")
@login_required
def admin_photo_delete(pid):
    photo = Photo.query.get_or_404(pid)
    if not photo.filename.startswith("http"):
        try:
            os.remove(os.path.join(app.config["PHOTOS_FOLDER"], photo.filename))
        except Exception:
            pass
    db.session.delete(photo)
    db.session.commit()
    flash("Photo supprimée.", "success")
    return redirect(url_for("admin_gallery"))


@app.route("/admin/gallery/toggle/<int:pid>")
@login_required
def admin_photo_toggle(pid):
    photo = Photo.query.get_or_404(pid)
    photo.visible = not photo.visible
    db.session.commit()
    return redirect(url_for("admin_gallery"))


@app.route("/admin/projects")
@login_required
def admin_projects():
    projects = Project.query.order_by(Project.order.asc()).all()
    return render_template("admin/projects.html", projects=projects, categories=CATEGORIES, unread=unread_count())


@app.route("/admin/projects/add", methods=["POST"])
@login_required
def admin_project_add():
    cover_url = ""
    cover_file = request.files.get("cover_photo")
    if cover_file and cover_file.filename:
        cover_url = save_image(cover_file, app.config["PHOTOS_FOLDER"], "photos") or ""
    project = Project(
        title=request.form.get("title", ""),
        description=request.form.get("description", ""),
        category=request.form.get("category", "autre"),
        cover_photo=cover_url,
        date=request.form.get("date", ""),
        order=int(request.form.get("order", 0)),
        visible=bool(request.form.get("visible"))
    )
    db.session.add(project)
    db.session.commit()
    flash("Projet ajouté.", "success")
    return redirect(url_for("admin_projects"))


@app.route("/admin/projects/edit/<int:pid>", methods=["POST"])
@login_required
def admin_project_edit(pid):
    project = Project.query.get_or_404(pid)
    project.title = request.form.get("title", project.title)
    project.description = request.form.get("description", project.description)
    project.category = request.form.get("category", project.category)
    project.date = request.form.get("date", project.date)
    project.order = int(request.form.get("order", project.order))
    project.visible = bool(request.form.get("visible"))
    cover_file = request.files.get("cover_photo")
    if cover_file and cover_file.filename:
        url = save_image(cover_file, app.config["PHOTOS_FOLDER"], "photos")
        if url:
            project.cover_photo = url
    db.session.commit()
    flash("Projet mis à jour.", "success")
    return redirect(url_for("admin_projects"))


@app.route("/admin/projects/delete/<int:pid>")
@login_required
def admin_project_delete(pid):
    project = Project.query.get_or_404(pid)
    db.session.delete(project)
    db.session.commit()
    flash("Projet supprimé.", "success")
    return redirect(url_for("admin_projects"))


CONTACT_TYPES = [
    ("whatsapp", "WhatsApp", "fab fa-whatsapp"),
    ("phone", "Téléphone", "fas fa-phone"),
    ("email", "Email", "fas fa-envelope"),
    ("instagram", "Instagram", "fab fa-instagram"),
    ("facebook", "Facebook", "fab fa-facebook"),
    ("tiktok", "TikTok", "fab fa-tiktok"),
    ("youtube", "YouTube", "fab fa-youtube"),
    ("autre", "Autre", "fas fa-link"),
]


@app.route("/admin/contact-info")
@login_required
def admin_contact_info():
    contacts = ContactInfo.query.order_by(ContactInfo.order.asc()).all()
    return render_template("admin/contact_info.html", contacts=contacts,
                           contact_types=CONTACT_TYPES, unread=unread_count())


@app.route("/admin/contact-info/add", methods=["POST"])
@login_required
def admin_contact_add():
    ctype = request.form.get("type", "autre")
    icon = next((t[2] for t in CONTACT_TYPES if t[0] == ctype), "fas fa-link")
    ci = ContactInfo(
        type=ctype,
        label=request.form.get("label", ""),
        value=request.form.get("value", ""),
        icon=icon,
        order=int(request.form.get("order", 0)),
        visible=bool(request.form.get("visible"))
    )
    db.session.add(ci)
    db.session.commit()
    flash("Contact ajouté.", "success")
    return redirect(url_for("admin_contact_info"))


@app.route("/admin/contact-info/edit/<int:cid>", methods=["POST"])
@login_required
def admin_contact_edit(cid):
    ci = ContactInfo.query.get_or_404(cid)
    ci.type = request.form.get("type", ci.type)
    ci.label = request.form.get("label", ci.label)
    ci.value = request.form.get("value", ci.value)
    ci.icon = next((t[2] for t in CONTACT_TYPES if t[0] == ci.type), "fas fa-link")
    ci.order = int(request.form.get("order", ci.order))
    ci.visible = bool(request.form.get("visible"))
    db.session.commit()
    flash("Contact mis à jour.", "success")
    return redirect(url_for("admin_contact_info"))


@app.route("/admin/contact-info/delete/<int:cid>")
@login_required
def admin_contact_delete(cid):
    db.session.delete(ContactInfo.query.get_or_404(cid))
    db.session.commit()
    flash("Contact supprimé.", "success")
    return redirect(url_for("admin_contact_info"))


@app.route("/admin/messages")
@login_required
def admin_messages():
    msgs = Message.query.order_by(Message.created_at.desc()).all()
    return render_template("admin/messages.html", messages=msgs, unread=unread_count())


@app.route("/admin/messages/read/<int:mid>")
@login_required
def admin_message_read(mid):
    msg = Message.query.get_or_404(mid)
    msg.is_read = True
    db.session.commit()
    return redirect(url_for("admin_messages"))


@app.route("/admin/messages/delete/<int:mid>")
@login_required
def admin_message_delete(mid):
    db.session.delete(Message.query.get_or_404(mid))
    db.session.commit()
    flash("Message supprimé.", "success")
    return redirect(url_for("admin_messages"))


@app.route("/admin/change-password", methods=["POST"])
@login_required
def admin_change_password():
    old_pw = request.form.get("old_password", "")
    new_pw = request.form.get("new_password", "")
    if not current_user.check_password(old_pw):
        flash("Ancien mot de passe incorrect.", "danger")
    elif len(new_pw) < 6:
        flash("Le nouveau mot de passe doit contenir au moins 6 caractères.", "danger")
    else:
        current_user.set_password(new_pw)
        db.session.commit()
        flash("Mot de passe modifié avec succès.", "success")
    return redirect(url_for("admin_dashboard"))


# ─────────────────────────────────────────────
#  Init DB
# ─────────────────────────────────────────────

def init_db():
    with app.app_context():
        db.create_all()
        if not Admin.query.first():
            admin = Admin(username=app.config["ADMIN_USERNAME"])
            admin.set_password(app.config["ADMIN_PASSWORD"])
            db.session.add(admin)
            db.session.commit()
            print(f"[INIT] Admin créé → {app.config['ADMIN_USERNAME']}")


init_db()

if __name__ == "__main__":
    app.run(debug=False)


# ─────────────────────────────────────────────
#  Route de diagnostic (admin seulement)
# ─────────────────────────────────────────────

@app.route("/admin/diagnostic")
@login_required
def admin_diagnostic():
    from flask import jsonify

    # Test base de données
    try:
        count_photos = Photo.query.count()
        first_photo = Photo.query.first()
        db_status = "OK"
        db_type = "PostgreSQL" if "postgresql" in app.config["SQLALCHEMY_DATABASE_URI"] else "SQLite"
        sample_url = first_photo.filename if first_photo else "aucune photo"
        url_type = "ImgBB OK" if sample_url.startswith("http") else "Local - NON PERSISTANT"
    except Exception as e:
        db_status = f"ERREUR: {e}"
        db_type = "inconnu"
        count_photos = 0
        sample_url = ""
        url_type = ""

    imgbb_key = os.getenv("IMGBB_API_KEY", "")
    db_url_raw = os.getenv("DATABASE_URL", "")

    return jsonify({
        "base_de_donnees": {
            "statut": db_status,
            "type": db_type,
            "DATABASE_URL": (db_url_raw[:25] + "...") if db_url_raw else "MANQUANT",
            "nombre_photos": count_photos,
            "exemple_url": sample_url,
            "type_stockage": url_type
        },
        "imgbb": {
            "cle_presente": bool(imgbb_key),
            "longueur_cle": len(imgbb_key)
        }
    })
