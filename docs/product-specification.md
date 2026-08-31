# Product Specification — Foundation MVP

**Working product name:** African Dishes Knowledge Base  
**Document status:** Draft for validation  
**Date:** 20 August 2026  
**Initial geography:** Ghana  
**Programme alignment:** Future of Knowledge

## 1. Product statement

African Dishes is an evidence-first, AI-assisted knowledge system that helps curators transform fragmented information about African dishes into reviewed, source-backed, searchable records.

## 2. Problem

Information about African dishes is distributed across public knowledge bases, research publications, cultural resources, recipe sites, videos, and community knowledge. Names and spellings vary across languages and regions. Closely related dishes can be incorrectly merged, while alternative names can be incorrectly treated as separate dishes. Source provenance and uncertainty are often lost during collection.

The immediate problem is therefore not simply finding more pages. It is establishing reliable dish identities and preserving the evidence behind every factual claim.

## 3. Initial user and job

### Primary user

A researcher, data curator, or developer who needs structured and traceable information about African dishes.

### Job to be done

When I encounter information about an African dish, help me extract the relevant claims, compare the candidate with existing records, review the supporting evidence, and publish it without losing alternative names, regional relationships, or uncertainty.

### Later users

- Consumers exploring African food
- Community contributors documenting cultural knowledge
- Nutrition and food-science researchers
- Fitness, food, travel, and education product developers

## 4. Foundation MVP

The MVP demonstrates one complete workflow:

1. A curator registers a permitted source and supplies relevant source text.
2. Gemini converts that text into a schema-conforming candidate record.
3. The system compares the candidate with existing dish names and records.
4. Gemini may recommend `new dish`, `same dish`, `regional variant`, `related dish`, or `uncertain`.
5. The system displays the candidate, source evidence, potential matches, and recommendation.
6. A human reviewer approves, edits, links, rejects, or requests more evidence.
7. Approved information becomes searchable in the public catalogue.

AI output is always a proposal. It never becomes a published fact without a recorded human decision.

## 5. Required capabilities

### Source registration

- Store source title, URL, publisher, author when known, source type, publication date, retrieval date, and licence information.
- Store only the minimum source excerpt needed to support a claim.
- Preserve the exact source used for an extraction run.

### Candidate extraction

- Return structured JSON conforming to an explicit schema.
- Extract only information supported by the supplied text.
- Return `null` or an empty list when evidence is absent.
- Attach each proposed claim to an evidence excerpt.
- Flag ambiguity, disagreement, and missing data.

### Candidate matching

- Normalise names deterministically before AI comparison.
- Search canonical and alternative names.
- Preserve separate outcomes for identical dishes, variants, related dishes, and uncertain cases.
- Show the basis for every model recommendation.

### Human review

- Require authentication for review actions.
- Record the reviewer, action, timestamp, and notes.
- Preserve the submitted candidate and model output even after correction.
- Prevent unreviewed candidates from appearing in the public catalogue.

### Public catalogue

- Search canonical and alternative names.
- Filter by location and category.
- Display reviewed names, associations, descriptions, relationships, source citations, and review status.
- Avoid claiming a single origin when the available evidence is uncertain, shared, or contested.

## 6. Pilot dataset target

- 20–30 reviewed Ghanaian dish records
- At least 5 records with alternative names or spellings
- At least 3 records demonstrating a cross-border, regional-variant, related-dish, or genuinely uncertain relationship
- Every published factual claim linked to at least one source excerpt
- No known unreviewed AI-generated claim displayed publicly

The relationship targets are demonstration targets, not assumptions about any specific dish. They must be satisfied only with evidence-backed examples.

## 7. Definition of done for the application prototype

The prototype is ready when a reviewer can complete the full workflow for a previously unseen source, publish an approved dish, find it through an alternative name, and inspect the evidence supporting its public claims.

Additional acceptance criteria:

- Structured extraction succeeds for the agreed test sources.
- Invalid model output is rejected by schema validation.
- A potential match is displayed before a new dish can be approved.
- Every review decision is auditable.
- Public pages exclude candidates in pending, rejected, or needs-evidence states.
- The application can export approved records and citations as JSON or CSV.
- No API key or credential is stored in source control.

## 8. Non-goals for this milestone

- Nutrient calculation or laboratory validation
- Fitness tracking or calorie targets
- Medical or dietary recommendations
- Full recipes and cooking instructions
- Automated cultural-origin adjudication
- Autonomous publishing
- Open-ended web crawling
- Photo-based dish recognition
- Complete coverage of Ghana or Africa
- Native mobile applications

## 9. Responsible-AI constraints

- Gemini is an extraction and recommendation layer, not a factual source.
- A confidence score is not evidence.
- Missing information must remain missing.
- Contested claims remain explicitly contested.
- Cultural association must not be rewritten as exclusive ownership.
- Reviewers must be able to override the model.
- Inputs, prompt version, model identifier, output, and review decision must be retained for audit.

## 10. Long-term direction

After establishing trusted dish identities, the system can add representative recipes, canonical ingredients, measured portions, food-composition sources, nutrient calculations, and eventually fitness-app integrations. The identity and provenance layer created here remains the foundation for those phases.

## 11. Decisions fixed for this milestone

- Ghana is the pilot geography.
- The core product is a curated knowledge system, not a recipe website.
- The public catalogue contains reviewed records only.
- AI suggestions require human approval.
- Source provenance is stored at claim level.
- Nutrition and fitness functionality are deferred.

## 12. Decisions still requiring founder confirmation

- Final product and company name
- Whether Rahmat Akintola is applying as an active co-founder or collaborator
- Which nutrition and cultural reviewers may be named in the team or advisor section
- Initial audience for pilot interviews
- Public licence for the original structured dataset
- Whether community submissions are included in the application demo or shown only on the roadmap
