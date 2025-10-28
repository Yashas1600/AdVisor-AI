import re
from typing import Dict, List, Optional, Tuple


_STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "of",
    "to",
    "for",
    "in",
    "on",
    "with",
    "by",
    "at",
    "from",
    "is",
    "are",
    "be",
    "this",
    "that",
    "it",
    "as",
    "your",
    "you",
    "we",
}


BENEFIT_VERBS = [
    "save",
    "protect",
    "track",
    "learn",
    "optimize",
    "insure",
    "get",
    "try",
    "improve",
    "sleep",
    "monitor",
]


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def find_numbers(text: str) -> List[str]:
    if not text:
        return []
    candidates: List[str] = []
    patterns = [
        r"\$\s?\d+(?:[\.,]\d{2})?(?:\s?/?\s?(?:mo|month))?",  # $299 or $9.99/mo
        r"\d+(?:[\.,]\d{2})?\s?/?\s?(?:mo|month)",  # 9.99/mo
        r"\d+\s?%\s?off",
        r"1\s?¢\s?down",
        r"free",
    ]
    for pat in patterns:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            s = m.group(0)
            if s not in candidates:
                candidates.append(s)
    return candidates


def map_price_tier(text: str, numbers: List[str]) -> Tuple[Optional[str], float, str]:
    tier: Optional[str] = None
    rationale = ""
    conf = 0.35

    # explicit prices
    money = []
    for n in numbers:
        m = re.search(r"\$\s?(\d+(?:[\.,]\d{2})?)", n)
        if m:
            try:
                value = float(m.group(1).replace(",", ""))
                money.append(value)
            except ValueError:
                pass

    if money:
        min_price = min(money)
        if min_price < 50:
            tier = "budget"
        elif min_price < 200:
            tier = "mid"
        else:
            tier = "premium"
        conf = 0.6
        rationale = f"price {min_price:g} suggests {tier}"

    # bias keywords
    low_bias = any(w in text for w in ["free", "discount", "sale", "per month", "mo", "only", "down"])
    high_bias = any(w in text for w in ["luxury", "premium", "flagship", "exclusive"])
    if tier is None:
        if high_bias:
            tier = "premium"
            conf = 0.45
            rationale = "premium wording"
        elif low_bias:
            tier = "budget"
            conf = 0.45
            rationale = "discount/free wording"

    return tier, conf, rationale


def map_category(text: str) -> Tuple[str, float, str]:
    """Freeform category inference with expanded domains (includes automotive)."""
    rules: List[Tuple[str, List[str]]] = [
        ("automotive", ["car", "cars", "auto", "automotive", "vehicle", "van", "sprinter", "mercedes", "bmw", "toyota"]),
        ("meal-prep", ["meal kit", "meal", "dinner", "recipe", "grocery", "kitchen"]),
        ("wearable health", ["wearable", "ring", "watch", "tracker", "health", "sleep"]),
        ("insurance", ["policy", "quote", "renters", "home", "coverage", "insured", "insurance"]),
        ("fintech", ["bank", "card", "credit", "invest", "pay", "wallet", "fintech"]),
        ("gaming", ["game", "gaming", "console", "fps", "rpg", "mobile game"]),
        ("beauty", ["beauty", "skincare", "makeup", "serum", "cosmetic"]),
        ("fitness", ["fitness", "gym", "workout", "membership"]),
        ("travel", ["hotel", "flight", "travel", "tour"]),
        ("technology", ["phone", "laptop", "tech", "ai", "software"]),
    ]
    for cat, tokens in rules:
        for tok in tokens:
            if tok in text:
                return cat, 0.6, f"token '{tok}'"
    return "other", 0.35, "no strong tokens"


def infer_industry(category: str, text: str) -> Tuple[str, float, str]:
    mapping = {
        "meal-prep": "food",
        "wearable health": "health & wellness",
        "insurance": "insurance",
        "fintech": "financial services",
        "gaming": "gaming",
        "beauty": "beauty & personal care",
        "other": "other",
    }
    return mapping.get(category, "other"), 0.45, "from category"


def infer_product(text: str, company: Optional[str]) -> Tuple[str, float, str]:
    # naive extraction: look for product-like nouns
    if company and company.strip():
        # e.g., "Crunch Fitness membership"
        if any(w in text for w in ["membership", "plan", "ring", "watch", "policy", "card", "app"]):
            for w in ["membership", "plan", "ring", "watch", "policy", "card", "app"]:
                if w in text:
                    return f"{company.strip()} {w}", 0.5, f"token '{w}'"
        return f"{company.strip()} product", 0.35, "company default"
    # fallback
    for w in ["membership", "plan", "ring", "watch", "policy", "card", "app"]:
        if w in text:
            return w, 0.4, f"token '{w}'"
    return "product", 0.3, "default"


