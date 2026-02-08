#!/usr/bin/env python3
"""PeopleWiki - 人物図鑑Webアプリ"""

import os
from datetime import datetime
from urllib.parse import quote
from flask import Flask, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from markupsafe import escape
import cloudinary
import cloudinary.uploader

app = Flask(__name__)

# Cloudinary 設定 (環境変数 CLOUDINARY_URL で自動設定される)
# 形式: cloudinary://API_KEY:API_SECRET@CLOUD_NAME
cloudinary.config(secure=True)

# Render は DATABASE_URL に postgres:// を設定するが、
# SQLAlchemy 2.x は postgresql:// を要求するため置換する
database_url = os.environ.get("DATABASE_URL", "sqlite:///people.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB
db = SQLAlchemy(app)


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

class Person(db.Model):
    __tablename__ = "people"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    organization = db.Column(db.String)
    met_at = db.Column(db.String)
    birthday = db.Column(db.String)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now)

    events = db.relationship("Event", back_populates="person",
                             order_by="desc(Event.event_date)",
                             cascade="all, delete-orphan")


    family_members = db.relationship("FamilyMember",
                                     foreign_keys="FamilyMember.person_id",
                                     back_populates="person",
                                     order_by="FamilyMember.id",
                                     cascade="all, delete-orphan")


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey("people.id"), nullable=False)
    event_date = db.Column(db.String, nullable=False)       # 'YYYY-MM-DD'
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String)                         # Cloudinary URL
    created_at = db.Column(db.DateTime, default=datetime.now)

    person = db.relationship("Person", back_populates="events")


class FamilyMember(db.Model):
    __tablename__ = "family_members"

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey("people.id"), nullable=False)
    name = db.Column(db.String, nullable=False)
    relationship = db.Column(db.String, nullable=False)      # 配偶者, 子供, etc.
    birthday = db.Column(db.String)                           # 'YYYY-MM-DD'
    linked_person_id = db.Column(db.Integer, db.ForeignKey("people.id"))
    created_at = db.Column(db.DateTime, default=datetime.now)

    person = db.relationship("Person", foreign_keys=[person_id],
                             back_populates="family_members")
    linked_person = db.relationship("Person", foreign_keys=[linked_person_id])


with app.app_context():
    db.create_all()
    # Migrate: add linked_person_id if missing (for existing DBs)
    with db.engine.connect() as conn:
        from sqlalchemy import text, inspect
        inspector = inspect(db.engine)
        cols = [c["name"] for c in inspector.get_columns("family_members")]
        if "linked_person_id" not in cols:
            conn.execute(text(
                "ALTER TABLE family_members ADD COLUMN linked_person_id INTEGER REFERENCES people(id)"
            ))
            conn.commit()


# ---------------------------------------------------------------------------
# CSS (shared across all pages)
# ---------------------------------------------------------------------------

