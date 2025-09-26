from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import httpx

from app.models.schemas import RerankRequest, RerankResponse, RerankResult
from app.services.external_service import (
    build_service_url,
    build_headers,
    get_timeout,
    is_configured,
)
from app.utils.logging import log


def _normalize_rerank_response(
    payload: Dict[str, Any], fallback_model: str, request: RerankRequest
) -> RerankResponse:
    data_items: List[Dict[str, Any]] = []
    if "data" in payload and isinstance(payload["data"], list):
        data_items = payload["data"]
    elif "results" in payload and isinstance(payload["results"], list):
        data_items = payload["results"]
    else:
        raise ValueError("No rerank results returned from external service")

    normalized_results: List[RerankResult] = []
    for idx, item in enumerate(data_items):
        if isinstance(item, dict):
            index_value = int(item.get("index", idx))
            score_value = item.get("score")
            if score_value is None:
                score_value = item.get("relevance_score")
            if score_value is None:
                raise ValueError("Missing score in rerank response item")
            document_value: Optional[Any] = item.get("document")
            if document_value is None and request.return_documents:
                if 0 <= index_value < len(request.documents):
                    document_value = request.documents[index_value]
            normalized_results.append(
                RerankResult(
                    index=index_value,
                    score=float(score_value),
                    relevance_score=(
                        float(item["relevance_score"]) if "relevance_score" in item else None
                    ),
                    document=document_value,
                )
            )
        else:
            raise ValueError("Unexpected rerank response structure")

    model_name = payload.get("model") or fallback_model

    return RerankResponse(
        object=payload.get("object", "list"),
        model=model_name,
        data=normalized_results,
    )


class RerankClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def rerank(self, request: RerankRequest) -> RerankResponse:
        if not is_configured():
            raise ValueError("External rerank service is not configured")

        url = build_service_url("rerank_path", "/v1/rerank")
        if not url:
            raise ValueError("External rerank service is not configured")

        headers = build_headers()
        payload = request.model_dump(exclude_none=True)

        try:
            async with httpx.AsyncClient(timeout=get_timeout()) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            log(
                "ERROR",
                f"External rerank request failed: {exc}",
                extra={"model": request.model},
            )
            raise

        response_json: Dict[str, Any] = response.json()
        return _normalize_rerank_response(response_json, request.model, request)
