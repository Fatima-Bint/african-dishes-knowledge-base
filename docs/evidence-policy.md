# Evidence, Provenance, and Verification Policy

**Status:** Draft policy for the foundation MVP  
**Date:** 20 August 2026

## 1. Purpose

This policy defines how African Dishes collects, stores, reviews, and publishes claims. Its purpose is to prevent AI-generated assumptions, weakly sourced origin claims, and copied web content from becoming authoritative database records.

## 2. Core rule

No factual claim may be published unless it is connected to an identifiable source and has received a recorded human review decision.

Gemini, another language model, a search-result snippet, or a confidence score is never a source.

## 3. Unit of evidence

Evidence is stored at the **claim level**, not only at the dish-page level.

Examples of separate claims include:

- “This dish is associated with Ghana.”
- “This alternative spelling is used for the same dish.”
- “The dish commonly contains a particular ingredient.”
- “This record is a regional variant of another dish.”

One source may support several claims, and one claim may be supported or contradicted by several sources.

## 4. Source tiers

Source tier is a review aid, not an automatic truth score.

### Tier A — Strong institutional or scholarly evidence

- Peer-reviewed research
- Government publications
- University or recognised research-institute publications
- National, regional, or international institutional datasets
- Museum, archive, or established cultural-heritage collections

### Tier B — Structured public references

- Wikidata statements with inspectable references
- Wikipedia articles with relevant citations
- Established encyclopaedic or cultural organisations
- Reputable published books with identifiable authors and editions

### Tier C — Attributed practitioner or community evidence

- Interviewed cooks and cultural knowledge holders
- Community submissions with consent
- Identifiable culinary professionals
- Established recipe publishers with clear authorship

### Tier D — Discovery-only material

- Unattributed listicles
- Social-media posts without adequate provenance
- Search snippets
- AI-generated text
- Anonymous or copied recipe pages

Tier D may identify a candidate for investigation but cannot independently support a published claim.

## 5. Required source metadata

Each registered source should store, where applicable:

- Title
- URL or stable publication identifier
- Publisher or institution
- Author or contributor
- Source type and tier
- Publication date
- Retrieval date
- Licence name and licence URL
- Citation text
- Notes about access, limitations, or suspected copying

## 6. Evidence excerpts

- Store only the minimum excerpt necessary to review a claim.
- Preserve exact wording and an available locator such as section, page, paragraph, or Wikidata statement identifier.
- Do not republish substantial copyrighted source text.
- A paraphrase may be published, but the internal review record should preserve the precise supporting excerpt where lawful.
- If a source changes, retain the retrieval date and do not silently rewrite the historical evidence record.

## 7. Claim statuses

| Status | Meaning |
|---|---|
| Extracted | Proposed by a person or system; not reviewed |
| Needs evidence | Plausible but inadequately supported |
| Reviewed | Human reviewer found the source supports the limited claim |
| Corroborated | Supported by more than one sufficiently independent source |
| Contested | Credible sources or communities disagree |
| Rejected | Evidence does not support the proposed claim |

“Reviewed” means the source supports the recorded wording. It does not mean the claim is universally or permanently true.

## 8. Origin and cultural-association rules

- Do not infer exclusive ownership from popularity or present-day prevalence.
- Prefer “associated with,” “documented in,” or “commonly consumed in” when that is what the evidence establishes.
- Allow multiple countries, regions, and communities to be linked to a dish.
- Store the source’s exact origin claim separately from the database’s neutral summary.
- Mark disputed origin claims as contested and show the disagreement.
- Do not use an AI model to resolve cultural disputes.

## 9. Name and identity rules

- Normalise case, whitespace, and punctuation for search without overwriting the display form.
- Do not remove diacritics or local-language characters from the stored name.
- Similar spelling is not sufficient to merge records.
- A merge requires reviewed evidence that two labels represent the same dish identity.
- Regional variants remain distinct when meaningful preparation, cultural, or identity differences are documented.
- Preserve aliases after a merge so users can still find the record.

## 10. AI extraction rules

Every extraction run must retain:

- Model identifier
- Prompt version
- Input source and supplied text
- Raw model output
- Parsed structured output
- Validation errors, if any
- Timestamp

Prompts must instruct the model to:

- Use only the supplied evidence
- Return `null` or an empty list when information is missing
- Separate explicit statements from interpretations
- Provide the supporting excerpt for every proposed claim
- Flag ambiguity and contradiction
- Avoid inventing translations, etymologies, ingredients, locations, or relationships

Schema compliance makes output predictable; it does not make the output factually correct.

## 11. Human review rules

- Reviewers must inspect the source excerpt, not only the AI summary.
- A reviewer can approve, edit, reject, link to an existing dish, classify as a variant, or request more evidence.
- Material corrections require a note.
- The system records the reviewer and timestamp.
- A reviewer should recuse themselves or request additional cultural expertise where a claim exceeds their knowledge.

## 12. Publication policy

Public records may contain only reviewed, corroborated, or explicitly contested claims. Each public claim must expose a citation or a clear path to its source metadata.

The public interface must distinguish:

- Verified database content
- Contested or uncertain content
- Community-contributed content awaiting further corroboration

Pending and rejected claims are never presented as facts.

## 13. Corrections and versioning

- Published records remain correctable.
- Do not erase earlier review decisions from the audit history.
- Record material changes with a timestamp, reason, and reviewer.
- Provide a correction channel for community members and subject-matter experts.
- A correction submission is a candidate claim until reviewed.

## 14. Dataset and content rights

- Record the licence of every external dataset or source.
- Do not assume that public accessibility permits database redistribution.
- Prefer facts and original structured records over copying expressive recipe text.
- Obtain explicit consent and contribution terms for community submissions.
- Decide and publish a licence for original database content before public export.
- Images require separate ownership or licence records.

## 15. Pilot publication checklist

Before a dish record is published, confirm:

- [ ] Canonical display name has been reviewed.
- [ ] Alternative names are individually sourced or clearly labelled.
- [ ] Location relationships use appropriately limited wording.
- [ ] Each public claim has evidence.
- [ ] Evidence excerpts are minimal and traceable.
- [ ] Possible duplicates have been reviewed.
- [ ] Variant or related-dish links are supported.
- [ ] Uncertainty and disagreement remain visible.
- [ ] Licence restrictions have been checked.
- [ ] Reviewer and decision are recorded.
