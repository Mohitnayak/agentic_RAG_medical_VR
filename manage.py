import click
from flask.cli import with_appcontext

from app import create_app
from app.models import db, Document, Chunk
from app.rag.chunker import split_text
from app.llm.ollama_client import OllamaClient
from app.rag.faiss_store import FAISSVectorStore


app = create_app()


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Create all database tables."""
    db.create_all()
    click.echo("Database initialized.")


@click.command("ingest-text")
@click.option("--text", "text_", type=str, required=False, help="Raw text to ingest")
@click.option("--file", "file_", type=click.Path(exists=True), required=False, help="Path to a text file")
@click.option("--title", type=str, required=False, help="Document title")
@click.option("--domain", type=str, required=False, help="Domain tag, e.g., dental")
@with_appcontext
def ingest_text_command(text_: str | None, file_: str | None, title: str | None, domain: str | None):
    """Ingest raw text or a text file into the vector store using Ollama embeddings."""
    if not text_ and not file_:
        raise click.UsageError("Provide --text or --file")
    payload = text_
    if file_:
        with open(file_, "r", encoding="utf-8") as f:
            payload = f.read()
    assert payload is not None

    # Create a new Document
    import uuid

    doc_id = str(uuid.uuid4())
    doc = Document(id=doc_id, source_type="text", title=title, domain=domain)
    db.session.add(doc)

    # Chunk and embed
    chunks = split_text(payload)
    client = OllamaClient()
    embeddings = client.embed(chunks)

    # Upsert into FAISS and persist chunks in DB
    store = FAISSVectorStore(dim=768)
    ids = []
    metas = []
    for idx, txt in enumerate(chunks):
        cid = str(uuid.uuid4())
        ids.append(cid)
        metas.append({"document_id": doc_id, "chunk_id": cid, "idx": idx})
        db.session.add(Chunk(id=cid, document_id=doc_id, text=txt, meta={"document_id": doc_id, "idx": idx}))
    db.session.commit()
    store.upsert(ids, embeddings, metas)
    store.persist()
    click.echo(f"Ingested document {doc_id} with {len(chunks)} chunks")


app.cli.add_command(init_db_command)
app.cli.add_command(ingest_text_command)

if __name__ == "__main__":
    # For development only
    app.run(host="0.0.0.0", port=5000, debug=True)


