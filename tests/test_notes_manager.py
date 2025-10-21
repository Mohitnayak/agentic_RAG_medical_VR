import pytest
from flask import Flask

from app import create_app
from app.models import db, Note
from app.notes.manager import NotesManager


@pytest.fixture()
def app_ctx(tmp_path):
    app = create_app()
    app.config.update(SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path}/test.db", TESTING=True)
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app


def test_notes_flow(app_ctx):
    mgr = NotesManager()
    session_id = "s1"
    mgr.start(session_id)
    n1 = mgr.add(session_id, "note 1")
    n2 = mgr.add(session_id, "note 2")
    assert n1.id != n2.id

    active = Note.query.filter_by(session_id=session_id, finalized=False).count()
    assert active == 2

    finalized = mgr.end(session_id)
    assert len(finalized) == 2
    active_after = Note.query.filter_by(session_id=session_id, finalized=False).count()
    assert active_after == 0


