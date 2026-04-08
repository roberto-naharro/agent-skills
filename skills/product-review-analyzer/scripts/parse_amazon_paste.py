#!/usr/bin/env python3
"""
parse_amazon_paste.py — Convert Amazon app copy-paste text to skill-ready JSON.

The Amazon mobile/desktop app allows copying review pages as plain text. This script
parses that format and outputs a JSON array in the Option 4 format accepted by the
product-review-analyzer skill (see references/review-input-formats.md).

Usage:
    python parse_amazon_paste.py reviews.txt
    python parse_amazon_paste.py reviews.txt -o reviews.json
    python parse_amazon_paste.py < reviews.txt

Output (stdout unless -o is given):
    JSON array ready to paste into the skill conversation or pipe into score.py.
"""

import argparse
import json
import re
import sys
from datetime import date

# ---------------------------------------------------------------------------
# Spanish and English month tables
# ---------------------------------------------------------------------------

_MONTHS_ES: dict[str, int] = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}

_MONTHS_EN: dict[str, int] = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}

# Country name → Amazon source label
_COUNTRY_SOURCE: dict[str, str] = {
    "españa": "Amazon ES",
    "spain": "Amazon ES",
    "united states": "Amazon.com",
    "estados unidos": "Amazon.com",
    "mexico": "Amazon MX",
    "méxico": "Amazon MX",
    "united kingdom": "Amazon UK",
    "reino unido": "Amazon UK",
    "germany": "Amazon DE",
    "alemania": "Amazon DE",
    "france": "Amazon FR",
    "francia": "Amazon FR",
    "italy": "Amazon IT",
    "italia": "Amazon IT",
    "portugal": "Amazon PT",
    "brasil": "Amazon BR",
    "brazil": "Amazon BR",
}

# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------

# The footer that terminates every Amazon review in the app copy-paste format.
# "Útil" is sometimes on the same line as the last body line, or on its own.
# " Compartir" has a leading space; "Informe" follows immediately.
_REVIEW_END_RE = re.compile(
    r"Útil\n[ \t]*Compartir\n[ \t]*Informe",
    re.MULTILINE,
)

# "5,0 de 5 estrellas" (Spanish) or "5.0 out of 5 stars" (English)
_RATING_ES_RE = re.compile(
    r"(\d)[,.](\d)\s*de\s*5\s*estrellas?",
    re.IGNORECASE,
)
_RATING_EN_RE = re.compile(
    r"(\d(?:[.,]\d)?)\s*out\s+of\s+5\s+stars?",
    re.IGNORECASE,
)

# "Reseñado en España el 2 de abril de 2026"
_DATE_ES_RE = re.compile(
    r"Rese[ñn]ado en (.+?) el (\d{1,2}) de (\w+) de (\d{4})",
    re.IGNORECASE,
)

# "Reviewed in the United States on April 2, 2026"
_DATE_EN_RE = re.compile(
    r"Reviewed in (.+?) on (\w+) (\d{1,2}),\s*(\d{4})",
    re.IGNORECASE,
)

# "A 2 personas les ha parecido esto útil" / "A una persona le ha parecido esto útil"
_HELPFUL_RE = re.compile(
    r"A (\d+|una) personas? les? ha parecido esto útil",
    re.IGNORECASE,
)

# Lines to strip/ignore inside a review block
_NOISE_LINE_RE = re.compile(
    r"^("
    r"Traducid[oa] (del|por)\b.*"
    r"|Traducir rese[ñn]a.*"
    r"|Ver original.*"
    r"|Informar de una mala traducción"
    r"|·\s*Informar.*"
    r"|Desde \w+.*"
    r"|\d{1,2}:\d{2}(:\d{2})?"  # video timestamp e.g. "0:25", "1:04:32"
    r")$",
    re.IGNORECASE,
)

# Variant/attribute line just after the date (Color: Negro, Talla: M, …)
_VARIANT_RE = re.compile(
    r"^(Color|Talla|Tama[ñn]o|Size|Style|Estilo|Configuraci[oó]n|Modelo|Model"
    r"|Nombre de estilo)\s*:",
    re.IGNORECASE,
)

