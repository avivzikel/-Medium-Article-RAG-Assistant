from app.rag.chunking import chunk_text


def test_chunk_text_overlap() -> None:
    text = ' '.join(f'w{i}' for i in range(20))
    chunks = chunk_text(text, chunk_size=10, overlap_ratio=0.2)

    assert len(chunks) == 3
    assert chunks[0].split()[0] == 'w0'
    assert chunks[1].split()[0] == 'w8'
