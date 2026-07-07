
# Shopfloor AI Assistant

An agentic AI assistant that learns the behavioural patterns of manufacturing operators
over repeated sessions and personalises responses based on accumulated interaction data.

---

## Project Structure

```
shopfloor_assistant/
├── agent.py            # ReAct agent loop and session management
├── profile.py          # OperatorProfile model, load/save utilities
├── prompt_builder.py   # Dynamic system prompt construction from profile
├── tools.py            # RAG retriever, escalation ticket creator, profile correction
├── updater.py          # LLM-as-judge profile updater and weighted aggregation
├── main.py             # Entry point — run this to start a session
│
├── data/
│   ├── manuals/        # Machine documentation (plain text files)
│   ├── profiles/       # Operator profiles stored as JSON (one per operator)
│   └── tickets.json    # Escalation ticket log (append-only)
│
├── requirements.txt
└── .env
```

---

## Setup

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Add API key**

Create a `.env` file in the project root:
```
OPENAI_API_KEY=your_key_here
```

**3. Add machine manuals**

Place plain text `.txt` files in `data/manuals/`. Three sample manuals are included:
- `hydraulic_press.txt`
- `cnc_lathe.txt`
- `conveyor_belt.txt`

---

## ▶ Running the Demo

```bash
python main.py
```

You will be prompted for:
- Operator ID (e.g. `operator_001`)
- Operator name
- Current shift (`day` or `night`)

If the operator ID exists in `data/profiles/`, the existing profile is loaded.
If not, a new profile is created automatically.

Type your queries as the operator. Type `quit` to end the session.

---

## How It Works

Each session runs a full ReAct agent loop. The agent can:
- Retrieve relevant sections from machine manuals based on your query
- Create escalation tickets when issues require maintenance attention
- Log profile corrections when the operator flags a wrong assumption

At the end of every session, an LLM-as-judge reads the full conversation transcript
and scores behavioural signals. These scores are aggregated into the operator profile
using a weighted average that gives diminishing weight to newer sessions as interaction
count grows.

**Personalisation activates after 5 interactions** (configurable in `prompt_builder.py`).
After this threshold, the system prompt is dynamically built from the operator's profile —
adjusting instruction style, troubleshooting guidance, and proactive tool use.

---

## Key Data Locations

| What | Where |
|------|-------|
| Operator profiles | `data/profiles/<operator_id>.json` |
| Escalation tickets | `data/tickets.json` |
| Machine manuals | `data/manuals/` |

Profiles and tickets are human-readable JSON — open them directly to inspect or manually
override values if needed.

---

## Demo Tip

Meaningful personalisation requires enough interaction data for the profile to stabilise. 
Five sessions is intentionally low for demonstration purposes — in a real deployment, 
20-30 sessions would produce a more reliable and nuanced behavioural profile.

To see personalisation in action without running multiple sessions, I have created two pre-built profiles 
are included that simulate an experienced operator and a new operator after 15 sessions of 
accumulated data. Run the same query through both and observe the contrast in response 
structure, depth, and proactive behaviour.


**Query to use:**
> The hydraulic press is making an unusual noise during the ram cycle and pressure looks normal, what should I do?

**Step 1** — Experienced operator (brief, tries-first, high machine confidence):
```bash
python main.py
# Enter operator ID: operator_expert
```

**Step 2** — New operator (step-by-step, escalates-quickly, low machine confidence):**
```bash
python main.py
# Enter operator ID: operator_new
```

**What to observe:**
- Alex Chen (expert operator): brief, direct, no hand-holding, no escalation offer
- Harshan Ashwad (new operator): numbered steps, visual breakdown, practical example, proactively offer to raise escalation

Both profiles are included in `data/profiles/`.
```