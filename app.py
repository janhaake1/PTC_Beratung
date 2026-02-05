import re
import unicodedata
from typing import Optional, List, Dict, Callable, Tuple

import streamlit as st

# =========================================================
# PTC – STAMMDATEN
# =========================================================
STUDIO = {
    "name": "PTC Fitnessstudio Hildesheim",
    "phone_display": "05121 2819760",
    "phone_tel": "tel:+4951212819760",
    "address": "Rudolf-Diesel-Straße 8, 31137 Hildesheim",
    "parking": "Direkt am Studio stehen ausreichend kostenlose Parkplätze zur Verfügung.",
    "opening_hours": (
        "Montag, Mittwoch, Freitag: 08:00–20:00 Uhr\n"
        "Dienstag & Donnerstag: 09:00–20:00 Uhr\n"
        "Samstag: 10:00–14:00 Uhr\n"
        "Sonntag: 11:00–15:00 Uhr"
    ),
}

PROBETRAINING = {
    "duration": "in der Regel 60 Minuten",
    "included": "mit persönlicher Betreuung",
    "options": "je nach Wunsch Geräte-Training und/oder Kurse",
    "price": "kostenlos",
}

COURSE_PLAN = {
    "Montag": [
        ("16:45–17:15", "Vibrationstraining"),
        ("17:15–17:45", "Fitness-Dance"),
        ("17:45–18:15", "Bauch, Beine, Po"),
        ("18:15–18:45", "Jumping"),
    ],
    "Dienstag": [
        ("11:30–12:00", "Vibrationstraining"),
    ],
    "Mittwoch": [
        ("13:30–14:00", "Vibrationstraining"),
        ("16:15–16:45", "Vibrationstraining"),
        ("16:45–17:45", "Jumping"),
        ("17:45–18:15", "Bauch, Beine, Po"),
    ],
    "Freitag": [
        ("15:30–16:00", "Plattenkurs"),
    ],
}

FEATURES = [
    "Vibrationstraining",
    "Körperanalyse",
    "Freihantelbereich",
    "Kurse",
    "persönliche Betreuung",
    "ruhige Atmosphäre",
    "Wellness (Infrarot & Massagesessel)",
    "Duschen, Umkleiden & Spinde/Schließfächer",
]

# =========================================================
# Helfer: Textbausteine
# =========================================================
def cta_short() -> str:
    return f"📞 Telefon: {STUDIO['phone_display']} ({STUDIO['phone_tel']})"


def cta_full() -> str:
    return (
        f"📞 Telefon: {STUDIO['phone_display']} ({STUDIO['phone_tel']})\n"
        f"📍 Adresse: {STUDIO['address']}\n"
        f"🕒 Öffnungszeiten:\n{STUDIO['opening_hours']}\n"
        f"🚗 Parken: {STUDIO['parking']}"
    )


def probetraining_block() -> str:
    return (
        "Kostenloses Probetraining:\n"
        f"• Dauer: {PROBETRAINING['duration']}\n"
        f"• Betreuung: {PROBETRAINING['included']}\n"
        f"• Inhalt: {PROBETRAINING['options']}\n"
        f"• Kosten: {PROBETRAINING['price']}"
    )


def course_plan_text() -> str:
    lines = []
    for day, items in COURSE_PLAN.items():
        for time, title in items:
            lines.append(f"• {day}: {time} {title}")
    return "\n".join(lines)


# =========================================================
# Normalisierung & Matching
# =========================================================
def normalize(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^\w\s€]", " ", text)  # € behalten
    text = re.sub(r"\s+", " ", text)
    return text


def count_matches(text: str, patterns: List[str]) -> int:
    """Zählt, wie viele Pattern in text matchen (für robustes Scoring)."""
    hits = 0
    for p in patterns:
        try:
            if re.search(p, text):
                hits += 1
        except re.error as e:
            st.error(f"Regex-Fehler im Pattern:\n{p}\n\n{e}")
            # Bei Regex-Fehler nicht crashen – Pattern einfach ignorieren
            continue
    return hits


