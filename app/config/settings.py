import os
import pathlib
import logging
import asyncio



def _get_env_str(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().strip('"')


def _get_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().strip('"').lower() in {"true", "1", "yes"}


def _get_optional_int(name: str):
    raw = os.environ.get(name)
    if raw is None:
        return None
    cleaned = raw.strip().strip('"')
    if not cleaned:
        return None
    try:
        return int(cleaned)
    except ValueError:
        return None


def _get_optional_float(name: str):
    raw = os.environ.get(name)
    if raw is None:
        return None
    cleaned = raw.strip().strip('"')
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _get_str_list(name: str):
    raw = os.environ.get(name, "")
    if raw is None:
        return []
    return [item.strip() for item in raw.split(',') if item.strip()]
# ---------- 以下是基础配置信息 ----------

# 调用本项目时使用的密码
PASSWORD = os.environ.get("PASSWORD", "123").strip('"')

# 网页配置密码，设置后，在网页修改配置时使用 WEB_PASSWORD 而不是上面的 PASSWORD
WEB_PASSWORD = os.environ.get("WEB_PASSWORD", PASSWORD).strip('"')

# API密钥
GEMINI_API_KEYS = os.environ.get("GEMINI_API_KEYS", "")

# 假流式是否开启
FAKE_STREAMING = os.environ.get("FAKE_STREAMING", "true").lower() in [
    "true",
    "1",
    "yes",
]

# 配置持久化存储目录
STORAGE_DIR = os.environ.get("STORAGE_DIR", "/hajimi/settings/")
ENABLE_STORAGE = os.environ.get("ENABLE_STORAGE", "false").lower() in [
    "true",
    "1",
    "yes",
]

# 并发请求配置
CONCURRENT_REQUESTS = int(os.environ.get("CONCURRENT_REQUESTS", "1"))  # 默认并发请求数
INCREASE_CONCURRENT_ON_FAILURE = int(
    os.environ.get("INCREASE_CONCURRENT_ON_FAILURE", "0")
)  # 失败时增加的并发数
MAX_CONCURRENT_REQUESTS = int(
    os.environ.get("MAX_CONCURRENT_REQUESTS", "3")
)  # 最大并发请求数

# 缓存配置
CACHE_EXPIRY_TIME = int(
    os.environ.get("CACHE_EXPIRY_TIME", "21600")
)  # 默认缓存 6 小时 (21600 秒)
MAX_CACHE_ENTRIES = int(
    os.environ.get("MAX_CACHE_ENTRIES", "500")
)  # 默认最多缓存500条响应
CALCULATE_CACHE_ENTRIES = int(
    os.environ.get("CALCULATE_CACHE_ENTRIES", "6")
)  # 默认取最后 6 条消息算缓存键
PRECISE_CACHE = os.environ.get("PRECISE_CACHE", "false").lower() in [
    "true",
    "1",
    "yes",
]  # 是否取所有消息来算缓存键

# 是否启用 Vertex AI
ENABLE_VERTEX = os.environ.get("ENABLE_VERTEX", "false").lower() in ["true", "1", "yes"]
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")

# 是否启用快速模式 Vertex
ENABLE_VERTEX_EXPRESS = os.environ.get("ENABLE_VERTEX_EXPRESS", "false").lower() in [
    "true",
    "1",
    "yes",
]
VERTEX_EXPRESS_API_KEY = os.environ.get("VERTEX_EXPRESS_API_KEY", "")

# 联网搜索配置
search = {
    "search_mode": os.environ.get("SEARCH_MODE", "false").lower()
    in ["true", "1", "yes"],
    "search_prompt": os.environ.get(
        "SEARCH_PROMPT", "（使用搜索工具联网搜索，需要在content中结合搜索内容）"
    ).strip('"'),
}

# RAG 配置
gemini_rag = {
    "enabled": _get_bool("ENABLE_GEMINI_RAG"),
    "source": _get_env_str("GEMINI_RAG_SOURCE", "vertex_rag_store"),
    "corpus": _get_env_str("GEMINI_RAG_CORPUS"),
    "file_ids": _get_str_list("GEMINI_RAG_FILE_IDS"),
    "datastore": _get_env_str("GEMINI_RAG_DATASTORE"),
    "engine": _get_env_str("GEMINI_RAG_ENGINE"),
    "filter": _get_env_str("GEMINI_RAG_FILTER"),
    "top_k": _get_optional_int("GEMINI_RAG_TOP_K"),
    "similarity_top_k": _get_optional_int("GEMINI_RAG_SIMILARITY_TOP_K"),
    "max_results": _get_optional_int("GEMINI_RAG_MAX_RESULTS"),
    "vector_distance_threshold": _get_optional_float("GEMINI_RAG_VECTOR_DISTANCE_THRESHOLD"),
    "ranking_mode": _get_env_str("GEMINI_RAG_RANKING_MODE"),
    "ranking_model": _get_env_str("GEMINI_RAG_RANKING_MODEL"),
}

embedding = {
    "default_model": _get_env_str("EMBEDDING_DEFAULT_MODEL", "text-embedding-004"),
}

embedding_service = {
    "base_url": _get_env_str(
        "EMBEDDING_SERVICE_BASE_URL", "https://miku39.tech:7666"
    ),
    "embeddings_path": _get_env_str(
        "EMBEDDING_SERVICE_EMBEDDINGS_PATH", "/v1/embeddings"
    ),
    "vector_query_path": _get_env_str(
        "EMBEDDING_SERVICE_VECTOR_QUERY_PATH", "/api/vector/query"
    ),
    "rerank_path": _get_env_str(
        "EMBEDDING_SERVICE_RERANK_PATH", "/v1/rerank"
    ),
    "api_key": _get_env_str("EMBEDDING_SERVICE_API_KEY", ""),
    "timeout": _get_optional_float("EMBEDDING_SERVICE_TIMEOUT") or 60.0,
}

vertex_embedding = {
    "default_model": _get_env_str(
        "VERTEX_EMBEDDING_DEFAULT_MODEL", "text-embedding-004"
    ),
}

vertex_rag = {
    "enabled": _get_bool("ENABLE_VERTEX_RAG"),
    "source": _get_env_str("VERTEX_RAG_SOURCE", "vertex_rag_store"),
    "corpus": _get_env_str("VERTEX_RAG_CORPUS"),
    "file_ids": _get_str_list("VERTEX_RAG_FILE_IDS"),
    "datastore": _get_env_str("VERTEX_RAG_DATASTORE"),
    "engine": _get_env_str("VERTEX_RAG_ENGINE"),
    "filter": _get_env_str("VERTEX_RAG_FILTER"),
    "top_k": _get_optional_int("VERTEX_RAG_TOP_K"),
    "similarity_top_k": _get_optional_int("VERTEX_RAG_SIMILARITY_TOP_K"),
    "max_results": _get_optional_int("VERTEX_RAG_MAX_RESULTS"),
    "vector_distance_threshold": _get_optional_float("VERTEX_RAG_VECTOR_DISTANCE_THRESHOLD"),
    "ranking_mode": _get_env_str("VERTEX_RAG_RANKING_MODE"),
    "ranking_model": _get_env_str("VERTEX_RAG_RANKING_MODEL"),
}

vertex_additional_models = {
    "embedding": _get_str_list("VERTEX_ADDITIONAL_EMBEDDING_MODELS"),
    "ranking": _get_str_list("VERTEX_ADDITIONAL_RANK_MODELS"),
}

if not vertex_additional_models["embedding"]:
    vertex_additional_models["embedding"] = ["text-embedding-004"]
else:
    vertex_additional_models["embedding"] = list(
        dict.fromkeys(vertex_additional_models["embedding"])
    )

if not vertex_additional_models["ranking"]:
    vertex_additional_models["ranking"] = [
        "text-rerank-002",
        "multimodal-rerank-001",
    ]
else:
    vertex_additional_models["ranking"] = list(
        dict.fromkeys(vertex_additional_models["ranking"])
    )

# 随机字符串
RANDOM_STRING = os.environ.get("RANDOM_STRING", "true").lower() in ["true", "1", "yes"]
RANDOM_STRING_LENGTH = int(os.environ.get("RANDOM_STRING_LENGTH", "5"))

# 是否全局启用思考过程
ENABLE_THINKING = os.environ.get("ENABLE_THINKING", "true").lower() in [
    "true",
    "1",
    "yes",
]

# 空响应重试次数限制
MAX_EMPTY_RESPONSES = int(
    os.environ.get("MAX_EMPTY_RESPONSES", "5")
)  # 默认最多允许5次空响应

# ---------- 以下是其他配置信息 ----------

# 访问限制
MAX_RETRY_NUM = int(os.environ.get("MAX_RETRY_NUM", "15"))  # 请求时的最大总轮询 key 数
MAX_REQUESTS_PER_MINUTE = int(os.environ.get("MAX_REQUESTS_PER_MINUTE", "30"))
MAX_REQUESTS_PER_DAY_PER_IP = int(os.environ.get("MAX_REQUESTS_PER_DAY_PER_IP", "600"))

# API密钥使用限制
API_KEY_DAILY_LIMIT = int(
    os.environ.get("API_KEY_DAILY_LIMIT", "100")
)  # 默认每个API密钥每24小时可使用100次

# 模型屏蔽黑名单，格式应为逗号分隔的模型名称集合
BLOCKED_MODELS = {
    model.strip()
    for model in os.environ.get("BLOCKED_MODELS", "").split(",")
    if model.strip()
}

# 公益站模式
PUBLIC_MODE = os.environ.get("PUBLIC_MODE", "false").lower() in ["true", "1", "yes"]
# 前端地址
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "")

