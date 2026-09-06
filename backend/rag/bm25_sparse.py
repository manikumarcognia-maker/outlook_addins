"""Local BM25 sparse embeddings — no HuggingFace downloads.

Matches the Qdrant/fastembed BM25 algorithm (mmh3 token hashing, Snowball
stemming, IDF applied by Qdrant at query time via modifier=idf).
"""

import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import mmh3
from langchain_qdrant.sparse_embeddings import SparseEmbeddings, SparseVector
from py_rust_stemmers import SnowballStemmer

_STOPWORDS_PATH = Path(__file__).resolve().parent / "data" / "bm25" / "english.txt"

_TOKEN_RE = re.compile(r"[^\w]", re.UNICODE)
_WHITESPACE_RE = re.compile(r"\s+")


def _get_punctuation() -> set[str]:
    return {
        chr(i)
        for i in range(sys.maxunicode)
        if unicodedata.category(chr(i)).startswith("P")
    }


def _remove_non_alphanumeric(text: str) -> str:
    return re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)


def _tokenize(text: str) -> list[str]:
    text = _TOKEN_RE.sub(" ", text.lower())
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip().split()


def _load_stopwords(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    return {line.strip().lower() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def _compute_token_id(token: str) -> int:
    return abs(mmh3.hash(token))


class LocalBm25Sparse(SparseEmbeddings):
    """BM25 sparse vectors compatible with Qdrant IDF modifier — fully offline."""

    def __init__(
        self,
        language: str = "english",
        k: float = 1.2,
        b: float = 0.75,
        avg_len: float = 256.0,
        token_max_length: int = 40,
        stopwords_path: Path | None = None,
    ):
        self.k = k
        self.b = b
        self.avg_len = avg_len
        self.token_max_length = token_max_length
        self.punctuation = _get_punctuation()
        stopwords_file = stopwords_path or _STOPWORDS_PATH
        self.stopwords = _load_stopwords(stopwords_file)
        self.stemmer = SnowballStemmer(language)

    def _stem(self, tokens: list[str]) -> list[str]:
        stemmed: list[str] = []
        for token in tokens:
            if token in self.punctuation:
                continue
            if token.lower() in self.stopwords:
                continue
            if len(token) > self.token_max_length:
                continue
            stemmed_token = self.stemmer.stem_word(token.lower())
            if stemmed_token:
                stemmed.append(stemmed_token)
        return stemmed

    def _term_frequency(self, tokens: list[str]) -> dict[int, float]:
        counter: dict[str, int] = defaultdict(int)
        for token in tokens:
            counter[token] += 1

        doc_len = len(tokens)
        tf_map: dict[int, float] = {}
        for stemmed_token, num_occurrences in counter.items():
            token_id = _compute_token_id(stemmed_token)
            tf_map[token_id] = num_occurrences * (self.k + 1)
            tf_map[token_id] /= num_occurrences + self.k * (
                1 - self.b + self.b * doc_len / self.avg_len
            )
        return tf_map

    def _document_vector(self, text: str) -> SparseVector:
        cleaned = _remove_non_alphanumeric(text)
        tokens = self._stem(_tokenize(cleaned))
        tf_map = self._term_frequency(tokens)
        indices = list(tf_map.keys())
        values = [tf_map[i] for i in indices]
        return SparseVector(indices=indices, values=values)

    def _query_vector(self, text: str) -> SparseVector:
        cleaned = _remove_non_alphanumeric(text)
        tokens = self._stem(_tokenize(cleaned))
        unique_ids = list({_compute_token_id(token) for token in tokens})
        return SparseVector(indices=unique_ids, values=[1.0] * len(unique_ids))

    def embed_documents(self, texts: list[str]) -> list[SparseVector]:
        return [self._document_vector(text) for text in texts]

    def embed_query(self, text: str) -> SparseVector:
        return self._query_vector(text)


def get_sparse_embeddings() -> LocalBm25Sparse:
    return LocalBm25Sparse()
