# Material search and source validation

Search the open web using the host's available search and page-reading tools. Do not bypass authentication, paywalls, DRM, or access controls. A public link is an acceptable deliverable.

## Candidate record

Record these fields before recommending a source:

```json
{
  "title": "...",
  "domain": "medical",
  "topic": "...",
  "source_name": "WHO / Stanford HAI / official company channel",
  "source_url": "https://...",
  "published_at": "2026-10-15",
  "freshness": "recent|current_classic|older_reference",
  "duration": "9:42",
  "source_type": "official_article_audio|official_podcast_transcript|official_talk_transcript|conference_transcript|interview_transcript|auto_caption_video|text_only",
  "format": "article|talk|interview|lecture|podcast|video",
  "audio_duration": "6:26",
  "listen_to_article": true,
  "accent": "US|UK|mixed|unknown",
  "transcript_type": "official|human_edited|auto_generated|none|unknown",
  "transcript_url": "https://...",
  "access": "public",
  "quality": "high|medium|low",
  "why_recommended": "..."
}
```

Prefer 5-15 minute sources. Accept longer materials as a self-paced project. Do not trim copyrighted audio merely to fit a duration window.

## Freshness and current-information priority

When the user does not request a classic talk, rank candidates by both **recency** and **learning reliability**:

1. Recent official company or research-organization articles with a `Listen to article` player and the official article text, then official talks, launch presentations, developer events, keynotes, and named expert interviews.
2. Recent reputable industry podcasts, conference sessions, and publications with public audio plus a reliable transcript.
3. Recent university or institutional lectures.
4. Older high-quality talks when newer material lacks a usable transcript.

Prefer material published within the last 12 months when available. If not, choose the newest credible source with a reliable transcript and explain its date. Never claim something is the latest without verifying `published_at`; include an `as_of` date in the recommendation.

For example, an official OpenAI article with `Listen to article` and the original article text is usually preferable to a generic old AI introduction; it combines current information, a controlled audio version, and reliable source text. A new *Economist* item is attractive when its audio and transcript are publicly accessible, but do not bypass a paywall or silently rely on an inaccurate auto-caption. Current information is valuable, but reliable text remains mandatory.

## Source tiers

### Cross-domain baseline

1. Official institutions, universities, research institutes, standards bodies.
2. Official company channels for talks by named employees or executives.
3. Established professional conferences and associations.
4. Reputable public media and podcasts with public transcripts.
5. Other sources only when the user asks and the provenance is clear.

### Medical

Prioritize WHO, NIH, CDC, FDA, national health agencies, medical schools, hospitals, professional societies, peer-reviewed journals, and medical conferences. Label material as educational listening practice, not medical advice. Flag dosage, trial, diagnostic, and treatment claims for careful transcription.

### Marketing and business

Prioritize official platform documentation/channels, business schools, industry associations, recognized research firms, and named conference presentations. Distinguish research claims, vendor claims, and opinion.

### Technology and AI

Prioritize official model/company channels, university labs, standards bodies, and named conference talks. Distinguish product demonstrations from research claims.

## Transcript quality

- `official` or `human_edited`: suitable for high-confidence diffs.
- `auto_generated`: usable, but mark uncertain words and tell the learner that caption errors are possible.
- `none`: do not run a word-level diff unless the user supplies a transcript or the host has an approved audio transcription workflow.
- Never present auto-generated text as an official transcript.

## Candidate output

Give the user a compact comparison table and ask them to select one. Include direct links, publication dates, freshness notes, and transcript provenance. If no candidate meets the duration or transcript requirement, say what is missing instead of lowering the standard silently.


## Source-type routing

Search in this order and record the source type explicitly:

1. **Official article + `Listen to article` + official article text.** Highest priority. Examples include official OpenAI, Google, DeepMind, Anthropic, Microsoft, IMF, World Bank, WHO, or industry-company articles with an audio player.
2. **Official podcast or interview + reliable transcript.**
3. **Official talk, keynote, lecture, or conference session + official/human-edited transcript.**
4. **Established publisher or institution + public audio + transcript.**
5. **Video with auto-generated captions only.** Usable with a clear quality warning, not equivalent to official text.
6. **Text-only pages.** Not suitable for dictation unless paired with authentic audio.

A `Listen to article` page is especially valuable because the page text is the source transcript and the audio is a controlled narration. Record `listen_to_article: true` and `audio_duration` when present.

## Domain registry

Use [domain-sources.json](domain-sources.json) as a starter registry, not an allowlist. Expand it when the user names a credible source. For example:

- **AI:** OpenAI, Anthropic, Google DeepMind, Microsoft Research, Stanford HAI, TED.
- **Economics:** The Economist, IMF, World Bank, BIS, central banks, NBER.
- **Law:** Supreme Court, federal courts, DOJ, ABA, law schools, legal podcasts.
- **Marketing:** Think with Google, LinkedIn Business, HubSpot, AMA, Nielsen, major conferences.
- **Medicine:** WHO, NIH, CDC, FDA, medical schools, NEJM, The Lancet, BMJ.

The registry only helps discovery; every candidate still needs its publication date, access status, audio, and transcript checked.

## Search routing

Use a focused source-type query before broad web search:

```text
site:openai.com "Listen to article" enterprise AI
site:imf.org "Listen to article" monetary policy
site:supremecourt.gov oral argument transcript
site:thinkwithgoogle.com "Listen to article" marketing
```

Then use official site search, RSS, or a known source page. Do not keep rewriting broad queries in loops. If search is unavailable, ask for a direct source link or use a known source page and disclose the limitation.

## Ranking and fallback

Run the deterministic shortlist helper:

```bash
python scripts/rank_candidates.py candidates.json --as-of 2026-11-15 --format markdown
```

The helper prioritizes source type, transcript quality, access, freshness, duration, and `listen_to_article`. It does not decide whether a page is genuinely current or whether its transcript is accurate.

If the best candidate is blocked by a paywall, login, region, or Cloudflare:

1. Do not bypass the restriction.
2. Try the official source's public article/audio page, RSS, or an accessible mirror only when the publisher provides it.
3. Return the best accessible candidate and state exactly what could not be verified.
4. Never silently replace official text with TTS or an unverified auto transcript.


## URL verification across domains

A title is not a URL. Slugs differ by publisher and may change after publication. Do not synthesize paths such as `/index/<title-slug>/` unless the page or a publisher link confirms that exact path.

Before saving a source URL:

1. Use the URL that actually opens in the user's browser, the publisher's share/canonical link, an official sitemap/RSS link, or a user-provided exact URL.
2. Confirm the page title, author/organization, and media type match the candidate.
3. Prefer the canonical URL over search-engine redirect or tracking links.
4. Record `url_status`:
   - `verified`: the agent opened the page and checked its metadata;
   - `user_provided_verified`: the user supplied the exact working link and the title/source match;
   - `inferred`: only a likely slug or search result was available;
   - `blocked`: the URL exists or may exist, but Cloudflare/paywall/login/region prevents verification.
5. Record `url_provenance`: `publisher_canonical`, `publisher_share`, `official_sitemap`, `user_provided`, `search_result`, or `inferred`.
6. If the page is blocked, do not claim the URL is verified. Ask for the original share link or choose another source.

This matters in every domain:

- AI company pages may use different `/index/`, `/news/`, `/business/`, or campaign paths.
- *The Economist* and other publishers may use article IDs, syndicated paths, or paywalls.
- Legal sources may use docket or opinion URLs rather than human-readable title slugs.
- Marketing sources may use campaign URLs or tracking redirects.

Search the publisher domain and media type first; never let a guessed slug become the saved source of truth.
