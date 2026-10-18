"""Clinical-note tokens from an independently generated, documented Synthea run."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

STOPWORDS = set(ENGLISH_STOP_WORDS) | {
    "patient", "patients", "history", "chief", "complaint", "complaints", "present", "presenting",
    "illness", "social", "assessment", "plan", "following", "known", "medications",
    "medication", "procedures", "procedure", "year", "old", "years", "male", "female",
    "is", "was", "has", "had", "mg", "tablet", "oral", "situation", "finding", "disorder",
    "employment", "background", "socioeconomic", "currently", "review", "comes", "time", "school",
    "heterosexual", "white", "high", "nonhispanic", "married", "identifies", "actual",
}
TOKEN = re.compile(r"[A-Za-z]+(?:\d+)?")


def clean_tokens(text: str) -> list[str]:
    """Discard headings, dates, alphanumeric generated names, short words and stopwords."""
    body = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#") and not re.fullmatch(r"\s*\d{4}-\d{2}-\d{2}\s*", line))
    return [word for match in TOKEN.finditer(body) if (word := match.group().lower()).isalpha() and len(word) >= 3 and word not in STOPWORDS]


def note_terms(notes_dir: Path, source_id: str = "synthea_v3_4_0_seed424242") -> tuple[list[dict[str, Any]], dict[str, Any]]:
    paths = sorted(notes_dir.glob("*.txt"))
    if not paths:
        raise ValueError(f"No Synthea .txt clinical notes found in {notes_dir}")
    counter: Counter[str] = Counter()
    combined = hashlib.sha256()
    for path in paths:
        content = path.read_bytes()
        combined.update(hashlib.sha256(content).digest())
        counter.update(clean_tokens(content.decode("utf-8")))
    rows = [{"term": term, "count": count, "source_id": source_id} for term, count in sorted(counter.items(), key=lambda pair: (-pair[1], pair[0])) if count >= 2]
    if not rows:
        raise ValueError("No repeated eligible terms found in clinical notes")
    return rows, {"source_id": source_id, "note_count": len(paths), "combined_note_hash_sha256": combined.hexdigest(),
                  "token_count_after_cleaning": sum(counter.values()), "unique_terms": len(counter),
                  "stopword_policy": "scikit-learn ENGLISH_STOP_WORDS plus documented template and nonclinical terms; no case identifiers retained",
                  "cohort_linkage": "independent run; not linked to existing Phase I Synthea patients or encounters"}


def write_wordcloud(rows: list[dict[str, Any]], output_stem: Path) -> None:
    """Deterministic frequency-scaled word cloud in PNG and editable SVG."""
    import math
    from html import escape
    from PIL import Image, ImageDraw, ImageFont
    cache = output_stem.parents[3] / ".cache"
    cache.mkdir(exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache / "matplotlib"))
    os.environ.setdefault("XDG_CACHE_HOME", str(cache))
    from matplotlib import font_manager

    values = rows[:50]
    maximum = max(row["count"] for row in values)
    width, height = 1600, 940
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    font_path = font_manager.findfont("DejaVu Sans")
    colors = ("#12304A", "#147D80", "#24698D", "#47727A", "#4E5D6C")
    title_font = ImageFont.truetype(font_path, 31)
    caption_font = ImageFont.truetype(font_path, 17)
    draw.text((45, 30), "Independent Synthea v3.4.0 clinical notes: frequent terms", font=title_font, fill=colors[0])
    caption = "10 separately generated synthetic patients; term size reflects frequency. No linkage to the existing hospital cohort."
    draw.text((45, 897), caption, font=caption_font, fill=colors[3])
    occupied: list[tuple[int, int, int, int]] = []
    svg_text = []
    for index, row in enumerate(values):
        size = int(22 + 50 * math.sqrt(row["count"] / maximum))
        font = ImageFont.truetype(font_path, size)
        left, top, right, bottom = draw.textbbox((0, 0), row["term"], font=font)
        word_width, word_height = right - left, bottom - top
        placed = None
        for step in range(3500):
            angle = step * 0.37
            radius = 10.5 * math.sqrt(step)
            x = int(width / 2 + radius * math.cos(angle) - word_width / 2)
            y = int(480 + radius * math.sin(angle) - word_height / 2)
            rectangle = (x - 9, y - 9, x + word_width + 9, y + word_height + 9)
            if x < 42 or y < 105 or rectangle[2] > width - 42 or rectangle[3] > 865:
                continue
            if all(rectangle[2] < old[0] or rectangle[0] > old[2] or rectangle[3] < old[1] or rectangle[1] > old[3] for old in occupied):
                placed = (x, y, rectangle)
                break
        if placed is None:
            continue
        x, y, rectangle = placed
        occupied.append(rectangle)
        color = colors[index % len(colors)]
        draw.text((x - left, y - top), row["term"], font=font, fill=color)
        svg_text.append(f'<text x="{x}" y="{y + word_height}" font-size="{size}" fill="{color}">{escape(row["term"])}</text>')
    canvas.save(output_stem.with_suffix(".png"), format="PNG", dpi=(200, 200))
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">' + '<rect width="100%" height="100%" fill="white"/>'
    svg += '<g font-family="DejaVu Sans,Arial,sans-serif">'
    svg += '<text x="45" y="66" font-size="31" fill="#12304A">Independent Synthea v3.4.0 clinical notes: frequent terms</text>'
    svg += "".join(svg_text)
    svg += f'<text x="45" y="920" font-size="17" fill="#47727A">{escape(caption)}</text></g></svg>\n'
    output_stem.with_suffix(".svg").write_text(svg, encoding="utf-8")
