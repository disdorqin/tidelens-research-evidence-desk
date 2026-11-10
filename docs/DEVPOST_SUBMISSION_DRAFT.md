# STEM2Connect / Devpost Submission Draft — NOT SUBMITTED

**Last prepared:** November 10, 2026. This is proposed copy for the owner's authenticated Devpost project form. No enrollment, project creation or submission receipt is asserted.

## Project title
TideLens Research Evidence Desk

## One-line tagline
From research questions to traceable arXiv evidence — without confusing an exact quotation with scientific truth.

## Primary track
Scientific Research

## Live links
- **Live project:** https://disdorqin.cn/tidelens-research-evidence-desk/
- **Public source and tests:** https://github.com/disdorqin/tidelens-research-evidence-desk
- **Preview walkthrough (2:06, MP4, not yet a YouTube/Vimeo entry):** https://disdorqin.cn/tidelens-research-evidence-desk/STEM2Connect_Research_Evidence_Desk_Demo_Draft.mp4
- **Official video URL for Devpost:** PENDING_OWNER_YOUTUBE_OR_VIMEO_UPLOAD

## What problem are you solving?

Students working on AI or scientific research face a recurring evidence problem. Search feeds provide titles, papers offer author-written abstracts, and large models can produce confident explanations. These three forms of information are often blended into one apparently authoritative answer. Finding an original sentence is useful, but that alone does not prove a claim is scientifically correct or peer reviewed.

Research Evidence Desk makes those trust boundaries explicit and lets a student begin with a practical research question rather than browse random links.

## What did you build?

A working, accessible web interface connected to **real arXiv author-submitted source metadata**. It includes:

1. A scientific research question input that shortlists up to three papers from the local source snapshot, showing matched title, topic or exact quote terms and clearly listing uncovered terms. This is transparent lexical matching, not semantic proof.
2. An original-source inspector with the author list, versioned arXiv link, UTC submission timestamp, a short exact quotation and SHA-256 fingerprint of the fetched abstract.
3. A user-operated quote checker. A matching string is labeled as a **textual match only**; unsupported quotes are rejected rather than invented.
4. Optional model-backed analysis through a configured and legitimately obtained free OpenAI-compatible model endpoint. Answers appear only when the generated short quotation is present in the exact original abstract.
5. Fully client-side filters, search, responsive layout and GitHub Pages hosting with no user accounts, private analytics or sensitive account permissions.

The public snapshot contains 12 real arXiv papers from the captured feed. **All 12 source excerpts passed exact matching against the fetched abstracts; one real model response passed the optional quote gate**. These are source-checking metrics, not accuracy scores for research conclusions.

## What AI did you use?

A pre-existing legally configured free-tier OpenAI-compatible model pool was used for the optional abstract extraction demonstration. Its raw output only became visible in the public snapshot after a direct source-quote check. An unavailable, unverifiable or unsupported output was left unverified rather than promoted to a correct scientific conclusion.

ChatGPT / GPT-6 was used as a coding assistant for architecture discussion, JavaScript/Python implementation, UI copy, QA design and debugging. The developer verified the changes using isolated reproducible tests, browser interactions and a real public-data canary. This AI assistance and the reuse of prior generic source-handling components are acknowledged in the repository README.

## What were the main challenges?

The most important design decision was treating **source integrity, quotation integrity, model validity and scientific validity as different questions**. Many demo applications promote a source URL to an authority badge without showing which source span backs the conclusion. We instead make a negative result first-class: irrelevant questions return "no matching evidence"; invented direct quotations are rejected.

Another challenge was privacy. This public competition build is isolated from the older private TideLens project. No email, enterprise chat messages, API keys, cookies or private opportunity records were exported. The current public artifact contains bounded author-attributed metadata and at most 20 words of source quotation per paper, not complete paper text.

## How did you validate it?

- Direct arXiv Atom API ingestion and traceable author/paper/version URLs.
- All 12 committed research-card quotes match their originally retrieved abstracts.
- The interactive browser shows three matches for an agent-memory example and two for forecasting, while unrelated questions produce a truthful no-match outcome.
- Exact positive and negative quote checks verified in a real browser.
- 390px mobile viewport verified without horizontal overflow.
- Python research parser/security tests and Node.js lexical ranking tests run in the public GitHub Actions workflow.
- The included MP4 preview is assembled from actual browser screenshots at interactive states with an English explanation. It is **not falsely described as a continuous human-camera recording** or proof of a Devpost submission.

## What did you learn?

Transparent explanations are more useful than a confidence percentage that cannot be audited. An original text fragment, a model extraction, and independently reproduced scientific evidence need distinct labels and separate validation steps. A small source set with honestly reported coverage is preferable to generating citations for questions the available evidence cannot answer. We also learned to prioritize reproducible negative tests, source attribution and isolation of public demo code from private operational infrastructure.

## What's next?

Broaden the authorized research corpus, introduce retrieval quality benchmarks with human relevance judgments, evaluate model claim-to-evidence entailment beyond exact quotation, and support open-access full text **only when licenses and data access permit it**. A second improvement is to capture research questions and evidence-selection feedback locally, without collecting personal information, to improve pedagogical value.

## Built with
Python 3.12, Python standard library, arXiv Atom public API, JavaScript, HTML, CSS, GitHub Pages, GitHub Actions, Git, optional verified-free OpenAI-compatible LLM endpoint.

## Team
Solo entrant (owner must add or verify identity and student eligibility in Devpost). Do not invent team members.

## Submission checklist (all required before marking submitted)
- [ ] Owner logged into their own Devpost account, accepted rules and joined STEM2Connect.
- [x] Public source repository and README link usable anonymously.
- [x] HTTPS demo running without an account.
- [x] Preview demonstration video prepared and publicly reachable.
- [ ] Final video uploaded to **YouTube or Vimeo**, public or unlisted, **≤ 6 minutes**.
- [ ] Devpost project form completed, Scientific Research selected, genuine team members supplied, official submission receipt saved.
- [ ] November 24 Demo Day participation or organizer-approved prerecorded presentation, with receipt where applicable.

**Submission deadline:** November 21, 2026, 23:59 EST. **Demo Day:** November 24, 2026. Follow any organizer changes announced to registered participants.
