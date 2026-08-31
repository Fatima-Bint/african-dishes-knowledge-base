# Project Structure

```text
african-dishes-knowledgebase/
├── config/                  # Django configuration
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── dishes/                  # Reviewed knowledge and candidate workflow
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   └── tests/
├── docs/
│   ├── product-specification.md
│   ├── evidence-policy.md
│   ├── database-design.md
│   └── project-structure.md
├── templates/               # Shared page templates, added in the next brick
├── static/                  # Shared styles and assets, added in the next brick
├── .env.example
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```

## Planned application boundaries

The initial `dishes` Django application owns:

- Reviewed dish identities
- Alternative names
- Locations and dish relationships
- Sources and evidence excerpts
- Candidate records
- AI match suggestions
- Human review decisions

Once needed, separate applications should own:

- `ingestion`: MediaWiki, Wikidata, and other connectors
- `ai_pipeline`: Gemini schemas, prompts, extraction, and comparison
- `catalogue`: public search and presentation logic
- `contributors`: community submissions and consent
- `nutrition`: recipes, ingredients, portions, and nutrients

They should not be created until the first vertical slice demonstrates a genuine boundary.
