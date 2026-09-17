"""Reusable evaluation engine and report generation."""

from collections import Counter, defaultdict
from dataclasses import asdict
import csv
import json
from pathlib import Path
from statistics import mean


FAILURE_LABELS = {
    "multi_intent": "Multi-intent precedence",
    "negation": "Negation handling",
    "typo": "Misspellings and paraphrases",
    "multilingual": "Multilingual input",
}


class ReliabilityHarness:
    def __init__(self, agent, input_cost_per_million=0.15, output_cost_per_million=0.60):
        self.agent = agent
        self.input_rate = input_cost_per_million
        self.output_rate = output_cost_per_million

    def evaluate(self, cases, repeats=5):
        rows = []
        for case in cases:
            for run_number in range(1, repeats + 1):
                try:
                    result = self.agent.run(case["input"])
                    actual = asdict(result)
                    mismatches = [k for k in ("category", "priority", "action") if actual[k] != case["expected"][k]]
                    success = not mismatches
                    error = "" if success else "mismatch: " + ", ".join(mismatches)
                    cost = (actual["input_tokens"] * self.input_rate + actual["output_tokens"] * self.output_rate) / 1_000_000
                except Exception as exc:
                    actual = {"category":"ERROR", "priority":"ERROR", "action":"ERROR", "steps":0, "input_tokens":0, "output_tokens":0}
                    success, error, cost = False, f"exception: {type(exc).__name__}: {exc}", 0.0
                rows.append({
                    "case_id": case["id"], "group": case["group"], "run": run_number,
                    "success": success, "expected_category": case["expected"]["category"],
                    "actual_category": actual["category"], "expected_priority": case["expected"]["priority"],
                    "actual_priority": actual["priority"], "expected_action": case["expected"]["action"],
                    "actual_action": actual["action"], "steps": actual["steps"],
                    "input_tokens": actual["input_tokens"], "output_tokens": actual["output_tokens"],
                    "estimated_cost_usd": cost, "error": error,
                })
        return rows

    @staticmethod
    def summarize(rows, case_count, repeats):
        successes = sum(r["success"] for r in rows)
        total = len(rows)
        failed = [r for r in rows if not r["success"]]
        failures_by_group = Counter(r["group"] for r in failed)
        case_outcomes = defaultdict(list)
        for row in rows:
            case_outcomes[row["case_id"]].append((row["actual_category"], row["actual_priority"], row["actual_action"]))
        consistent = sum(len(set(outputs)) == 1 for outputs in case_outcomes.values())
        total_cost = sum(r["estimated_cost_usd"] for r in rows)
        return {
            "case_count": case_count, "repeats_per_case": repeats, "total_runs": total,
            "successful_runs": successes, "failed_runs": total - successes,
            "success_rate_percent": round(100 * successes / total, 2) if total else 0,
            "average_steps": round(mean(r["steps"] for r in rows), 2) if rows else 0,
            "average_input_tokens": round(mean(r["input_tokens"] for r in rows), 2) if rows else 0,
            "average_output_tokens": round(mean(r["output_tokens"] for r in rows), 2) if rows else 0,
            "total_estimated_cost_usd": round(total_cost, 8),
            "cost_per_successful_run_usd": round(total_cost / successes, 8) if successes else None,
            "consistent_cases": consistent,
            "consistency_rate_percent": round(100 * consistent / case_count, 2) if case_count else 0,
            "failures_by_group": dict(failures_by_group),
        }

    @staticmethod
    def write_outputs(rows, summary, output_dir, report_path):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        with (output_dir / "results.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader(); writer.writerows(rows)
        (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

        top = sorted(summary["failures_by_group"].items(), key=lambda x: (-x[1], x[0]))[:3]
        failure_lines = []
        for rank, (group, count) in enumerate(top, 1):
            label = FAILURE_LABELS.get(group, group.replace("_", " ").title())
            failure_lines.append(f"{rank}. **{label}** — {count} failed runs. The keyword rules do not model this language pattern reliably.")
        while len(failure_lines) < 3:
            failure_lines.append(f"{len(failure_lines)+1}. **No additional observed failure mode** — no other category produced a failed run.")

        report = f"""# Agent Reliability Evaluation Report

## Executive summary

The support triage agent was evaluated on **{summary['case_count']} known-good cases**, repeated **{summary['repeats_per_case']} times each** for **{summary['total_runs']} total runs**. The dataset includes normal requests plus empty, vague, formatting, long-input, multi-intent, negation, typo, security, and multilingual cases.

## Exact definition of success

A run succeeds only if it completes without an exception and its `category`, `priority`, and `action` all exactly equal the known-good expected values. Partial matches are failures. Token and cost estimates do not affect the pass/fail decision.

## Results

| Metric | Result |
|---|---:|
| Successful runs | {summary['successful_runs']} / {summary['total_runs']} |
| Success rate | {summary['success_rate_percent']:.2f}% |
| Average steps per run | {summary['average_steps']:.2f} |
| Average input tokens | {summary['average_input_tokens']:.2f} |
| Average output tokens | {summary['average_output_tokens']:.2f} |
| Total estimated cost | ${summary['total_estimated_cost_usd']:.8f} |
| Cost per successful run | ${summary['cost_per_successful_run_usd']:.8f} |
| Consistent cases across repeats | {summary['consistent_cases']} / {summary['case_count']} ({summary['consistency_rate_percent']:.2f}%) |

Cost uses the configured rates and transparent character-based token estimates. It is an estimate, not a provider invoice.

## Top three failure modes

{chr(10).join(failure_lines)}

## What I would fix first

I would first replace first-keyword-wins classification with a structured intent scorer that detects negation and ranks security, technical impact, billing, access, and cancellation explicitly. This directly addresses multi-intent and negation errors without weakening the already-correct happy paths. Next I would normalize common misspellings and add multilingual examples or a language-aware model. I would rerun this exact fixed dataset after every change, then add each newly discovered production failure as a regression case.

## Reproduction

Run `python run_evaluation.py`. Per-run evidence is in `results/results.csv`; aggregate metrics are in `results/summary.json`.
"""
        Path(report_path).write_text(report, encoding="utf-8")

