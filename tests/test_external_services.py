import pytest

from app.models.schemas import RerankRequest
from app.services.embedding import _normalize_embedding_response
from app.services.rerank import _normalize_rerank_response


def test_normalize_embedding_response_handles_embedding_list():
    payload = {
        "data": [
            {
                "index": 2,
                "embedding": [0.1, 0.2, 0.3],
            }
        ],
        "model": "external-embedding",
        "usage": {"prompt_tokens": 3, "completion_tokens": 0, "total_tokens": 3},
    }

    response = _normalize_embedding_response(payload, "fallback-model")

    assert response.model == "external-embedding"
    assert len(response.data) == 1
    assert response.data[0].index == 2
    assert response.data[0].embedding == [0.1, 0.2, 0.3]
    assert response.usage.prompt_tokens == 3
    assert response.usage.total_tokens == 3


def test_normalize_rerank_response_populates_documents_from_request():
    payload = {
        "results": [
            {
                "index": 1,
                "score": 0.85,
            }
        ],
    }

    request = RerankRequest(
        model="text-rerank-002",
        query="test query",
        documents=["doc0", "doc1"],
        return_documents=True,
    )

    response = _normalize_rerank_response(payload, request.model, request)

    assert response.model == "text-rerank-002"
    assert len(response.data) == 1
    result = response.data[0]
    assert result.index == 1
    assert result.score == pytest.approx(0.85)
    assert result.document == "doc1"


def test_normalize_rerank_response_raises_on_missing_scores():
    payload = {"data": [{"index": 0}]}
    request = RerankRequest(
        model="text-rerank-002",
        query="query",
        documents=["doc"],
        return_documents=False,
    )

    with pytest.raises(ValueError):
        _normalize_rerank_response(payload, "fallback", request)
