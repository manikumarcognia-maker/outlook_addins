from rag.bm25_sparse import LocalBm25Sparse


def test_local_bm25_produces_sparse_vectors():
    embedder = LocalBm25Sparse()
    doc = embedder.embed_documents(["Freight transit from Mumbai to Singapore takes 14 days."])
    query = embedder.embed_query("Mumbai Singapore transit")

    assert len(doc) == 1
    assert len(doc[0].indices) == len(doc[0].values)
    assert len(doc[0].indices) > 0
    assert len(query.indices) == len(query.values)
    assert len(query.indices) > 0


def test_local_bm25_no_duplicate_indices_in_document():
    embedder = LocalBm25Sparse()
    doc = embedder.embed_documents(["policy policy policy terms terms"])
    assert len(doc[0].indices) == len(set(doc[0].indices))
