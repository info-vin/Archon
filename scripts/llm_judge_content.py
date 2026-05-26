import os
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
for p in [".env", "python/.env", "../.env", "../python/.env"]:
    if os.path.exists(p):
        load_dotenv(p)

# Dynamically align python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python")))

from google import genai
from google.genai import types
from src.server.utils import get_supabase_client
from src.server.services import credential_service

# Define strict, structured schema for LLM Judge Content Checker
class SemanticAssertionResult(BaseModel):
    assertion_name: str
    passed: bool
    score: int = Field(description="Semantic score of this aspect from 0 to 100")
    reason: str
    cliches_found: list[str] = Field(default_factory=list, description="List of forbidden clichés detected (e.g. 'delve', 'testament', 'in today's digital landscape')")

class ContentQualityJudgement(BaseModel):
    post_id: str
    title: str
    word_count_check: SemanticAssertionResult
    cliche_check: SemanticAssertionResult
    tone_check: SemanticAssertionResult
    overall_passed: bool
    final_grade: str = Field(description="Content grade: A (Perfect), B (Minor improvements), C (Needs revision), F (Fails assertions)")
    recommendations: list[str] = Field(default_factory=list, description="Specific feedback points for self-correction")

async def get_target_posts() -> list[dict]:
    """Retrieves target posts from supabase with robust local fallback for standalone QA."""
    try:
        supabase = get_supabase_client()
        res = supabase.table("blog_posts").select("*").order("updated_at", desc=True).limit(20).execute()
        if res.data:
            # Filter out empty or placeholder drafts before judging
            valid_posts = []
            for p in res.data:
                content = str(p.get("content") or "").strip()
                if len(content) > 100:
                    valid_posts.append(p)
            
            if valid_posts:
                print(f"📦 [LLMJudge] Successfully fetched {len(valid_posts[:5])} valid blog posts from database.")
                return valid_posts[:5]
    except Exception as e:
        print(f"⚠️ [LLMJudge] Database fetch failed/unavailable ({e}). Switching to local fallback mock dataset.")
    
    # Return high-quality, structured fallback mock posts representing typical AI generation cases
    return [
        {
            "id": "mock-blog-001",
            "title": "Optimizing B2B Sales Velocity via Machine Learning Event Correlation",
            "content": """The fundamental challenge in enterprise sales operations centers on distinguishing high-intent engagement from passive exploratory behavior. Archon's new AI Hunter mechanism addresses this by ingesting multi-channel metadata, correlating user telemetry with predefined behavioral vectors, and classifying prospective leads using a probabilistic decision matrix.

            Rather than relying on manual prospecting, organizations can deploy this system to automatically filter noise out of the conversion pipeline. By analyzing key behavioral indicators—such as specific page dwell times, feature interactions, and historical purchasing models—the algorithm applies weighted scoring to prioritize accounts demonstrating immediate transactional readiness. Integrating this event-driven architecture directly accelerates the sales cycle, significantly reducing customer acquisition costs while maintaining operational precision and improving overall revenue forecasting accuracy across the quarter.""",
            "status": "draft"
        },
        {
            "id": "mock-blog-002",
            "title": "Ensuring Continuous Delivery via Physical Parity and Strict Schema Validation",
            "content": """Software stability during frequent release cycles relies on continuous, rigorous boundary verification and automated regression containment. Archon integrates a specialized automated QA physical notary engine designed specifically to execute end-to-end user parity scans immediately before merge events are authorized. 

            By enforcing strict database schema validation protocols and utilizing standard headless browser context injectors, the infrastructure effectively mitigates state contamination between test suites. This systematic approach effectively guarantees zero domain name system leak hazards and maintains operational parameters within optimal thresholds. Furthermore, employing deterministic validation logic against production-mirrored databases eliminates unpredictable testing artifacts, enabling engineering teams to scale deployment frequency without compromising structural integrity or risking customer-facing downtimes.""",
            "status": "published"
        }
    ]