CSS = """
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Hiragino Sans",
                 "Noto Sans JP", sans-serif;
    background: #eef2f7;
    color: #2c3e50;
    line-height: 1.6;
  }
  a { color: #3b82c4; text-decoration: none; }
  a:hover { text-decoration: underline; }

  /* Header */
  .header {
    background: linear-gradient(135deg, #2b6cb0, #3b82c4);
    color: #fff;
    padding: 18px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,.15);
  }
  .header-inner {
    max-width: 960px; margin: 0 auto; padding: 0 20px;
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 10px;
  }
  .header h1 { font-size: 1.5rem; letter-spacing: .02em; }
  .header h1 a { color: #fff; }
  .header h1 a:hover { text-decoration: none; }
  .header-nav a {
    color: #d4e5f7; font-size: .95rem; margin-left: 18px;
  }
  .header-nav a:hover { color: #fff; text-decoration: none; }

  /* Container */
  .container { max-width: 960px; margin: 28px auto; padding: 0 20px; }

  /* Search */
  .search-form { margin-bottom: 24px; display: flex; gap: 8px; }
  .search-form input[type="text"] {
    flex: 1; padding: 10px 14px; border: 1px solid #cbd5e1;
    border-radius: 8px; font-size: 1rem; outline: none;
    transition: border .2s;
  }
  .search-form input[type="text"]:focus { border-color: #3b82c4; }
  .search-form button {
    padding: 10px 20px; background: #3b82c4; color: #fff; border: none;
    border-radius: 8px; font-size: 1rem; cursor: pointer;
  }
  .search-form button:hover { background: #2b6cb0; }

  /* Cards */
  .card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 18px;
  }
  .card {
    background: #fff; border-radius: 12px; padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,.06);
    transition: box-shadow .2s, transform .2s;
  }
  .card:hover { box-shadow: 0 4px 16px rgba(0,0,0,.12); transform: translateY(-2px); }
  .card h3 { font-size: 1.15rem; margin-bottom: 6px; }
  .card .meta { font-size: .85rem; color: #64748b; margin-bottom: 8px; }
  .card .notes-preview {
    font-size: .9rem; color: #475569;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
    overflow: hidden;
  }

  /* Detail */
  .detail-card {
    background: #fff; border-radius: 12px; padding: 28px;
    box-shadow: 0 2px 10px rgba(0,0,0,.07);
  }
  .detail-card h2 { font-size: 1.5rem; margin-bottom: 16px; color: #1e3a5f; }
  .detail-row { margin-bottom: 14px; }
  .detail-label { font-size: .8rem; color: #64748b; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 2px; }
  .detail-value { font-size: 1rem; }
  .detail-value.notes { white-space: pre-wrap; }
  .detail-actions { margin-top: 22px; display: flex; gap: 10px; flex-wrap: wrap; }

  /* Forms */
  .form-card {
    background: #fff; border-radius: 12px; padding: 28px;
    box-shadow: 0 2px 10px rgba(0,0,0,.07);
    max-width: 600px; margin: 0 auto;
  }
  .form-card h2 { font-size: 1.35rem; margin-bottom: 20px; color: #1e3a5f; }
  .form-group { margin-bottom: 16px; }
  .form-group label {
    display: block; font-size: .9rem; font-weight: 600; margin-bottom: 4px;
    color: #334155;
  }
  .form-group input, .form-group textarea {
    width: 100%; padding: 10px 12px; border: 1px solid #cbd5e1;
    border-radius: 8px; font-size: 1rem; font-family: inherit;
    outline: none; transition: border .2s;
  }
  .form-group input:focus, .form-group textarea:focus { border-color: #3b82c4; }
  .form-group textarea { min-height: 100px; resize: vertical; }

  /* Buttons */
  .btn {
    display: inline-block; padding: 10px 22px; border-radius: 8px;
    font-size: .95rem; cursor: pointer; border: none; text-align: center;
  }
  .btn-primary { background: #3b82c4; color: #fff; }
  .btn-primary:hover { background: #2b6cb0; text-decoration: none; }
  .btn-secondary { background: #e2e8f0; color: #334155; }
  .btn-secondary:hover { background: #cbd5e1; text-decoration: none; }
  .btn-danger { background: #e74c3c; color: #fff; }
  .btn-danger:hover { background: #c0392b; text-decoration: none; }

  /* Sort bar */
  .sort-bar {
    display: flex; align-items: center; gap: 8px; margin-bottom: 18px;
    flex-wrap: wrap;
  }
  .sort-label { font-size: .85rem; color: #64748b; }
  .sort-btn {
    font-size: .85rem; padding: 5px 14px; border-radius: 20px;
    background: #e2e8f0; color: #475569; transition: all .2s;
  }
  .sort-btn:hover { background: #cbd5e1; text-decoration: none; }
  .sort-btn.active { background: #3b82c4; color: #fff; }
  .sort-btn.active:hover { background: #2b6cb0; text-decoration: none; }

  /* Birthday badge */
  .birthday-meta { color: #7c3aed; }
  .birthday-badge {
    font-size: .75rem; padding: 1px 7px; border-radius: 10px;
    font-weight: 600;
  }
  .birthday-badge.soon { background: #fef3c7; color: #b45309; }
  .birthday-badge.today { background: #fee2e2; color: #dc2626; }

  /* Empty state */
  .empty { text-align: center; padding: 60px 20px; color: #94a3b8; }
  .empty p { font-size: 1.1rem; margin-bottom: 16px; }

  /* Flash */
  .flash {
    max-width: 960px; margin: 16px auto 0; padding: 12px 20px;
    background: #d1fae5; color: #065f46; border-radius: 8px;
    font-size: .95rem;
  }

  /* Section shared */
  .section-card {
    margin-top: 32px;
  }
  .section-header {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 16px; flex-wrap: wrap; gap: 10px;
  }
  .section-header h3 { font-size: 1.2rem; color: #1e3a5f; }

  /* Accordion Timeline */
  .timeline {
    position: relative;
    padding-left: 28px;
  }
  .timeline::before {
    content: '';
    position: absolute; left: 8px; top: 0; bottom: 0;
    width: 3px; background: #cbd5e1; border-radius: 2px;
  }
  .acc-item {
    position: relative;
    margin-bottom: 8px;
  }
  .acc-item::before {
    content: '';
    position: absolute; left: -24px; top: 16px;
    width: 12px; height: 12px; border-radius: 50%;
    background: #3b82c4; border: 3px solid #eef2f7;
    z-index: 1;
  }
  .acc-toggle {
    width: 100%; text-align: left; padding: 12px 16px;
    background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
    cursor: pointer; display: flex; align-items: center; gap: 10px;
    transition: background .2s, box-shadow .2s;
  }
  .acc-toggle:hover { background: #f8fafc; box-shadow: 0 1px 4px rgba(0,0,0,.06); }
  .acc-toggle .acc-arrow {
    transition: transform .2s; font-size: .7rem; color: #94a3b8;
  }
  .acc-toggle .acc-date {
    font-size: .8rem; color: #64748b; font-weight: 600; min-width: 100px;
  }
  .acc-toggle .acc-preview {
    font-size: .9rem; color: #475569;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;
  }
  .acc-body {
    max-height: 0; overflow: hidden;
    transition: max-height .3s ease;
    padding: 0 16px;
  }
  .acc-body-inner {
    padding: 14px 0;
  }
  .acc-item.open .acc-toggle { background: #f0f7ff; border-color: #bdd7f1; border-radius: 10px 10px 0 0; }
  .acc-item.open .acc-arrow { transform: rotate(90deg); }
  .acc-item.open .acc-body { max-height: 600px; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 10px 10px; background: #fff; }
  .acc-content { font-size: .95rem; white-space: pre-wrap; }
  .acc-image { margin-top: 10px; }
  .acc-image img {
    max-width: 100%; max-height: 320px;
    border-radius: 8px; object-fit: cover;
    cursor: pointer; transition: opacity .2s;
  }
  .acc-image img:hover { opacity: .9; }
  .acc-actions { margin-top: 10px; }
  .tl-btn {
    font-size: .78rem; padding: 3px 10px; border-radius: 6px;
    border: none; cursor: pointer;
  }
  .tl-btn-del { background: #fee2e2; color: #dc2626; }
  .tl-btn-del:hover { background: #fecaca; }
  .tl-empty {
    text-align: center; padding: 30px; color: #94a3b8;
    font-size: .95rem;
  }

  /* Family */
  .family-list { display: flex; flex-direction: column; gap: 10px; }
  .family-item {
    display: flex; align-items: center; justify-content: space-between;
    background: #fff; border-radius: 10px; padding: 14px 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,.05);
    flex-wrap: wrap; gap: 8px;
  }
  .family-info { flex: 1; min-width: 0; }
  .family-name { font-size: 1rem; font-weight: 600; color: #2c3e50; }
  a.family-name { color: #3b82c4; }
  a.family-name:hover { text-decoration: underline; }
  .family-link-badge {
    font-size: .7rem; padding: 1px 6px; border-radius: 8px;
    background: #d1fae5; color: #065f46; font-weight: 600;
    margin-left: 6px; vertical-align: middle;
  }
  .family-link-new {
    font-size: .7rem; padding: 1px 6px; border-radius: 8px;
    background: #fef3c7; color: #92400e; font-weight: 600;
    margin-left: 6px; vertical-align: middle;
  }
  .family-reverse {
    font-size: .78rem; color: #64748b; font-style: italic;
    padding: 2px 0;
  }
  .family-rel {
    font-size: .78rem; padding: 2px 8px; border-radius: 10px;
    background: #ede9fe; color: #6d28d9; font-weight: 600;
    margin-left: 8px;
  }
  .family-age {
    font-size: .85rem; color: #64748b; margin-top: 2px;
  }
  .family-empty {
    text-align: center; padding: 24px; color: #94a3b8;
    font-size: .95rem;
  }

  /* File input */
  .form-group input[type="file"] {
    border: none; padding: 6px 0;
  }
  .form-group select {
    width: 100%; padding: 10px 12px; border: 1px solid #cbd5e1;
    border-radius: 8px; font-size: 1rem; font-family: inherit;
    outline: none; background: #fff; transition: border .2s;
  }
  .form-group select:focus { border-color: #3b82c4; }

  /* Responsive */
  @media (max-width: 600px) {
    .header-inner { flex-direction: column; align-items: flex-start; }
    .header-nav a { margin-left: 0; margin-right: 14px; }
    .card-grid { grid-template-columns: 1fr; }
    .detail-actions { flex-direction: column; }
    .btn { width: 100%; text-align: center; }
    .timeline { padding-left: 24px; }
  }
</style>
"""


