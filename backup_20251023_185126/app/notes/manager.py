from __future__ import annotations

from typing import List

from ..models import db, Note, Session


class NotesManager:
    def start(self, session_id: str) -> None:
        sess = Session.query.get(session_id)
        if not sess:
            sess = Session(id=session_id)
            db.session.add(sess)
        # no explicit state column; active is inferred by presence of non-finalized notes
        db.session.commit()

    def add(self, session_id: str, text: str) -> Note:
        note = Note(session_id=session_id, text=text, finalized=False)
        db.session.add(note)
        db.session.commit()
        return note

    def end(self, session_id: str) -> List[Note]:
        notes = Note.query.filter_by(session_id=session_id, finalized=False).all()
        for n in notes:
            n.finalized = True
        db.session.commit()
        return notes

    def list(self, session_id: str) -> List[Note]:
        return Note.query.filter_by(session_id=session_id).order_by(Note.created_at.asc()).all()