# =========================================================
# Session-Memory
# =========================================================
def init_memory() -> None:
    if "memory" not in st.session_state:
        st.session_state.memory = {"goal": None}


def set_goal(goal: Optional[str]) -> None:
    st.session_state.memory["goal"] = goal


def get_goal() -> Optional[str]:
    return st.session_state.memory.get("goal")


def goal_phrase() -> str:
    g = get_goal()
    return f"Da Ihr Ziel „{g}“ ist, " if g else ""


# =========================================================
# Analytics (Session)
# =========================================================
def init_stats() -> None:
    if "stats" not in st.session_state:
        st.session_state.stats = {"intents": {}, "fallback": 0}


# =========================================================
# Ziel-Erkennung
# =========================================================
GOAL_PATTERNS = [
    ("abnehmen", [r"\babnehmen\b", r"\bgewicht\b", r"\bfett\b", r"\bfigur\b", r"\bkalorien\b", r"\bdiae?t\b"]),
    ("muskelaufbau", [r"\bmuskel(n)?\b", r"\bkraft\b", r"\baufbau\b", r"\bhypertroph\b", r"\bmasse\b"]),
    ("ruecken staerken", [r"\bruck(en)?\b", r"\bhaltung\b", r"\bverspann"]),
    ("allgemeine fitness", [r"\bfitter\b", r"\bausdauer\b", r"\bkondition\b", r"\bfit\b", r"\bgesund(heit)?\b"]),
]


def infer_goal(text_norm: str) -> Optional[str]:
    for goal, pats in GOAL_PATTERNS:
        if count_matches(text_norm, pats) > 0:
            return goal
    return None


def recommend_for_goal(goal: str) -> List[str]:
    if goal == "abnehmen":
        return ["Jumping", "Bauch, Beine, Po", "Fitness-Dance"]
    if goal == "muskelaufbau":
        return ["Freihantelbereich (Technik & Progression mit Betreuung)", "Körperanalyse zur Verlaufskontrolle"]
    if goal == "ruecken staerken":
        return ["Vibrationstraining (ruhiger Einstieg)", "Geräte-Training mit Fokus auf saubere Ausführung (angepasst)"]
    if goal == "allgemeine fitness":
        return ["Fitness-Dance", "Jumping", "Vibrationstraining"]
    return []


# =========================================================
# Antwort-Handler
# =========================================================
def answer_greeting(_t: str) -> str:
    return (
        f"Guten Tag! Ich bin der digitale Beratungsassistent vom {STUDIO['name']}.\n\n"
        "Wobei kann ich Ihnen helfen – Probetraining/Beratung, Kurse, Öffnungszeiten/Anfahrt oder eher Trainingseinstieg?\n\n"
        f"{cta_short()}"
    )


def answer_thanks(_t: str) -> str:
    return (
        "Sehr gern. 🙂\n\n"
        "Wenn Sie möchten, können wir direkt den nächsten Schritt planen – z. B. ein kostenloses Probetraining oder ein kurzes Beratungsgespräch.\n\n"
        f"{cta_short()}"
    )


def answer_goodbye(_t: str) -> str:
    return (
        "Sehr gern – ich wünsche Ihnen einen schönen Tag.\n\n"
        "Wenn Sie später noch Fragen haben oder direkt ein Probetraining vereinbaren möchten, melden Sie sich gern telefonisch.\n\n"
        f"{cta_short()}"
    )


def answer_unsicherheit(_t: str) -> str:
    return (
        "Das ist überhaupt kein Problem.\n\n"
        "Wir legen großen Wert auf einen ruhigen, gut betreuten Einstieg und passen das Training individuell an – ohne Überforderung.\n\n"
        "Ein persönliches Beratungsgespräch oder ein kostenloses Probetraining ist dafür ideal.\n\n"
        f"{cta_short()}"
    )


def answer_orientierung(_t: str) -> str:
    return (
        "Das geht vielen so – und ist überhaupt kein Problem.\n\n"
        "Wir unterstützen Sie dabei, einen passenden Einstieg zu finden: ruhig, strukturiert und mit persönlicher Betreuung.\n\n"
        "Am besten eignet sich dafür ein persönliches Beratungsgespräch oder ein kostenloses Probetraining.\n\n"
        f"{cta_short()}"
    )


