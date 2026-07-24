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


class CrawlerJobConfig(BaseModel):
    crawler_job_keywords: str = Field(default="Python,AI,Marketing,Sales", alias="CRAWLER_JOB_KEYWORDS")
    crawler_job_limit: int = Field(default=4, alias="CRAWLER_JOB_LIMIT")
    lead_gen_similarity_threshold: float = Field(default=0.65, alias="LEAD_GEN_SIMILARITY_THRESHOLD")


class LeadScoringConfig(BaseModel):
    score_strategic: int = Field(default=95, alias="SCORE_STRATEGIC")
    score_technical: int = Field(default=85, alias="SCORE_TECHNICAL")
    score_operational: int = Field(default=70, alias="SCORE_OPERATIONAL")
    score_base: int = Field(default=40, alias="SCORE_BASE")


class EnrichmentConfig(BaseModel):
    scoring_vital_contact: int = Field(default=20, alias="SCORING_VITAL_CONTACT")
    scoring_news_funding: int = Field(default=30, alias="SCORING_NEWS_FUNDING")
    scoring_has_job_url: int = Field(default=15, alias="SCORING_HAS_JOB_URL")


class CodeExtractionConfig(BaseModel):
    min_code_block_length: int = Field(default=250, alias="MIN_CODE_BLOCK_LENGTH")
    max_code_block_length: int = Field(default=5000, alias="MAX_CODE_BLOCK_LENGTH")
    enable_prose_filtering: bool = Field(default=True, alias="ENABLE_PROSE_FILTERING")
    max_prose_ratio: float = Field(default=0.15, alias="MAX_PROSE_RATIO")
    min_code_indicators: int = Field(default=3, alias="MIN_CODE_INDICATORS")
    enable_diagram_filtering: bool = Field(default=True, alias="ENABLE_DIAGRAM_FILTERING")
    enable_contextual_length: bool = Field(default=True, alias="ENABLE_CONTEXTUAL_LENGTH")
    context_window_size: int = Field(default=1000, alias="CONTEXT_WINDOW_SIZE")
    enable_code_summaries: bool = Field(default=True, alias="ENABLE_CODE_SUMMARIES")


class RagConfig(BaseModel):
    agents_enabled: bool = Field(default=False, alias="AGENTS_ENABLED")
    use_reranking: bool = Field(default=False, alias="USE_RERANKING")
    sentinel_rag_match_count: int = Field(default=2, alias="SENTINEL_RAG_MATCH_COUNT")


class ProjectConfig(BaseModel):
    default_business_project: str = Field(default="", alias="default_business_project")
