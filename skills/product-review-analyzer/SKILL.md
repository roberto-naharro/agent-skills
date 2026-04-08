---
name: product-review-analyzer
description: Use when asked to evaluate a product. Collects user reviews in Spanish/English, filters fake/promotional/AI-generated content using research signals, and produces a 0–10 score with pros/cons summary.
---

# Product Review Analyzer

When a user asks to evaluate a product, follow these phases in order.

---

## Phase 0 — Determine Input Mode

Before searching, check whether the user has already provided reviews. There are two
input modes:

### Mode A — User-provided reviews (priority)

The user may provide reviews in any of these forms (see
`references/review-input-formats.md` for full examples):

- **SingleFile HTML upload** *(best for mobile — recommended for Amazon)*: user saves
  the Amazon review page with the SingleFile extension and uploads the `.html` file.
  Claude parses review containers, star ratings, verified-purchase badges, and dates
  directly from the HTML. Multiple files (one per star-filter or page) are accepted
  and deduplicated automatically.
- **Plain paste**: raw text from any platform, one review per block separated by `---`.
- **Labeled paste**: each review preceded by `[★4 | Amazon ES | verified]`.
- **CSV/TSV**: columns `rating,source,verified,text` (from browser extensions).
- **JSON**: array of objects with fields `rating`, `source`, `verified`, `text`, `date`.

If the user provides reviews in any of these formats (including attached HTML files),
skip Phase 1 entirely and go to Phase 2. Acknowledge the number of reviews parsed.

**Parsing HTML files:** look for Amazon review containers using `[data-hook="review"]`
as the primary selector. Extract: star rating from `[data-hook="review-star-rating"]`,
verified badge from `[data-hook="avp-badge"]`, title from `[data-hook="review-title"]`,
body from `[data-hook="review-body"]`, date from `[data-hook="review-date"]`.
If the layout has changed, fall back to heuristic extraction from visible text.

### Mode B — Autonomous web search

If no reviews are provided, proceed with Phase 1.

---

## Phase 1 — Review Collection (Mode B only)

Use `web_search` to find user reviews for the product. Search **Spanish first, then
English**. If fewer than 10 genuine results exist in both, expand to any language.

### Search strategy

Run these queries (adapt `[product name]` accordingly):

```
"[product name]" opiniones reseñas usuarios site:amazon.es OR site:reddit.com OR site:xataka.com
"[product name]" reviews users site:amazon.com OR site:reddit.com OR site:rtings.com OR site:pcmag.com
"[product name]" problemas defectos quejas
"[product name]" problems issues complaints
"[product name]" review foro OR forum
```

Target: **15–25 individual user reviews** minimum. Expert media articles (Xataka,
PCMag, Rtings, The Verge, etc.) count as secondary sources with weight ×0.75.
Prioritize verified-purchase reviews and independent forums over aggregator summaries.

### Platform-specific collection notes

Different platforms have different levels of accessibility for autonomous scraping:

| Platform | Accessibility | Notes |
|----------|--------------|-------|
| Reddit | ✅ High | Threads are fully indexable; search for product name + subreddit |
| Xataka / GSMArena / PCMag | ✅ High | Indexed by search engines |
| Amazon (web search) | ⚠️ Partial | Top reviews surface via Google; deep pagination blocked |
| Amazon (direct) | ❌ Blocked | Anti-bot measures prevent systematic scraping |
| El Corte Inglés / FNAC | ⚠️ Partial | Some reviews indexable via Google |
| Trustpilot / Google Reviews | ✅ High | Indexable |
| YouTube comments | ❌ Not accessible | Requires API |

**If web search yields fewer than 10 reviews**: inform the user and suggest they
provide reviews manually using the paste methods described in Phase 0 and in
`references/review-input-formats.md`.

---

## Phase 2 — Review Classification and Filtering

Apply the taxonomy and rubric defined in `references/fake-review-signals.md`.

### Step 1: Taxonomic classification

Classify each review into one of these types before reliability assessment:

| Type | Description |
|------|-------------|
| `non-truthful` | Fabricates or exaggerates product experience |
| `brand-focused` | Talks about the seller/brand generically, not the specific product |
| `non-review` | Off-topic, empty, or irrelevant content |
| `genuine-candidate` | Contains product-specific experience → proceed to reliability check |

Non-`genuine-candidate` reviews are automatically labeled `discard`.

### Step 2: Reliability labeling (genuine-candidates only)

| Label | Meaning | Weight |
|-------|---------|--------|
| `genuine` | Passes all checks | 1.0 |
| `suspicious` | 1–2 weak signals present | 0.5 |
| `ai_generated` | Shows AI generation signals (see rubric) | 0.25 |
| `promo` | Clearly incentivized or paid | 0 — discard |
| `discard` | Hard-discard signal confirmed | 0 — discard |