def layout(title, body, flash_msg=None):
    flash_html = ""
    if flash_msg:
        flash_html = f'<div class="flash">{escape(flash_msg)}</div>'
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(title)} - PeopleWiki</title>
  {CSS}
</head>
<body>
  <div class="header">
    <div class="header-inner">
      <h1><a href="/">PeopleWiki</a></h1>
      <nav class="header-nav">
        <a href="/">一覧</a>
        <a href="/add">新規登録</a>
      </nav>
    </div>
  </div>
  {flash_html}
  <div class="container">
    {body}
  </div>
  <script>
  document.addEventListener('click', function(e) {{
    var toggle = e.target.closest('.acc-toggle');
    if (!toggle) return;
    var item = toggle.closest('.acc-item');
    if (item) item.classList.toggle('open');
  }});
  </script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_birthday(bd):
    """Format 'YYYY-MM-DD' as 'M月D日' and return (display_str, days_until_next)."""
    if not bd:
        return "", None
    try:
        m, d = int(bd[5:7]), int(bd[8:10])
        today = datetime.now().date()
        import calendar
        # Handle Feb 29 for non-leap years
        if m == 2 and d == 29 and not calendar.isleap(today.year):
            next_bd = today.replace(year=today.year, month=3, day=1)
        else:
            next_bd = today.replace(month=m, day=d)
        if next_bd < today:
            yr = today.year + 1
            if m == 2 and d == 29 and not calendar.isleap(yr):
                next_bd = today.replace(year=yr, month=3, day=1)
            else:
                next_bd = next_bd.replace(year=yr)
        days = (next_bd - today).days
        return f"{m}月{d}日", days
    except (ValueError, IndexError):
        return str(escape(bd)), None