# Lines that are definitely part of the product header (star distribution summary)
_HEADER_NOISE_RE = re.compile(
    r"^\d+\s*estrellas?$"
    r"|^\d+[%％]$"
    r"|^Rese[ñn]as de clientes$"
    r"|^\d[\d.,]* de \d[\d.,]* estrellas?$"
    r"|^\d[\d.,]* valoraciones globales$"
    r"|^Escribir una opini[oó]n$"
    r"|^Ordenar por tipo de rese[ñn]a$"
    r"|^M[aá]s recientes$"
    r"|^Rese[ñn]as m[aá]s importantes.*$"
    r"|^Filtro »$"
    r"|^\d[\d.,]* rese[ñn]as de clientes$"
    r"|^Traducido por Amazon$"
    r"|^C[oó]mo funcionan las opiniones.*$",
    re.IGNORECASE,
)

# Inline "Nombre de estilo: VARIANT" prefix in compact-format date lines
_NOMBRE_ESTILO_RE = re.compile(
    r"Nombre de estilo:\s*",
    re.IGNORECASE,
)

# Split point between a lowercase-ending variant value and an uppercase-starting body.
# Example: "recambiosEl artículo" → split between 's' and 'E'
_LOWER_UPPER_BOUNDARY_RE = re.compile(
    r"(?<=[a-záéíóúüñ])(?=[A-ZÁÉÍÓÚÜÑ])"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_rating_es(line: str) -> int | None:
    m = _RATING_ES_RE.search(line)
    if m:
        return round(float(f"{m.group(1)}.{m.group(2)}"))
    return None


def _parse_rating_en(line: str) -> int | None:
    m = _RATING_EN_RE.search(line)
    if m:
        return round(float(m.group(1).replace(",", ".")))
    return None


def _parse_date_es(line: str) -> tuple[str | None, str | None]:
    m = _DATE_ES_RE.search(line)
    if not m:
        return None, None
    country_raw = m.group(1).strip().lower()
    day, month_name, year = int(m.group(2)), m.group(3).strip().lower(), int(m.group(4))
    month = _MONTHS_ES.get(month_name)
    if not month:
        return None, None
    try:
        date_str = date(year, month, day).isoformat()
    except ValueError:
        return None, None
    source = _COUNTRY_SOURCE.get(country_raw, f"Amazon ({m.group(1).strip()})")
    return date_str, source


def _parse_date_en(line: str) -> tuple[str | None, str | None]:
    m = _DATE_EN_RE.search(line)
    if not m:
        return None, None
    country_raw = m.group(1).strip().lower()
    month_name, day, year = m.group(2).strip().lower(), int(m.group(3)), int(m.group(4))
    month = _MONTHS_EN.get(month_name)
    if not month:
        return None, None
    try:
        date_str = date(year, month, day).isoformat()
    except ValueError:
        return None, None
    source = _COUNTRY_SOURCE.get(country_raw, f"Amazon ({m.group(1).strip()})")
    return date_str, source


def _parse_helpful(line: str) -> int | None:
    m = _HELPFUL_RE.search(line)
    if not m:
        return None
    raw = m.group(1).lower()
    if raw == "una":
        return 1
    return int(raw)


def _extract_compact_date_line(line: str, date_match: re.Match) -> dict:
    """Extract fields from a compact date line (Format B).

    Format B concatenates all review metadata onto a single line:
        [Compra verificada][TITLE]Reseñado en COUNTRY el DATE[Nombre de estilo: VARIANT][BODY]

    Returns a dict with zero or more of: verified, title, variant, body, helpful_votes.
    """
    result: dict = {}

    # --- Pre-date segment: [Compra verificada][TITLE] ------------------------
    pre = line[: date_match.start()].strip()
    if pre.lower().startswith("compra verificada"):
        result["verified"] = True
        pre = pre[len("compra verificada") :].strip()
    elif pre.lower().startswith("verified purchase"):
        result["verified"] = True
        pre = pre[len("verified purchase") :].strip()
    else:
        result["verified"] = False

    if pre:
        result["title"] = pre

    # --- Post-date segment: [Nombre de estilo: VARIANT][BODY][helpful_votes] -
    post = line[date_match.end() :].strip()
    if not post:
        return result

    m_variant = _NOMBRE_ESTILO_RE.match(post)
    if m_variant:
        rest = post[m_variant.end() :]
        # Split at the first camelCase boundary: lowercase→uppercase
        # e.g. "recambiosEl artículo" → ["recambios", "El artículo"]
        parts = _LOWER_UPPER_BOUNDARY_RE.split(rest, maxsplit=1)
        result["variant"] = parts[0].strip()
        post = parts[1].strip() if len(parts) == 2 else ""

    if not post:
        return result

    # Check if what remains is a helpful-votes note
    hv = _parse_helpful(post)
    if hv is not None:
        result["helpful_votes"] = hv
    else:
        result["body"] = post

    return result


# ---------------------------------------------------------------------------
# Block parser
# ---------------------------------------------------------------------------

def _parse_block(raw_block: str) -> dict | None:
    """Parse a single review block (text between two footer separators).

    Strategy:
    1. Find the date line — it anchors the whole review.
    2. Walk *backwards* from the date to find the rating line, then the reviewer name.
    3. Walk *forwards* from the date to collect the body text.

    This makes the parser robust against leading product-header content that may
    appear in the first block (before any Útil/Compartir/Informe separator).
    """
    lines = [ln.rstrip() for ln in raw_block.splitlines()]

    # --- 1. Find the date line (first occurrence = the review date) ----------
    date_idx: int | None = None
    review_date: str | None = None
    review_source: str | None = None
    date_match_obj: re.Match | None = None  # the regex match on the date line

    for i, line in enumerate(lines):
        stripped = line.strip()
        m = _DATE_ES_RE.search(stripped)
        if m:
            try:
                month = _MONTHS_ES.get(m.group(3).strip().lower())
                if month:
                    d = date(int(m.group(4)), month, int(m.group(2))).isoformat()
                    review_date = d
                    review_source = _COUNTRY_SOURCE.get(
                        m.group(1).strip().lower(),
                        f"Amazon ({m.group(1).strip()})",
                    )
                    date_idx = i
                    date_match_obj = m
                    break
            except ValueError:
                pass
        m = _DATE_EN_RE.search(stripped)
        if m:
            try:
                month = _MONTHS_EN.get(m.group(2).strip().lower())
                if month:
                    d = date(int(m.group(4)), month, int(m.group(3))).isoformat()
                    review_date = d
                    review_source = _COUNTRY_SOURCE.get(
                        m.group(1).strip().lower(),
                        f"Amazon ({m.group(1).strip()})",
                    )
                    date_idx = i
                    date_match_obj = m
                    break
            except ValueError:
                pass

    if date_idx is None:
        return None  # no date line → no review in this block

    # --- 1b. Detect compact format (Format B) --------------------------------
    # In Format B the date is embedded in a longer line that also holds the
    # verified badge, title, variant, and body — all without newlines between them.
    date_line_stripped = lines[date_idx].strip()
    compact_extra: dict = {}
    is_compact = len(date_line_stripped) > (date_match_obj.end() - date_match_obj.start() + 5)
    if is_compact:
        compact_extra = _extract_compact_date_line(date_line_stripped, date_match_obj)

    # --- 2. Find rating line by scanning backwards from the date line --------
    rating_idx: int | None = None
    review_rating: int | None = None
    review_verified = compact_extra.get("verified", False)

    for i in range(date_idx - 1, -1, -1):
        stripped = lines[i].strip()
        r = _parse_rating_es(stripped)
        if r is None:
            r = _parse_rating_en(stripped)
        if r is not None:
            rating_idx = i
            review_rating = r
            # In Format A the verified badge is on the rating line; in Format B
            # it was already extracted from the compact date line above.
            if not is_compact:
                review_verified = (
                    "compra verificada" in stripped.lower()
                    or "verified purchase" in stripped.lower()
                )
            break

    # --- 3. Find reviewer name: non-empty, non-noise line just before rating --
    reviewer: str | None = None
    if rating_idx is not None:
        for i in range(rating_idx - 1, -1, -1):
            stripped = lines[i].strip()
            if stripped and not _HEADER_NOISE_RE.match(stripped) and not _NOISE_LINE_RE.match(stripped):
                reviewer = stripped
                break

    # --- 4. Find review title: between rating line and date line -------------
    # In Format B the title comes from the compact line extraction.
    title: str | None = compact_extra.get("title")
    if title is None and rating_idx is not None:
        for i in range(rating_idx + 1, date_idx):
            stripped = lines[i].strip()
            if stripped and not _HEADER_NOISE_RE.match(stripped) and not _NOISE_LINE_RE.match(stripped):
                title = stripped
                break

    # --- 5. Collect body text ------------------------------------------------
    # Seed with body already extracted from the compact date line (if any).
    body_lines: list[str] = []
    if compact_extra.get("body"):
        body_lines.append(compact_extra["body"])

    helpful_votes: int | None = compact_extra.get("helpful_votes")
    first_body_line = not bool(body_lines)

    for i in range(date_idx + 1, len(lines)):
        stripped = lines[i].strip()

        if not stripped:
            if not first_body_line:
                body_lines.append("")
            continue

        # Skip the first variant line immediately after the date (Color: X, …)
        if first_body_line and _VARIANT_RE.match(stripped):
            continue

        # Helpful-votes line
        hv = _parse_helpful(stripped)
        if hv is not None:
            helpful_votes = hv
            continue

        # Noise lines
        if _NOISE_LINE_RE.match(stripped):
            continue

        body_lines.append(stripped)
        first_body_line = False

    # Trim trailing blank lines
    while body_lines and not body_lines[-1]:
        body_lines.pop()

    body = "\n".join(body_lines).strip()

    # Handle "Ver más" truncation marker
    truncated = False
    if body.endswith("Ver más"):
        body = body[: -len("Ver más")].rstrip(" \n….")
        truncated = True

    # Fall back: use title as text when body is empty
    if not body and title:
        body = title
        title = None

    if not body:
        return None  # nothing useful to pass to the skill

    # --- 6. Assemble output dict ---------------------------------------------
    review: dict = {
        "text": body,
        "source": review_source or "Amazon",
        "verified": review_verified,
    }
    if review_date:
        review["date"] = review_date
    if review_rating is not None:
        review["rating"] = review_rating
    if reviewer:
        review["reviewer"] = reviewer
    if title:
        review["title"] = title
    if helpful_votes is not None:
        review["helpful_votes"] = helpful_votes
    if truncated:
        review["truncated"] = True

    return review


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

def parse_amazon_paste(text: str) -> list[dict]:
    """Parse Amazon app copy-paste text and return a list of review dicts."""
    # Split on the "Útil / Compartir / Informe" footer (end of each review)
    blocks = _REVIEW_END_RE.split(text)

    reviews = []
    for block in blocks:
        result = _parse_block(block)
        if result:
            reviews.append(result)

    return reviews


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Parse Amazon app copy-paste reviews into skill-ready JSON.\n"
            "Output is the Option 4 (JSON) format accepted by the "
            "product-review-analyzer skill."
        )
    )
    p.add_argument(
        "input",
        nargs="?",
        metavar="FILE",
        help="Path to the plain-text file with the pasted reviews. "
             "Reads from stdin if omitted.",
    )
    p.add_argument(
        "-o", "--output",
        metavar="FILE",
        help="Write JSON output to FILE instead of stdout.",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    args = _build_arg_parser().parse_args(argv)

    if args.input:
        with open(args.input, encoding="utf-8") as fh:
            text = fh.read()
    else:
        text = sys.stdin.read()

    reviews = parse_amazon_paste(text)

    output = json.dumps(reviews, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output)
        print(f"Wrote {len(reviews)} review(s) to {args.output}", file=sys.stderr)
    else:
        print(output)

    if not reviews:
        print(
            "Warning: no reviews were parsed. "
            "Check that the input is an Amazon app copy-paste.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
