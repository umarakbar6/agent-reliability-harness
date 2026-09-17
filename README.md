# Agent Reliability Harness

An evaluation harness for a customer-support triage agent. It measures whether
the agent returns the correct category, priority, and next action on a fixed set
of known-good cases, including difficult and adversarial inputs.

## What is measured

A run is successful only when it completes without an exception **and** all
three fields exactly match the expected values:

- `category`
- `priority`
- `action`

The harness reports success rate, consistency across repeated runs, average
steps, estimated token usage and cost, cost per successful run, and failure
categories. Costs are estimates based on configurable per-million-token rates.

## Quick start

```bash
python run_evaluation.py
```

This executes all 25 cases five times (125 total runs) and writes:

- `results/results.csv` — one row per run
- `results/summary.json` — machine-readable aggregate metrics
- `EVALUATION_REPORT.md` — human-readable analysis

No API key or third-party package is required. Python 3.10+ is recommended.

## Useful options

```bash
python run_evaluation.py --repeats 10
python run_evaluation.py --cases evaluation_cases.json --output-dir results
python -m unittest discover -s tests -v
```

Pricing assumptions can be changed with `--input-cost-per-million` and
`--output-cost-per-million`. The default agent is deterministic, so repeated
runs also verify consistency and make the harness ready for a probabilistic LLM
adapter later.

## Project structure

```text
support_agent.py          Agent under evaluation
evaluation_cases.json    25 known-good cases
harness.py                Evaluator and report generation
run_evaluation.py         CLI entry point
tests/                    Automated tests
results/                  Generated run-level and summary results
EVALUATION_REPORT.md      Generated evaluation report
```

## Replacing the agent

Implement a class with a `run(text)` method returning a `TriageResult` (or
adapt another result into it), then pass the instance to `ReliabilityHarness`.
This keeps the dataset and scoring logic separate from the system under test.

