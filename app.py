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
    twitter = db.Column(db.String)
    instagram = db.Column(db.String)
    facebook = db.Column(db.String)
    linkedin = db.Column(db.String)
    marital_status = db.Column(db.String)  # 既婚・未婚
    has_children = db.Column(db.String)     # 子供あり・なし
    has_pets = db.Column(db.String)         # ペットあり・なし
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
    # Migrate: add columns if missing (for existing DBs)
    with db.engine.connect() as conn:
        from sqlalchemy import text, inspect
        inspector = inspect(db.engine)

        # Add linked_person_id to family_members
        fm_cols = [c["name"] for c in inspector.get_columns("family_members")]
        if "linked_person_id" not in fm_cols:
            conn.execute(text(
                "ALTER TABLE family_members ADD COLUMN linked_person_id INTEGER REFERENCES people(id)"
            ))
            conn.commit()

        # Add SNS and personal info columns to people
        people_cols = [c["name"] for c in inspector.get_columns("people")]
        new_cols = ["twitter", "instagram", "facebook", "linkedin", "marital_status", "has_children", "has_pets"]
        for col in new_cols:
            if col not in people_cols:
                conn.execute(text(f"ALTER TABLE people ADD COLUMN {col} VARCHAR"))
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
    max-width: 1400px; margin: 0 auto; padding: 0 32px;
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
  .container { max-width: 1400px; margin: 28px auto; padding: 0 32px; }

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

  /* Dashboard Table */
  .dashboard-table {
    background: #fff;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
    width: 100%;
  }
  .table-header {
    display: grid;
    grid-template-columns: minmax(200px, 2.5fr) minmax(150px, 1.5fr) minmax(120px, 1.3fr) minmax(180px, 2fr) minmax(120px, 1.2fr);
    gap: 24px;
    padding: 18px 28px;
    background: #f8fafc;
    border-bottom: 1px solid #e2e8f0;
    font-size: .8rem;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: .05em;
  }
  .table-row {
    display: grid;
    grid-template-columns: minmax(200px, 2.5fr) minmax(150px, 1.5fr) minmax(120px, 1.3fr) minmax(180px, 2fr) minmax(120px, 1.2fr);
    gap: 24px;
    padding: 20px 28px;
    border-bottom: 1px solid #f1f5f9;
    transition: background .15s ease, box-shadow .15s ease;
    cursor: pointer;
    align-items: center;
  }
  .table-row:hover {
    background: #f8fafc;
    box-shadow: inset 4px 0 0 #3b82c4;
  }
  .table-row:last-child {
    border-bottom: none;
  }
  .table-cell {
    display: flex;
    align-items: center;
    min-width: 0;
    overflow: hidden;
  }
  .table-cell-name {
    font-size: 1rem;
    font-weight: 600;
    color: #1e293b;
  }
  .table-cell-org {
    font-size: .9rem;
    color: #64748b;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .table-cell-date {
    font-size: .85rem;
    color: #94a3b8;
  }
  .table-cell-family {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    font-size: .85rem;
  }
  .family-tag {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    background: #f1f5f9;
    border-radius: 12px;
    color: #475569;
    font-size: .8rem;
    white-space: nowrap;
  }
  .family-tag-icon {
    margin-right: 4px;
    font-size: .7rem;
  }
  .table-cell-sns {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
  }
  .sns-icons-container {
    display: flex;
    gap: 8px;
    align-items: center;
    justify-content: center;
    flex-wrap: nowrap;
  }
  .sns-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 8px;
    transition: all .2s ease;
    text-decoration: none;
    flex-shrink: 0;
  }
  .sns-icon:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,.15);
  }
  .sns-icon svg {
    width: 18px;
    height: 18px;
    fill: currentColor;
    flex-shrink: 0;
  }
  .sns-icon.twitter {
    background: #1DA1F2;
    color: #fff;
  }
  .sns-icon.instagram {
    background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);
    color: #fff;
  }
  .sns-icon.facebook {
    background: #1877F2;
    color: #fff;
  }
  .sns-icon.linkedin {
    background: #0A66C2;
    color: #fff;
  }
  .sns-icon-empty {
    color: #e2e8f0;
    font-size: .85rem;
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
    max-width: 700px; margin: 0 auto;
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
    max-width: 1400px; margin: 16px auto 0; padding: 12px 32px;
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
  .section-add-btn {
    display: none;
  }
  body.editing .section-add-btn {
    display: inline-block;
  }

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
  .acc-item.open .acc-body { max-height: none; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 10px 10px; background: #fff; }
  .acc-content { font-size: .95rem; white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word; }
  .acc-image { margin-top: 10px; }
  .acc-image img {
    max-width: 100%; max-height: 320px;
    border-radius: 8px; object-fit: cover;
    cursor: pointer; transition: opacity .2s;
  }
  .acc-image img:hover { opacity: .9; }
  .acc-actions {
    margin-top: 10px;
    display: none;
  }
  body.editing .acc-actions {
    display: block;
  }
  .tl-btn {
    font-size: .78rem; padding: 3px 10px; border-radius: 6px;
    border: none; cursor: pointer; margin-right: 6px;
  }
  .tl-btn-edit { background: #dbeafe; color: #1e40af; }
  .tl-btn-edit:hover { background: #bfdbfe; }
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
  .family-delete-btn {
    display: none;
  }
  body.editing .family-delete-btn {
    display: block;
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

  /* View/Edit Mode Toggle */
  .mode-toggle {
    margin-bottom: 24px;
    padding-bottom: 24px;
    border-bottom: 2px solid #e2e8f0;
  }
  .btn-edit-mode {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    padding: 14px 32px;
    border-radius: 12px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    border: none;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    transition: all .3s ease;
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }
  .btn-edit-mode:hover {
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
    transform: translateY(-2px);
  }
  .btn-edit-mode:active {
    transform: translateY(0);
  }
  .edit-mode-actions {
    display: none;
    gap: 10px;
    flex-wrap: wrap;
  }
  .edit-mode-field {
    display: none;
  }
  .view-mode-only {
    display: block;
  }
  body.editing .edit-mode-actions {
    display: flex;
  }
  body.editing .edit-mode-field {
    display: block;
  }
  body.editing .view-mode-only {
    display: none;
  }
  body.editing .mode-toggle {
    background: #fef3c7;
    padding: 12px;
    border-radius: 8px;
    border-bottom: none;
  }
  body.editing .detail-value {
    background: #fffbeb;
    padding: 8px 12px;
    border-radius: 6px;
    border: 1px solid #fcd34d;
  }
  .edit-field {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    font-size: 1rem;
    font-family: inherit;
    outline: none;
    transition: border .2s;
  }
  .edit-field:focus {
    border-color: #3b82c4;
  }
  .edit-field.textarea {
    min-height: 100px;
    resize: vertical;
  }

  /* Responsive - タブレット以下のみ */
  @media (max-width: 768px) {
    .table-header, .table-row {
      grid-template-columns: minmax(120px, 2fr) minmax(100px, 1fr) minmax(120px, 1.5fr) minmax(80px, 1fr);
      gap: 12px;
      padding: 14px 16px;
    }
    .table-cell-date {
      display: none !important;
    }
    .table-header > div:nth-child(3) {
      display: none !important;
    }
    .table-cell-family {
      font-size: .75rem;
    }
    .family-tag {
      font-size: .7rem;
      padding: 3px 8px;
    }
    .sns-icon {
      width: 28px;
      height: 28px;
    }
    .sns-icon svg {
      width: 14px;
      height: 14px;
    }
    .sns-icons-container {
      gap: 4px;
    }
  }
  @media (max-width: 600px) {
    .header-inner { flex-direction: column; align-items: flex-start; }
    .header-nav a { margin-left: 0; margin-right: 14px; }
    .detail-actions { flex-direction: column; }
    .btn { width: 100%; text-align: center; }
    .timeline { padding-left: 24px; }
    .table-header {
      display: none;
    }
    .table-row {
      grid-template-columns: 1fr;
      gap: 8px;
      padding: 16px;
    }
    .table-cell {
      display: block;
    }
    .table-cell::before {
      content: attr(data-label);
      font-size: .75rem;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: .05em;
      display: block;
      margin-bottom: 4px;
    }
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
  // Accordion toggle
  document.addEventListener('click', function(e) {{
    var toggle = e.target.closest('.acc-toggle');
    if (!toggle) return;
    var item = toggle.closest('.acc-item');
    if (item) item.classList.toggle('open');
  }});

  // Edit mode functions
  function enterEditMode() {{
    document.body.classList.add('editing');
  }}

  function cancelEdit() {{
    document.body.classList.remove('editing');
  }}

  function confirmDelete() {{
    var personName = document.querySelector('.detail-card h2').textContent;
    if (confirm('「' + personName + '」を削除してよろしいですか？')) {{
      var form = document.createElement('form');
      form.method = 'POST';
      form.action = window.location.pathname + '/delete';
      document.body.appendChild(form);
      form.submit();
    }}
  }}

  // Handle form submission
  var editForm = document.getElementById('edit-form');
  if (editForm) {{
    editForm.addEventListener('submit', function(e) {{
      e.preventDefault();
      var formData = new FormData(this);
      fetch(this.action, {{
        method: 'POST',
        body: formData
      }})
      .then(response => {{
        if (response.ok) {{
          window.location.reload();
        }} else {{
          alert('更新に失敗しました。');
        }}
      }})
      .catch(error => {{
        alert('エラーが発生しました: ' + error);
      }});
    }});
  }}
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

    # Build table rows
    table_rows = ""
    for r in rows:
        # Organization
        org_display = escape(r.organization) if r.organization else '<span style="color:#cbd5e1;">未設定</span>'

        # Registration date (formatted)
        reg_date = r.created_at.strftime("%Y年%m月%d日") if r.created_at else "不明"

        # Family members
        family_tags = ""
        family_count = 0
        for fm in r.family_members:
            if family_count >= 3:  # Limit to 3 tags for display
                remaining = len(r.family_members) - 3
                family_tags += f'<span class="family-tag">+{remaining}名</span>'
                break
            # Use linked person's name if available
            display_name = fm.name
            if fm.linked_person_id and fm.linked_person:
                display_name = fm.linked_person.name
            family_tags += f'<span class="family-tag"><span class="family-tag-icon">👤</span>{escape(display_name)}</span>'
            family_count += 1

        if not family_tags:
            family_tags = '<span style="color:#cbd5e1;font-size:.85rem;">―</span>'

        # SNS icons - build list of icons
        sns_icon_list = []
        if r.twitter:
            sns_icon_list.append(f'<a href="{escape(r.twitter)}" class="sns-icon twitter" target="_blank" rel="noopener" onclick="event.stopPropagation();"><svg viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg></a>')
        if r.instagram:
            sns_icon_list.append(f'<a href="{escape(r.instagram)}" class="sns-icon instagram" target="_blank" rel="noopener" onclick="event.stopPropagation();"><svg viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg></a>')
        if r.facebook:
            sns_icon_list.append(f'<a href="{escape(r.facebook)}" class="sns-icon facebook" target="_blank" rel="noopener" onclick="event.stopPropagation();"><svg viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg></a>')
        if r.linkedin:
            sns_icon_list.append(f'<a href="{escape(r.linkedin)}" class="sns-icon linkedin" target="_blank" rel="noopener" onclick="event.stopPropagation();"><svg viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg></a>')

        # Wrap icons in a container div for proper layout
        if sns_icon_list:
            sns_icons_html = f'<div class="sns-icons-container">{"".join(sns_icon_list)}</div>'
        else:
            sns_icons_html = '<span class="sns-icon-empty">―</span>'

        table_rows += f"""
        <div class="table-row" onclick="window.location.href='/person/{r.id}'">
          <div class="table-cell table-cell-name">{escape(r.name)}</div>
          <div class="table-cell table-cell-org">{org_display}</div>
          <div class="table-cell table-cell-date">{reg_date}</div>
          <div class="table-cell table-cell-family">{family_tags}</div>
          <div class="table-cell table-cell-sns">{sns_icons_html}</div>
        </div>"""

    if not rows:
        if q:
            table_rows = f'<div class="empty"><p>「{escape(q)}」に一致する人物は見つかりませんでした。</p><a href="/" class="btn btn-secondary">一覧に戻る</a></div>'
        else:
            table_rows = '<div class="empty"><p>まだ人物が登録されていません。</p><a href="/add" class="btn btn-primary">最初の人物を登録する</a></div>'

    search_val = escape(q) if q else ""
    sort_updated_cls = "active" if sort != "birthday" else ""
    sort_birthday_cls = "active" if sort == "birthday" else ""
    q_param = f"&q={search_val}" if q else ""

    # Build table HTML
    if rows:
        table_html = f"""
        <div class="dashboard-table">
          <div class="table-header">
            <div>名前</div>
            <div>所属</div>
            <div>登録日</div>
            <div>家族</div>
            <div>SNS</div>
          </div>
          {table_rows}
        </div>"""
    else:
        table_html = table_rows  # Empty state

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
    {table_html}
    """
    return layout("一覧", body)


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            link_fid = request.form.get("link_family_id", "")
            prefill_bd = request.form.get("birthday", "").strip()
            return layout("新規登録", _form("名前は必須です。", prefill_name="", prefill_birthday=prefill_bd, link_family_id=link_fid)), 400
        person = Person(
            name=name,
            organization=request.form.get("organization", "").strip(),
            met_at=request.form.get("met_at", "").strip(),
            birthday=request.form.get("birthday", "").strip() or None,
            marital_status=request.form.get("marital_status", "").strip() or None,
            has_children=request.form.get("has_children", "").strip() or None,
            has_pets=request.form.get("has_pets", "").strip() or None,
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
    prefill_birthday = request.args.get("birthday", "")
    link_family_id = request.args.get("link_family_id", "")
    return layout("新規登録", _form(prefill_name=prefill_name, prefill_birthday=prefill_birthday, link_family_id=link_family_id))


def _form(error=None, person=None, prefill_name="", prefill_birthday="", link_family_id=""):
    err_html = f'<p style="color:#e74c3c;margin-bottom:12px;">{escape(error)}</p>' if error else ""
    name = escape(person.name) if person else escape(prefill_name)
    org = escape(person.organization or "") if person else ""
    met = escape(person.met_at or "") if person else ""
    birthday = escape(person.birthday or "") if person else escape(prefill_birthday)
    marital_status = escape(person.marital_status or "") if person else ""
    has_children = escape(person.has_children or "") if person else ""
    has_pets = escape(person.has_pets or "") if person else ""
    notes = escape(person.notes or "") if person else ""
    action = f'/edit/{person.id}' if person else "/add"
    title = "人物情報を編集" if person else "新しい人物を登録"
    btn_text = "更新する" if person else "登録する"
    hidden = f'<input type="hidden" name="link_family_id" value="{escape(link_family_id)}">' if link_family_id else ""
    link_note = ""
    if link_family_id and not person:
        birthday_note = " （生年月日も自動入力されました）" if prefill_birthday else ""
        link_note = f'<p style="color:#3b82c4;margin-bottom:12px;font-size:.9rem;">✨ 家族メンバーから新規登録 — 登録すると自動的にリンクされます{birthday_note}</p>'

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
          <label for="marital_status">既婚・未婚</label>
          <select id="marital_status" name="marital_status">
            <option value="">選択してください</option>
            <option value="既婚"{' selected' if marital_status == '既婚' else ''}>既婚</option>
            <option value="未婚"{' selected' if marital_status == '未婚' else ''}>未婚</option>
          </select>
        </div>
        <div class="form-group">
          <label for="has_children">子供</label>
          <select id="has_children" name="has_children">
            <option value="">選択してください</option>
            <option value="あり"{' selected' if has_children == 'あり' else ''}>あり</option>
            <option value="なし"{' selected' if has_children == 'なし' else ''}>なし</option>
          </select>
        </div>
        <div class="form-group">
          <label for="has_pets">ペット</label>
          <select id="has_pets" name="has_pets">
            <option value="">選択してください</option>
            <option value="あり"{' selected' if has_pets == 'あり' else ''}>あり</option>
            <option value="なし"{' selected' if has_pets == 'なし' else ''}>なし</option>
          </select>
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

    def row(label, value, field_name="", css_class="", input_type="text"):
        """Generate a row with view and edit modes"""
        if not value and not field_name:
            return ""

        # View mode display
        if input_type == "url" and value:
            view_val = f'<a href="{escape(value)}" target="_blank" rel="noopener" style="color:#3b82c4;">{escape(value)}</a>'
        else:
            view_val = escape(value) if value else '<span style="color:#94a3b8;">未設定</span>'
        cls = f' class="{css_class}"' if css_class else ""

        # Edit mode input
        edit_input = ""
        if field_name:
            val_escaped = escape(value) if value else ""
            if input_type == "textarea":
                edit_input = f'<textarea class="edit-field textarea" name="{field_name}" data-field="{field_name}">{val_escaped}</textarea>'
            elif input_type == "date":
                edit_input = f'<input type="date" class="edit-field" name="{field_name}" value="{val_escaped}" data-field="{field_name}">'
            elif input_type == "url":
                edit_input = f'<input type="url" class="edit-field" name="{field_name}" value="{val_escaped}" data-field="{field_name}" placeholder="https://...">'
            else:
                edit_input = f'<input type="text" class="edit-field" name="{field_name}" value="{val_escaped}" data-field="{field_name}">'

        return f'''<div class="detail-row">
          <div class="detail-label">{label}</div>
          <div class="detail-value view-mode-only"{cls}>{view_val}</div>
          <div class="edit-mode-field">{edit_input}</div>
        </div>'''

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
              <a href="/event/{ev.id}/edit" class="tl-btn tl-btn-edit">編集</a>
              <form method="post" action="/event/{ev.id}/delete" style="display:inline;"
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
        # Get actual name: use linked person's name if available, otherwise use family member's name
        display_name = fm.name
        display_birthday = fm.birthday
        if fm.linked_person_id and fm.linked_person:
            display_name = fm.linked_person.name
            # Use linked person's birthday if family member birthday is not set
            if not display_birthday and fm.linked_person.birthday:
                display_birthday = fm.linked_person.birthday

        age = _calc_age(display_birthday)
        age_html = f'<div class="family-age">{display_birthday}（{age}歳）</div>' if age is not None else ""
        if not age_html and display_birthday:
            age_html = f'<div class="family-age">{escape(display_birthday)}</div>'

        # Clickable name: linked → detail page, not linked → add page with name and birthday prefilled
        if fm.linked_person_id:
            name_html = f'<a href="/person/{fm.linked_person_id}" class="family-name">{escape(display_name)}</a><span class="family-link-badge">図鑑登録済</span>'
        else:
            # Include birthday in URL if available
            birthday_param = f'&amp;birthday={quote(display_birthday)}' if display_birthday else ''
            name_html = f'<a href="/add?name={quote(display_name)}&amp;link_family_id={fm.id}{birthday_param}" class="family-name">{escape(display_name)}</a><span class="family-link-new">未登録</span>'
        family_items += f"""
        <div class="family-item">
          <div class="family-info">
            {name_html}
            <span class="family-rel">{escape(fm.relationship)}</span>
            {age_html}
          </div>
          <form method="post" action="/family/{fm.id}/delete" class="family-delete-btn"
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

    # Format birthday for display
    bd_display = _format_birthday(person.birthday)[0] if person.birthday else ""
    bd_value = person.birthday if person.birthday else ""

    body = f"""
    <div class="detail-card">
      <div class="mode-toggle">
        <button type="button" class="btn-edit-mode view-mode-only" onclick="enterEditMode()">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
          </svg>
          編集を開始する
        </button>
        <div class="edit-mode-field" style="color:#92400e;font-weight:600;font-size:.95rem;">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:6px;">
            <path d="M12 20h9"></path>
            <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
          </svg>
          編集モード - 変更後は保存してください
        </div>
      </div>

      <h2 class="view-mode-only">{escape(person.name)}</h2>

      <form id="edit-form" method="post" action="/person/{person.id}/update">
        <div class="detail-row edit-mode-field" style="margin-bottom:20px;">
          <div class="detail-label">名前 <span style="color:#e74c3c;">*</span></div>
          <input type="text" class="edit-field" name="name" value="{escape(person.name)}" required data-field="name" style="font-size:1.2rem;font-weight:600;">
        </div>
        {row("所属・会社名", person.organization, "organization")}
        {row("出会った場所・きっかけ", person.met_at, "met_at")}
        <div class="detail-row">
          <div class="detail-label">誕生日</div>
          <div class="detail-value view-mode-only">{escape(bd_display) if bd_display else '<span style="color:#94a3b8;">未設定</span>'}</div>
          <div class="edit-mode-field">
            <input type="date" class="edit-field" name="birthday" value="{escape(bd_value)}" data-field="birthday">
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-label">既婚・未婚</div>
          <div class="detail-value view-mode-only">{escape(person.marital_status) if person.marital_status else '<span style="color:#94a3b8;">未設定</span>'}</div>
          <div class="edit-mode-field">
            <select class="edit-field" name="marital_status" data-field="marital_status">
              <option value="">選択してください</option>
              <option value="既婚"{' selected' if person.marital_status == '既婚' else ''}>既婚</option>
              <option value="未婚"{' selected' if person.marital_status == '未婚' else ''}>未婚</option>
            </select>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-label">子供</div>
          <div class="detail-value view-mode-only">{escape(person.has_children) if person.has_children else '<span style="color:#94a3b8;">未設定</span>'}</div>
          <div class="edit-mode-field">
            <select class="edit-field" name="has_children" data-field="has_children">
              <option value="">選択してください</option>
              <option value="あり"{' selected' if person.has_children == 'あり' else ''}>あり</option>
              <option value="なし"{' selected' if person.has_children == 'なし' else ''}>なし</option>
            </select>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-label">ペット</div>
          <div class="detail-value view-mode-only">{escape(person.has_pets) if person.has_pets else '<span style="color:#94a3b8;">未設定</span>'}</div>
          <div class="edit-mode-field">
            <select class="edit-field" name="has_pets" data-field="has_pets">
              <option value="">選択してください</option>
              <option value="あり"{' selected' if person.has_pets == 'あり' else ''}>あり</option>
              <option value="なし"{' selected' if person.has_pets == 'なし' else ''}>なし</option>
            </select>
          </div>
        </div>
        {row("メモ・特徴", person.notes, "notes", "notes", "textarea")}

        <div style="margin-top:24px;padding-top:24px;border-top:1px solid #e2e8f0;">
          <h3 style="font-size:1.1rem;margin-bottom:16px;color:#1e3a5f;">SNS・ウェブサイト</h3>
          {row("X (Twitter)", person.twitter, "twitter", "", "url")}
          {row("Instagram", person.instagram, "instagram", "", "url")}
          {row("Facebook", person.facebook, "facebook", "", "url")}
          {row("LinkedIn", person.linkedin, "linkedin", "", "url")}
        </div>

        <div class="detail-row view-mode-only">
          <div class="detail-label">登録日</div>
          <div class="detail-value">{escape(str(person.created_at))}</div>
        </div>
        <div class="detail-row view-mode-only">
          <div class="detail-label">最終更新</div>
          <div class="detail-value">{escape(str(person.updated_at))}</div>
        </div>

        <div class="detail-actions view-mode-only">
          <a href="/" class="btn btn-secondary">一覧に戻る</a>
        </div>

        <div class="detail-actions edit-mode-actions">
          <button type="submit" class="btn btn-primary">💾 保存する</button>
          <button type="button" class="btn btn-secondary" onclick="cancelEdit()">キャンセル</button>
          <button type="button" class="btn btn-danger" onclick="confirmDelete()">削除</button>
        </div>
      </form>
    </div>

    <div class="section-card">
      <div class="section-header">
        <h3>家族</h3>
        <a href="/person/{person.id}/family/add" class="btn btn-primary section-add-btn" style="padding:8px 18px;font-size:.9rem;">+ 家族を追加</a>
      </div>
      <div class="family-list">
        {family_items}
      </div>
    </div>

    <div class="section-card">
      <div class="section-header">
        <h3>沿革</h3>
        <a href="/person/{person.id}/events/add" class="btn btn-primary section-add-btn" style="padding:8px 18px;font-size:.9rem;">+ イベントを追加</a>
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
        person.marital_status = request.form.get("marital_status", "").strip() or None
        person.has_children = request.form.get("has_children", "").strip() or None
        person.has_pets = request.form.get("has_pets", "").strip() or None
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


@app.route("/person/<int:person_id>/update", methods=["POST"])
def update_person(person_id):
    """Inline update from detail page"""
    person = db.session.get(Person, person_id)
    if not person:
        return "Not found", 404

    # Update name if provided
    name = request.form.get("name", "").strip()
    if name:
        person.name = name

    person.organization = request.form.get("organization", "").strip()
    person.met_at = request.form.get("met_at", "").strip()
    person.birthday = request.form.get("birthday", "").strip() or None
    person.notes = request.form.get("notes", "").strip()

    # Update SNS fields
    person.twitter = request.form.get("twitter", "").strip() or None
    person.instagram = request.form.get("instagram", "").strip() or None
    person.facebook = request.form.get("facebook", "").strip() or None
    person.linkedin = request.form.get("linkedin", "").strip() or None

    # Update personal info fields
    person.marital_status = request.form.get("marital_status", "").strip() or None
    person.has_children = request.form.get("has_children", "").strip() or None
    person.has_pets = request.form.get("has_pets", "").strip() or None

    person.updated_at = datetime.now()
    db.session.commit()
    return "", 200


@app.route("/person/<int:person_id>/delete", methods=["POST"])
def delete_person(person_id):
    """Delete from detail page"""
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


@app.route("/event/<int:event_id>/edit", methods=["GET", "POST"])
def edit_event(event_id):
    event = db.session.get(Event, event_id)
    if not event:
        return layout("見つかりません", '<div class="empty"><p>指定されたイベントが見つかりません。</p></div>'), 404

    person = db.session.get(Person, event.person_id)
    if not person:
        return layout("見つかりません", '<div class="empty"><p>指定された人物が見つかりません。</p></div>'), 404

    if request.method == "POST":
        event_date = request.form.get("event_date", "").strip()
        content = request.form.get("content", "").strip()
        if not event_date or not content:
            return layout("イベント編集", _event_form(person, event=event, error="日付と内容は必須です。")), 400

        # Handle image upload if new image provided
        new_image = request.files.get("image")
        if new_image and new_image.filename:
            image_url, upload_err = _upload_image(new_image)
            if upload_err:
                return layout("イベント編集", _event_form(person, event=event, error=upload_err)), 400
            event.image_url = image_url

        event.event_date = event_date
        event.content = content
        person.updated_at = datetime.now()
        db.session.commit()
        return redirect(url_for("detail", person_id=person.id))

    return layout("イベント編集", _event_form(person, event=event))


def _event_form(person, event=None, error=None):
    err_html = f'<p style="color:#e74c3c;margin-bottom:12px;">{escape(error)}</p>' if error else ""

    # Set defaults for add or edit mode
    if event:
        title = "イベント編集"
        action = f"/event/{event.id}/edit"
        btn_text = "更新する"
        event_date = escape(event.event_date)
        content = escape(event.content)
        current_image = event.image_url
    else:
        title = "イベント追加"
        action = f"/person/{person.id}/events/add"
        btn_text = "追加する"
        event_date = datetime.now().strftime("%Y-%m-%d")
        content = ""
        current_image = None

    # Show current image if exists
    image_preview = ""
    if current_image:
        image_preview = f'<div style="margin-bottom:10px;"><img src="{escape(current_image)}" style="max-width:200px;max-height:200px;border-radius:8px;"><p style="font-size:.85rem;color:#64748b;margin-top:4px;">現在の写真（新しい写真をアップロードすると置き換わります）</p></div>'

    return f"""
    <div class="form-card">
      <h2>{escape(person.name)} - {title}</h2>
      {err_html}
      <form method="post" action="{action}" enctype="multipart/form-data">
        <div class="form-group">
          <label for="event_date">日付 <span style="color:#e74c3c;">*</span></label>
          <input type="date" id="event_date" name="event_date" value="{event_date}" required>
        </div>
        <div class="form-group">
          <label for="content">内容 <span style="color:#e74c3c;">*</span></label>
          <textarea id="content" name="content" placeholder="何があったかを記録..." required>{content}</textarea>
        </div>
        <div class="form-group">
          <label for="image">写真（任意・1枚まで）</label>
          {image_preview}
          <input type="file" id="image" name="image" accept="image/*">
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;">
          <button type="submit" class="btn btn-primary">{btn_text}</button>
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