def _birthday_sort_key(person):
    """Sort key: days until next birthday (None/invalid → last)."""
    _, days = _format_birthday(person.birthday)
    if days is None:
        return 9999
    return days


def _upload_image(file_storage):
    """Upload image to Cloudinary. Returns (url, error_message)."""
    if not file_storage or not file_storage.filename:
        return None, None
    if not os.environ.get("CLOUDINARY_URL"):
        return None, "CLOUDINARY_URL が設定されていません。Render の環境変数を確認してください。"
    try:
        result = cloudinary.uploader.upload(
            file_storage,
            folder="people-wiki",
            transformation=[{"width": 1200, "crop": "limit"}],
            resource_type="image",
        )
        return result.get("secure_url"), None
    except Exception as e:
        return None, f"画像アップロードに失敗しました: {e}"


def _format_event_date(d):
    """Format 'YYYY-MM-DD' as 'YYYY年M月D日'."""
    try:
        y, m, d = int(d[:4]), int(d[5:7]), int(d[8:10])
        return f"{y}年{m}月{d}日"
    except (ValueError, IndexError):
        return str(escape(d))


def _calc_age(birthday_str):
    """Calculate age from 'YYYY-MM-DD'. Returns age int or None."""
    if not birthday_str:
        return None
    try:
        born = datetime.strptime(birthday_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        return age
    except (ValueError, IndexError):
        return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "updated")

    query = Person.query

    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Person.name.ilike(like),
                Person.organization.ilike(like),
                Person.notes.ilike(like),
            )
        )

    if sort == "birthday":
        rows = query.all()
        rows.sort(key=_birthday_sort_key)
    else:
        rows = query.order_by(Person.updated_at.desc()).all()

    cards = ""
    for r in rows:
        org = f'<div class="meta">{escape(r.organization)}</div>' if r.organization else ""
        bd_display, bd_days = _format_birthday(r.birthday)
        bd_html = ""
        if bd_display:
            badge = ""
            if bd_days is not None and bd_days == 0:
                badge = ' <span class="birthday-badge today">TODAY!</span>'
            elif bd_days is not None and bd_days <= 7:
                badge = f' <span class="birthday-badge soon">あと{bd_days}日</span>'
            bd_html = f'<div class="meta birthday-meta">{bd_display}{badge}</div>'
        notes = f'<div class="notes-preview">{escape(r.notes)}</div>' if r.notes else ""
        cards += f"""
        <a href="/person/{r.id}" style="text-decoration:none;color:inherit;">
          <div class="card">
            <h3>{escape(r.name)}</h3>
            {org}
            {bd_html}
            {notes}
          </div>
        </a>"""

    if not rows:
        if q:
            cards = f'<div class="empty"><p>「{escape(q)}」に一致する人物は見つかりませんでした。</p><a href="/" class="btn btn-secondary">一覧に戻る</a></div>'
        else:
            cards = '<div class="empty"><p>まだ人物が登録されていません。</p><a href="/add" class="btn btn-primary">最初の人物を登録する</a></div>'

    search_val = escape(q) if q else ""
    sort_updated_cls = "active" if sort != "birthday" else ""
    sort_birthday_cls = "active" if sort == "birthday" else ""
    q_param = f"&q={search_val}" if q else ""
    body = f"""
    <form class="search-form" action="/" method="get">
      <input type="text" name="q" placeholder="名前・所属・メモで検索..." value="{search_val}">
      <button type="submit">検索</button>
    </form>
    <div class="sort-bar">
      <span class="sort-label">並び順:</span>
      <a href="/?sort=updated{q_param}" class="sort-btn {sort_updated_cls}">更新日順</a>
      <a href="/?sort=birthday{q_param}" class="sort-btn {sort_birthday_cls}">誕生日が近い順</a>
    </div>
    <div class="card-grid">
      {cards}
    </div>
    """
    return layout("一覧", body)


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            link_fid = request.form.get("link_family_id", "")
            return layout("新規登録", _form("名前は必須です。", prefill_name="", link_family_id=link_fid)), 400
        person = Person(
            name=name,
            organization=request.form.get("organization", "").strip(),
            met_at=request.form.get("met_at", "").strip(),
            birthday=request.form.get("birthday", "").strip() or None,
            notes=request.form.get("notes", "").strip(),
        )
        db.session.add(person)
        db.session.commit()

        # Auto-link family member if link_family_id was provided
        link_family_id = request.form.get("link_family_id", "").strip()
        if link_family_id:
            fm = db.session.get(FamilyMember, int(link_family_id))
            if fm and not fm.linked_person_id:
                fm.linked_person_id = person.id
                db.session.commit()
                return redirect(url_for("detail", person_id=fm.person_id))

        return redirect(url_for("detail", person_id=person.id))

    # GET: check for prefill params from family link
    prefill_name = request.args.get("name", "")
    link_family_id = request.args.get("link_family_id", "")
    return layout("新規登録", _form(prefill_name=prefill_name, link_family_id=link_family_id))