def answer_preise(t: str) -> str:
    goal = infer_goal(t) or get_goal()
    if goal:
        set_goal(goal)

    parts = [
        "Die Mitgliedsbeiträge können je nach Laufzeit und Trainingsumfang variieren.",
        "Am sinnvollsten ist ein kurzes persönliches Beratungsgespräch oder ein kostenloses Probetraining, "
        "damit wir gemeinsam das passende Angebot für Sie finden.",
    ]
    if goal:
        parts.append(f"{goal_phrase()}können wir im Probetraining/Beratungsgespräch genau passend starten.")

    parts.append(probetraining_block())
    parts.append("Für die Anmeldung melden Sie sich am besten kurz telefonisch.")
    parts.append(cta_full())
    return "\n\n".join(parts)


def answer_contract_general(_t: str) -> str:
    return (
        "Zu Vertrag/Laufzeit/Kündigung: Das hängt vom gewählten Modell ab.\n\n"
        "Ich nenne hier keine konkreten Preise oder Konditionen – am besten klären wir das kurz persönlich, damit es wirklich zu Ihnen passt.\n\n"
        f"{cta_short()}"
    )


def answer_medizin(_t: str) -> str:
    return (
        "Bei Beschwerden ist ein gut betreuter Einstieg besonders wichtig.\n\n"
        "Hinweis: Ich kann keine medizinische Einschätzung geben. Wenn Sie akute oder starke Beschwerden haben, "
        "lassen Sie das bitte ärztlich abklären.\n\n"
        "Am besten eignet sich dafür ein persönliches Beratungsgespräch oder ein kostenloses Probetraining – "
        "dann können wir in Ruhe besprechen, wie ein sinnvoller Einstieg aussehen kann.\n\n"
        f"{cta_short()}"
    )


def answer_infos(_t: str) -> str:
    return (
        "Gern – hier die wichtigsten Infos:\n\n"
        f"📍 Adresse: {STUDIO['address']}\n\n"
        f"🕒 Öffnungszeiten:\n{STUDIO['opening_hours']}\n\n"
        f"🚗 Parken: {STUDIO['parking']}\n\n"
        "Wenn Sie möchten, können Sie direkt ein persönliches Beratungsgespräch oder ein kostenloses Probetraining vereinbaren.\n\n"
        f"{cta_short()}"
    )


def answer_hours(_t: str) -> str:
    return (
        "Gern – unsere Öffnungszeiten sind:\n\n"
        f"{STUDIO['opening_hours']}\n\n"
        "Wenn Sie möchten, vereinbaren wir direkt ein kostenloses Probetraining.\n\n"
        f"{cta_short()}"
    )


def answer_address(_t: str) -> str:
    return (
        f"Unsere Adresse:\n📍 {STUDIO['address']}\n\n"
        f"🚗 Parken: {STUDIO['parking']}\n\n"
        f"{cta_short()}"
    )


def answer_parking(_t: str) -> str:
    return (
        f"Ja – {STUDIO['parking']}\n\n"
        "Wenn Sie möchten, können Sie direkt ein kostenloses Probetraining vereinbaren.\n\n"
        f"{cta_short()}"
    )


def answer_probetraining(t: str) -> str:
    goal = infer_goal(t) or get_goal()
    if goal:
        set_goal(goal)

    parts = [
        "Sehr gern – ein kostenloses Probetraining ist ideal, um unser Studio kennenzulernen.",
        probetraining_block(),
        "Wenn Sie möchten, kann das Probetraining auch als kurzes Beratungsgespräch genutzt werden, um den passenden Start zu planen.",
        "Für die Anmeldung melden Sie sich am besten kurz telefonisch.",
        cta_full(),
    ]
    return "\n\n".join(parts)


