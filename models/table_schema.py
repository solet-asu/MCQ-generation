from typing import Dict

TABLE_SCHEMAS: Dict[str, Dict[str, str]] = {
        "plan_metadata": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "invocation_id": "TEXT",
        "system_prompt": "TEXT",
        "user_prompt": "TEXT",
        "model": "TEXT",
        "completion": "TEXT",
        "summary": "TEXT",
        "facts": "JSON",
        "inferences": "JSON",
        "execution_time": "TEXT",
        "input_tokens": "INTEGER",
        "output_tokens": "INTEGER",
        "timestamp": "TEXT"
    },
    "mcq_metadata": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "invocation_id": "TEXT",
        "question_type": "TEXT",
        "system_prompt": "TEXT",
        "user_prompt": "TEXT",
        "model": "TEXT",
        "completion": "TEXT",
        "mcq": "TEXT",
        "mcq_answer": "TEXT",
        "execution_time": "TEXT",
        "input_tokens": "INTEGER",
        "output_tokens": "INTEGER",
        "timestamp": "TEXT"
    },

}