from typing import Any, List
import json, ast, re, logging
logger = logging.getLogger(__name__)
_CAND_KEY_RE = re.compile(r"^candidate[_\s\-]?(\d+)$", re.IGNORECASE)

def normalize_candidates(raw: Any, n: int = 5, *, allow_python_literal: bool = False) -> List[str]:
    if isinstance(raw, str):
        s = raw.strip()
        try:
            raw = json.loads(s)
        except json.JSONDecodeError:
            if allow_python_literal:
                try:
                    raw = ast.literal_eval(s)
                except Exception:
                    raw = [s]
            else:
                raw = [s]

    if isinstance(raw, dict):
        ordered: List[str] = []
        # 1) Prefer candidate_1..candidate_n
        for i in range(1, n + 1):
            ordered.append(str(raw.get(f"candidate_{i}", "") or "").strip())
        # 2) Fill gaps with numeric-like keys (e.g., "1", "#2", "candidate-3")
        if all(x == "" for x in ordered):
            numeric_items = []
            for k, v in raw.items():
                k_str = str(k).strip().lstrip("#")
                m = _CAND_KEY_RE.match(k_str)
                if m:
                    k_str = m.group(1)
                try:
                    num = int(k_str)
                except ValueError:
                    continue
                numeric_items.append((num, v))
            for _, v in sorted(numeric_items, key=lambda t: t[0]):
                if len(ordered) >= n:
                    break
                ordered.append(str(v or "").strip())

    elif isinstance(raw, list):
        ordered = [str(x or "").strip() for x in raw[:n]]
    else:
        ordered = [str(raw or "").strip()]

    while len(ordered) < n:
        ordered.append("")
    return ordered[:n]