from __future__ import annotations

import csv
from pathlib import Path

from rdflib import Graph


LLM_DIR = Path(__file__).resolve().parent
TASK6_DIR = LLM_DIR.parent
TEAM_DIR = TASK6_DIR.parent
KG_PATH = TEAM_DIR / "task4" / "kg" / "output.nt"
LINKS_PATH = TASK6_DIR / "data" / "wikidata_links.ttl"
RESULTS_DIR = TASK6_DIR / "results" / "query_results"
GENERATED_QUERIES = LLM_DIR / "generated_queries.rq"


def split_queries(text: str) -> list[tuple[str, str]]:
    chunks: list[tuple[str, str]] = []
    current_title = ""
    current_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("### "):
            if current_title and current_lines:
                chunks.append((current_title, "\n".join(current_lines).strip()))
            current_title = line.removeprefix("### ").strip()
            current_lines = []
        elif current_title:
            current_lines.append(line)
    if current_title and current_lines:
        chunks.append((current_title, "\n".join(current_lines).strip()))
    return chunks


def output_name(index: int, title: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "_" for ch in title)
    slug = "_".join(part for part in slug.split("_") if part)
    return f"llm_query_{index:02d}_{slug}.csv"


def term_to_text(value) -> str:
    return "" if value is None else str(value)


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    graph = Graph()
    graph.parse(KG_PATH, format="nt")
    graph.parse(LINKS_PATH, format="turtle")

    for index, (title, query) in enumerate(split_queries(GENERATED_QUERIES.read_text(encoding="utf-8")), 1):
        result = graph.query(query)
        columns = [str(var) for var in result.vars]
        rows = [
            {column: term_to_text(row.get(column)) for column in columns}
            for row in result
        ]
        out_path = RESULTS_DIR / output_name(index, title)
        with out_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        print(f"{title}: {len(rows)} rows -> {out_path.relative_to(TASK6_DIR)}")


if __name__ == "__main__":
    main()