# 模型屏蔽白名单
WHITELIST_MODELS = {
    x.strip() for x in os.environ.get("WHITELIST_MODELS", "").split(",") if x.strip()
}
# 白名单User-Agent
WHITELIST_USER_AGENT = {
    x.strip().lower()
    for x in os.environ.get("WHITELIST_USER_AGENT", "").split(",")
    if x.strip()
}

# 跨域配置
# 允许的源列表，逗号分隔，例如 "http://localhost:3000,https://example.com"
ALLOWED_ORIGINS_STR = os.environ.get("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = [
    origin.strip() for origin in ALLOWED_ORIGINS_STR.split(",") if origin.strip()
]

# ---------- 运行时全局信息，无需修改 ----------

# 基础目录设置
BASE_DIR = pathlib.Path(__file__).parent.parent

# 失效的API密钥
INVALID_API_KEYS = os.environ.get("INVALID_API_KEYS", "")

version = {"local_version": "0.0.0", "remote_version": "0.0.0", "has_update": False}

# API调用统计
# 这个对象保留为空结构以保持向后兼容性
# 实际统计数据已迁移到 app/utils/stats.py 中的 ApiStatsManager 类
api_call_stats = {
    "calls": []  # 兼容旧版代码结构
}

# 用于保护 api_call_stats 并发访问的锁
stats_lock = asyncio.Lock()

