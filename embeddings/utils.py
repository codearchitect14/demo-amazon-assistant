import json
from pathlib import Path
from typing import Generator, Dict


def load_jsonl(path: str) -> Generator[Dict, None, None]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)
