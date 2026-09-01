# African Dishes Knowledge Base

An evidence-first, AI-assisted system for turning fragmented information about African dishes into reviewed, source-backed, searchable records.

The application-stage pilot is intentionally limited to Ghana. It demonstrates one complete vertical slice:

`source → structured candidate → match suggestion → human review → published record`

This is not yet a recipe, calorie, fitness, or medical app. Those layers are deliberately deferred until dish identity and provenance are trustworthy.

## What now works

- A Django data model for dishes, alternative names, locations, relationships, sources, evidence excerpts, claims, AI candidates, match suggestions, and review decisions.
- A public catalogue that excludes draft and unreviewed records.
- Search across canonical and alternative names.
- Location and category filters.
- Dish pages with claim-level provenance and source links.
- JSON API plus JSON and CSV downloads.
- A curator admin with auditable human-review actions.
- Structured Wikidata ingestion for exact entity IDs.
- Wikidata discovery for Ghana-linked dish entities via the Wikidata Query Service.
- Optional schema-constrained Gemini extraction from bounded source text.
- A deterministic name-matching baseline that runs before approval.
- An idempotent 12-record Ghana demo seed and automated tests.

## Quick start

Python 3.12+ is recommended.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Windows: copy .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

Open:

- Public catalogue: `http://127.0.0.1:8000/`
- Curator review workspace: `http://127.0.0.1:8000/admin/`
- Project demo: `http://127.0.0.1:8000/demo/`
- JSON API: `http://127.0.0.1:8000/api/dishes/`
- JSON export: `http://127.0.0.1:8000/exports/dishes.json`
- CSV export: `http://127.0.0.1:8000/exports/dishes.csv`

The seed command creates a non-login audit user named `demo-curator` to own the demo review decisions. Use the superuser you create to sign in.

To embed the unlisted YouTube recording on the demo page, set `DEMO_VIDEO_ID`
to the 11-character value after `youtu.be/` or `watch?v=` in the video URL.

## Run the tests

```bash
python manage.py test
```

## Curator workflow

### Route A: structured discovery with Wikidata

Start with the structured discovery query. It finds items typed as a dish and
linked to Ghana through a country-of-origin or indigenous-to statement. The
query only proposes candidates; it does not publish anything.

```bash
python manage.py discover_wikidata --limit 12
```

Select the QIDs that look relevant, then register those exact entities:

```bash
python manage.py ingest_wikidata Q12345 Q67890
python manage.py suggest_matches <candidate-id>
```

You can also register the discovery results in one step for a demo:

```bash
python manage.py discover_wikidata --limit 5 --ingest
```

Then open `/curator/`. Inspect the QID, captured structured fields, evidence
excerpt and deterministic match suggestion before choosing a review action.
Wikidata labels and aliases alone do not establish cultural origin or name
equivalence.

### Route B: bounded extraction with Gemini

Register a permitted source first. The included Wikipedia command is discovery-only and records that limitation explicitly.

```bash
python manage.py ingest_wikipedia "Exact article title"
python manage.py extract_with_gemini <candidate-id>
python manage.py suggest_matches <candidate-id>
```

Gemini requires `GEMINI_API_KEY` and optionally `GEMINI_MODEL` in `.env`. The model output is schema-validated and remains a candidate until a human reviewer acts.

### Human approval

In the review queue or Admin:

1. Open **Candidate records** and inspect the source, excerpt, payload, validation result, and proposed matches.
2. Move the candidate into review or request stronger evidence.
3. Select **Approve selected candidates as new published dishes** only after the evidence and match checks pass.
4. The action records the reviewer, decision, resulting dish, notes, and timestamp.

Approval is intentionally blocked when the candidate lacks a name, evidence excerpt, match suggestion, or unique dish identity.

## Project map

```text
config/                         Django settings and root URLs
dishes/
  admin.py                      curator review workspace and actions
  demo_data.py                  traceable Ghana pilot fixtures
  management/commands/          ingestion, extraction, matching and seeding
  models.py                     identity, provenance and audit models
  services.py                   public-query and serialization rules
  views.py                      catalogue, details, API and exports
  tests/                        model and public-boundary tests
templates/dishes/               public catalogue templates
static/dishes/                  catalogue styling
docs/                           product, evidence, application and demo notes
```

## Important documents

- [`docs/application-brief.md`](docs/application-brief.md)
- [`docs/demo-script.md`](docs/demo-script.md)
- [`docs/railway-deployment.md`](docs/railway-deployment.md)
- [`docs/source-register.md`](docs/source-register.md)
- [`docs/product-specification.md`](docs/product-specification.md)
- [`docs/evidence-policy.md`](docs/evidence-policy.md)
- [`docs/database-design.md`](docs/database-design.md)
- [`docs/project-structure.md`](docs/project-structure.md)

## Deploy to Railway

The project includes production static-file handling and Railway-compatible
environment settings. Follow the step-by-step configuration in
[`docs/railway-deployment.md`](docs/railway-deployment.md).

## Data and safety boundaries

- `.env`, API keys, credentials, virtual environments, caches, and local database files must not be committed or distributed.
- AI output is a proposal, never a factual source.
- A confidence score is not evidence.
- Cultural association is not rewritten as exclusive ownership.
- Public pages query reviewed domain records and eligible claims, never raw candidate payloads.
- The pilot records are an application demo, not complete Ghanaian coverage or a substitute for validation with cultural custodians.
