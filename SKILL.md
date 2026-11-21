---
name: shangwenjie-dictation-coach
description: Run a Shangwenjie-style English dictation workflow for any subject domain. Find credible 5+ minute speeches, talks, lectures, interviews, or podcasts with usable transcripts; diagnose a learner's dictation errors; generate a same-day printable HTML shadowing sheet; save self-paced progress and learning notes in an Obsidian-compatible Markdown vault; and produce weekly/monthly summaries plus a final highlighted transcript. Use when the user requests material discovery, dictation correction, listening-error diagnosis, shadowing practice sheets, or long-material learning records.
---

# Shangwenjie Dictation Coach

Treat a long source as a **self-paced learning project**, not a one-session exercise. Preserve the learner's original dictation, separate observable errors from inferred causes, and create a usable practice sheet after every study session.

## Required inputs

Use the information already provided. Do not block on optional setup questions.

- **Domain and topic:** for example medical imaging, AI agents, brand positioning, finance, education.
- **Minimum duration:** default to 5 minutes or longer unless the user asks otherwise.
- **Source material:** a public URL. Search for credible sources when no URL is supplied.
- **Dictation:** the learner's raw text. Preserve blanks and uncertain markers; do not silently correct it.
- **Learning position:** at the end of each session ask, `今天学到哪里？时间戳、段落编号，还是已经学完全文？`

If the source transcript is unavailable, explain the limitation and ask for a transcript or audio before attempting a reliable diff. Never pretend that auto-generated captions are official transcripts.

## Workflow

For a sentence-by-sentence study session, read [session-flow.md](references/session-flow.md). The default rhythm is: separate raw/corrected/source text → understand one sentence → shadow continuously → checkpoint correction → unscripted output → save the sentence record → move to the next red correction.

1. **Find or validate the material.** Read [material-search.md](references/material-search.md) and [domain-sources.json](references/domain-sources.json) when searching. Route by source type first: official article with `Listen to article`, then official podcast with transcript, then official talk/lecture, then other credible audio. Return 2-3 candidates with source, publication date, duration, transcript quality, domain credibility, freshness, access, and URL. Prefer newer material and current domain information, but never sacrifice transcript reliability merely to chase recency. Use `scripts/rank_candidates.py` to shortlist candidates consistently. Prefer full public material over paywalled or scraped copies.
2. **Prepare the source transcript.** Save the exact transcript used for comparison and record whether it is official, human-edited, auto-generated, or user-provided. Use stable paragraphs and timestamps when available.
3. **Align the dictation.** Run the deterministic aligner rather than comparing only by eye:
   ```bash
   python scripts/dictation_tools.py align \
     --source source.txt \
     --dictation dictation.txt \
     --output alignment.json
   ```
   The script distinguishes omissions, insertions, replacements, and spelling. Read [error-taxonomy.md](references/error-taxonomy.md) before interpreting causes such as weak forms, linking, vocabulary, grammar, or memory load. Use `annotations.json` to override automatic categories when audio evidence supports a better diagnosis.
4. **Create today's practice sheet immediately.** Do not wait until a long material is complete. Build the daily HTML with the clean source, the learner's original dictation, inline error highlights, short shadowing chunks, expressions, and a completion checklist:
   ```bash
   python scripts/dictation_tools.py daily-html \
     --source source.txt \
     --dictation dictation.txt \
     --alignment alignment.json \
     --metadata metadata.json \
     --diagnosis diagnosis.json \
     --output daily-practice.html
   ```
   The learner should be able to print this one file and use it for the day's listening and shadowing.
5. **Save the daily record.** Use the Obsidian-compatible Markdown workflow in [obsidian-schema.md](references/obsidian-schema.md):
   ```bash
   python scripts/dictation_tools.py save-session \
     --vault-root /absolute/path/to/ObsidianVault \
     --metadata metadata.json \
     --alignment alignment.json \
     --dictation dictation.txt \
     --learned-until "00:12:18" \
     --html daily-practice.html
   ```
   If no vault path is available, save the same structure under the current workspace and say where it is.
