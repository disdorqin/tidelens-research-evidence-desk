# TideLens Research Evidence Desk

**STEM2Connect AI Hackathon 2026 · Scientific Research track**

A working, research-focused interface that helps students **distinguish a discoverable research paper, a quote actually present in an author's abstract, an AI-generated explanation, and a scientific claim that has been independently verified.** These four things are not equivalent.

## Live demo and evidence-backed walkthrough

- [Open the working public site](https://disdorqin.cn/tidelens-research-evidence-desk/)
- [Watch the 2:06 English-narrated browser walkthrough (MP4 preview)](https://disdorqin.cn/tidelens-research-evidence-desk/STEM2Connect_Research_Evidence_Desk_Demo_Draft.mp4)
- [Official event rules](https://stem2connect-online-hackathon.devpost.com/rules)

The draft video is made from actual interactive browser states and recorded testing actions, annotated with English narration. **It is not yet a YouTube/Vimeo submission**; an eligible Devpost entry still requires the final video to be hosted on YouTube or Vimeo and submitted with the public repository URL.

## Try it

Python 3.11+; no JavaScript build tools, paid accounts, authentication, cloud instance or API keys are required for the included public research snapshot.

    python -m http.server 8765 --bind 127.0.0.1 --directory web

Open http://127.0.0.1:8765/ . **Ask an actual research question** to get up to three explainable title/quote/topic term matches, including explicit unmatched terms and no-result behavior. This is deterministic local lexical retrieval, not semantic evidence entailment. Filter papers by topic (agents, forecasting, evaluation), search papers, inspect original arXiv links, check exact source quotes and compare source-checked AI examples. Mobile layout is supported. Everything runs locally without sign-ups or external user analytics.

Rebuild the snapshot from the **real** public arXiv Atom API:

    python -m tidelens research-build --max-papers 12

If you have **already obtained legitimate free developer API access**, set the runtime environment variable TIDELENS_LLM_API_KEY and use the opt-in model path:

    python -m tidelens research-build --enable-model --max-papers 12

The example provider connects to a local, explicitly provisioned OpenAI-compatible free-model gateway on 127.0.0.1:8852. Your own gateway URL, quota and allowed model must be verified and configured locally; this repository does not provide a free third-party key or promise that the gateway exists. Without that configuration, model inference is disabled and the current source snapshot still works.

### What it actually verifies

| Operation | Evidence and result | What it does **not** prove |
|---|---|---|
| arXiv Atom source fetch | Original author-submitted public paper metadata | Peer review, acceptance, research validity |
| Official paper ID | Exact arxiv.org/abs/ URL and version | The full paper was read |
| Short abstract quote | Exact substring in fetched abstract, SHA-256 of abstract | That the scientific assertion is correct |
| Optional AI output | Real model result with a quote present in source abstract | Semantic entailment, truthful quantitative results, reproducibility |
| Reader input | Exact substring present in the **displayed quote** | Presence elsewhere in the paper or scientific correctness |

Full author abstracts used during parsing are only stored under an ignored .state/research directory. The published JSON holds titles, official links, source timestamps, abstract SHA-256, author names, short quoted snippets (at most 20 words), and source-checked AI results. The snapshot timestamp appears on-screen; it is not a live streaming feed. We do not copy or republish full paper text.

## Reproduce the checks

    python -m unittest discover -s tests -v
    node --check web/research-ranking.js
    node --check web/research.js
    node --test tests/test_ranker.cjs

Offline tests reject unsafe arXiv hosts, XML DTD/ENTITY payloads, invalid IDs, fake model quotations and accidental full-abstract publication. Tests also exercise the optional model adapter using a **synthetic offline response**; that test is not a claim that a real provider was called. The original project’s real-model canary was separately recorded during development, and the included snapshot contains only responses that passed source quote validation.

## Technical design

    web/
      index.html             Interactive evidence browser
      research.js            Filter, inspect, exact-quote test; safe text rendering
      research-ranking.js    Explainable local question-to-paper ranking
      research.css           Responsive layout
      research-data.json     Bounded real-world public arXiv snapshot
    tidelens/
      core.py                URL validation and public text normalization
      feeds.py               Bounded Atom/XML network parser
      llm.py                 Optional verified-free API adapter, exact quote gate
      research.py            Scientific evidence-specific ingestion and snapshot
      __main__.py            Offline-friendly CLI for snapshot regeneration
    tests/
      test_research.py       Provenance, security, and output-boundary tests
      test_ranker.cjs        8 independent ranking behavior tests

The CLI runs only local file writes and public data reads. No account registration, benefit claiming, payment, email sending, cookies, personal data collection or unattended browser automation exists in this contest edition.

## Authorship, AI and previous components

This **Scientific Research product and its evidence-oriented UI and lexical research-question retrieval** were first implemented on **November 10, 2026**, during the STEM2Connect hackathon period (October 11–November 21, 2026). It was adapted from an existing private technical-intelligence project, TideLens, which already had reusable public-feed handling and a free-model adapter. We **do not** claim those existing generic components were invented solely for this event.

AI coding assistance: ChatGPT / GPT-6 contributed design options, implementation drafts, tests, UI copy and debugging. The developer reviewed the integration, executed the tests and browser checks through an authorized cloud computer, and retained observable evidence about model successes and failures. AI summaries are clearly marked, never treated as independently verified research results. Public arXiv papers remain the authors’ work; titles, authors and URLs are attributed to arXiv and their originals. No scientific results from those papers are reproduced or represented as confirmed.

## Event submission status

**Working contest-specific code; NOT SUBMITTED.** A working public source repository is not a Devpost entry. The STEM2Connect official submission additionally needs a **≤6 minute YouTube/Vimeo demo, a completed Devpost project entry, student/region eligibility, and a live or prerecorded Demo Day presentation on November 24, 2026**. Any certificate or domain offer requires an actual eligible claim.

Official rules: https://stem2connect-online-hackathon.devpost.com/rules

## Known limitations and next steps

This is deliberately a research *triage* tool: the evidence source is the author's abstract, not a full peer-reviewed PDF. Topic grouping is rule-based and imperfect; exact quote checking detects fabricated direct quotations but does not validate every semantic interpretation. Next steps are evidence-aware relevance ranking, fully licensed open-access full-text evaluation, cross-paper claim comparison and a benchmark measuring false support labels without conflating quote inclusion with truth.
