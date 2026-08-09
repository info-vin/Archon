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


class NetworkConfig(BaseModel):
    agents_service_url: str = Field(default="http://archon-agents:8052", alias="AGENTS_SERVICE_URL")
    mcp_service_url: str = Field(default="http://archon-mcp:8051", alias="MCP_SERVICE_URL")
    ollama_base_url: str = Field(default="http://host.docker.internal:11434", alias="LLM_BASE_URL")
    anthropic_base_url: str = Field(default="https://api.anthropic.com/v1/", alias="ANTHROPIC_BASE_URL")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL")
    google_base_url: str = Field(default="https://generativelanguage.googleapis.com/v1beta/openai/", alias="GOOGLE_BASE_URL")
    hf_base_url: str = Field(default="https://api-inference.huggingface.co/v1/", alias="HF_BASE_URL")
    frontend_url: str = Field(default="https://archon-enduser.vercel.app", alias="FRONTEND_URL")

class NotificationConfig(BaseModel):
    telegram_token: str | None = Field(default=None, alias="TELEGRAM_TOKEN")
    telegram_chat_id: str | None = Field(default=None, alias="TELEGRAM_TO")

class BudgetConfig(BaseModel):
    weekly_budget_threshold: float = Field(default=0.05, alias="WEEKLY_BUDGET_THRESHOLD")


class TTSConfig(BaseModel):
    tts_truncation_limit: int = Field(default=4000, alias="TTS_TRUNCATION_LIMIT")


class TaskDispatcherConfig(BaseModel):
    task_reclaim_timeout: int = Field(default=60, alias="TASK_RECLAIM_TIMEOUT")
    zombie_task_alert_threshold: int = Field(default=3, alias="ZOMBIE_TASK_ALERT_THRESHOLD")

class SchedulerConfig(BaseModel):
    # 🚨 絕對鐵律：若修改以下 HF 睡眠時間，必須「先檢查並同步修改」
    # .github/workflows/hf-pause.yml 與 hf-restart.yml 的 Cron 排程！
    hf_sleep_start: str = Field(default="17:18", alias="HF_SLEEP_START")
    hf_sleep_end: str = Field(default="07:20", alias="HF_SLEEP_END")

    system_probe_interval_mins: int = Field(default=60, alias="SYSTEM_PROBE_INTERVAL_MINS")
    log_patrol_interval_mins: int = Field(default=30, alias="LOG_PATROL_INTERVAL_MINS")
    task_dispatcher_interval_mins: int = Field(default=15, alias="TASK_DISPATCHER_INTERVAL_MINS")
    model_verification_interval_mins: int = Field(default=150, alias="MODEL_VERIFICATION_INTERVAL_MINS")
    meta_twin_audit_interval_mins: int = Field(default=45, alias="META_TWIN_AUDIT_INTERVAL_MINS")

    # Category 2: Stateful Daily Jobs
    system_probe_cleanup_hour: int = Field(default=11, alias="SYSTEM_PROBE_CLEANUP_HOUR")
    system_probe_cleanup_minute: int = Field(default=50, alias="SYSTEM_PROBE_CLEANUP_MINUTE")
    prune_stale_leads_hour: int = Field(default=11, alias="PRUNE_STALE_LEADS_HOUR")
    prune_stale_leads_minute: int = Field(default=50, alias="PRUNE_STALE_LEADS_MINUTE")
    alice_auto_fetch_hour: int = Field(default=10, alias="ALICE_AUTO_FETCH_HOUR")
    alice_auto_fetch_minute: int = Field(default=25, alias="ALICE_AUTO_FETCH_MINUTE")
    alice_auto_fetch_days: str = Field(default="tue,wed,fri", alias="ALICE_AUTO_FETCH_DAYS")
    token_analysis_hour: int = Field(default=8, alias="TOKEN_ANALYSIS_HOUR")
    token_analysis_minute: int = Field(default=20, alias="TOKEN_ANALYSIS_MINUTE")
    business_sentinel_hour: int = Field(default=8, alias="BUSINESS_SENTINEL_HOUR")
    business_sentinel_minute: int = Field(default=40, alias="BUSINESS_SENTINEL_MINUTE")

    # Category 3: Stateful Weekly / Monthly Jobs
    weekly_executive_summary_days: str = Field(default="sun", alias="WEEKLY_EXECUTIVE_SUMMARY_DAYS")
    architecture_health_audit_days: str = Field(default="fri", alias="ARCHITECTURE_HEALTH_AUDIT_DAYS")
    monthly_summary_day: int = Field(default=1, alias="MONTHLY_SUMMARY_DAY")
    monthly_summary_hour: int = Field(default=9, alias="MONTHLY_SUMMARY_HOUR")
    monthly_summary_minute: int = Field(default=0, alias="MONTHLY_SUMMARY_MINUTE")

    # Category 4: Stateful Bi-weekly Maintenance
    maintenance_audit_hour: int = Field(default=14, alias="MAINTENANCE_AUDIT_HOUR")
    maintenance_audit_minute: int = Field(default=0, alias="MAINTENANCE_AUDIT_MINUTE")
    maintenance_audit_days: str = Field(default="sat,sun", alias="MAINTENANCE_AUDIT_DAYS")



class CrawlerJobConfig(BaseModel):
    crawler_job_keywords: str = Field(default="Python,AI,AI行銷自動化,AI自動化流程,大語言模型應用", alias="CRAWLER_JOB_KEYWORDS")
    crawler_job_limit: int = Field(default=32, alias="CRAWLER_JOB_LIMIT")
    lead_gen_similarity_threshold: float = Field(default=0.68, alias="LEAD_GEN_SIMILARITY_THRESHOLD")
    crawler_waf_delay_min: float = Field(default=6.0, alias="CRAWLER_WAF_DELAY_MIN")
    crawler_waf_delay_max: float = Field(default=17.0, alias="CRAWLER_WAF_DELAY_MAX")


class LeadScoringConfig(BaseModel):
    score_strategic: int = Field(default=95, alias="SCORE_STRATEGIC")
    score_technical: int = Field(default=85, alias="SCORE_TECHNICAL")
    score_operational: int = Field(default=70, alias="SCORE_OPERATIONAL")
    score_base: int = Field(default=40, alias="SCORE_BASE")


class EnrichmentConfig(BaseModel):
    scoring_vital_contact: int = Field(default=20, alias="SCORING_VITAL_CONTACT")
    scoring_news_funding: int = Field(default=30, alias="SCORING_NEWS_FUNDING")
    scoring_has_job_url: int = Field(default=15, alias="SCORING_HAS_JOB_URL")
    enrichment_api_delay_long: float = Field(default=3.0, alias="ENRICHMENT_API_DELAY_LONG")
    enrichment_api_delay_short: float = Field(default=1.5, alias="ENRICHMENT_API_DELAY_SHORT")

class SystemTaskConfig(BaseModel):
    background_cleanup_interval_secs: int = Field(default=300, alias="BACKGROUND_CLEANUP_INTERVAL_SECS")
    background_error_retry_secs: int = Field(default=60, alias="BACKGROUND_ERROR_RETRY_SECS")
    embedding_process_delay_secs: int = Field(default=15, alias="EMBEDDING_PROCESS_DELAY_SECS")


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
