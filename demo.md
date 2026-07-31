# Debate Sparring Partner — Stripped-Down Demo Build Plan

**Purpose:** A lean, public, no-login version of the app for a LinkedIn post / portfolio link — showcases the core AI debate mechanic (RAG-grounded opponent, 3 practice modes, Judge feedback) without any of the multi-school/auth/dashboard infrastructure.

**Relationship to the full build plan:** This is a separate, parallel track — not a replacement. The full multi-school version (`debate_sparring_partner_build_plan.md`) remains the "real" product and portfolio-repo deliverable. This demo reuses the RAG/LLM core (`rag/`, `llm/`) already built, but skips everything auth/Sheets/squad-related in favor of a single hardcoded/pre-loaded scenario anyone can try instantly.

---

## 1. Scope

### Cut entirely
- Google login / `st.login()`
- Schools, squads, coaches, students, rosters
- Google Sheets logging
- Teacher dashboard
- Multi-school data isolation

### Kept, simplified
- **1–3 hardcoded motions**, pre-ingested into ChromaDB with real sources (done once, ahead of time, not through a live coach UI)
- **One fixed case line per side, per motion** (hardcoded in a Python dict or small JSON file, not editable in the UI)
- **All 3 practice modes**, fully functional:
  - Mode 1 — Single-Speech Practice
  - Mode 2 — Turn-by-Turn Round (LangGraph)
  - Mode 3 — Timed Adaptation Drill
- **Judge feedback** — role-specific + coherence criteria, same as the full plan
- **Source transparency panel** — shows which retrieved chunks the AI used (good demo credibility signal)

### Explicitly not needed for a demo
- Result persistence between sessions (a visitor's practice session doesn't need to be saved anywhere)
- Multi-user isolation (every visitor effectively shares the same read-only motion library; nothing personal is stored)

---

## 2. Tech Stack (reused from the main build)

