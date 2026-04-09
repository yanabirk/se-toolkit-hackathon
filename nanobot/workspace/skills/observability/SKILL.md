---
name: observability
description: Use observability tools to investigate errors and trace failures
always: true
---

# Observability Skill

Use VictoriaLogs and VictoriaTraces MCP tools to investigate system health and debug failures.

## Available Tools

- `obs_logs_search` — Search VictoriaLogs using LogsQL query
- `obs_logs_error_count` — Count errors for a service over a time window
- `obs_traces_list` — List recent traces for a service
- `obs_traces_get` — Fetch a specific trace by ID

## Strategy

### When the user asks "What went wrong?" or "Check system health":
**Perform a one-shot investigation that chains log and trace evidence:**

1. **Check error count first** — Call `obs_logs_error_count` with service="Learning Management Service" and a fresh time window (last 10 minutes)
2. **If errors exist, search for details** — Call `obs_logs_search` with query=`_time:10m service.name:"Learning Management Service" severity:ERROR`
3. **Extract trace_id from error logs** — Look for `trace_id` or `otelTraceID` fields in the results
4. **Fetch the matching trace** — Call `obs_traces_get` with the trace_id to inspect the full span hierarchy
5. **Synthesize findings** — Provide a coherent summary that explicitly mentions:
   - What the error logs show (event type, error message, affected operation)
   - What the trace reveals (which spans failed, duration, service involvement)
   - The root cause and affected service
   - Any discrepancies (e.g., logs show database failure but response says 404)

### When the user asks about errors or system health:
1. Start with `obs_logs_error_count` to check if there are recent errors for the relevant service
2. If errors exist, use `obs_logs_search` to find the specific error logs
3. Extract any `trace_id` from the error logs
4. Use `obs_traces_get` to fetch the full trace and understand the failure path
5. Summarize findings concisely — don't dump raw JSON

### When the user asks about system health:
1. Check error counts for key services (e.g., "Learning Management Service")
2. Report whether the system is healthy or if there are recent errors
3. If there are errors, provide a brief summary of what went wrong

### Query tips:
- Use narrow time windows for fresh data: `_time:10m` for last 10 minutes
- Filter by service: `service.name:"Learning Management Service"`
- Filter by severity: `severity:ERROR`
- Example query: `_time:10m service.name:"Learning Management Service" severity:ERROR`

### Response style:
- Summarize findings in plain language
- Don't dump raw JSON unless explicitly asked
- If you find a trace, explain what went wrong in the request flow
- If no errors found, say so clearly
- **For "What went wrong?" responses, cite both log evidence AND trace evidence explicitly**

## Example reasoning flow

User: "Any LMS backend errors in the last 10 minutes?"

1. Call `obs_logs_error_count` with service="Learning Management Service", minutes=10
2. If count > 0:
   - Call `obs_logs_search` with query=`_time:10m service.name:"Learning Management Service" severity:ERROR`
   - Look for `trace_id` in the results
   - If trace_id found, call `obs_traces_get` to inspect the failure
   - Summarize: what failed, where, and why
3. If count = 0:
   - Report: "No errors found in the last 10 minutes"

User: "What went wrong?"

1. Call `obs_logs_error_count` with service="Learning Management Service", minutes=10
2. If count > 0:
   - Call `obs_logs_search` with query=`_time:10m service.name:"Learning Management Service" severity:ERROR`
   - Extract trace_id from first error entry
   - Call `obs_traces_get` with that trace_id
   - **Synthesize**: "I found {count} errors in the LMS backend. The error logs show {event} with message '{error}'. The trace {trace_id} reveals the failure occurred in {span/operation}, taking {duration}ms. Root cause: {explanation}."
3. If count = 0:
   - Report: "No recent errors found. The system looks healthy."
