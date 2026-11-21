# Obsidian-compatible storage

Use plain Markdown, YAML frontmatter, JSON, and CSV so Dataview, Tasks, or Calendar can read the records without a special plugin. A plugin with an HTTP/REST API may be used as an enhancement, but it is not required.

## Vault layout

```text
EnglishListening/
├── Materials/
│   └── <material-slug>/
│       ├── source.md
│       ├── transcript.txt
│       ├── progress.json
│       ├── sessions.jsonl
│       ├── expressions.md
│       ├── daily/
│       │   ├── 2026-11-10.md
│       │   └── 2026-11-10-practice.html
│       └── annotated-transcript.html
└── Reports/
    ├── weekly/
    └── monthly/
```

If the user's Obsidian Vault is available, use its absolute path as `--vault-root`. If not, write the same layout under the current workspace and disclose the path.

## Daily note frontmatter

```yaml
---
material_id: ai-agents-in-medicine
title: AI Agents in Medicine
date: 2026-11-10
segment: 00:08:42-00:12:18
learned_until: "00:12:18"
status: in_progress
error_count: 18
main_weakness: 弱读和医学词汇
---
```

The daily note should link to the same-day HTML practice sheet. Keep the raw dictation in `sessions.jsonl` or a separate `dictation.txt`; do not replace it with the corrected text.

## Progress rules

- Ask for progress at the natural end of each study session.
- `learned_until` may be a timestamp or segment identifier.
- If the user does not answer, save `null` and `progress_status: unconfirmed`.
- A long material remains `in_progress` until the user explicitly says it is complete.
- On completion, set `status: completed` and generate the final full transcript.

## Plugin note

Dataview/Tasks/Calendar can render Markdown and frontmatter. A Local REST API or similar plugin can provide programmatic note creation if configured. Never store API tokens in skill files; use environment variables or local configuration outside the repository.