def _form(error=None, person=None, prefill_name="", link_family_id=""):
    err_html = f'<p style="color:#e74c3c;margin-bottom:12px;">{escape(error)}</p>' if error else ""
    name = escape(person.name) if person else escape(prefill_name)
    org = escape(person.organization or "") if person else ""
    met = escape(person.met_at or "") if person else ""
    birthday = escape(person.birthday or "") if person else ""
    notes = escape(person.notes or "") if person else ""
    action = f'/edit/{person.id}' if person else "/add"
    title = "人物情報を編集" if person else "新しい人物を登録"
    btn_text = "更新する" if person else "登録する"
    hidden = f'<input type="hidden" name="link_family_id" value="{escape(link_family_id)}">' if link_family_id else ""
    link_note = ""
    if link_family_id and not person:
        link_note = '<p style="color:#3b82c4;margin-bottom:12px;font-size:.9rem;">家族メンバーから新規登録 — 登録すると自動的にリンクされます</p>'

    return f"""
    <div class="form-card">
      <h2>{title}</h2>
      {err_html}
      {link_note}
      <form method="post" action="{action}">
        {hidden}
        <div class="form-group">
          <label for="name">名前 <span style="color:#e74c3c;">*</span></label>
          <input type="text" id="name" name="name" value="{name}" required>
        </div>
        <div class="form-group">
          <label for="organization">所属・会社名</label>
          <input type="text" id="organization" name="organization" value="{org}">
        </div>
        <div class="form-group">
          <label for="met_at">出会った場所・きっかけ</label>
          <input type="text" id="met_at" name="met_at" value="{met}">
        </div>
        <div class="form-group">
          <label for="birthday">誕生日</label>
          <input type="date" id="birthday" name="birthday" value="{birthday}">
        </div>
        <div class="form-group">
          <label for="notes">メモ・特徴</label>
          <textarea id="notes" name="notes">{notes}</textarea>
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;">
          <button type="submit" class="btn btn-primary">{btn_text}</button>
          <a href="/" class="btn btn-secondary">キャンセル</a>
        </div>
      </form>
    </div>"""