def answer_kurse(t: str) -> str:
    goal = infer_goal(t) or get_goal()
    if goal:
        set_goal(goal)

    parts = [
        "Gern – hier unser aktueller Kursplan:",
        course_plan_text(),
    ]
    rec = recommend_for_goal(goal) if goal else []
    if rec:
        parts.append(f"{goal_phrase()}würden sich z. B. diese Optionen anbieten: " + ", ".join(rec) + ".")

    parts += [
        "Wenn Sie möchten, können Sie Kurse auch im Rahmen eines kostenlosen Probetrainings ausprobieren.",
        "Für die Anmeldung melden Sie sich am besten kurz telefonisch.",
        cta_short(),
    ]
    return "\n\n".join(parts)


def answer_features(_t: str) -> str:
    return (
        "Gern – hier ein Überblick über unsere Ausstattung/Angebote:\n\n"
        "• " + "\n• ".join(FEATURES) + "\n\n"
        "Wenn Sie möchten, können Sie das bei einem persönlichen Beratungsgespräch oder einem kostenlosen Probetraining in Ruhe kennenlernen.\n\n"
        f"{cta_short()}"
    )


def answer_facilities(_t: str) -> str:
    return (
        "Gern – bei uns gibt es:\n\n"
        "• Duschen\n"
        "• Umkleiden\n"
        "• Spinde/Schließfächer\n"
        "• Getränke (vor Ort verfügbar)\n\n"
        "Wenn Sie möchten, können Sie das alles bei einem persönlichen Beratungsgespräch oder einem kostenlosen Probetraining in Ruhe kennenlernen.\n\n"
        f"{cta_short()}"
    )


def answer_wellness(_t: str) -> str:
    return (
        "Gern – bei uns gibt es Wellness-Angebote wie:\n\n"
        "• Infrarot\n"
        "• Massagesessel\n\n"
        "Wenn Sie möchten, erklären wir Ihnen im persönlichen Beratungsgespräch oder beim kostenlosen Probetraining, wie Sie das sinnvoll nutzen können.\n\n"
        f"{cta_short()}"
    )


def answer_payment(_t: str) -> str:
    return (
        "Hinweis zur Zahlung: Aktuell bieten wir keine Kartenzahlung an.\n\n"
        "Wenn Sie dazu Fragen haben oder ein kostenloses Probetraining / Beratungsgespräch vereinbaren möchten, melden Sie sich am besten kurz telefonisch.\n\n"
        f"{cta_short()}"
    )


def answer_age(_t: str) -> str:
    return (
        "Zum Mindestalter: Das ist bei uns nach Absprache möglich.\n\n"
        "Am besten klären wir das kurz telefonisch – dann können wir direkt sagen, was in Ihrem Fall passt.\n\n"
        f"{cta_short()}"
    )


def answer_accessibility(_t: str) -> str:
    return (
        "Hinweis zur Barrierefreiheit: Aktuell ist das Studio nicht barrierefrei.\n\n"
        "Wenn Sie mir kurz sagen, was genau Sie benötigen (z. B. Stufen, Zugang, Begleitung), klären wir das gern telefonisch und finden eine passende Lösung.\n\n"
        f"{cta_short()}"
    )


def answer_no_sauna(_t: str) -> str:
    return (
        "Eine Sauna haben wir aktuell nicht.\n\n"
        "Wenn Sie Wellness suchen: Wir bieten Infrarot und einen Massagesessel – gern erkläre ich Ihnen das im Probetraining oder Beratungsgespräch.\n\n"
        f"{cta_short()}"
    )


def answer_hygiene(_t: str) -> str:
    return (
        "Verständlich – Hygiene ist wichtig.\n\n"
        "Wir achten auf eine gepflegte Trainingsumgebung. Wenn Sie möchten, können Sie sich beim kostenlosen Probetraining in Ruhe selbst ein Bild machen.\n\n"
        f"{cta_short()}"
    )


def answer_trainer_support(_t: str) -> str:
    return (
        "Ja – bei uns steht persönliche Betreuung im Vordergrund.\n\n"
        "Gerade am Anfang hilft das sehr: ruhiger Einstieg, Geräte-Einweisung und ein Plan, der zu Ihnen passt.\n\n"
        "Am besten: kostenloses Probetraining oder kurzes Beratungsgespräch.\n\n"
        f"{cta_short()}"
    )


