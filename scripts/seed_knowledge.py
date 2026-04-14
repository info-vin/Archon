import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "python" / "src"))

from server.config.logfire_config import get_logger
from server.services.librarian_service import LibrarianService

logger = get_logger("seed_knowledge")

# Dynamic Path Detection for Host vs Docker
# Pattern 14: Cross-Env Path Resilience
POSSIBLE_DIRS = [
    "../enduser-ui-fe/public/aus/156_resource",      # Host relative
    "/app/frontend_public/aus/156_resource",        # Docker internal mapping
    "enduser-ui-fe/public/aus/156_resource"          # Root relative
]

SYSTEM_DOCS = [
    "../CONTRIBUTING_tw.md",
    "/app/CONTRIBUTING_tw.md",
    "CONTRIBUTING_tw.md"
]

TARGET_DIRS = []
for p in POSSIBLE_DIRS:
    if Path(p).resolve().exists():
        TARGET_DIRS.append(p)
        break

TARGET_FILES = []
for p in SYSTEM_DOCS:
    if Path(p).resolve().is_file():
        TARGET_FILES.append(p)
        break

async def seed_knowledge():
    if not TARGET_DIRS and not TARGET_FILES:
        print("❌ Error: No valid knowledge source directory or file found.")
        return

    librarian = LibrarianService()

    print("🤖 Librarian Robot: Initialized.")
    print(f"📂 Scanning directories: {TARGET_DIRS}")
    print(f"📄 Scanning system files: {TARGET_FILES}")

    total_files = 0
    success_files = 0

    all_file_paths = []
    
    # Combine directory files
    for dir_path in TARGET_DIRS:
        abs_path = Path(dir_path).resolve()
        if abs_path.exists():
            for root, _, files in os.walk(abs_path):
                for file in files:
                    all_file_paths.append(Path(root) / file)
                    
    # Combine individual system documents
    for file_p in TARGET_FILES:
        fp = Path(file_p).resolve()
        if fp.exists():
            all_file_paths.append(fp)

    for file_path in all_file_paths:
        file = file_path.name

                # Filter useful files
                if file.startswith('.') or file == "DS_Store":
                    continue

                total_files += 1
                content = ""

                try:
                    if file.endswith('.md') or file.endswith('.txt'):
                        with open(file_path, encoding='utf-8') as f:
                            content = f.read()
                    elif file.endswith('.pdf'):
                        import pdfplumber
                        with pdfplumber.open(file_path) as pdf:
                            content = ""
                            for page in pdf.pages:
                                content += (page.extract_text() or "") + "\n"
                    else:
                        print(f"⚠️  Skipping unsupported file type: {file}")
                        continue

                    if not content.strip():
                        print(f"⚠️  Skipping empty file: {file}")
                        continue

                    print(f"📄 Archiving: {file} ({len(content)} chars)...")

                    # Call Librarian
                    source_id = await librarian.archive_file(
                        file_name=file,
                        content=content,
                        file_path=str(file_path),
                        knowledge_type="technical" # or infer from folder
                    )

                    if source_id:
                        print(f"   ✅ Done! ID: {source_id}")
                        success_files += 1
                    else:
                        print(f"   ❌ Failed to archive {file}")

                except Exception as e:
                    print(f"   ❌ Error processing {file}: {e}")

    print(f"\n🎉 Seeding Complete. Processed {success_files}/{total_files} files.")

if __name__ == "__main__":
    asyncio.run(seed_knowledge())
