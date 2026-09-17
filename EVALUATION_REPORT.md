# Agent Reliability Evaluation Report

## Executive summary

The support triage agent was evaluated on **25 known-good cases**, repeated **5 times each** for **125 total runs**. The dataset includes normal requests plus empty, vague, formatting, long-input, multi-intent, negation, typo, security, and multilingual cases.

## Exact definition of success

A run succeeds only if it completes without an exception and its `category`, `priority`, and `action` all exactly equal the known-good expected values. Partial matches are failures. Token and cost estimates do not affect the pass/fail decision.

## Results

| Metric | Result |
|---|---:|
| Successful runs | 100 / 125 |
| Success rate | 80.00% |
| Average steps per run | 3.00 |
| Average input tokens | 10.00 |
| Average output tokens | 9.08 |
| Total estimated cost | $0.00086850 |
| Cost per successful run | $0.00000869 |
| Consistent cases across repeats | 25 / 25 (100.00%) |

Cost uses the configured rates and transparent character-based token estimates. It is an estimate, not a provider invoice.

## Top three failure modes

1. **Multilingual input** — 10 failed runs. The keyword rules do not model this language pattern reliably.
2. **Misspellings and paraphrases** — 10 failed runs. The keyword rules do not model this language pattern reliably.
3. **Negation handling** — 5 failed runs. The keyword rules do not model this language pattern reliably.

## What I would fix first

I would first replace first-keyword-wins classification with a structured intent scorer that detects negation and ranks security, technical impact, billing, access, and cancellation explicitly. This directly addresses multi-intent and negation errors without weakening the already-correct happy paths. Next I would normalize common misspellings and add multilingual examples or a language-aware model. I would rerun this exact fixed dataset after every change, then add each newly discovered production failure as a regression case.

## Reproduction

Run `python run_evaluation.py`. Per-run evidence is in `results/results.csv`; aggregate metrics are in `results/summary.json`.
