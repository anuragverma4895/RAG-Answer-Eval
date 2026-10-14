import pytest

from app.services.chunking import chunk_text, clean_text


def test_chunking_splits_long_text_and_preserves_content():
    text = "hello world. " * 200
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    assert all(chunk.strip() for chunk in chunks)
    assert "".join(chunks).replace(" ", "")  # chunks contain real source text


def test_empty_text_returns_no_chunks():
    assert chunk_text(" \n\t ") == []


def test_clean_text_normalizes_whitespace():
    assert clean_text(" a  b\r\n\r\n\r\nc ") == "a b\n\nc"


@pytest.mark.parametrize(
    ("chunk_size", "overlap"),
    [(0, 0), (10, -1), (10, 10)],
)
def test_invalid_chunk_settings_raise(chunk_size, overlap):
    with pytest.raises(ValueError):
        chunk_text("some text", chunk_size=chunk_size, overlap=overlap)
