# Application Brief — African Dishes Knowledge Base

**Pilot geography:** Ghana  
**Prototype date:** August 2026  
**Product stage:** Evidence foundation and working vertical slice

## One-sentence pitch

African Dishes is an evidence-first, AI-assisted knowledge system that helps curators preserve African food heritage as reviewed, source-backed, searchable data.

## The problem

African food knowledge is fragmented across public archives, books, websites, research, video, and community memory. Names vary across languages and regions. Similar dishes can be merged incorrectly, while one dish can be duplicated under several spellings. Most collections preserve the final label or recipe but lose the evidence, uncertainty, relationships, and community context behind it.

This weak foundation also creates a later product problem: nutrition and fitness tools cannot represent African meals reliably when the identity of the dish, its variants, ingredients, and portion assumptions are unclear.

## The insight

The project should not begin with calories. It should begin with identity and provenance.

Before calculating nutrients, the system must be able to answer:

- What is this dish called, and what other reviewed names are used?
- Where is it documented or commonly associated?
- Is it the same dish, a regional variant, or a related dish?
- Which source supports each public statement?
- What remains unknown, shared, uncertain, or contested?

## The solution

The MVP gives a curator one accountable workflow:

1. Register a permitted source and the minimum relevant excerpt.
2. Use structured ingestion or AI to propose a schema-conforming candidate.
3. Compare the candidate with canonical and alternative names already in the database.
4. Show the candidate, evidence, possible matches, ambiguity, and missing fields together.
5. Let a human approve, edit, link, reject, or request stronger evidence.
6. Publish only reviewed records to the searchable catalogue and exports.

## Where AI is genuinely useful

AI is used for bounded, reviewable work—not as a cultural authority.

- Extracting structured candidate fields from supplied source text.
- Identifying possible name matches or related records for curator attention.
- Flagging ambiguity and unsupported fields.
- Reducing repetitive curation work as the source collection grows.

AI is not used as a source, to invent missing facts, to decide exclusive origin, or to publish automatically.

## What the prototype proves

- The Django foundation separates raw candidates from published dishes.
- Evidence is attached to individual claims.
- Canonical and alternative names are searchable.
- Location and category filters work on public, reviewed data.
- A user can inspect the evidence and source behind a public claim.
- Approved data can be exported as JSON or CSV.
- Human review decisions remain auditable.
- The Ghana pilot contains 12 source-linked demonstration records.

## What the prototype does not claim

- Complete coverage of Ghanaian or African dishes.
- Community validation of every pilot record.
- Laboratory-grade nutrient values.
- Full recipes, portion standards, or medical guidance.
- Autonomous adjudication of cultural ownership.
- Production-scale AI quality or cost performance.

## Responsible-AI design

- Model input, model identifier, prompt version, raw output, validation errors, and human decision are retained.
- Invalid structured output is rejected instead of silently repaired into a fact.
- Missing evidence remains missing.
- The public catalogue excludes pending, rejected, and needs-evidence records.
- Reviewers can override every AI recommendation.
- Cultural association is represented separately from claimed origin.

## Why this can grow

The stable `Dish` identity can later support representative recipes, ingredients, measured portions, food-composition references, nutrient calculations, and third-party integrations without discarding the provenance layer.

The expansion order is deliberate:

1. Validate and deepen the Ghana pilot.
2. Improve curator extraction and matching with real review feedback.
3. Expand country by country with local contributors and reviewers.
4. Add measured recipe and nutrition modules only after identity quality is established.

## Current ask from an incubator

- Access to cultural-heritage, food-science, nutrition, and data-governance mentors.
- Support validating the pilot workflow with researchers and community knowledge holders.
- Technical guidance for retrieval, multilingual entity resolution, evaluation, and human-in-the-loop review.
- Product support for contributor incentives, licensing, and a sustainable data-access model.

## Success measures for the next phase

- A growing set of reviewed Ghanaian dish records with claim-level provenance.
- Measured alternative-name retrieval quality.
- Reviewer agreement and correction rates for extracted candidates.
- Percentage of candidates resolved as same dish, variant, related dish, new dish, or uncertain.
- Time saved per curator without lowering evidence quality.
- Documented participation from relevant community or domain reviewers.
