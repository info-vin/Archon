from pydantic import BaseModel, Field


class CredentialCreate(BaseModel):
    key: str
    value: str
    is_encrypted: bool = False
    category: str = "ai"
    description: str | None = None


class CredentialResponse(BaseModel):
    key: str
    value: str | None = None
    encrypted_value: str | None = None
    is_encrypted: bool = False
    category: str | None = None
    description: str | None = None
    updated_at: str | None = None


class CredentialStatusResponse(BaseModel):
    provider: str
    status: str
    message: str | None = None


class CredentialStatusRequest(BaseModel):
    keys: list[str]


class UserUpdateRequest(BaseModel):
    name: str | None = None
    full_name: str | None = None
    avatar: str | None = None
    role: str | None = None
    department: str | None = None

# ---------------------------------------------------------
# Job Configuration Models (SSOT)
# ---------------------------------------------------------

class PruningConfig(BaseModel):
    max_size_mb: float = Field(default=500.0, alias="PRUNING_MAX_SIZE_MB")
    l1_pct: float = Field(default=50.0, alias="PRUNING_L1_PCT")
    l2_pct: float = Field(default=80.0, alias="PRUNING_L2_PCT")

    l1_logs_days: int = Field(default=90, alias="PRUNING_L1_LOGS_DAYS")
    l1_tokens_days: int = Field(default=180, alias="PRUNING_L1_TOKENS_DAYS")

    l2_logs_days: int = Field(default=30, alias="PRUNING_L2_LOGS_DAYS")
    l2_leads_days: int = Field(default=90, alias="PRUNING_L2_LEADS_DAYS")
    l2_tokens_days: int = Field(default=90, alias="PRUNING_L2_TOKENS_DAYS")

    l3_logs_days: int = Field(default=14, alias="PRUNING_L3_LOGS_DAYS")
    l3_crawled_days: int = Field(default=30, alias="PRUNING_L3_CRAWLED_DAYS")
    l3_tokens_days: int = Field(default=30, alias="PRUNING_L3_TOKENS_DAYS")


class BudgetConfig(BaseModel):
    weekly_budget_threshold: float = Field(default=0.05, alias="WEEKLY_BUDGET_THRESHOLD")


class TTSConfig(BaseModel):
    tts_truncation_limit: int = Field(default=4000, alias="TTS_TRUNCATION_LIMIT")


class TaskDispatcherConfig(BaseModel):
    task_reclaim_timeout: int = Field(default=60, alias="TASK_RECLAIM_TIMEOUT")
