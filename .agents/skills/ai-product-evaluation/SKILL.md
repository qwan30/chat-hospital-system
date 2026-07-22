---
name: ai-product-evaluation
description: Evaluate an AI product or release with baseline-first gates, deterministic and live lanes, reproducible evidence, and report-integrity checks. Use for planning, running, reviewing, or reporting AI quality and safety evaluations.
---

# AI Product Evaluation

## Establish the evaluation contract

1. Define the decision to support, release candidate, owners, risks, and pass/fail thresholds before running an evaluation.
2. Freeze a baseline: commit, configuration, model/provider version, prompt version, dataset revision, evaluator version, and environment.
3. Separate deterministic checks from live checks. Do not let a live-provider outage hide a deterministic regression.
4. State what each lane proves and does not prove. Local results do not certify CI, production behavior, or a different model configuration.

## Run baseline-first gates

1. Run schema, fixture, unit, policy, and replayable integration checks first.
2. Record total, passed, failed, skipped, xfailed, duration, command, and artifact locations for every gate.
3. Treat a changed baseline, missing artifact, unapproved threshold change, or unresolved safety failure as a blocked verdict.
4. Run live-model or live-service evaluation only after deterministic gates pass or the report explicitly isolates the exception.
5. Label live runs with provider, model, region, timestamp, budget, retries, and nondeterminism controls.

## Preserve report integrity

1. Link every claimed metric to its raw result, input revision, and exact command.
2. Report denominators, exclusions, failures, and uncertainty; never replace a failed run with a selective sample.
3. Keep baseline and candidate results comparable. Explain any dataset, prompt, evaluator, or environment drift.
4. Issue one verdict: `GO`, `NO-GO`, or `CONDITIONAL`. List blocking evidence and required follow-up for conditional results.

## Install globally

Run `scripts/Install-AiEvaluationSkills.ps1 -WhatIf` to preview the four supported global skill-root junctions. Run it without `-WhatIf` only after reviewing the targets. The installer refuses to replace a non-junction directory.
