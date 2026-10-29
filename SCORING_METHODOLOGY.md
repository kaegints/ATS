# Scoring methodology and validation status

**Version 1.0 — October 2026**

## Intended use

RoleFit Auditor measures **textual support in a resume for explicitly selected job requirements**. It is an applicant-side revision aid, not an employer ATS simulation, a psychometric measure or a calibrated prediction of interview outcomes.

## Formula

For each assessed criterion `i`, textual credit `c_i` is 0, 0.30/0.35, 0.45, 0.65, 0.75, 0.80, 0.85 or 1.00 depending on the matching mode and the evidence pattern. Match credit is derived from a single most relevant passage, except when a requirement lists multiple named software programs; in that case independent passages may be combined. An optional importance weight `w_i` defaults to 1.0.

```
Category_score = 100 × sum(w_i × c_i) / sum(w_i)
Overall_score = sum(Category_score × Category_weight) / sum(Active_category_weights)
```

Category weights are Required = 55, Preferred = 20, Responsibilities = 25. A category without any assessable items is removed from the denominator. Requirements including years of experience, right-to-work, visa status, security clearance and related items are set to **manual review** and are not scored. The tool displays the count of manually excluded requirements. Duplicate keyword occurrences do not increase score.

### Match evidence levels

| Level | Typical textual credit | Meaning |
| --- | ---: | --- |
| Direct | 1.0 | The full requirement phrase appears in one resume passage without detected negation. |
| Strong evidence | 0.80–0.85 | High meaningful-word coverage and/or all specified recognized terms in one passage. |
| Related evidence | 0.65–0.75 | Specific technology names supported in a combination of passages, or specified terms with weaker context (strict mode). |
| Partial | 0.30–0.45 | Some aligned terms found, without enough context to establish the whole requirement. |
| Not evidenced | 0.0 | No sufficiently specific text was found. This does *not* imply that the candidate lacks the skill. |
| Manual review | Excluded | Cannot verify automatically from the available text. |

**The credit numbers and thresholds are explicit design choices.** They are not estimated from a representative labeled validation set, so the score cannot be interpreted as a probability or a validated recruiter-fit percentile. Look at the evidence rows, particularly near a decision boundary.

## Extraction and normalization

PDF extraction uses PyMuPDF with sorted text output; DOCX extraction uses python-docx including table cells; simple text files use UTF-8. The app does not OCR scanned documents. Job-ad lines are classified by headings, bullet structure and a small set of textual cues; the user edits this draft checklist. Skill aliases cover close written variants only. No model is trained on candidate profiles or hiring outcomes.

The **document readability diagnostic** is scored separately and reports an extraction-quality heuristic. It does not check proprietary parser behavior or ensure that all ATS platforms will accept the document.

## Research basis and what has not been validated

- Raghavan et al. (2020, ACM FAT*, DOI 10.1145/3351095.3372828) discuss the difficult and often underspecified task of evaluating algorithmic hiring systems, motivating transparent claims and caution around bias.
- Köchling & Wehner (2020, *Business Research*, DOI 10.1007/s40685-020-00134-w) systematically review fairness and discrimination risks with algorithmic recruitment.
- *Job description parsing with explainable transformer based ensemble models to extract the technical and non-technical skills* (2024, *Natural Language Processing Journal*, DOI 10.1016/j.nlp.2024.100102) demonstrates that identifying requirements from ads is a non-trivial information extraction task.
- Greenhouse's public **Talent Matching - Data Processing FAQ** documents employer-defined calibrations and explicit candidate evidence; one vendor's matching system cannot be generalized to every employer.
- Concordia University Career Services recommends readable documents and relevant job-specific wording, while noting format and parsing considerations.

These references informed design decisions, **not** the formula's 55/20/25 weights or evidence thresholds. We have not conducted external validation against hand-labeled requirement matches or recruiter decisions, and we have not audited the tool for demographic fairness in real hiring contexts. Use it to inspect your document, not to reject candidates or rank people.

## Reproducibility checks

The bundled `tests/test_engine.py` covers document ingestion, category parsing, synonym recognition, missing/negated skills, duplicate frequency effects, and deterministic output. It is a small software test suite, **not an empirical validity study**.