@app.route("/person/<int:person_id>")
def detail(person_id):
    person = db.session.get(Person, person_id)
    if not person:
        return layout("見つかりません", '<div class="empty"><p>指定された人物が見つかりません。</p><a href="/" class="btn btn-secondary">一覧に戻る</a></div>'), 404

    def row(label, value, css_class=""):
        if not value:
            return ""
        cls = f' class="{css_class}"' if css_class else ""
        return f'<div class="detail-row"><div class="detail-label">{label}</div><div class="detail-value"{cls}>{escape(value)}</div></div>'

    # Build accordion timeline HTML
    timeline_items = ""
    for ev in person.events:
        img_html = ""
        if ev.image_url:
            img_html = f'<div class="acc-image"><a href="{escape(ev.image_url)}" target="_blank"><img src="{escape(ev.image_url)}" alt="event photo" loading="lazy"></a></div>'
        preview = escape(ev.content)[:60]
        timeline_items += f"""
        <div class="acc-item">
          <button type="button" class="acc-toggle">
            <span class="acc-arrow">&#9654;</span>
            <span class="acc-date">{_format_event_date(ev.event_date)}</span>
            <span class="acc-preview">{preview}</span>
          </button>
          <div class="acc-body"><div class="acc-body-inner">
            <div class="acc-content">{escape(ev.content)}</div>
            {img_html}
            <div class="acc-actions">
              <form method="post" action="/event/{ev.id}/delete"
                    onsubmit="return confirm('このイベントを削除しますか？');">
                <button type="submit" class="tl-btn tl-btn-del">削除</button>
              </form>
            </div>
          </div></div>
        </div>"""

    if not person.events:
        timeline_items = '<div class="tl-empty">まだイベントがありません</div>'

    # Build family members HTML
    family_items = ""
    for fm in person.family_members:
        age = _calc_age(fm.birthday)
        age_html = f'<div class="family-age">{fm.birthday}（{age}歳）</div>' if age is not None else ""
        if not age_html and fm.birthday:
            age_html = f'<div class="family-age">{escape(fm.birthday)}</div>'
        # Clickable name: linked → detail page, not linked → add page with name prefilled
        if fm.linked_person_id:
            name_html = f'<a href="/person/{fm.linked_person_id}" class="family-name">{escape(fm.name)}</a><span class="family-link-badge">図鑑登録済</span>'
        else:
            name_html = f'<a href="/add?name={quote(fm.name)}&amp;link_family_id={fm.id}" class="family-name">{escape(fm.name)}</a><span class="family-link-new">未登録</span>'
        family_items += f"""
        <div class="family-item">
          <div class="family-info">
            {name_html}
            <span class="family-rel">{escape(fm.relationship)}</span>
            {age_html}
          </div>
          <form method="post" action="/family/{fm.id}/delete"
                onsubmit="return confirm('この家族メンバーを削除しますか？');">
            <button type="submit" class="tl-btn tl-btn-del">削除</button>
          </form>
        </div>"""

    # Reverse relations: other people who linked to this person as family
    reverse_fms = FamilyMember.query.filter_by(linked_person_id=person.id).all()
    for rfm in reverse_fms:
        owner = db.session.get(Person, rfm.person_id)
        if owner:
            family_items += f"""
        <div class="family-item">
          <div class="family-info">
            <a href="/person/{owner.id}" class="family-name">{escape(owner.name)}</a>
            <span class="family-rel">{escape(rfm.relationship)}の関係</span>
            <div class="family-reverse">{escape(owner.name)} の家族として登録</div>
          </div>
        </div>"""

    if not person.family_members and not reverse_fms:
        family_items = '<div class="family-empty">まだ家族が登録されていません</div>'

    body = f"""
    <div class="detail-card">
      <h2>{escape(person.name)}</h2>
      {row("所属・会社名", person.organization)}
      {row("出会った場所・きっかけ", person.met_at)}
      {row("誕生日", _format_birthday(person.birthday)[0] if person.birthday else None)}
      {row("メモ・特徴", person.notes, "notes")}
      {row("登録日", str(person.created_at))}
      {row("最終更新", str(person.updated_at))}
      <div class="detail-actions">
        <a href="/edit/{person.id}" class="btn btn-primary">編集</a>
        <form method="post" action="/delete/{person.id}" style="display:inline;"
              onsubmit="return confirm('「{escape(person.name)}」を削除してよろしいですか？');">
          <button type="submit" class="btn btn-danger">削除</button>
        </form>
        <a href="/" class="btn btn-secondary">一覧に戻る</a>
      </div>
    </div>

    <div class="section-card">
      <div class="section-header">
        <h3>家族</h3>
        <a href="/person/{person.id}/family/add" class="btn btn-primary" style="padding:8px 18px;font-size:.9rem;">+ 家族を追加</a>
      </div>
      <div class="family-list">
        {family_items}
      </div>
    </div>

    <div class="section-card">
      <div class="section-header">
        <h3>沿革</h3>
        <a href="/person/{person.id}/events/add" class="btn btn-primary" style="padding:8px 18px;font-size:.9rem;">+ イベントを追加</a>
      </div>
      <div class="timeline">
        {timeline_items}
      </div>
    </div>"""
    return layout(person.name, body)


