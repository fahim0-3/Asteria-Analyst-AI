# Analytics agent design

The implemented workflow is bounded and non-autonomous: validate request → retrieve owned source → load schema/profile → classify intent → detect material ambiguity → construct Pydantic plan → validate columns/operators/limits → execute registered functions → serialize and validate result → choose chart → form grounded explanation → persist context/audit. There is no tool-selection loop and no hidden retry spiral.

`mock_planner.py` is deterministic and deliberately conservative. A provider adapter should return the identical `AnalysisPlan` schema with temperature zero; output must still cross the same validators. The user-facing trace contains methodology and assumptions, never private chain-of-thought. Follow-up state stores the prior plan/data reference so later resolution can be based on reproducible facts rather than prose alone.

