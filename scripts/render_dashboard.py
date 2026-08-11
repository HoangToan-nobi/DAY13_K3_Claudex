from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from datetime import datetime, timedelta
from html import escape
from pathlib import Path
from statistics import mean


REPO_ROOT = Path(__file__).resolve().parents[1]


def percentile(values: list[float], p: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil((p / 100) * len(ordered)) - 1)
    return ordered[index]


def load_records(path: Path, window_minutes: int = 60) -> list[dict]:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    timestamps = [datetime.fromisoformat(record["ts"].replace("Z", "+00:00")) for record in records]
    if not timestamps:
        return []
    cutoff = max(timestamps) - timedelta(minutes=window_minutes)
    return [
        record
        for record in records
        if datetime.fromisoformat(record["ts"].replace("Z", "+00:00")) >= cutoff
    ]


def build_panels(records: list[dict]) -> list[tuple[str, str, str, bool]]:
    received = [record for record in records if record.get("event") == "request_received"]
    sent = [record for record in records if record.get("event") == "response_sent"]
    failed = [record for record in records if record.get("event") == "request_failed"]
    latencies = [float(record["latency_ms"]) for record in sent if "latency_ms" in record]
    error_types = Counter(record.get("error_type", "unknown") for record in failed)
    error_rate = len(failed) / len(received) * 100 if received else 0.0
    total_cost = sum(float(record.get("cost_usd", 0)) for record in sent)
    tokens_in = sum(int(record.get("tokens_in", 0)) for record in sent)
    tokens_out = sum(int(record.get("tokens_out", 0)) for record in sent)
    quality = [float(record["quality_score"]) for record in sent if "quality_score" in record]
    breakdown = ", ".join(f"{key}: {value}" for key, value in error_types.items()) or "none"

    return [
        (
            "Latency percentiles",
            f"P50 {percentile(latencies, 50):.0f}  |  P95 {percentile(latencies, 95):.0f}  |  P99 {percentile(latencies, 99):.0f}",
            "ms · SLO P95 ≤ 3000 ms",
            percentile(latencies, 95) <= 3000,
        ),
        ("Request traffic", f"{len(received)} requests", "requests / 60 min", len(received) > 0),
        ("Error rate and breakdown", f"{error_rate:.2f}%", f"errors: {breakdown} · SLO ≤ 2%", error_rate <= 2),
        ("Cost over time", f"${total_cost:.4f}", "USD / 60 min · budget ≤ $2.50", total_cost <= 2.5),
        ("Input and output tokens", f"IN {tokens_in:,}  |  OUT {tokens_out:,}", "tokens · threshold 50,000", max(tokens_in, tokens_out) <= 50_000),
        ("Quality proxy", f"{mean(quality) if quality else 0:.3f}", "score 0–1 · SLO ≥ 0.75", bool(quality) and mean(quality) >= 0.75),
    ]


def render_svg(panels: list[tuple[str, str, str, bool]], output: Path) -> None:
    width, height = 1200, 720
    cards = []
    for index, (title, value, detail, healthy) in enumerate(panels):
        col, row = index % 2, index // 2
        x, y = 55 + col * 570, 145 + row * 175
        accent = "#32d583" if healthy else "#f97066"
        cards.append(
            f'<rect x="{x}" y="{y}" width="520" height="140" rx="14" fill="#172033" stroke="#344054"/>'
            f'<rect x="{x}" y="{y}" width="7" height="140" rx="3" fill="{accent}"/>'
            f'<text x="{x + 28}" y="{y + 35}" class="title">{escape(title)}</text>'
            f'<text x="{x + 28}" y="{y + 80}" class="value">{escape(value)}</text>'
            f'<text x="{x + 28}" y="{y + 112}" class="detail">{escape(detail)}</text>'
        )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>.heading{{font:700 28px Arial;fill:#f2f4f7}}.meta{{font:16px Arial;fill:#98a2b3}}.title{{font:600 17px Arial;fill:#d0d5dd}}.value{{font:700 28px Arial;fill:#fff}}.detail{{font:14px Arial;fill:#98a2b3}}</style>
<rect width="100%" height="100%" fill="#0b1220"/>
<text x="55" y="58" class="heading">Day 13 AI Observability</text>
<text x="55" y="91" class="meta">Runtime evidence · source: data/logs.jsonl · time range: last 60 minutes · refresh contract: 30 seconds</text>
{''.join(cards)}
</svg>'''
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the six-panel dashboard evidence as SVG")
    parser.add_argument("--logs", type=Path, default=REPO_ROOT / "data" / "logs.jsonl")
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "submission" / "evidence" / "dashboard-runtime.svg",
    )
    args = parser.parse_args()
    records = load_records(args.logs)
    if not records:
        raise SystemExit("No log records found in the selected 60-minute window")
    render_svg(build_panels(records), args.output)
    print(f"Rendered dashboard evidence: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