@app.route("/edit/<int:person_id>", methods=["GET", "POST"])
def edit(person_id):
    person = db.session.get(Person, person_id)
    if not person:
        return layout("見つかりません", '<div class="empty"><p>指定された人物が見つかりません。</p><a href="/" class="btn btn-secondary">一覧に戻る</a></div>'), 404

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            return layout("編集", _form("名前は必須です。", person)), 400
        person.name = name
        person.organization = request.form.get("organization", "").strip()
        person.met_at = request.form.get("met_at", "").strip()
        person.birthday = request.form.get("birthday", "").strip() or None
        person.notes = request.form.get("notes", "").strip()
        person.updated_at = datetime.now()
        db.session.commit()
        return redirect(url_for("detail", person_id=person_id))

    return layout("編集", _form(person=person))


@app.route("/delete/<int:person_id>", methods=["POST"])
def delete(person_id):
    person = db.session.get(Person, person_id)
    if person:
        db.session.delete(person)
        db.session.commit()
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Event routes
# ---------------------------------------------------------------------------

@app.route("/person/<int:person_id>/events/add", methods=["GET", "POST"])
def add_event(person_id):
    person = db.session.get(Person, person_id)
    if not person:
        return layout("見つかりません", '<div class="empty"><p>指定された人物が見つかりません。</p></div>'), 404

    if request.method == "POST":
        event_date = request.form.get("event_date", "").strip()
        content = request.form.get("content", "").strip()
        if not event_date or not content:
            return layout("イベント追加", _event_form(person, error="日付と内容は必須です。")), 400

        image_url, upload_err = _upload_image(request.files.get("image"))
        if upload_err:
            return layout("イベント追加", _event_form(person, error=upload_err)), 400

        event = Event(
            person_id=person.id,
            event_date=event_date,
            content=content,
            image_url=image_url,
        )
        db.session.add(event)
        person.updated_at = datetime.now()
        db.session.commit()
        return redirect(url_for("detail", person_id=person.id))

    return layout("イベント追加", _event_form(person))


