# Review Input Formats — User Guide

This document explains how to manually provide reviews to the `product-review-analyzer`
skill when autonomous web search is insufficient (e.g. Amazon, which blocks scraping).

---

## Why you may need to provide reviews manually

Amazon is the most review-rich platform for consumer products, but it actively blocks
automated scraping. Claude cannot reliably access Amazon review pages directly. Other
platforms with similar restrictions include El Corte Inglés, FNAC, and Booking.com.

For these platforms, you can extract reviews yourself and paste them into the
conversation. Claude will accept any of the formats below.

---

## Option 0 — SingleFile HTML upload (best for mobile, recommended)

**Requires: SingleFile extension for Firefox or Chrome (mobile or desktop).**

SingleFile saves the fully rendered page as a single self-contained HTML file,
including all rendered content, styles, and dynamic elements that were loaded when the
page was saved. This is the easiest and most reliable method for capturing Amazon
reviews.

### Steps

1. Install the **SingleFile** extension
   ([Firefox](https://addons.mozilla.org/en-US/firefox/addon/single-file/),
   [Chrome](https://chromewebstore.google.com/detail/singlefile/mpiodijhfdgdmhkkcmdfhhoacjhmidah)).
2. Navigate to the Amazon product review page.
3. Optionally filter reviews by star rating (e.g. show only 1-star reviews) to capture
   specific segments.
4. Click the SingleFile icon in the browser toolbar and wait for the page to be saved.
5. Upload the resulting `.html` file to the conversation with Claude.
6. Repeat for additional pages or star-rating filters if desired.

### What Claude extracts

Claude parses the HTML looking for Amazon review containers using these selectors:

| Data | Selector |
|------|----------|
| Review container | `[data-hook="review"]` |
| Star rating | `[data-hook="review-star-rating"]` |
| Verified purchase | `[data-hook="avp-badge"]` |
| Review title | `[data-hook="review-title"]` |
| Review body | `[data-hook="review-body"]` |
| Review date | `[data-hook="review-date"]` |

Multiple HTML files are accepted and deduplicated automatically based on review text
content.

---

## Option 1 — Plain paste

Simply copy and paste reviews from any platform. Separate each review with a line
containing only `---`.

### Example

```
Gran producto, llevo usándolo 3 meses para correr y la batería me dura una semana.
La pantalla se ve bien incluso con sol. Solo pega es que la correa es un poco rígida
al principio.
---
Terrible experience. Stopped working after 2 weeks. Customer service was unhelpful.
Would not recommend.
---
Funciona bien para lo que cuesta. No esperes calidad premium pero cumple su función.
Lo uso para notificaciones y seguimiento de pasos.
```

Claude will treat each block as a separate review. Source and rating information will
be inferred from content when possible, or marked as unknown.

---

## Option 2 — Labeled paste

Add a metadata header to each review for more accurate processing. Format:

```
[★{rating} | {source} | {verified/unverified}]
```

### Example

```
[★4 | Amazon ES | verified]
Gran producto, llevo usándolo 3 meses para correr y la batería me dura una semana.
La pantalla se ve bien incluso con sol. Solo pega es que la correa es un poco rígida.
---
[★1 | Amazon.com | verified]
Terrible experience. Stopped working after 2 weeks. Customer service was unhelpful.
Would not recommend.
---
[★3 | El Corte Inglés | unverified]
Funciona bien para lo que cuesta. No esperes calidad premium pero cumple su función.
```

### Supported fields

| Field | Values | Required |
|-------|--------|----------|
| Rating | `★1` through `★5` | Optional (inferred from content if missing) |
| Source | Any platform name (e.g. `Amazon ES`, `Reddit`, `PCMag`) | Optional |
| Verified | `verified` or `unverified` | Optional (defaults to `unverified`) |

---

## Option 3 — CSV/TSV

Provide reviews in comma-separated or tab-separated format. This is useful when
exporting reviews from browser extensions or scraping tools.

### Required columns

```
rating,source,verified,text
```

### Example (CSV)

```csv
rating,source,verified,text
4,Amazon ES,true,"Gran producto, llevo usándolo 3 meses y la batería dura una semana."
1,Amazon.com,true,"Terrible experience. Stopped working after 2 weeks."
3,El Corte Inglés,false,"Funciona bien para lo que cuesta."
```

### Example (TSV)

```tsv
rating	source	verified	text
4	Amazon ES	true	Gran producto, llevo usándolo 3 meses y la batería dura una semana.
1	Amazon.com	true	Terrible experience. Stopped working after 2 weeks.
3	El Corte Inglés	false	Funciona bien para lo que cuesta.
```

### Notes

- The `verified` column accepts `true`/`false`, `yes`/`no`, or `1`/`0`.
- Additional columns (e.g. `date`, `reviewer`, `helpful_votes`) are accepted and used
  if present but not required.
- Enclose text fields in double quotes if they contain commas.

---

## Option 4 — JSON

Provide reviews as a JSON array. This is the most structured option and maps directly
to the internal representation used by the skill.

### Schema

```json
[
  {
    "rating": 4,
    "source": "Amazon ES",
    "verified": true,
    "text": "Gran producto, llevo usándolo 3 meses...",
    "date": "2025-01-15"
  }
]
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rating` | number (1–5) | Optional | Original star rating from the platform |
| `source` | string | Optional | Platform name or URL |
| `verified` | boolean | Optional | Whether the review is a verified purchase |
| `text` | string | **Required** | Full review text |
| `date` | string (ISO 8601) | Optional | Date the review was published |
| `lang` | string | Optional | Language code (e.g. `es`, `en`). Auto-detected if omitted |
| `reviewer` | string | Optional | Reviewer name or handle |
| `helpful_votes` | number | Optional | Number of helpful votes on the platform |

---

## Tips for best results

- **More reviews = higher confidence.** Aim for at least 15 reviews when possible.
- **Include negative reviews.** A mix of ratings produces a more accurate analysis.
  Avoid selecting only positive or only negative reviews.
- **Use multiple sources.** If available, combine reviews from Amazon, Reddit, and
  other platforms to avoid single-source bias.
- **Include the star rating when available.** While Claude scores sentiment
  independently, the original rating helps calibrate the analysis.
- **For Amazon, use SingleFile on different star filters.** Save one HTML page for
  "All reviews", one for "1-star", and one for "5-star" to get a representative sample.
