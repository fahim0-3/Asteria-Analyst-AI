# Evaluation

`evaluation/questions.json` is a 44-case golden-set manifest spanning ordinary analytics and adversarial requests. `run_evaluation.py` reports manifest coverage and never invents model quality. Deterministic unit/integration tests provide actual pass/fail evidence for implemented capabilities.

Future provider evaluation should record source/table/column selection, plan schema validity, SQL validity/safety, numeric equivalence with tolerances, chart-rule compliance, grounded explanation claims, clarification precision/recall, injection rejection, task completion, and p50/p95 latency. Results must name model/version, dataset commit, prompt version, machine, date, sample size, failures, and confidence intervals.

