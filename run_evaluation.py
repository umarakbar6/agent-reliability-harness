#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from harness import ReliabilityHarness
from support_agent import SupportTriageAgent


def main():
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Evaluate the support triage agent repeatedly.")
    parser.add_argument("--cases", type=Path, default=base / "evaluation_cases.json")
    parser.add_argument("--output-dir", type=Path, default=base / "results")
    parser.add_argument("--report", type=Path, default=base / "EVALUATION_REPORT.md")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--input-cost-per-million", type=float, default=0.15)
    parser.add_argument("--output-cost-per-million", type=float, default=0.60)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be at least 1")
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    harness = ReliabilityHarness(SupportTriageAgent(), args.input_cost_per_million, args.output_cost_per_million)
    rows = harness.evaluate(cases, args.repeats)
    summary = harness.summarize(rows, len(cases), args.repeats)
    harness.write_outputs(rows, summary, args.output_dir, args.report)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

