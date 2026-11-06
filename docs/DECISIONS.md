# Architecture Decisions -- ADK Orchestration

## Why Google ADK?

Google's Agent Development Kit (ADK) provides a structured framework for
multi-agent workflows with first-class support for parallel execution,
session/state management, and observability.  Compared to the previous
Fetch.ai/Agentverse approach (which required an external EC2 instance and
inter-service HTTP calls), ADK runs everything in-process.

## Custom BaseAgent vs LlmAgent

We use a **custom `BaseAgent`** (`AdvisorCoordinator`) rather than an
`LlmAgent` for the coordinator.  The pipeline order is deterministic:

1. Select personas
2. Fan-out persona critiques
3. Aggregate results

There is no reason for an LLM to "decide" which step to run next -- it would
add latency and cost for no benefit.  A `BaseAgent` with a hard-coded
`_run_async_impl` gives us full control, zero wasted tokens, and
predictable behaviour.

Individual persona analyses still use an LLM (GPT-4o-mini by default) but
they are invoked as plain async calls, not as `LlmAgent` instances, because
each call is a single-shot completion with no tool use or multi-turn
reasoning.

## Parallel fan-out design

Rather than using ADK's built-in `ParallelAgent` (which requires sub-agents
to be defined at construction time), we dynamically fan-out using
`asyncio.gather` with a semaphore inside `fan_out_persona_analyses()`.  This
is because:

- The number and identity of persona agents are determined at runtime from
  Supabase query results.
- Each "agent" is really a single LLM call -- no tools, no memory, no
  multi-turn.  Wrapping each in a full ADK `LlmAgent` would add overhead
  without benefit.
- The semaphore (`concurrency=10` by default) respects API rate limits
  while maximising throughput.

If persona agents grow more complex in the future (e.g. multi-turn
reasoning, tool use), they can be upgraded to proper ADK `LlmAgent`
instances without changing the coordinator.

## Dynamic persona agent creation

Persona agents are **never** hand-written.  They are created at request time
from Supabase persona records.  The `build_system_prompt()` function in
`persona_agent.py` templates the persona's demographics, psychographics,
pain points, and motivations into a system prompt.  This means:

- Adding new personas to Supabase automatically makes them available.
- No code changes are needed when the persona set changes.
- The same prompt template is shared by both ADK and legacy paths.

## ADK vs legacy comparison

| Dimension | ADK path | Legacy path |
|-----------|----------|-------------|
| Concurrency | 10 parallel LLM calls via semaphore | Sequential with 0.2s sleep |
| Latency (50 personas) | ~1-2 min | ~10+ min |
| Session/state | ADK session state | Local variables |
| Observability | ADK events | Print statements |
| Dependency | `google-adk` pip package | None (stdlib only) |

The `ORCHESTRATOR` env var (`adk` or `legacy`) controls which path is used.
Default is `adk`.  Setting `ORCHESTRATOR=legacy` preserves the original
behaviour for rollback safety.

## Graceful degradation

If `google-adk` is not installed (e.g. in a lightweight CI environment), the
ADK coordinator automatically falls back to a plain-async implementation
that uses the same `fan_out_persona_analyses` function.  This means the
`ORCHESTRATOR=adk` path works even without the pip package -- it just skips
the ADK runner/session wrapper.
