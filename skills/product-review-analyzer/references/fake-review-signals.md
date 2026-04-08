# Fake, Promotional & AI-Generated Review Detection Signals

Reference rubric for the `product-review-analyzer` skill. Applied during Phase 2.

Methodological basis: Ott et al. (2011), Li et al. (2014), Mukherjee et al. (2013),
Fei et al. (2013), Moon et al. (2021), Salminen et al. (2022), Jansen et al. (2025),
MAiDE-up multilingual dataset (2024).

---

## Taxonomic types (pre-reliability classification)

Before applying reliability signals, classify each review:

| Type | Description | Action |
|------|-------------|--------|
| `non-truthful` | Fabricates or grossly exaggerates experience | → discard |
| `brand-focused` | Talks about seller/brand generically without product specifics | → discard |
| `non-review` | Off-topic, empty, single emoji, or irrelevant | → discard |
| `genuine-candidate` | Contains product-specific first-hand experience | → apply signals below |

---

## 🔴 Hard-discard signals (any single one → `discard`)

- **Copy-paste pattern**: near-identical phrasing found in 2+ reviews of the same
  product across the same or different platforms.
- **Explicit incentive disclosure**: "received free in exchange for review", "discount
  provided", "brand sent me this to review" — unless the reviewer discloses AND is
  clearly critical.
- **Zero product-specific content**: review mentions only the brand, shipping, or
  seller without any detail about the product itself.
- **Incoherent product reference**: review clearly refers to a different product (wrong
  ASIN aggregation, review transplanted from another listing).

---

## 🟠 Promotional signals (→ `promo`, weight = 0)

- **Affiliate / influencer language**: "use my code", "link in bio", "sponsored", "in
  partnership with", "gifted".
- **Brand ambassador self-identification**: reviewer identifies as employee, seller, or
  brand representative.
- **Perfect superlatives with zero negatives**: 5-star review with phrases like
  "absolutely perfect in every way", "no issues whatsoever", "best I've ever owned" —
  with zero specific critical observation and no concrete use context.

---

## 🟡 Suspicious signals — human-written fakes
(1–2 signals → `suspicious`; 3+ signals → `discard`)

Research finding: fake reviews written by humans show **heightened emotional
exaggeration, excessive first-person references, lack of concrete detail, and
present/future time orientation** (Li et al. 2014; Moon et al. 2021).

- **Hyperbolic density**: more than 3 superlatives ("amazing", "incredible", "perfect",
  "love it", "fantastic") in a short review without any concrete factual claims.
- **Temporal cluster**: this review is part of a group of 5+ reviews for the same
  product published within 48 hours from accounts with no prior review history.
- **Reviewer burstiness**: the reviewer appears systematically during burst periods of
  *multiple unrelated products* — strong signal when visible in platform history.
- **New/thin reviewer profile**: fewer than 5 reviews total, all 5-star, across
  unrelated product categories.
- **Vague praise loop**: restates product listing features without any first-person use
  experience ("This product has great battery life and excellent display").
- **Unverified purchase (Amazon)**: "NOT a verified purchase" tag. Use as a signal,
  not a standalone disqualifier.
- **Language mismatch**: review posted on a Spanish platform in flawless formal English
  (or vice versa) with no contextual explanation.
- **Rating distribution anomaly**: reviewer's visible history contains exclusively
  5-star or exclusively 1-star ratings across diverse product categories.

> ⚠️ Important: fake reviews can be **negative** as well as positive. Review bombing
> (coordinated 1-star attacks to damage competitors) is documented. Do not treat
> negativity as a signal of authenticity.

---

## 🤖 AI-generated signals
(2+ signals → label `ai_generated`, weight = 0.25, not discarded)

Research finding: LLM-generated reviews differ from human fakes in specific ways —
they show **greater verbosity and lexical sophistication, lower linguistic complexity
for their length, positivity bias, content realism without experiential grounding, and
repetitive structural patterns** (Jansen et al. 2025; MAiDE-up 2024; ScienceDirect
2025).

- **Formally structured despite short length**: intro → bullet points → conclusion,
  even for a 3-sentence review.
- **Specificity gap**: long, fluent text that mentions generic product features but
  lacks any first-person use detail ("I used this for X months and noticed Y").
- **Certainty excess**: absolute assertions without hedging — "definitely", "without
  a doubt", "absolutely flawless" — alongside general rather than personal experience.
- **Positivity bias without contrast**: strong positive sentiment with no acknowledged
  trade-offs, even for complex products where real users always find something.
- **Repetitive schema across reviews**: multiple reviews of the same product follow
  the same structural template (even in different words).
- **Readability/complexity mismatch**: highly readable, simple sentences combined with
  sophisticated vocabulary — the inverse of typical user writing.
- **High rating + low-reputation profile**: 5-star review from an account with few
  reviews, low helpful-vote count, and recently created (visible on Amazon).

> **⚠️ Endogamy-risk guard:** An LLM evaluating another LLM's output is prone to
> over-flagging well-written human text. Apply these mitigations:
>
> - **"Specificity gap" is not a standalone signal.** A meticulously written review
>   that is fluent and well-structured must not be labelled `ai_generated` on that
>   basis alone. Require at least one additional corroborating signal.
> - **Structure is not proof.** Careful human reviewers do write in clear, organised
>   prose. Only treat structure as a signal when combined with absence of any
>   first-person experiential grounding.
> - **The 2-signal threshold is a floor, not a target.** When in doubt, prefer
>   `suspicious` (weight 0.5) over `ai_generated` (weight 0.25).

> Note: AI-generated reviews are included at reduced weight (0.25) rather than
> discarded, because detection is probabilistic and a legitimate review could match
> some of these patterns.

---

## ✅ Genuine signals (increase confidence toward `genuine`)

- Mentions specific use context with time reference ("I've been using this daily for 6
  months for X task").
- Notes **both positives and negatives** — genuine reviews almost always have both.
- References product-specific details not in the listing (firmware version, serial
  number, specific failure mode, comparison to a previous model).
- Verified purchase tag.
- Written in the expected language for the platform.
- Reviewer has a diverse review history across product categories.
- Mentions **concrete numbers**: battery lasted X hours, downloaded in Y seconds, broke
  after Z uses.
- Uses hedging language: "in my experience", "might be different for others", "so far".
