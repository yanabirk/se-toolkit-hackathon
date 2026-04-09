---
name: lms
description: Use LMS MCP tools for live course data
always: true
---

# LMS Skill

Use LMS MCP tools to query live data from the Learning Management System backend.

## Available Tools

- `lms_health` — Check if the LMS backend is healthy and report the item count
- `lms_labs` — List all labs available in the LMS
- `lms_learners` — List all learners registered in the LMS
- `lms_pass_rates` — Get pass rates (avg score and attempt count per task) for a lab (requires `lab` parameter)
- `lms_timeline` — Get submission timeline (date + submission count) for a lab (requires `lab` parameter)
- `lms_groups` — Get group performance (avg score + student count per group) for a lab (requires `lab` parameter)
- `lms_top_learners` — Get top learners by average score for a lab (requires `lab` and optional `limit` parameter)
- `lms_completion_rate` — Get completion rate (passed / total) for a lab (requires `lab` parameter)
- `lms_sync_pipeline` — Trigger the LMS sync pipeline

## Strategy

### When the user asks for scores, pass rates, completion, groups, timeline, or top learners without naming a lab:
1. Call `lms_labs` first to get the list of available labs
2. Use the shared structured-ui skill to present the choice to the user
3. Use each lab's `title` field as the user-facing label
4. Pass the lab's `id` field as the `lab` parameter when calling the requested tool

### When the user asks about backend health:
- Call `lms_health` and report whether the backend is healthy along with the item count

### When the user asks what labs are available:
- Call `lms_labs` and present them in a numbered list with titles

### When the user asks for learner-related data:
- For overall learner list: call `lms_learners`
- For top performers in a specific lab: call `lms_top_learners` with the lab ID
- If lab not specified, follow the "missing lab" strategy above

### Formatting numeric results:
- Format percentages with one decimal place (e.g., "88.5%")
- Format counts as plain numbers (e.g., "56 items", "258 learners")
- Present tabular data in a readable format (markdown table or bullet list)

### Response style:
- Keep responses concise and focused on the data requested
- Do not send a separate plain text preamble before calling tools
- If the backend returns an error, explain what went wrong and suggest trying again or checking if the sync pipeline needs to run

## When the user asks "what can you do?"

Explain your current capabilities clearly:

"I can help you query data from the Learning Management System. I can:
- Check if the LMS backend is healthy
- List available labs and learners
- Get pass rates, completion rates, and submission timelines for specific labs
- Show group performance and top learners for a lab
- Trigger the data sync pipeline

Just ask me about any of these, and I'll fetch the live data for you."