6. **Close each session by asking for progress.** Ask only once at a natural end: `今天学到哪里？时间戳、段落编号，还是已经学完全文？` Save the answer as `learned_until`. If unanswered, store `null` and `progress_status: unconfirmed`; never invent progress.
7. **Finish a long material only after explicit confirmation.** When the user says the material is complete, merge all recorded errors and create the full annotated transcript:
   ```bash
   python scripts/dictation_tools.py final-html \
     --source source.txt \
     --alignment combined-alignment.json \
     --metadata metadata.json \
     --vault-root /absolute/path/to/ObsidianVault \
     --output annotated-transcript.html
   ```
8. **Build period summaries from actual records.** Use weekly/monthly reports from [reporting.md](references/reporting.md), not from model memory:
   ```bash
   python scripts/dictation_tools.py report \
     --vault-root /absolute/path/to/ObsidianVault \
     --period weekly \
     --output Reports/weekly/current.md
   ```

## Material rules

- Support any domain. Use the domain source policy in [material-search.md](references/material-search.md); medical materials require stricter official/peer-reviewed sourcing and an educational-use disclaimer.
- Prefer newer material that also teaches current domain information: recent official company talks, launches, keynotes, research presentations, reputable industry podcasts, and current publications such as *The Economist* when their audio and transcript are publicly accessible. **Highest priority:** official company/article pages that provide a `Listen to article` audio player plus the official article text, such as OpenAI articles. Record `published_at`, `audio_duration`, `source_type`, and a freshness note. If the newest item lacks a reliable transcript, choose the newest credible item that does and explain the tradeoff.
- Use the source-type fallback ladder and per-domain registry in [material-search.md](references/material-search.md). Do not rely on one search engine or one website. If the host cannot access a page, say so and try an official source or user-provided link rather than silently substituting low-quality content.
- Accept materials of 5 minutes or more. Do not force a long material into a single day.
- Prefer sources with a transcript, captions, or reliable audio. Record transcript provenance and uncertainty.
- Link to the public source. Do not bypass paywalls, login walls, DRM, or access controls.
- Keep the learner's raw dictation unchanged in `dictation.txt` or the saved record.
- **Never infer a URL from a title or slug.** Save only a URL that was opened successfully, returned by the publisher's canonical/share link, or explicitly supplied by the user. Record `url_status` (`verified`, `user_provided_verified`, `inferred`, or `blocked`) and use `canonical_url` when available. If a page is blocked by Cloudflare, a paywall, login, or region restrictions, ask for the exact user link or choose another accessible source instead of sending a guessed URL.

## Feedback rules

- Give only 2-3 highest-priority weaknesses per day.
- Distinguish the observed error from the inferred cause. Use confidence labels when the audio cannot prove a cause.
- Do not call spelling mistakes listening errors unless the learner actually heard the word incorrectly.
- Do not judge pronunciation or fluency from written dictation alone.
- Keep the daily HTML practice-oriented: clean source first, corrections second, shadowing tasks third.
- Prefer one sentence or one red correction per learning turn. Use the mobile-friendly sequence from [session-flow.md](references/session-flow.md): short conclusion → chunked understanding → continuous shadowing → checkpoint correction → Chinese-cued unscripted output.
- **Do not interrupt every shadowing repetition by default.** Let the learner speak or repeat continuously. Correct only at a natural checkpoint (for example after a sentence group or 2-3 repetitions), when the learner asks for feedback, or when an error would seriously change the meaning. Offer these modes explicitly when useful: `flow` (no mid-practice interruption; summary at checkpoint/end), `checkpoint` (feedback after each sentence group), and `coaching` (feedback after each repetition). The user's choice overrides the default.
- Preserve useful expressions from the actual material and actual errors; do not pad the list with unrelated vocabulary.

## Outputs

Daily session:

```text
Materials/<material>/
  daily/YYYY-MM-DD.md
  daily/YYYY-MM-DD-practice.html
  progress.json
  sessions.jsonl
```

After completion:

```text
Materials/<material>/
  annotated-transcript.html
  expressions.md
```

Period reports:

```text
Reports/weekly/YYYY-Www.md
Reports/weekly/YYYY-Www.csv
Reports/monthly/YYYY-MM.md
Reports/monthly/YYYY-MM.csv
```
