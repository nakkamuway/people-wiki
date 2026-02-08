#!/usr/bin/env python3
"""PeopleWiki - 人物図鑑Webアプリ"""

import os
from datetime import datetime
from flask import Flask, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from markupsafe import escape

app = Flask(__name__)

# Render は DATABASE_URL に postgres:// を設定するが、
# SQLAlchemy 2.x は postgresql:// を要求するため置換する
database_url = os.environ.get("DATABASE_URL", "sqlite:///people.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
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


with app.app_context():
    db.create_all()


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

  /* Responsive */
  @media (max-width: 600px) {
    .header-inner { flex-direction: column; align-items: flex-start; }
    .header-nav a { margin-left: 0; margin-right: 14px; }
    .card-grid { grid-template-columns: 1fr; }
    .detail-actions { flex-direction: column; }
    .btn { width: 100%; text-align: center; }
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
            return layout("新規登録", _form("名前は必須です。")), 400
        person = Person(
            name=name,
            organization=request.form.get("organization", "").strip(),
            met_at=request.form.get("met_at", "").strip(),
            birthday=request.form.get("birthday", "").strip() or None,
            notes=request.form.get("notes", "").strip(),
        )
        db.session.add(person)
        db.session.commit()
        return redirect(url_for("index"))
    return layout("新規登録", _form())


def _form(error=None, person=None):
    err_html = f'<p style="color:#e74c3c;margin-bottom:12px;">{escape(error)}</p>' if error else ""
    name = escape(person.name) if person else ""
    org = escape(person.organization or "") if person else ""
    met = escape(person.met_at or "") if person else ""
    birthday = escape(person.birthday or "") if person else ""
    notes = escape(person.notes or "") if person else ""
    action = f'/edit/{person.id}' if person else "/add"
    title = "人物情報を編集" if person else "新しい人物を登録"
    btn_text = "更新する" if person else "登録する"

    return f"""
    <div class="form-card">
      <h2>{title}</h2>
      {err_html}
      <form method="post" action="{action}">
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
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
