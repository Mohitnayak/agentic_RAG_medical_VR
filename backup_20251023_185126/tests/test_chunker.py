from app.rag.chunker import split_text


def test_split_text_basic():
    text = "a" * 3000
    chunks = split_text(text, max_chars=1000, overlap=100)
    assert len(chunks) >= 3
    assert sum(len(c) for c in chunks) >= 3000 - 50


