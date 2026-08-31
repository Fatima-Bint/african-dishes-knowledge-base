# Two-Minute Demo Script

## 0:00–0:20 — Lead with the problem

“African Dishes exists to preserve food knowledge before it disappears or is flattened into generic lists. The first challenge is not calorie calculation. It is establishing trustworthy dish identities, names, relationships, and sources.”

Show the landing page and the line: **Food is memory. Let’s preserve it.**

## 0:20–0:55 — Prove alternative-name search

Open the catalogue and search for **Komi**.

Explain: “Komi is not a separate duplicate in this pilot. The search finds the reviewed Ga Kenkey record through its alternative name.”

Open the record. Point to:

- canonical and alternative names;
- location and community context;
- reviewed status;
- the supporting government source and locator.

## 0:55–1:20 — Show cultural care

Open **Fante Kenkey** or **Akplijii**.

Explain: “The model does not flatten similar foods or community names. The data model can keep two forms distinct, connect related records, and represent uncertainty instead of forcing one origin story.”

## 1:20–1:40 — Show the AI boundary

Scroll to **Evidence before scale**.

Say: “AI proposes structured claims and possible matches from a bounded source excerpt. A human must review the source, the match, and the uncertainty before anything becomes public. AI confidence is not evidence.”

## 1:40–1:55 — Show reusable data

Return to the catalogue and download the filtered results as JSON or CSV.

Say: “The knowledge is not trapped in a webpage. Reviewed records can later support research tools, cultural archives, and—after measured recipe and nutrition work—African-centred health products.”

## 1:55–2:00 — Close honestly

“This is a 12-record Ghana pilot, not complete coverage. The next step is to validate the workflow with cultural custodians and food researchers, deepen the evidence, and then expand carefully.”

## Backup if the live site is unavailable

Run the local Django demo:

```bash
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Then open `http://127.0.0.1:8000/`.
