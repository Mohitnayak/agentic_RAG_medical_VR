from app.rag.retriever import Retriever
from app.rag.faiss_store import FAISSVectorStore


class DummyClient:
    def embed(self, texts):
        # map text to simple vectors: count of 'a', 'b'
        vecs = []
        for t in texts:
            vecs.append([float(t.count('a')), float(t.count('b')), 0.0, 0.0])
        return vecs


def test_retriever_query_and_context(monkeypatch, tmp_path):
    store = FAISSVectorStore(dim=4, storage_dir=str(tmp_path))
    retr = Retriever(store, embedding_dim=4)

    # Patch client
    from app.llm import ollama_client as oc
    monkeypatch.setattr(oc, 'OllamaClient', lambda *a, **k: DummyClient())

    ids = ["c1", "c2"]
    embeddings = DummyClient().embed(["aaaa", "bbbb"])  # [4,0] and [0,4]
    metas = [{"chunk_id": "c1"}, {"chunk_id": "c2"}]
    store.upsert(ids, embeddings, metas)

    res = retr.retrieve("aaaa")
    assert res[0][0] == "c1"

    lookup = {"c1": "aaaa text", "c2": "bbbb text"}
    ctx = retr.build_context("q", res, lookup)
    assert "aaaa text" in ctx