def answer_default(_t: str) -> str:
    return (
        "Gern helfe ich Ihnen weiter. Geht es bei Ihnen eher um Probetraining/Beratung, Kurse, Öffnungszeiten/Anfahrt oder Mitgliedschaft?\n\n"
        f"{cta_short()}"
    )


# =========================================================
# INTENT-DEFINITION (Priorität + Scoring)
# =========================================================
Handler = Callable[[str], str]


class Intent(Tuple[str, int, List[str], Handler]):
    """
    (name, priority, patterns, handler)

    priority: kleiner = wichtiger
    scoring: wie viele patterns matchen -> höhere Trefferzahl gewinnt
    """


def mk_intent(name: str, priority: int, patterns: List[str], handler: Handler) -> Dict[str, object]:
    return {"name": name, "priority": priority, "patterns": patterns, "handler": handler}


# --- Pattern-Bausteine (bewusst NICHT zu generisch) ---
P_HELLO = [r"\bhallo\b", r"\bhi\b", r"\bhey\b", r"\bguten tag\b", r"\bmoin\b", r"\bservus\b"]
P_THANKS = [r"\bdanke\b", r"\bvielen dank\b", r"\bdankesch(oe|o)n\b", r"\bthx\b"]
P_BYE = [r"\btsch(u|ü)ss\b", r"\bciao\b", r"\bauf wiedersehen\b", r"\bbis dann\b", r"\bbye\b"]

# Sensibel/No-Go
P_MED = [
    r"\bschmerz(en)?\b", r"\bbeschwerden\b", r"\bverletzung\b", r"\bbandscheibe\b",
    r"\bphysio\b", r"\barzt\b", r"\boperation\b", r"\bkrankheit\b",
    r"\bblutdruck\b", r"\bherz\b", r"\bkreislauf\b", r"\bschwindel\b",
    r"\bknie\b", r"\bschulter\b", r"\bh(ue|u)fte\b", r"\bnacken\b"
]
P_PRICE = [
    r"\bpreis(e)?\b", r"\bkosten\b", r"\bbeitrag\b", r"\bmitglied(schaft)?\b", r"\babo\b",
    r"\btarif\b", r"\bangebot\b.*\bpreis\b",
    r"\bmonat(lich)?\b", r"\bpro monat\b", r"\beuro\b", r"€",
]
P_CONTRACT = [
    r"\bvertrag\b", r"\blaufzeit\b", r"\bk(ue|ü)ndigen\b", r"\bk(ue|ü)ndigungsfrist\b"
]
P_STUDENTS = [r"\bstudent(en)?\b", r"\bazubi\b", r"\bsch(ue|ü)ler\b", r"\brabatt\b", r"\berm(ae|ä)ssigung\b"]

# Conversion
P_TRIAL = [
    r"\bprobetraining\b", r"\b(termin|vereinbaren|anmelden)\b.*\b(prob(e)?|training|beratung)\b",
    r"\bberatung(sgespr(ae|ä)ch)?\b", r"\bkennenlernen\b", r"\btesten\b",
]

# Orga (hier bewusst ohne reines "\bwo\b")
P_HOURS = [r"\b(o(e|ff)nungszeiten|offen|ge(o|ö)ffnet|zeiten)\b"]
P_ADDRESS = [
    r"\badresse\b", r"\banfahrt\b", r"\bstandort\b",
    r"\bwo\b.*\b(studio|ihr|adresse|finde|seid)\b"
]
P_PARKING = [r"\bparken\b", r"\bparkplatz\b", r"\bkostenlos\b.*\bpark\b", r"\bpark\b.*\bkostenlos\b"]

