import asyncio
import random
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.models.schemas import (
    EmbeddingData,
    EmbeddingRequest,
    EmbeddingResponse,
    Usage,
)
from app.vertex.auth import get_api_key
from app.vertex.credentials_manager import (
    CredentialManager,
    parse_multiple_json_credentials,
)
from app.utils.logging import vertex_log
from app.config import settings
import app.vertex.config as app_config

from google import genai
from google.genai import types

router = APIRouter()


def _build_contents(inputs: List[str]) -> List[types.Content]:
    contents: List[types.Content] = []
    for text in inputs:
        contents.append(types.Content(parts=[types.Part(text=text)]))
    return contents


async def _embed_with_express(inputs: List[str], model: str) -> List[List[float]]:
    express_keys: List[str] = []
    if getattr(settings, "VERTEX_EXPRESS_API_KEY", ""):
        express_keys = [
            key.strip()
            for key in settings.VERTEX_EXPRESS_API_KEY.split(",")
            if key.strip()
        ]
    elif app_config.VERTEX_EXPRESS_API_KEY_VAL:
        express_keys = list(app_config.VERTEX_EXPRESS_API_KEY_VAL)

    if not express_keys:
        return None

    indexed_keys = list(enumerate(express_keys))
    random.shuffle(indexed_keys)

    contents = _build_contents(inputs)
    last_error = None

    for original_idx, key_val in indexed_keys:
        try:
            client = genai.Client(vertexai=True, api_key=key_val)
            vertex_log(
                "info",
                f"Vertex embeddings using Express key (original index {original_idx})",
            )

            loop = asyncio.get_running_loop()

            def _call_embed():
                return client.models.embed_content(
                    model=model,
                    contents=contents,
                )

            response = await loop.run_in_executor(None, _call_embed)
            return [embedding.values for embedding in response.embeddings]
        except Exception as exc:  # pragma: no cover - network path
            vertex_log(
                "warning",
                f"Express embedding request failed for key index {original_idx}: {exc}",
            )
            last_error = exc

    if last_error:
        vertex_log(
            "error",
            f"All express keys failed for Vertex embeddings: {last_error}",
        )
    return None


async def _embed_with_service_account(
    credential_manager: CredentialManager, inputs: List[str], model: str
) -> List[List[float]]:
    credentials, project_id = credential_manager.get_random_credentials()
    if not credentials or not project_id:
        return None

    location = getattr(app_config, "LOCATION", "us-central1") or "us-central1"

    try:
        client = genai.Client(
            vertexai=True,
            credentials=credentials,
            project=project_id,
            location=location,
        )
        vertex_log(
            "info",
            f"Vertex embeddings using SA credential (project {project_id}, location {location})",
        )

        contents = _build_contents(inputs)
        loop = asyncio.get_running_loop()

        def _call_embed():
            return client.models.embed_content(
                model=model,
                contents=contents,
            )

        response = await loop.run_in_executor(None, _call_embed)
        return [embedding.values for embedding in response.embeddings]
    except Exception as exc:  # pragma: no cover - network path
        vertex_log(
            "error",
            f"Service account embedding request failed for project {project_id}: {exc}",
        )
        return None


@router.post("/v1/embeddings", response_model=EmbeddingResponse)
async def create_embeddings(
    request: Request,
    embedding_request: EmbeddingRequest,
    _api_key: str = Depends(get_api_key),
):
    try:
        credential_manager = request.app.state.credential_manager
    except AttributeError:
        credential_manager = CredentialManager()
        request.app.state.credential_manager = credential_manager

    current_total = credential_manager.get_total_credentials()
    if current_total == 0:
        vertex_log(
            "debug",
            f"settings.GOOGLE_CREDENTIALS_JSON length: {len(getattr(settings, 'GOOGLE_CREDENTIALS_JSON', '') or '')}",
        )
        if getattr(settings, "GOOGLE_CREDENTIALS_JSON", ""):
            parsed_json = parse_multiple_json_credentials(
                settings.GOOGLE_CREDENTIALS_JSON
            )
            if parsed_json:
                vertex_log(
                    "debug", f"Parsed {len(parsed_json)} credentials from settings JSON"
                )
                credential_manager.load_credentials_from_json_list(parsed_json)
        credential_manager.refresh_credentials_list()
    vertex_log(
        "debug",
        f"Vertex embeddings credential manager total: {credential_manager.get_total_credentials()}",
    )

    inputs: List[str]
    if isinstance(embedding_request.input, str):
        inputs = [embedding_request.input]
    else:
        inputs = list(embedding_request.input)

    if not inputs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Embedding input 不能为空",
        )

    model_name = (embedding_request.model or "").strip()
    if not model_name:
        vertex_default = getattr(settings, "vertex_embedding", {}).get(
            "default_model", ""
        )
        model_name = vertex_default or settings.embedding.get("default_model", "")

    if not model_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Embedding model 未配置",
        )

    embeddings = await _embed_with_express(inputs, model_name)
    if embeddings is None:
        embeddings = await _embed_with_service_account(
            credential_manager, inputs, model_name
        )

    if embeddings is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="无法创建 Vertex Embedding，缺少可用凭据或请求失败",
        )

    embedding_data = [
        EmbeddingData(embedding=vector, index=idx)
        for idx, vector in enumerate(embeddings)
    ]

    usage = Usage(prompt_tokens=0, total_tokens=0)

    return EmbeddingResponse(
        object="list",
        data=embedding_data,
        model=model_name,
        usage=usage,
    )
