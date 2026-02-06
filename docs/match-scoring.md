# Match Scoring

## Scoring Formula

Based on spec `06_search_and_ranking.md`:

```
score_total = w1 * coverage + w2 * evidence_quality + w3 * (1 - blackbox_penalty) + w4 * legal_status_bonus
```

## Score Components

### Coverage (`score_coverage`)

Measures how many claim elements are satisfied by the candidate product's documentation.

| Level | Value | Description |
|-------|-------|-------------|
| strong | 1.0 | Specification explicitly describes the requirement |
| weak | 0.5 | Similar description exists but key points are missing |
| none | 0.0 | No evidence found |

`coverage = mean(max score per element)`

### Evidence Quality (`score_evidence_quality`)

Rates the reliability of source documents used as evidence.

| Source Type | Value | Examples |
|-------------|-------|---------|
| official | 1.0 | Official spec, manual, API documentation |
| third_party | 0.7 | Trusted review articles, technical analysis |
| unknown | 0.4 | Forum posts, user content |

`evidence_quality = mean(source type score of top evidence per element)`

### Blackbox Penalty (`score_blackbox_penalty`)

Fraction of claim elements that rely on internal implementation details which cannot be verified from public information.

- Higher penalty = more elements are unverifiable
- Score contribution: `(1 - blackbox_penalty)`, so high penalty reduces total score

### Legal Status Bonus (`score_legal_status`)

- Patent is active/enforced: bonus applied
- Patent expired/unknown: no bonus (0)

## Default Weights

Initial weights prioritize coverage:

| Weight | Value | Description |
|--------|-------|-------------|
| w1 | 0.5 | Coverage (most important) |
| w2 | 0.2 | Evidence quality |
| w3 | 0.2 | Blackbox penalty |
| w4 | 0.1 | Legal status |

Weights are configurable per domain/use case. Stored in `match_candidates.logic_version` for reproducibility.

## Score Storage

All scores are stored in the `match_candidates` table:

- `score_total` - Final weighted score (0.0 - 1.0)
- `score_coverage` - Coverage component
- `score_evidence_quality` - Evidence quality component
- `score_blackbox_penalty` - Blackbox penalty (0.0 = no penalty)
- `score_legal_status` - Legal status component

## Future: Automated Score Generation

Currently scores are populated manually or via analysis pipeline results. Future phases will:

1. Auto-generate `score_coverage` from Stage 13 element assessments
2. Auto-generate `score_evidence_quality` from evidence source types
3. Auto-detect `score_blackbox_penalty` from element assessment confidence
4. Auto-populate `score_legal_status` from JP status events