def _event_form(person, error=None):
    err_html = f'<p style="color:#e74c3c;margin-bottom:12px;">{escape(error)}</p>' if error else ""
    today = datetime.now().strftime("%Y-%m-%d")
    return f"""
    <div class="form-card">
      <h2>{escape(person.name)} - イベント追加</h2>
      {err_html}
      <form method="post" action="/person/{person.id}/events/add" enctype="multipart/form-data">
        <div class="form-group">
          <label for="event_date">日付 <span style="color:#e74c3c;">*</span></label>
          <input type="date" id="event_date" name="event_date" value="{today}" required>
        </div>
        <div class="form-group">
          <label for="content">内容 <span style="color:#e74c3c;">*</span></label>
          <textarea id="content" name="content" placeholder="何があったかを記録..."></textarea>
        </div>
        <div class="form-group">
          <label for="image">写真（任意・1枚まで）</label>
          <input type="file" id="image" name="image" accept="image/*">
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;">
          <button type="submit" class="btn btn-primary">追加する</button>
          <a href="/person/{person.id}" class="btn btn-secondary">キャンセル</a>
        </div>
      </form>
    </div>"""


# ---------------------------------------------------------------------------
# Family routes
# ---------------------------------------------------------------------------

@app.route("/person/<int:person_id>/family/add", methods=["GET", "POST"])
def add_family(person_id):
    person = db.session.get(Person, person_id)
    if not person:
        return layout("見つかりません", '<div class="empty"><p>指定された人物が見つかりません。</p></div>'), 404

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        relationship = request.form.get("relationship", "").strip()
        if not name or not relationship:
            return layout("家族追加", _family_form(person, error="名前と続柄は必須です。")), 400

        # Check if linking to existing person
        linked_person_id = request.form.get("linked_person_id", "").strip()
        linked_pid = int(linked_person_id) if linked_person_id else None

        fm = FamilyMember(
            person_id=person.id,
            name=name,
            relationship=relationship,
            birthday=request.form.get("birthday", "").strip() or None,
            linked_person_id=linked_pid,
        )
        db.session.add(fm)
        person.updated_at = datetime.now()
        db.session.commit()
        return redirect(url_for("detail", person_id=person.id))

    return layout("家族追加", _family_form(person))


def _family_form(person, error=None):
    err_html = f'<p style="color:#e74c3c;margin-bottom:12px;">{escape(error)}</p>' if error else ""
    # Build options for linking to existing people (exclude self)
    all_people = Person.query.order_by(Person.name).all()
    link_options = '<option value="">リンクしない（後で登録）</option>'
    for p in all_people:
        if p.id != person.id:
            link_options += f'<option value="{p.id}">{escape(p.name)}</option>'

    return f"""
    <div class="form-card">
      <h2>{escape(person.name)} - 家族追加</h2>
      {err_html}
      <form method="post" action="/person/{person.id}/family/add">
        <div class="form-group">
          <label for="name">名前 <span style="color:#e74c3c;">*</span></label>
          <input type="text" id="name" name="name" required>
        </div>
        <div class="form-group">
          <label for="relationship">続柄 <span style="color:#e74c3c;">*</span></label>
          <select id="relationship" name="relationship" required>
            <option value="">選択してください</option>
            <option value="配偶者">配偶者</option>
            <option value="子供">子供</option>
            <option value="父親">父親</option>
            <option value="母親">母親</option>
            <option value="兄弟姉妹">兄弟姉妹</option>
            <option value="その他">その他</option>
          </select>
        </div>
        <div class="form-group">
          <label for="birthday">生年月日（年齢自動計算）</label>
          <input type="date" id="birthday" name="birthday">
        </div>
        <div class="form-group">
          <label for="linked_person_id">図鑑の人物とリンク（任意）</label>
          <select id="linked_person_id" name="linked_person_id">
            {link_options}
          </select>
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;">
          <button type="submit" class="btn btn-primary">追加する</button>
          <a href="/person/{person.id}" class="btn btn-secondary">キャンセル</a>
        </div>
      </form>
    </div>"""


@app.route("/family/<int:family_id>/delete", methods=["POST"])
def delete_family(family_id):
    fm = db.session.get(FamilyMember, family_id)
    if not fm:
        return redirect(url_for("index"))
    person_id = fm.person_id
    db.session.delete(fm)
    db.session.commit()
    return redirect(url_for("detail", person_id=person_id))


@app.route("/event/<int:event_id>/delete", methods=["POST"])
def delete_event(event_id):
    event = db.session.get(Event, event_id)
    if not event:
        return redirect(url_for("index"))
    person_id = event.person_id
    db.session.delete(event)
    db.session.commit()
    return redirect(url_for("detail", person_id=person_id))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
