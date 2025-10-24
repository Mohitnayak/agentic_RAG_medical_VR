from app.rag.faiss_store import FAISSVectorStore


def test_faiss_upsert_and_query(tmp_path):
    store = FAISSVectorStore(dim=4, storage_dir=str(tmp_path))
    ids = ["a", "b"]
    embeddings = [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
    ]
    metas = [{"i": 0}, {"i": 1}]
    store.upsert(ids, embeddings, metas)
    store.persist()

    results = store.query([1.0, 0.0, 0.0, 0.0], k=1)
    assert len(results) == 1
    rid, score, meta = results[0]
    assert rid == "a"
    assert score > 0.9