# Angebote
P_COURSES = [
    r"\bkurse?\b", r"\bkursplan\b", r"\bjumping\b", r"\btrampolin\b",
    r"\bfitt?ness[- ]dance\b", r"\btanz\b",
    r"\bbauch\b.*\bbeine\b.*\bpo\b", r"\bbb\s?p\b",
    r"\bvibration(straining)?\b", r"\bgalileo\b", r"\bplattenkurs\b"
]
P_FEATURES = [
    r"\bausstattung\b", r"\bger(ae|ä)te\b", r"\bmaschinen\b", r"\bfrei?hantel\b",
    r"\bk(oe|ö)rperanalyse\b", r"\binbody\b"
]
P_FACILITIES = [
    r"\bdusch(e|en)\b", r"\bumkleide(n)?\b", r"\bspind(e)?\b",
    r"\bschlie(ss|ß)fach\b", r"\bgetr(ae|ä)nk(e)?\b", r"\bwasser\b"
]
P_WELLNESS = [r"\bwellness\b", r"\binfrarot(kabine)?\b", r"\bmassage(sessel|stuhl)?\b"]
P_SAUNA = [r"\bsauna\b", r"\bdampfbad\b"]
P_HYGIENE = [r"\bhygiene\b", r"\bsauber(keit)?\b", r"\bdesinf\b", r"\bkeime\b"]
P_TRAINER = [r"\btrainer\b", r"\bbeta?reuung\b", r"\beinweisung\b", r"\btrainingsplan\b"]

# Regeln
P_PAYMENT = [
    r"\bkartenzahlung\b", r"\bec\b", r"\bgirocard\b", r"\bvisa\b", r"\bmastercard\b",
    r"\bapple pay\b", r"\bgoogle pay\b", r"\bkontaktlos\b", r"\b(nur )?bar\b",
    r"\bzahlungsm(oe|o)glichkeiten\b"
]
P_AGE = [r"\bmindestalter\b", r"\bjugend(liche)?\b", r"\bab wie ?viel jahren\b", r"\bnach absprache\b"]
P_ACCESS = [r"\bbarrierefrei\b", r"\brollstuhl\b", r"\baufzug\b", r"\bstufen\b", r"\btreppe\b"]

# Einstieg
P_UNCERTAIN = [
    r"\blange(r)?\b.*\b(keinen sport|nicht trainiert|pause)\b",
    r"\bunsportlich\b", r"\banf(ae|ä)nger\b", r"\bneuling\b",
    r"\bwieder anfangen\b", r"\bwieder starten\b",
]
P_ORIENTATION = [
    r"\b(weiss|weiß)\b.*\b(nicht|nich)\b.*\b(wo|wie)\b.*\b(anfangen|starten)\b",
    r"\bwo anfangen\b", r"\bwie anfangen\b", r"\bwie starte ich\b", r"\bkeine ahnung\b",
]


INTENTS: List[Dict[str, object]] = [
    # 0) Smalltalk
    mk_intent("smalltalk_greeting", 0, P_HELLO, answer_greeting),
    mk_intent("smalltalk_thanks", 0, P_THANKS, answer_thanks),
    mk_intent("smalltalk_goodbye", 0, P_BYE, answer_goodbye),

    # 1) Sensibel / No-Go zuerst
    mk_intent("sensible_medizin", 1, P_MED, answer_medizin),

    # 2) Vertrag/Preis sehr früh (keine konkreten Zahlen)
    mk_intent("vertrag_kuendigung", 2, P_CONTRACT, answer_contract_general),
    mk_intent("preise_kosten", 2, P_PRICE + P_STUDENTS, answer_preise),

    # 3) Conversion
    mk_intent("conversion_probetraining", 3, P_TRIAL, answer_probetraining),

    # 4) Orga (getrennt statt “alles in einem”)
    mk_intent("orga_oeffnungszeiten", 4, P_HOURS, answer_hours),
    mk_intent("orga_adresse", 4, P_ADDRESS, answer_address),
    mk_intent("orga_parken", 4, P_PARKING, answer_parking),
    mk_intent("orga_infos_allgemein", 5, [r"\binfo(s)?\b", r"\bkontakt\b", r"\btelefon\b", r"\bnummer\b"], answer_infos),

    # 5) Angebote
    mk_intent("kurse", 6, P_COURSES, answer_kurse),
    mk_intent("ausstattung", 6, P_FEATURES, answer_features),
    mk_intent("komfort_facilities", 6, P_FACILITIES, answer_facilities),
    mk_intent("komfort_wellness", 6, P_WELLNESS, answer_wellness),
    mk_intent("komfort_sauna", 6, P_SAUNA, answer_no_sauna),
    mk_intent("komfort_hygiene", 6, P_HYGIENE, answer_hygiene),
    mk_intent("betreuung_trainer", 6, P_TRAINER, answer_trainer_support),

    # 6) Einstieg
    mk_intent("einstieg_unsicherheit", 7, P_UNCERTAIN, answer_unsicherheit),
    mk_intent("einstieg_orientierung", 7, P_ORIENTATION, answer_orientierung),

    # 7) Regeln
    mk_intent("regel_zahlung", 8, P_PAYMENT, answer_payment),
    mk_intent("regel_alter", 8, P_AGE, answer_age),
    mk_intent("regel_barrierefreiheit", 8, P_ACCESS, answer_accessibility),
]