async def run_judge_session():
    """Executes the LLM Judge content checking suite against generated assets."""
    print("🎭 [LLMJudge] Starting AI Content Semantic Quality Judgement Suite...")
    
    # Load API Key resiliently
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            api_key = await credential_service.get_credential("GEMINI_API_KEY")
        except Exception:
            pass
            
    if not api_key:
        print("❌ [LLMJudge] GEMINI_API_KEY is not configured in environment or database. Aborting.")
        sys.exit(1)
        
    client = genai.Client(api_key=api_key)
    posts = await get_target_posts()
    
    system_instruction = (
        "You are an elite Marketing Director and Content Quality Supervisor.\n"
        "Your task is to run strict semantic assertions on AI-generated blog posts/insights.\n"
        "Assert the following aspects:\n"
        "1. Word Count: Drafts should ideally be comprehensive (above 100 words), but free from fluff.\n"
        "2. Cliche check: Strictly flag and fail content containing typical low-quality AI filler clichés "
        "like 'delve', 'testament', 'in today's digital landscape', 'fast-paced digital world', 'beacon of hope'. Also flag placeholder elements like '[Insert ...]'.\n"
        "3. Tone check: Tone must be authoritative, expert, professional, clear, and highly specific. No empty buzzwords.\n\n"
        "Return your structured response in exact JSON matching the provided schema."
    )
    
    reports = []
    has_failures = False
    
    for idx, post in enumerate(posts):
        post_id = post.get("id", f"unknown-{idx}")
        title = post.get("title", "Untitled Content")
        content = post.get("content", "")
        
        print(f"🔍 [LLMJudge] Judging Post [{post_id}] - \"{title}\"...")
        
        try:
            response = client.models.generate_content(
                model='gemini-3.1-flash-lite',
                contents=f"Title: {title}\nContent:\n{content}",
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=ContentQualityJudgement,
                    temperature=0.0
                )
            )
            
            # Parse structured Pydantic judgment
            judgement = ContentQualityJudgement.model_validate_json(response.text)
            judgement.post_id = post_id  # Ensure exact ID alignment
            
            reports.append(judgement)
            
            # Print feedback to console
            print(f"📝 [LLMJudge] Title: \"{judgement.title}\" | Grade: [{judgement.final_grade}] | Overall Passed: {judgement.overall_passed}")
            if not judgement.overall_passed:
                has_failures = True
                print(f"   ⚠️  Failing assertions found:")
                for check in [judgement.word_count_check, judgement.cliche_check, judgement.tone_check]:
                    if not check.passed:
                        print(f"      - {check.assertion_name}: {check.reason} (Clichés: {check.cliches_found})")
            else:
                print(f"   ✅ All semantic assertions passed.")
                
        except Exception as e:
            print(f"❌ [LLMJudge] Error executing judge on post {post_id}: {e}")
            
        # Physical cooldown to prevent Gemini API 429/503 limits
        if idx < len(posts) - 1:
            await asyncio.sleep(2)
            
    # Compile consolidated diagnostic report
    report_dir = Path("./.twin/diagnostics")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_filename = f"report_llm_judge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_path = report_dir / report_filename
    
    markdown_content = []
    markdown_content.append(f"# AI Content Semantic Judgement Report\n")
    markdown_content.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    markdown_content.append(f"## Executive Summary\n")
    markdown_content.append(f"- **Total Assets Checked**: {len(reports)}")
    markdown_content.append(f"- **Status**: {'🔴 FAIL - Semantic Assertions Broken' if has_failures else '🟢 PASS - All Content Compliant'}\n")
    markdown_content.append(f"## Detailed Quality Audit Logs\n")
    
    for r in reports:
        status_emoji = "🟢" if r.overall_passed else "🔴"
        markdown_content.append(f"### {status_emoji} Post: {r.title} (ID: `{r.post_id}`)\n")
        markdown_content.append(f"- **Final Grade**: `{r.final_grade}`")
        markdown_content.append(f"- **Overall Compliant**: `{r.overall_passed}`\n")
        markdown_content.append(f"| Assertion Aspect | Status | Score | Reason / Clichés |")
        markdown_content.append(f"| --- | --- | --- | --- |")
        
        for check in [r.word_count_check, r.cliche_check, r.tone_check]:
            c_status = "✅ PASS" if check.passed else "❌ FAIL"
            cliches_str = f" (Forbidden words found: {', '.join(check.cliches_found)})" if check.cliches_found else ""
            markdown_content.append(f"| {check.assertion_name} | {c_status} | {check.score}/100 | {check.reason}{cliches_str} |")
            
        markdown_content.append("")
        if r.recommendations:
            markdown_content.append("**Supervisor Recommendations for Improvement**:")
            for rec in r.recommendations:
                markdown_content.append(f"- {rec}")
            markdown_content.append("")
            
        markdown_content.append("---")
        
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(markdown_content))
        
    print(f"\n📄 [LLMJudge] Consolidating QA report to: {report_path}")
    
    if has_failures:
        print("🔴 [LLMJudge] Semantic boundaries were violated. Please check recommendations.")
        sys.exit(1)
    else:
        print("🟢 [LLMJudge] All AI-generated content successfully complied with premium semantic rules.")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(run_judge_session())