def infer_audience(text: str) -> Tuple[Dict[str, any], float, str]:
    age = "unknown"
    if re.search(r"\b1[3-7]\b|13-17", text):
        age = "13-17"
    elif re.search(r"\b1[8-9]|2[0-4]\b|18-24", text):
        age = "18-24"
    elif re.search(r"25-34|\b2[5-9]|3[0-4]\b", text):
        age = "25-34"
    elif re.search(r"35-44|\b3[5-9]|4[0-4]\b", text):
        age = "35-44"
    elif re.search(r"45\+|\b4[5-9]|5\d\b", text):
        age = "45+"

    life = "unknown"
    if any(t in text for t in ["student", "college", "university"]):
        life = "student"
    elif any(t in text for t in ["mom", "dad", "parent", "family"]):
        life = "parent"
    elif any(t in text for t in ["retiree", "retired"]):
        life = "retiree"
    elif any(t in text for t in ["career", "work", "job"]):
        life = "early-career"

    region = "unknown"
    for r in ["UK", "EST", "PST", "CST", "Toronto", "NYC", "USA", "US", "North America", "Europe"]:
        if r.lower() in text:
            region = f"{r}"
            break

    lang = "english"
    if any(w in text for w in ["el", "la", "de", "y", "los", "las"]) and not any(w in text for w in [" the "]):
        lang = "spanish"

    media = "unknown"
    if any(t in text for t in ["video", "tiktok", "shorts", "reel"]):
        media = "short videos"
    elif any(t in text for t in ["carousel", "gallery"]):
        media = "image carousels"
    elif any(t in text for t in ["blog", "article", "long post"]):
        media = "long posts"
    else:
        media = "mixed"

    values: List[str] = []
    for v in ["sustainability", "frugality", "performance", "aesthetics", "promotion", "discount", "free"]:
        if v in text:
            values.append(v)

    tone = "unknown"
    if any(t in text for t in ["funny", "humor", "lol"]):
        tone = "humorous"
    elif any(t in text for t in ["expert", "guide", "how to", "explainer"]):
        tone = "authoritative"
    elif any(t in text for t in ["minimal", "clean"]):
        tone = "minimalist"
    elif any(t in text for t in ["hype", "limited time", "act now", "urgent"]):
        tone = "hype"

    audience = {
        "age_cohort": age,
        "life_stage": life,
        "region": region,
        "language": lang,
        "media_preference": media,
        "values": values,
        "tone_preference": tone,
    }
    return audience, 0.4, "inferred from text"


def choose_product_name(
    declared_company: Optional[str], detected_brand_names: List[str], moondream_summary: str, ocr_text_raw: str
) -> Tuple[str, float, str]:
    if detected_brand_names:
        return detected_brand_names[0].strip(), 0.6, "detected brand"
    if declared_company and declared_company.strip():
        return declared_company.strip(), 0.6, "declared company"

    # Try to synthesize from moondream: pick up to first 2 tokens before comma
    md = (moondream_summary or "").strip()
    if md:
        head = md.split(",")[0].strip()
        head = re.sub(r"[^A-Za-z0-9\s]", "", head).strip()
        words = head.split()
        if words:
            candidate = " ".join(words[:2]).title()
            return candidate, 0.35, "from moondream"

    # Fallback: generic product name from category-ish word
    for token in ["service", "product", "brand"]:
        if token in ocr_text_raw.lower():
            return f"{token.title()}", 0.3, "generic from OCR"
    return "Brand Product", 0.3, "default"


def extract_value_prop(md: str, ocr: str) -> Tuple[str, float, str]:
    text = f"{md} {ocr}".strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    # pick first sentence with benefit verb
    for s in sentences:
        for v in BENEFIT_VERBS:
            if v in s.lower():
                vp = s.strip()
                return vp, 0.5, f"verb '{v}'"
    # fallback to short summary
    vp = (md or ocr).strip()
    vp = vp.split(".")[0].strip()
    return vp[:200], 0.35, "fallback"


def extract_keywords(md: str, ocr: str, extra: Optional[List[str]] = None) -> Tuple[List[str], float, str]:
    text = f"{md} {ocr}".lower()
    tokens = re.split(r"[^a-z0-9\-]+", text)
    tokens = [t for t in tokens if t and t not in _STOPWORDS and len(t) > 2]
    # bias words
    seeds = set(tokens)
    bias = {
        "audience": ["parents", "gamers", "students", "athletes", "professionals", "biohackers"],
        "intent": ["time-saving", "privacy", "budget", "premium", "promotion", "limited-time", "discount"],
        "domain": ["fitness", "sleep", "health", "insurance", "finance", "gaming", "beauty"],
    }
    for g in bias.values():
        for w in g:
            if w in text:
                seeds.add(w)

    if extra:
        for k in extra:
            seeds.add(k.lower())

    # Keep unique order by frequency approximation: original order suffices
    kws = list(seeds)
    # prefer audience and intent terms at front
    priority = [
        "parents",
        "gamers",
        "biohackers",
        "sleep",
        "privacy",
        "promotion",
        "limited-time",
        "fitness",
    ]
    kws.sort(key=lambda x: (0 if x in priority else 1, len(x)))
    kws = [k for k in kws if not k.isdigit()][:8]
    # ensure minimum length
    if len(kws) < 5:
        fill = ["audience", "intent", "style", "brand", "offer"]
        for f in fill:
            if f not in kws:
                kws.append(f)
            if len(kws) >= 5:
                break
    conf = 0.5 if len(kws) >= 5 else 0.35
    return kws[:8], conf, "derived from OCR+Moondream"


