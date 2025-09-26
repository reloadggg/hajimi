import httpx
import random
import asyncio
from typing import List, Union, Optional, Dict, Any
from app.models.schemas import EmbeddingRequest, EmbeddingData, EmbeddingResponse, Usage
from app.utils.logging import log, vertex_log
from app.services.external_service import build_service_url, build_headers, get_timeout, is_configured
import app.config.settings as settings

# Optional Vertex imports
try:
    from google import genai
    from google.genai import types
    import app.vertex.config as app_vertex_config
    from app.vertex.credentials_manager import (
        CredentialManager,
        parse_multiple_json_credentials,
    )
except Exception:  # ImportError or runtime missing deps
    genai = None
    types = None
    app_vertex_config = None
    CredentialManager = None
    parse_multiple_json_credentials = None




def _extract_embedding_values(item: Any) -> Optional[List[float]]:
    if isinstance(item, dict):
        for key in ("embedding", "values", "vector"):
            candidate = item.get(key)
            if isinstance(candidate, list):
                return candidate
        # Some services may return embeddings nested under metadata
        metadata = item.get("metadata")
        if isinstance(metadata, dict):
            for key in ("embedding", "values", "vector"):
                candidate = metadata.get(key)
                if isinstance(candidate, list):
                    return candidate
        return None
    if isinstance(item, list):
        return item
    return None


def _normalize_embedding_response(payload: Dict[str, Any], fallback_model: str) -> EmbeddingResponse:
    data_items = payload.get("data") or payload.get("embeddings") or []
    embedding_data: List[EmbeddingData] = []

    for idx, item in enumerate(data_items):
        vector = _extract_embedding_values(item)
        if vector is None:
            continue
        index_value = idx
        if isinstance(item, dict):
            index_value = int(item.get("index", idx))
        embedding_data.append(EmbeddingData(embedding=vector, index=index_value))

    if not embedding_data:
        raise ValueError("No embeddings returned from external service")

    usage_payload = payload.get("usage") or {}
    prompt_tokens = int(usage_payload.get("prompt_tokens", 0))
    completion_tokens = int(usage_payload.get("completion_tokens", 0))
    total_tokens = int(usage_payload.get("total_tokens", prompt_tokens + completion_tokens))

    usage = Usage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )

    model_name = payload.get("model") or fallback_model

    return EmbeddingResponse(
        object=payload.get("object", "list"),
        data=embedding_data,
        model=model_name,
        usage=usage,
    )

def _as_list(input_value: Union[str, List[str]]) -> List[str]:
    if isinstance(input_value, list):
        return input_value
    return [input_value]


def _build_contents(inputs: List[str]) -> List["types.Content"]:
    if types is None:
        return []
    contents: List["types.Content"] = []
    for text in inputs:
        contents.append(types.Content(parts=[types.Part(text=text)]))
    return contents


async def _vertex_embed_with_express(inputs: List[str], model: str) -> Optional[List[List[float]]]:
    if genai is None:
        return None

    # Collect keys from settings or app config
    express_keys: List[str] = []
    if getattr(settings, "VERTEX_EXPRESS_API_KEY", ""):
        express_keys = [key.strip() for key in settings.VERTEX_EXPRESS_API_KEY.split(",") if key.strip()]
    elif app_vertex_config and getattr(app_vertex_config, "VERTEX_EXPRESS_API_KEY_VAL", None):
        express_keys = list(app_vertex_config.VERTEX_EXPRESS_API_KEY_VAL)

    if not express_keys:
        return None

    indexed_keys = list(enumerate(express_keys))
    random.shuffle(indexed_keys)

    contents = _build_contents(inputs)
    last_error = None

    for original_idx, key_val in indexed_keys:
        try:
            client = genai.Client(vertexai=True, api_key=key_val)
            vertex_log("info", f"Vertex embeddings using Express key (original index {original_idx})")

            loop = asyncio.get_running_loop()

            def _call_embed():
                return client.models.embed_content(model=model, contents=contents)

            response = await loop.run_in_executor(None, _call_embed)
            return [embedding.values for embedding in response.embeddings]
        except Exception as exc:  # pragma: no cover
            vertex_log("warning", f"Express embedding request failed for key index {original_idx}: {exc}")
            last_error = exc

    if last_error:
        vertex_log("error", f"All express keys failed for Vertex embeddings: {last_error}")
    return None


