# Crocoblock Smart Ticket Classifier

A small Python service that reads a raw support ticket and classifies it on four axes so
it can be triaged and routed automatically:

| Axis | Values |
|------|--------|
| **category** | `bug` · `feature_request` · `how_to` |
| **priority** | `low` · `medium` · `high` · `urgent` |
| **plugin** | the primary Jet/Crocoblock plugin (JetEngine, JetFormBuilder, JetBooking, …) |
| **sentiment** | `positive` · `neutral` · `frustrated` · `angry` |

It also returns a **confidence** score and one-sentence **reasoning** for each decision.

Built on the **Google Gemini API** (free tier) using **few-shot prompting** and
**structured output** (`response_schema`), so the response is a validated, typed object —
never a raw string that has to be parsed and hope-checked.

## Why this exists

A support queue for a plugin ecosystem like Crocoblock's mixes urgent regressions
("site down after update") with simple how-to questions and feature requests. Reading and
tagging each ticket by hand is slow. This service does the first pass in ~1 second per
ticket, producing a structured label that a workflow (n8n, Zapier, a webhook) can route:
urgent bugs to on-call, how-tos to docs/self-service, feature requests to the roadmap board.

## How it works

```
ticket text
    │
    ▼
system instruction (triage rules + 3 worked examples)  +  the ticket
    │
    ▼
client.models.generate_content(response_schema=TicketClassification)   ← schema enforced
    │
    ▼
response.parsed  ->  TicketClassification  (Pydantic object, guaranteed valid enums)
```

Two techniques do the work:

- **Few-shot prompting** — three hand-labelled tickets are embedded in the system
  instruction so the model learns *our* conventions for priority and sentiment instead of
  guessing them.
- **Structured output** — the Pydantic schema in `schema.py` is passed as `response_schema`
  with `response_mime_type="application/json"`. Gemini constrains generation to the schema
  and the SDK hands back a parsed Pydantic object via `response.parsed`. The model can't
  return an invalid category or malformed JSON.

**Gemini-specific design note:** Google recommends *not* dumping example JSON that
duplicates the response schema into the prompt (it lowers output quality). So the few-shot
examples are written as compact shorthand (`ticket -> bug | urgent | JetEngine | frustrated`)
rather than full JSON objects. Still few-shot — it just anchors the decision boundaries
without repeating the schema the API already enforces.

## Project layout

```
schema.py       Pydantic models + enums (the contract)
prompts.py      system instruction + few-shot worked examples
classifier.py   classify_ticket() — the core function
main.py         CLI (single ticket / file / batch)
examples/
  tickets.json  5 real-world support tickets
```

## Setup

```bash
git clone <your-repo-url>
cd crocoblock-ticket-classifier

python -m venv .venv
.venv\Scripts\activate          # Windows / PowerShell
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt

cp .env.example .env            # then paste your GEMINI_API_KEY into .env
```

Get a free Gemini API key at <https://aistudio.google.com/apikey> — no credit card required.

## Usage

```bash
# Classify one ticket
python main.py "After updating JetEngine my dynamic fields are all blank and the site is live!"

# Classify a ticket stored in a file
python main.py --file ticket.txt

# Run the 5 bundled real-world examples and print a summary table
python main.py --examples
```

### Example output

```
[TCK-1042] JetBooking allowing double bookings on the same dates
-----------------------------------------------------------------
  category   : bug
  priority   : urgent
  plugin     : JetBooking
  sentiment  : frustrated
  confidence : 0.96
  reasoning  : Overlapping reservations indicate the availability check is broken, costing live revenue.
  (gemini-2.5-flash, 910 ms, 512 in / 70 out tokens)
```

*(Exact scores and latency vary per run and model.)*

## Design decisions

- **Structured output over "parse the text".** `response_schema` guarantees a schema-valid
  object, so downstream automation can trust the fields without validation retries.
- **Enums for `plugin`.** Constraining the plugin field to the real Jet product list keeps the
  labels clean and routable, with `unknown`/`other` as safe fallbacks.
- **`temperature=0`** for deterministic triage.
- **Free tier.** Runs at zero cost on `gemini-2.5-flash`. Model is configurable via
  `GEMINI_MODEL` (`gemini-2.5-flash-lite` for higher RPM, `gemini-3.5-flash` for newer).
  Note: on the free tier Google may use prompts to improve its products — fine for a demo,
  but use a billed project for anything with customer data.

## Possible extensions

- Wire `classify_ticket()` into an **n8n / webhook** flow: HTTP node → classifier → Switch
  node that routes by `category` + `priority` (Slack for urgent bugs, Notion for feature
  requests, docs autoresponder for how-tos).
- Add a small eval set of labelled tickets and measure per-field accuracy.
- Disable "thinking" on 2.5 Flash (`thinking_config`) to shave latency/tokens for this
  simple classification task.

## License

MIT