# 日志配置
logging.getLogger("uvicorn").disabled = True
logging.getLogger("uvicorn.access").disabled = True


# ---------- 以下配置信息已废弃 ----------

# 假流式请求的空内容返回间隔（秒）
FAKE_STREAMING_INTERVAL = float(os.environ.get("FAKE_STREAMING_INTERVAL", "1"))
# 假流式响应的每个块大小
FAKE_STREAMING_CHUNK_SIZE = int(os.environ.get("FAKE_STREAMING_CHUNK_SIZE", "10"))
# 假流式响应的每个块之间的延迟（秒）
FAKE_STREAMING_DELAY_PER_CHUNK = float(
    os.environ.get("FAKE_STREAMING_DELAY_PER_CHUNK", "0.1")
)

# 非流式请求TCP保活配置
NONSTREAM_KEEPALIVE_ENABLED = os.environ.get(
    "NONSTREAM_KEEPALIVE_ENABLED", "true"
).lower() in ["true", "1", "yes"]
NONSTREAM_KEEPALIVE_INTERVAL = float(
    os.environ.get("NONSTREAM_KEEPALIVE_INTERVAL", "5.0")
)


# 随机字符串
RANDOM_STRING = os.environ.get("RANDOM_STRING", "true").lower() in ["true", "1", "yes"]
RANDOM_STRING_LENGTH = int(os.environ.get("RANDOM_STRING_LENGTH", "5"))