| Component | Source |
|---|---|
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`) — already built |
| Vector store | ChromaDB — already built (`get_chroma_collection`, `store_source`) |
| Chunking | `chunk_text()` — already built |
| LLM (debater + judge) | SenseNova (OpenAI-compatible API) — already confirmed working |
| Orchestration (Mode 2) | LangGraph |
| Orchestration (Modes 1 & 3) | CrewAI — Debater + Judge agents |
| Frontend | Streamlit — new, minimal, no multipage/auth |
| Hosting | Streamlit Community Cloud (free) |

No new infrastructure decisions needed — this reuses everything already proven to work.

---

## 3. File Structure

```
debate-sparring-demo/          # separate small project, or a `demo/` folder within the main repo
├── demo_app.py                 # single-file entry point, no login, no multipage
├── data/
│   └── demo_motions.py         # hardcoded list: motion text, case lines (both sides), pre-ingested motion_id
├── rag/
│   └── retrieve.py              # REUSED from main project (retrieve_relevant_chunks)
├── llm/
│   ├── debater.py               # REUSED/adapted — generates AI response grounded in retrieved chunks + case line
│   └── judge.py                  # REUSED/adapted — role-specific + coherence scoring
├── graph/
│   └── mode2_graph.py            # REUSED — LangGraph state machine for Mode 2
├── crew/
│   ├── mode1_crew.py              # CrewAI: Debater + Judge agents for Mode 1
│   └── mode3_crew.py              # CrewAI: reuses Mode 1's agents for the timed drill
├── ingest/
│   └── seed_demo_data.py         # one-time script: ingest the 1–3 demo motions' sources into ChromaDB
├── requirements.txt
└── README.md                     # written for a LinkedIn/portfolio audience — explain the RAG grounding, the modes, the HK LLM-access story
```

---

## 4. Phased Build Plan

### Phase D0 — Seed demo data (offline, one-time)
**Files:** `ingest/seed_demo_data.py`, `data/demo_motions.py`
- Pick 1–3 strong, recognizable motions (something a LinkedIn audience finds intuitive — e.g., "This House Would ban single-use plastics")
- Write a short case line for both Affirmative and Negative for each, hardcoded
- Find/paste 2-4 real source excerpts per motion (articles, reports)
- Run `store_source()` (already built) once per motion to embed and store into ChromaDB, tagged with a fixed `team_id="demo"` and a `motion_id` per motion
- **Checkpoint:** confirm `retrieve_relevant_chunks()` returns sensible results for a test query against this seeded data

### Phase D1 — Retrieval (if not already finished from the main track)
**Files:** `rag/retrieve.py`
- `retrieve_relevant_chunks(query_text, team_id, motion_id, n_results=3)` — already in progress from the main build; this demo reuses it as-is

### Phase D2 — Debater
**Files:** `llm/debater.py`
- Function that takes: student's speech text, the opposing side's case line, retrieved chunks → calls SenseNova → returns a grounded rebuttal
- **Checkpoint:** manually sanity-check 2-3 exchanges for quality before moving on

### Phase D3 — Judge
**Files:** `llm/judge.py`
- Role-specific scoring (1st/2nd/3rd speaker criteria) + coherence check against retrieved sources
- Returns structured feedback (strengths, unaddressed points, summary)

### Phase D4 — Minimal Setup Screen
**Files:** `demo_app.py`
- No login. Just: pick a motion (from the small hardcoded list) → pick a stance (free choice here, no squad-locking needed for a solo demo visitor) → pick a mode

### Phase D5 — Mode 1: Single-Speech Practice, with CrewAI
**Files:** `demo_app.py`, `rag/retrieve.py`, `crew/mode1_crew.py`, `llm/debater.py`, `llm/judge.py`
- Simplified version of the full plan's Mode 1 — skip the "cached prior-speaker context" complexity (Phase 2 of the main plan) for the demo; just let the visitor pick a speaker role and write one speech directly
- A two-agent crew (Debater, Judge) handles the exchange — build and verify the plain-function version first, then wrap in CrewAI

### Phase D6 — Mode 2: Turn-by-Turn Round (LangGraph)
**Files:** `demo_app.py`, `graph/mode2_graph.py`
- Reuse the state machine design from the main plan; this is a good one to keep fully featured since it's the most technically interesting piece to show off

### Phase D7 — Mode 3: Timed Adaptation Drill, with CrewAI
**Files:** `demo_app.py`, `crew/mode3_crew.py`
- Paste-in draft, live AI response (reuses Mode 1's crew), countdown timer, diff view — same as main plan, no changes needed for the demo context

### Phase D8 — Source Transparency Panel
**Files:** `demo_app.py`
- Show retrieved chunks alongside AI responses — this is a good, visible "look, it's not just an LLM wrapper" signal for a portfolio audience

### Phase D9 — Polish + Deploy
**Files:** `requirements.txt`, `README.md`
- Basic styling pass, mobile-friendly check
- Deploy to Streamlit Community Cloud
- Write a README aimed at a portfolio/recruiter audience: what the app does, the RAG architecture, the LangGraph state machine, and briefly the real Hong Kong LLM-access story (Groq/Gemini blocked, landing on SenseNova) — this is a genuinely good talking point, shows real-world problem-solving, not just following a tutorial

---

## 5. Suggested LinkedIn/portfolio framing
- Lead with what it does and a live link, not the tech stack
- One or two lines on the RAG grounding (why sourced arguments matter vs. a generic chatbot)
- One or two lines on the multi-speaker-role fidelity (the thing that differentiates it from generic AI debate bots)
- Optionally, a short note on the access-constraint problem-solving (build plan Section on LLM provider selection has the full trail, if you want to reference specifics)
- Link to the GitHub repo for the **full** multi-school version as "the real product this was built toward," if you want to show scope/ambition beyond just the demo

---

## 6. Time Estimate

**Already done** (from the main-track build): chunking, embeddings, ChromaDB storage/ingestion — fully built and tested.

**Remaining work, roughly:**
| Piece | Estimate |
|---|---|
| Finish retrieval (`rag/retrieve.py`) | ~30 min |
| Debater + Judge (plain functions, `llm/`) | ~1–2 hrs + prompt iteration |
| CrewAI wrapping (Modes 1 & 3) | ~1–2 hrs |
| LangGraph for Mode 2 | ~2–3 hrs |
| Demo UI assembly (`demo_app.py`, all 3 modes) | ~2–3 hrs |
| Seed demo data (motions, case lines, sources) | ~1 hr |
| Timer/diff for Mode 3, source transparency panel | ~1–2 hrs |
| Polish + deploy | ~1–2 hrs |

**Total: roughly 10–15 focused hours remaining** — realistically **2–3 days** at a few hours per session, or a full weekend push.