async def _vertex_embed_with_service_account(inputs: List[str], model: str) -> Optional[List[List[float]]]:
    if genai is None or CredentialManager is None:
        return None

    credential_manager = CredentialManager()
    # Opportunistically load GOOGLE_CREDENTIALS_JSON if provided
    if getattr(settings, "GOOGLE_CREDENTIALS_JSON", None) and parse_multiple_json_credentials:
        try:
            parsed = parse_multiple_json_credentials(settings.GOOGLE_CREDENTIALS_JSON)
            if parsed:
                credential_manager.load_credentials_from_json_list(parsed)
        except Exception:
            pass

    credentials, project_id = credential_manager.get_random_credentials()
    if not credentials or not project_id:
        return None

    location = getattr(app_vertex_config, "LOCATION", "us-central1") if app_vertex_config else "us-central1"

    try:
        client = genai.Client(vertexai=True, credentials=credentials, project=project_id, location=location)
        vertex_log("info", f"Vertex embeddings using SA credential (project {project_id}, location {location})")

        contents = _build_contents(inputs)
        loop = asyncio.get_running_loop()

        def _call_embed():
            return client.models.embed_content(model=model, contents=contents)

        response = await loop.run_in_executor(None, _call_embed)
        return [embedding.values for embedding in response.embeddings]
    except Exception as exc:  # pragma: no cover
        vertex_log("error", f"Service account embedding request failed for project {project_id}: {exc}")
        return None


class EmbeddingClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def _create_external_embeddings(self, request: EmbeddingRequest) -> Optional[EmbeddingResponse]:
        if not is_configured():
            return None

        url = build_service_url("embeddings_path", "/v1/embeddings")
        if not url:
            return None

        headers = build_headers()
        payload = request.model_dump(exclude_none=True)

        try:
            async with httpx.AsyncClient(timeout=get_timeout()) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            log(
                "ERROR",
                f"External embedding request failed: {exc}",
                extra={"model": request.model},
            )
            raise

        response_json = response.json()
        return _normalize_embedding_response(response_json, request.model)

    async def create_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        model_name = request.model
        inputs = _as_list(request.input)

        external_response = await self._create_external_embeddings(request)
        if external_response is not None:
            return external_response

        # Prefer Vertex path when enabled
        if getattr(settings, "ENABLE_VERTEX_EXPRESS", False) or getattr(settings, "ENABLE_VERTEX", False):
            # Try Express keys first
            embeddings = await _vertex_embed_with_express(inputs, model_name)
            if not embeddings and getattr(settings, "ENABLE_VERTEX", False):
                embeddings = await _vertex_embed_with_service_account(inputs, model_name)

            if embeddings:
                embedding_data = [
                    EmbeddingData(embedding=vec, index=i) for i, vec in enumerate(embeddings)
                ]
                usage = Usage(prompt_tokens=0, total_tokens=0)
                return EmbeddingResponse(
                    object="list",
                    data=embedding_data,
                    model=model_name,
                    usage=usage,
                )

        # Fallback to Google AI Studio embeddings HTTP API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:batchEmbedContents"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

        data = {
            "requests": [
                {
                    "model": f"models/{model_name}",
                    "content": {"parts": [{"text": text}]},
                }
                for text in inputs
            ]
        }

        extra_log = {"key": self.api_key[:8], "model": model_name}
        log("INFO", "Embedding request started", extra=extra_log)

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()

            response_json = response.json()
            log("INFO", f"Google AI API response: {response_json}")

            embeddings = response_json.get("embeddings", [])
            embedding_data = [
                EmbeddingData(embedding=item["values"], index=i)
                for i, item in enumerate(embeddings)
            ]

            usage = Usage(prompt_tokens=0, total_tokens=0)
            return EmbeddingResponse(
                object="list",
                data=embedding_data,
                model=model_name,
                usage=usage,
            )