# 空响应重试次数限制
MAX_EMPTY_RESPONSES = int(
    os.environ.get("MAX_EMPTY_RESPONSES", "5")
)  # 默认最多允许5次空响应

# API密钥空回时是否替换文本信息
SHOW_API_ERROR_MESSAGE = os.environ.get("SHOW_API_ERROR_MESSAGE", "true").lower() in [
    "true",
    "1",
    "yes",
]  # 默认为True，显示替换文本；False时返回空响应

# ---------- 以下是其他配置信息 ----------

# 访问限制
MAX_RETRY_NUM = int(os.environ.get("MAX_RETRY_NUM", "15"))  # 请求时的最大总轮询 key 数
MAX_REQUESTS_PER_MINUTE = int(os.environ.get("MAX_REQUESTS_PER_MINUTE", "30"))
MAX_REQUESTS_PER_DAY_PER_IP = int(os.environ.get("MAX_REQUESTS_PER_DAY_PER_IP", "600"))

# API密钥使用限制
API_KEY_DAILY_LIMIT = int(
    os.environ.get("API_KEY_DAILY_LIMIT", "100")
)  # 默认每个API密钥每24小时可使用100次

# 模型屏蔽黑名单，格式应为逗号分隔的模型名称集合
BLOCKED_MODELS = {
    model.strip()
    for model in os.environ.get("BLOCKED_MODELS", "").split(",")
    if model.strip()
}

# 公益站模式
PUBLIC_MODE = os.environ.get("PUBLIC_MODE", "false").lower() in ["true", "1", "yes"]
# 前端地址
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "")

# 模型屏蔽白名单
WHITELIST_MODELS = {
    x.strip() for x in os.environ.get("WHITELIST_MODELS", "").split(",") if x.strip()
}
# 白名单User-Agent
WHITELIST_USER_AGENT = {
    x.strip().lower()
    for x in os.environ.get("WHITELIST_USER_AGENT", "").split(",")
    if x.strip()
}

# 跨域配置
# 允许的源列表，逗号分隔，例如 "http://localhost:3000,https://example.com"
ALLOWED_ORIGINS_STR = os.environ.get("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = [
    origin.strip() for origin in ALLOWED_ORIGINS_STR.split(",") if origin.strip()
]

# ---------- 运行时全局信息，无需修改 ----------

# 基础目录设置
BASE_DIR = pathlib.Path(__file__).parent.parent

# 失效的API密钥
INVALID_API_KEYS = os.environ.get("INVALID_API_KEYS", "")

version = {"local_version": "0.0.0", "remote_version": "0.0.0", "has_update": False}

# API调用统计
# 这个对象保留为空结构以保持向后兼容性
# 实际统计数据已迁移到 app/utils/stats.py 中的 ApiStatsManager 类
api_call_stats = {
    "calls": []  # 兼容旧版代码结构
}

# 用于保护 api_call_stats 并发访问的锁
stats_lock = asyncio.Lock()

# 日志配置
logging.getLogger("uvicorn").disabled = True
logging.getLogger("uvicorn.access").disabled = True


# ---------- 以下配置信息已废弃 ----------

# 假流式请求的空内容返回间隔（秒）
FAKE_STREAMING_INTERVAL = float(os.environ.get("FAKE_STREAMING_INTERVAL", "1"))
# 假流式响应的每个块大小
FAKE_STREAMING_CHUNK_SIZE = int(os.environ.get("FAKE_STREAMING_CHUNK_SIZE", "10"))
# 假流式响应的每个块之间的延迟（秒）
FAKE_STREAMING_DELAY_PER_CHUNK = float(
    os.environ.get("FAKE_STREAMING_DELAY_PER_CHUNK", "0.1")
)

# 非流式请求TCP保活配置
NONSTREAM_KEEPALIVE_ENABLED = os.environ.get(
    "NONSTREAM_KEEPALIVE_ENABLED", "true"
).lower() in ["true", "1", "yes"]
NONSTREAM_KEEPALIVE_INTERVAL = float(
    os.environ.get("NONSTREAM_KEEPALIVE_INTERVAL", "5.0")
)