**Critical rules:**
- No single weak signal is sufficient for `discard`. Require ≥2 confirmed weak signals
  OR 1 hard-discard signal.
- Always document the reason for each discard.
- **Fake reviews can be negative** (review bombing to harm competitors is a documented
  pattern). Do not treat negativity as a signal of authenticity.
- When in doubt between `suspicious` and `genuine`, prefer `suspicious` (included at
  reduced weight) over `discard` (excluded entirely).

---

## Phase 3 — Sentiment Scoring

For each non-discarded review, assign a `sentiment_score` from **-5 to +5** based on
actual content — ignore the original star rating entirely:

| Score | Description |
|-------|-------------|
| +5 | Enthusiastic, specific praise, recommends without reservation |
| +3 | Mostly positive, minor issues mentioned |
| 0 | Neutral or genuinely mixed |
| -3 | Notable problems, would not fully recommend |
| -5 | Serious defects, strong negative recommendation |

Build a JSON array:

```json
[
  {
    "source": "Amazon ES",
    "lang": "es",
    "type": "genuine-candidate",
    "reliability": "genuine",
    "sentiment_score": 3,
    "key_points": ["buena batería", "pantalla brillante"]
  },
  {
    "source": "Reddit r/gadgets",
    "lang": "en",
    "type": "genuine-candidate",
    "reliability": "suspicious",
    "sentiment_score": -2,
    "key_points": ["charging port broke after 2 months"]
  },
  {
    "source": "Amazon.com",
    "lang": "en",
    "type": "genuine-candidate",
    "reliability": "ai_generated",
    "sentiment_score": 4,
    "key_points": []
  },
  {
    "source": "Amazon ES",
    "lang": "es",
    "type": "brand-focused",
    "reliability": "discard",
    "sentiment_score": null,
    "key_points": [],
    "discard_reason": "brand-focused: no product-specific content"
  }
]
```

---

## Phase 4 — Score Calculation

Run `scripts/score.py` passing the JSON array as the first argument.

If the execution environment does not support running scripts, apply manually:

```
weights: genuine=1.0 · suspicious=0.5 · ai_generated=0.25 · expert_media=0.75

weighted_sum   = Σ (sentiment_score × weight)  for all non-discarded reviews with a sentiment score
weighted_count = Σ weight                       for all non-discarded reviews with a sentiment score
raw            = weighted_sum / weighted_count   # range −5 to +5
final_score    = (raw + 5) / 10 × 10            # normalized to 0–10
```

**Confidence levels:**

| Level | Condition |
|-------|-----------|
| Alta | ≥15 genuine reviews |
| Media | 7–14 genuine reviews |
| Baja | <7 genuine reviews — add explicit warning in output |

---

## Phase 5 — Pros/Cons Aggregation

From the `key_points` fields of all non-discarded reviews, group by theme and count
independent mentions. Report only points that appear in ≥2 independent sources (or 1
if total reviews < 10). Separate positive from negative.

---

## Phase 6 — Output Format

```
## 📦 [Product Name]

**Puntuación ajustada:** X.X / 10  (confianza: Alta / Media / Baja)
**Reseñas analizadas:** N total
  · G genuinas · S sospechosas · A generadas por IA · D descartadas

### ✅ Puntos positivos recurrentes
- [Pro 1] — mencionado en X fuentes independientes
- [Pro 2] — ...

### ❌ Puntos negativos recurrentes
- [Con 1] — mencionado en X fuentes independientes
- [Con 2] — ...

### 🚫 Reseñas descartadas
- X marcadas como promocionales
- Y descartadas como brand-focused (sin contenido específico del producto)
- Z identificadas como generadas por IA (peso reducido a 0.25, no descartadas)

### 🔍 Fuentes consultadas
- [lista de fuentes con idioma e indicador de fiabilidad]

### ⚠️ Advertencias
- [si confianza Baja: "Menos de 7 reseñas genuinas — resultado poco fiable"]
- [si todas las fuentes son de una sola plataforma: "Sesgo de fuente única"]
- [si el producto es reciente: "Pocas reseñas disponibles — se recomienda revisión manual"]
```

---

## Edge Cases

- **Producto nuevo (<10 reseñas)**: indica confianza Baja, busca previews y expert
  reviews para compensar, y sugiere al usuario que aporte reseñas manualmente.
- **Solo reseñas de una plataforma**: advierte sesgo de fuente única en el output.
- **Producto de nicho sin reseñas en ES/EN**: busca en otros idiomas e indícalo.
- **Usuario proporciona reseñas y también hay búsqueda web**: combina ambas fuentes,
  marcando el origen de cada bloque en la fase de scoring.
- **Reseñas en idioma desconocido**: incluir con etiqueta `lang: "other"` y peso
  reducido a ×0.6 si no es posible evaluarlas con la misma profundidad.