# =========================================================
# Routing: Best-Match (Score) + Priorität
# =========================================================
def route_and_answer(user_text: str) -> str:
    t = normalize(user_text)

    # Goal memory
    g = infer_goal(t)
    if g:
        set_goal(g)

    best = None  # (score, priority, name, handler)

    for intent in INTENTS:
        patterns = intent["patterns"]
        score = count_matches(t, patterns)

        if score <= 0:
            continue

        name = intent["name"]
        priority = int(intent["priority"])
        handler = intent["handler"]

        # Best Match: höherer score gewinnt; bei Gleichstand niedrigere priority
        candidate = (score, -priority, name, handler)
        if best is None or candidate > best:
            best = candidate

    if best is not None:
        score, neg_prio, name, handler = best
        stats = st.session_state.stats["intents"]
        stats[name] = stats.get(name, 0) + 1
        if callable(handler):
            return handler(t)

    st.session_state.stats["fallback"] += 1
    return answer_default(t)


# =========================================================
# STREAMLIT UI
# =========================================================
st.set_page_config(page_title="PTC Online-Beratung", page_icon="💬")

st.title("💬 Online-Beratung – PTC Fitnessstudio Hildesheim")
st.caption(
    "Guten Tag, ich bin der digitale Beratungsassistent des PTC Fitnessstudios Hildesheim. "
    "Wie kann ich Ihnen helfen?"
)

with st.expander("Datenschutz-Hinweis", expanded=False):
    st.write(
        "Bitte geben Sie keine sensiblen Gesundheitsdaten ein. "
        "Bei akuten Beschwerden wenden Sie sich an medizinisches Fachpersonal. "
        "Ich gebe keine medizinischen Einschätzungen, sondern allgemeine Hinweise zum Studiostart."
    )

if "chat" not in st.session_state:
    st.session_state.chat = []

init_memory()
init_stats()

col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("Neues Gespräch"):
        st.session_state.chat = []
        st.session_state.memory = {"goal": None}
        st.session_state.stats = {"intents": {}, "fallback": 0}
        st.rerun()

with col2:
    st.link_button("📞 Anrufen", STUDIO["phone_tel"])

with col3:
    g = get_goal()
    if g:
        st.info(f"Merke ich mir: Ziel = {g}")

with st.expander("📊 Interne Statistik (nur intern)", expanded=False):
    stats = st.session_state.stats
    if stats["intents"]:
        st.write("**Intent-Treffer:**")
        for k, v in sorted(stats["intents"].items(), key=lambda x: x[1], reverse=True):
            st.write(f"• {k}: {v}")
    else:
        st.write("Noch keine Daten.")
    st.write("---")
    st.write(f"❓ Fallback (nicht erkannt): {stats['fallback']}")

for msg in st.session_state.chat:
    with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
        st.write(msg["content"])

user_input = st.chat_input("Ihre Frage (z.B. Probetraining, Kurse, Öffnungszeiten, Mitgliedschaft)")
if user_input:
    st.session_state.chat.append({"role": "user", "content": user_input})
    answer = route_and_answer(user_input)
    st.session_state.chat.append({"role": "assistant", "content": answer})
    st.rerun()

st.markdown("---")
st.markdown(f"**Direkter Kontakt:** [{STUDIO['phone_display']}]({STUDIO['phone_tel']})")
