# debug_invoke_quality_first.py
import asyncio
import logging
import json
import uuid
import inspect
from pathlib import Path

import sys
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# configure logging to show INFO and above to stdout
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

async def main():
    import src.mcq_generation as mg
    print("imported module file:", inspect.getsourcefile(mg))
    # Build a minimal task (same shape generate_mcq_quality_first expects)
    task = {
        "question_type": "fact",
        "text": "Photosynthesis is the process by which green plants convert light energy into chemical energy.",
        "content": "Photosynthesis involves chlorophyll in plant leaves.",
        "context": ""
    }

    res = await mg.generate_mcq_quality_first(
        session_id="debug-session",
        api_token=None,            # set a real token if your agent needs it
        invocation_id=str(uuid.uuid4()),
        model="gpt-4o",
        task=task,
        mcq_metadata_table_name="mcq_metadata",
        evaluation_metadata_table_name="evaluation_metadata",
        ranking_metadata_table_name="ranking_metadata",
        database_file=str(Path("..") / "database" / "mcq_metadata.db"),
        max_attempt=1,
        attempt=1,
        candidate_num=1,           # single candidate for clarity
    )
    print("RESULT:", json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
