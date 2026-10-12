# AI Debate Sparring Partner

A Streamlit app that lets a student practice competitive debate speeches against an AI opponent, then get scored by an AI judge. The same debate mechanic — write a speech, get an AI rebuttal grounded in live web search, get judged on role-specific criteria — is implemented three separate times, once on each of three different agent orchestration frameworks, as a comparison/portfolio piece.

## Modes

The app is a single page with three tabs, each a standalone implementation of the debate loop:

| Tab | Framework | File | How it works |
|---|---|---|---|
| **Mode 1** | [Pydantic AI](https://ai.pydantic.dev/) | `pydantic_ai_mode/provider.py` | A single exchange: the AI opponent speaking before you opens, you write your speech in a chat box, the AI opponent speaking after you responds, then the judge scores you. One continuous script run per turn. |
| **Mode 2** | [CrewAI](https://www.crewai.com/) | `crew/mode2_crew.py` (+ `crew/agents.py`) | A full 6-speech round (1st/2nd/3rd speaker, both sides). Whichever speaker slot you pick, the AI fills every other slot before and after your turn, then the judge scores your speech. |
| **Mode 3** | [LangGraph](https://www.langchain.com/langgraph) | `graph/mode3_graph.py` | The same round, modeled as an explicit state graph with `interrupt`/`Command(resume=...)` for human-in-the-loop turn-taking, checkpointed per session via `InMemorySaver`. |

In every mode:
- You pick a **motion**, your **stance** (affirmative/negative), and your **speaker position** (1st/2nd/3rd).
- The AI generates a team line (case) for the side it's arguing automatically.
- AI speeches call a `web_search` tool (Tavily) to ground their rebuttals in current, real evidence rather than hallucinating it.
- The judge returns structured JSON feedback: role-specific scores, unaddressed points, fallacies/gaps, strengths, and a summary.

## Architecture

- **Frontend:** Streamlit (`demo_app.py` wires up the three tabs).
- **LLM backend:** SenseNova, an OpenAI-compatible API (`sensenova-6.8-flash-lite`), used directly via `openai` in Modes 1's helper code, through `pydantic-ai`'s `OpenAIChatModel` in Mode 1, through `crewai.LLM` in Mode 2, and through `langchain_openai.ChatOpenAI` in Mode 3.
- **Grounding:** live web search via the Tavily API, exposed as a tool to each framework's agent/LLM.
- **Judge:** a separate agent/LLM call per mode that returns structured scoring JSON.

`rag/` also contains a ChromaDB + `sentence-transformers` embedding pipeline (`ingest.py`, `retrieve.py`) for grounding speeches in a pre-ingested document store instead of live search. It's present and working standalone (see each file's `__main__` block) but isn't currently wired into any of the three live modes — all three use live web search instead.

## Project structure

```
demo_app.py              # entry point: st.tabs() wiring for the three modes
pydantic_ai_mode/
  provider.py             # Mode 1 (Pydantic AI) — the live implementation
  schemas.py               # unused: a JudgeFeedback model duplicating the one defined inline in provider.py
crew/
  mode2_crew.py            # Mode 2 round orchestration (CrewAI) — the live implementation
  agents.py                 # CrewAI agent/LLM definitions, arguments + rebuttals + judge crews
  mode1_crew.py              # unused: an earlier CrewAI-based Mode 1, superseded by pydantic_ai_mode/provider.py
graph/
  mode3_graph.py            # Mode 3 state graph (LangGraph) — the live implementation
llm/
  debater.py                # shared prompts, role labels, team-line generation
  judge.py                   # shared judge prompt + scoring criteria
rag/
  ingest.py, retrieve.py      # ChromaDB + sentence-transformers pipeline (not currently wired in)
  web_search.py                 # Tavily search tool used by all three modes
utils/
  diff.py                        # Streamlit markdown-safe text display helper
data/
  demo_motions.py                 # placeholder, currently empty
```

## Running locally

Requires Python 3.13 (Mode 2's dependency, `chromadb`, does not yet support 3.14).

```bash
git clone https://github.com/mancykokms/rag_debater_demo.git
cd rag_debater_demo
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml` (already gitignored):

```toml
[sensenova]
api_key = "your-sensenova-key"

[tavily]
api_key = "your-tavily-key"
```

Then run:

```bash
streamlit run demo_app.py
```

## Deployment

Deployed on Streamlit Community Cloud from the `main` branch. Two things that matter there and aren't obvious from the code:

- **Python version must be pinned to 3.13** in the app's deploy settings — `chromadb` breaks on 3.14.
- **Secrets** (`sensenova` and `tavily` API keys, same shape as `secrets.toml` above) must be set in the app's dashboard under Settings → Secrets; they aren't read from any file in the repo.

## Notes

- The `test_*.py` files at the repo root (`test_crew.py`, `test_langgraph.py`, `test_llm_api.py`, `test_pydantic.py`, `test_web_crew.py`, `test_web_graph.py`) are ad-hoc manual debug scripts (mostly commented-out scratch code used while building each mode), not an automated test suite — there's no `pytest` setup here.
- `pydantic_ai_mode/schemas.py` and `crew/mode1_crew.py` are dead code, left over from earlier iterations and not imported anywhere.
