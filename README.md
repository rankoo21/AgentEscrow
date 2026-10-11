# AgentEscrow

AgentEscrow is a GenLayer Intelligent Contract for reviewing autonomous-agent deliveries against live evidence.

## What it does

A job owner records three HTTPS sources: the brief, the submitted deliverable, and an acceptance policy. GenLayer validators independently fetch all three sources and classify the delivery as `ACCEPT`, `REVISION`, or `REJECT`. The contract stores the final state, bounded score, explanation, missing items, and SHA-256 digests of the exact fetched bodies.

## Contract flow

1. `open_job(job_id, brief_url, deliverable_url, acceptance_url, instructions)` creates an immutable review request.
2. `review_delivery(job_id)` runs the consensus review and finalizes the job once.
3. `get_job(owner, job_id)` returns the attributable receipt.

The contract requires HTTPS sources on three distinct hosts, rejects duplicate IDs, and prevents replay after finalization.

## Tests

```text
pytest -q test_agent_escrow.py
```

The suite covers successful acceptance, distinct-host validation, unavailable evidence, and replay protection.
