from dataclasses import dataclass

_CACHE_TTL_SECONDS = 300

CHAT_MODEL_PATTERNS = ["llama", "qwen", "mistral", "codellama", "phi", "gemma", "vicuna", "orca"] # 合法
EMBEDDING_MODEL_PATTERNS = ["embed", "embedding"] # 合法
VISION_MODEL_PATTERNS = ["vision", "llava", "moondream"] # 合法

MODEL_CONTEXT_WINDOWS = {
    "llama3": 8192,
    "qwen": 32768,
    "mistral": 8192,
    "codellama": 16384,
    "phi": 4096,
    "gemma": 8192,
}

EMBEDDING_DIMENSIONS = {
    "nomic-embed": 768,
    "mxbai-embed": 1024,
    "all-minilm": 384,
}


@dataclass
class ModelSpec:
    name: str
    provider: str
    context_window: int
    supports_tools: bool = False
    supports_vision: bool = False
    supports_embeddings: bool = False
    embedding_dimensions: int | None = None
    pricing_input: float | None = None
    pricing_output: float | None = None
    description: str = ""
    aliases: list[str] | None = None

    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []


@dataclass
class ProviderStatus:
    provider: str
    is_available: bool
    response_time_ms: float | None = None
    error_message: str | None = None
    models_available: int = 0
    base_url: str | None = None
    last_checked: float | None = None
