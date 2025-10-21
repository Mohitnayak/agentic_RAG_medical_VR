from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON


db = SQLAlchemy()


class Session(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.String(64), primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    meta = db.Column("metadata", JSON, nullable=True)


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.String(64), primary_key=True)
    source_type = db.Column(db.String(32), nullable=False)
    title = db.Column(db.String(256), nullable=True)
    domain = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Chunk(db.Model):
    __tablename__ = "chunks"

    id = db.Column(db.String(64), primary_key=True)
    document_id = db.Column(db.String(64), db.ForeignKey("documents.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    # NOTE: embeddings are stored in vector store (FAISS) not DB in v1
    meta = db.Column("metadata", JSON, nullable=True)

    document = db.relationship("Document", backref=db.backref("chunks", lazy=True))


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.String(64), db.ForeignKey("sessions.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    finalized = db.Column(db.Boolean, nullable=False, default=False)

    session = db.relationship("Session", backref=db.backref("notes", lazy=True))


