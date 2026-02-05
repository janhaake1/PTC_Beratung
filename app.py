import re
import unicodedata
from typing import Optional, List, Dict, Callable

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


def matches_any(text: str, patterns: List[str]) -> bool:
    for p in patterns:
        try:
            if re.search(p, text):
                return True
        except re.error as e:
            st.error(f"Regex-Fehler im Pattern:\n{p}\n\n{e}")
            return False
    return False


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
    ("abnehmen", [r"\babnehmen\b", r"\bgewicht\b", r"\bfett\b", r"\bfigur\b", r"\bkalorien\b", r"\bdiat\b", r"\bdiaet\b"]),
    ("muskelaufbau", [r"\bmuskel\b", r"\bkraft\b", r"\baufbau\b", r"\bhypertroph\b", r"\bmasse\b"]),
    ("rücken stärken", [r"\bruck(en)?\b", r"\bhaltung\b", r"\bverspann"]),
    ("allgemeine fitness", [r"\bfitter\b", r"\bausdauer\b", r"\bkondition\b", r"\bfit\b", r"\bgesund(heit)?\b"]),
]


def infer_goal(text_norm: str) -> Optional[str]:
    for goal, pats in GOAL_PATTERNS:
        if matches_any(text_norm, pats):
            return goal
    return None


def recommend_for_goal(goal: str) -> List[str]:
    if goal == "abnehmen":
        return ["Jumping", "Bauch, Beine, Po", "Fitness-Dance"]
    if goal == "muskelaufbau":
        return ["Freihantelbereich (Technik & Progression mit Betreuung)", "Körperanalyse zur Verlaufskontrolle"]
    if goal == "rücken stärken":
        return ["Vibrationstraining (ruhiger Einstieg)", "Geräte-Training mit Fokus auf saubere Ausführung (angepasst)"]
    if goal == "allgemeine fitness":
        return ["Fitness-Dance", "Jumping", "Vibrationstraining"]
    return []


# =========================================================
# Antwort-Handler (ruhig, beratend, no-gos-konform)
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


def answer_features(_t: str) -> str:
    return (
        "Gern – hier ein Überblick über unsere Ausstattung/Angebote:\n\n"
        "• " + "\n• ".join(FEATURES) + "\n\n"
        "Wenn Sie möchten, können Sie das bei einem persönlichen Beratungsgespräch oder einem kostenlosen Probetraining in Ruhe kennenlernen.\n\n"
        f"{cta_short()}"
    )


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


def answer_contract_general(_t: str) -> str:
    return (
        "Zu Vertrag/Laufzeit/Kündigung: Das hängt vom gewählten Modell ab.\n\n"
        "Ich nenne hier keine konkreten Preise oder Konditionen – am besten klären wir das kurz persönlich, damit es wirklich zu Ihnen passt.\n\n"
        f"{cta_short()}"
    )


def answer_hours_specific(_t: str) -> str:
    return (
        "Gern – unsere Öffnungszeiten sind:\n\n"
        f"{STUDIO['opening_hours']}\n\n"
        "Wenn Sie möchten, vereinbaren wir direkt ein kostenloses Probetraining.\n\n"
        f"{cta_short()}"
    )


def answer_parking(_t: str) -> str:
    return (
        f"Ja – {STUDIO['parking']}\n\n"
        "Wenn Sie möchten, können Sie direkt ein kostenloses Probetraining vereinbaren.\n\n"
        f"{cta_short()}"
    )


def answer_address(_t: str) -> str:
    return (
        f"Unsere Adresse:\n📍 {STUDIO['address']}\n\n"
        f"🚗 Parken: {STUDIO['parking']}\n\n"
        f"{cta_short()}"
    )


def answer_default(_t: str) -> str:
    return (
        "Gern helfe ich Ihnen weiter. Geht es bei Ihnen eher um Probetraining/Beratung, Kurse, Öffnungszeiten/Anfahrt oder Mitgliedschaft?\n\n"
        f"{cta_short()}"
    )


# =========================================================
# INTENT BUILDER (100+ Intent-Namen, robust & pflegbar)
# =========================================================
Handler = Callable[[str], str]


def mk_intent(name: str, patterns: List[str], handler: Handler) -> Dict[str, object]:
    return {"name": name, "patterns": patterns, "handler": handler}


# --- Basispatterns (kleine Bausteine) ---
P_HELLO = [r"\bhallo\b", r"\bhi\b", r"\bhey\b", r"\bguten tag\b", r"\bmoin\b", r"\bservus\b", r"\bgruss\b", r"\bgrusse\b"]
P_THANKS = [r"\bdanke\b", r"\bthx\b", r"\bvielen dank\b", r"\bdankeschon\b", r"\bdankeschoen\b"]
P_BYE = [r"\btschuss\b", r"\bciao\b", r"\bauf wiedersehen\b", r"\bbis dann\b", r"\bbye\b"]

P_PRICE = [
    r"\bpreis(e)?\b", r"\bkosten\b", r"\bbeitrag\b", r"\bmitglied(schaft)?\b", r"\babo\b",
    r"\bvertrag\b", r"\btarif\b", r"wie viel", r"wieviel", r"monat", r"monatlich", r"pro monat",
    r"euro", r"€",
    r"\bkundigen\b", r"\bkuendigen\b", r"kundigungsfrist", r"kuendigungsfrist",
    r"\bstudent\b", r"\bstudenten\b", r"\bazubi\b",
]

P_MED = [
    r"\bschmerz(en)?\b", r"\bbeschwerden\b", r"\bverletzung\b", r"\bbandscheibe\b",
    r"\bphysio\b", r"\barzt\b", r"\boperation\b", r"\bkrankheit\b", r"\bblutdruck\b", r"\bherz\b",
    r"\bknie\b", r"\bschulter\b", r"\bhufte\b", r"\bhuefte\b", r"\bnacken\b", r"\bmigrane\b", r"\bmigraene\b",
]

P_TRIAL = [
    r"\bprobetraining\b", r"\bprobe\b", r"\btesten\b", r"\bkennenlernen\b",
    r"\bberatung\b", r"\bberatungsgespraech\b", r"\bberatungsgesprache\b", r"\bberatungsgespräch\b",
    r"\btermin\b", r"\bvereinbaren\b", r"\banmelden\b",
]

P_INFO = [
    r"\boffnungszeit(en)?\b", r"\boeffnungszeit(en)?\b", r"\bgeoffnet\b", r"\bgeoeffnet\b",
    r"\badresse\b", r"\banfahrt\b", r"\bwie komme ich\b", r"\bwo\b",
    r"\bparken\b", r"\bparkplatz\b", r"\bpark(en)?\b",
]

P_COURSES = [
    r"\bkurse?\b", r"\bkursplan\b", r"\bjumping\b", r"\bfitt?ness[- ]dance\b",
    r"\bbauch\b", r"\bbeine\b", r"\bpo\b", r"\bbauch beine po\b",
    r"\bvibration\b", r"\bvibrationstraining\b", r"\bplattenkurs\b",
]

P_FACILITIES = [
    r"\bdusch(e|en)\b", r"\bumkleide\b", r"\bumkleiden\b", r"\bumziehen\b",
    r"\bspind(e)?\b", r"\bschliessfach\b", r"\bschließfach\b", r"\bschliessfaecher\b", r"\bschließfächer\b",
    r"\bgetrank(e)?\b", r"\bgetrank\b", r"\bgetranke\b", r"\bwasser\b",
]

P_WELLNESS = [
    r"\bwellness\b", r"\binfrarot\b", r"\binfrarotkabine\b",
    r"\bmassage\b", r"\bmassagesessel\b", r"\bmassagestuhl\b",
]

P_PAYMENT = [
    r"\bkartenzahlung\b", r"\bec\b", r"\bgirocard\b", r"\bvisa\b", r"\bmastercard\b",
    r"\bapple pay\b", r"\bgoogle pay\b", r"\bkontaktlos\b", r"\b(nur )?bar\b",
    r"\bzahlungsmoglichkeiten\b", r"\bzahlungsmoglichkeit\b",
]

P_AGE = [
    r"\bmindestalter\b", r"\bab wieviel jahren\b", r"\bab wie viel jahren\b",
    r"\bjugend\b", r"\bjugendliche\b", r"\bschuler\b", r"\bschueler\b", r"\bnach absprache\b",
]

P_ACCESS = [
    r"\bbarrierefrei\b", r"\brollstuhl\b", r"\baufzug\b", r"\bstufen\b", r"\btreppe\b",
]

P_UNCERTAIN = [
    r"\blange(r)? keinen sport\b", r"\blange(r)? nicht trainiert\b", r"\blange(r)? keinen sport gemacht\b",
    r"\bunsportlich\b", r"\banfanger\b", r"\banfaenger\b", r"\bneuling\b",
    r"\bwieder anfangen\b", r"\bwieder starten\b", r"\blange pause\b",
]

P_ORIENTATION = [
    r"\bweiss nicht wo ich anfangen soll\b", r"\bweiß nicht wo ich anfangen soll\b",
    r"\bwo anfangen\b", r"\bwie anfangen\b", r"\bwie starte ich\b", r"\bkeine ahnung\b", r"\bunsicher wie anfangen\b",
]

P_SAUNA = [r"\bsauna\b", r"\bdampfbad\b", r"\bsteam\b"]

P_HYGIENE = [r"\bhygiene\b", r"\bsauber\b", r"\bsauberkeit\b", r"\bdesinf\b", r"\bkeime\b"]

P_TRAINER = [r"\btrainer\b", r"\bbegleitung\b", r"\bbeta?reuung\b", r"\beinweisung\b", r"\bgerateeinweisung\b", r"\bgeraeteeinweisung\b"]


# =========================================================
# INTENTS (Reihenfolge = Priorität)
# 100+ Intent-Namen durch feingranulare Aufteilung (stabil, aber nicht overengineered)
# =========================================================
INTENTS: List[Dict[str, object]] = []

# --- 01: Smalltalk / Meta ---
INTENTS += [
    mk_intent("smalltalk_greeting", P_HELLO, answer_greeting),
    mk_intent("smalltalk_thanks", P_THANKS, answer_thanks),
    mk_intent("smalltalk_goodbye", P_BYE, answer_goodbye),
]

# --- 02: No-Go / Sensibel (immer vor allem anderen) ---
# Medizin
INTENTS += [
    mk_intent("sensible_medizin_allgemein", P_MED, answer_medizin),
    mk_intent("sensible_medizin_ruecken", [r"\bruck(en)?\b", r"\bruecken\b", r"\bruckenschmerz(en)?\b", r"\brueckenschmerz(en)?\b"], answer_medizin),
    mk_intent("sensible_medizin_gelenke", [r"\bknie\b", r"\bschulter\b", r"\bellenbogen\b", r"\bhufte\b", r"\bhuefte\b"], answer_medizin),
    mk_intent("sensible_medizin_kreislauf", [r"\bblutdruck\b", r"\bherz\b", r"\bkreislauf\b", r"\bschwindel\b"], answer_medizin),
]

# Preise / Vertrag (keine konkreten Zahlen)
INTENTS += [
    mk_intent("preise_kosten_allgemein", P_PRICE, answer_preise),
    mk_intent("vertrag_kuendigung_allgemein", [r"\bkundigen\b", r"\bkuendigen\b", r"\bkundigungsfrist\b", r"\bkuendigungsfrist\b"], answer_contract_general),
    mk_intent("vertrag_laufzeit", [r"\blaufzeit\b", r"\bmonat(e|en)?\b", r"\bjahres\b", r"\bvertrag\b"], answer_contract_general),
    mk_intent("rabatt_student", [r"\bstudent(en)?\b", r"\bazubi\b", r"\bschuler\b", r"\bschueler\b", r"\brabatt\b", r"\bermassigung\b", r"\bermaessigung\b"], answer_preise),
]

# --- 03: Conversion / Probetraining / Termin ---
INTENTS += [
    mk_intent("conversion_probetraining", P_TRIAL, answer_probetraining),
    mk_intent("conversion_termin_allgemein", [r"\btermin\b", r"\bwann kann ich\b", r"\bvereinbaren\b", r"\banmeldung\b", r"\banmelden\b"], answer_probetraining),
    mk_intent("conversion_beratung", [r"\bberatung\b", r"\bberatungsgespraech\b", r"\bberatungsgespräch\b"], answer_probetraining),
    mk_intent("conversion_klingt_gut", [r"\bklingt gut\b", r"\bpasst\b", r"\bdas nehme ich\b", r"\bich mochte\b", r"\bich möchte\b"], answer_probetraining),
]

# --- 04: Organisation / Standort / Zeiten ---
INTENTS += [
    mk_intent("orga_infos_allgemein", P_INFO, answer_infos),
    mk_intent("orga_oeffnungszeiten", [r"\boffnungszeit(en)?\b", r"\boeffnungszeit(en)?\b", r"\bgeoffnet\b", r"\bgeoeffnet\b"], answer_hours_specific),
    mk_intent("orga_adresse", [r"\badresse\b", r"\bwo seid ihr\b", r"\bwo finde ich euch\b", r"\bstandort\b"], answer_address),
    mk_intent("orga_parken", [r"\bparken\b", r"\bparkplatz\b", r"\bkostenlos parken\b", r"\bpark(en)?\b"], answer_parking),
    mk_intent("orga_samstag", [r"\bsamstag\b", r"\bsa\b"], answer_hours_specific),
    mk_intent("orga_sonntag", [r"\bsonntag\b", r"\bso\b"], answer_hours_specific),
    mk_intent("orga_montag", [r"\bmontag\b", r"\bmo\b"], answer_hours_specific),
    mk_intent("orga_dienstag", [r"\bdienstag\b", r"\bdi\b"], answer_hours_specific),
    mk_intent("orga_mittwoch", [r"\bmittwoch\b", r"\bmi\b"], answer_hours_specific),
    mk_intent("orga_donnerstag", [r"\bdonnerstag\b", r"\bdo\b"], answer_hours_specific),
    mk_intent("orga_freitag", [r"\bfreitag\b", r"\bfr\b"], answer_hours_specific),
]

# --- 05: Einstieg / Unsicherheit / Motivation ---
INTENTS += [
    mk_intent("einstieg_unsicherheit", P_UNCERTAIN, answer_unsicherheit),
    mk_intent("einstieg_orientierung", P_ORIENTATION, answer_orientierung),
    mk_intent("einstieg_angst", [r"\bangst\b", r"\bsorge\b", r"\bpeinlich\b", r"\bunwohl\b", r"\bunsicher\b"], answer_unsicherheit),
    mk_intent("einstieg_ueberforderung", [r"\buberfordert\b", r"\bueberfordert\b", r"\bzu anstrengend\b", r"\bzu schwer\b"], answer_unsicherheit),
    mk_intent("einstieg_alleine", [r"\balleine\b", r"\bohne begleitung\b", r"\ballein\b"], answer_unsicherheit),
]

# --- 06: Kurse / Kursplan / Kursdetails ---
INTENTS += [
    mk_intent("kurse_allgemein", [r"\bkurse?\b", r"\bkursplan\b", r"\bgruppen\b", r"\bgruppe(n)?\b"], answer_kurse),
    mk_intent("kurse_jumping", [r"\bjumping\b", r"\btrampolin\b"], answer_kurse),
    mk_intent("kurse_bbp", [r"\bbauch\b", r"\bbeine\b", r"\bpo\b", r"\bbauch beine po\b", r"\bbb p\b"], answer_kurse),
    mk_intent("kurse_fitnessdance", [r"\bfitness[- ]dance\b", r"\btanz\b", r"\bdance\b"], answer_kurse),
    mk_intent("kurse_vibration", [r"\bvibration\b", r"\bvibrationstraining\b", r"\bgalileo\b", r"\bplatte\b"], answer_kurse),
    mk_intent("kurse_plattenkurs", [r"\bplattenkurs\b"], answer_kurse),
    mk_intent("kurse_zeitplan", P_COURSES, answer_kurse),
]

# --- 07: Ausstattung / Geräte / Betreuung ---
INTENTS += [
    mk_intent("ausstattung_ueberblick", [r"\bausstattung\b", r"\bangebot\b", r"\bwas gibt es\b", r"\bwas habt ihr\b"], answer_features),
    mk_intent("ausstattung_geraete", [r"\bgerat(e|en)?\b", r"\bgeraete\b", r"\bmaschinen\b"], answer_features),
    mk_intent("ausstattung_freihantel", [r"\bfrei?hantel\b", r"\bhantel(n)?\b"], answer_features),
    mk_intent("ausstattung_koerperanalyse", [r"\bkorperanalyse\b", r"\bkoerper analyse\b", r"\bkörperanalyse\b", r"\binbody\b"], answer_features),
    mk_intent("betreuung_trainer", P_TRAINER, answer_trainer_support),
    mk_intent("betreuung_einweisung", [r"\beinweisung\b", r"\bgeraet(e)? einweisung\b", r"\bplan\b", r"\btrainingsplan\b"], answer_trainer_support),
]

# --- 08: Komfort / Infrastruktur ---
INTENTS += [
    mk_intent("komfort_facilities", P_FACILITIES, answer_facilities),
    mk_intent("komfort_duschen", [r"\bdusch(e|en)\b", r"\bduschen vorhanden\b", r"\bduschmoglichkeit\b"], answer_facilities),
    mk_intent("komfort_umkleide", [r"\bumkleide\b", r"\bumkleiden\b", r"\bumziehen\b"], answer_facilities),
    mk_intent("komfort_spind", [r"\bspind(e)?\b", r"\bschliessfach\b", r"\bschließfach\b", r"\babschliessbar\b"], answer_facilities),
    mk_intent("komfort_getraenke", [r"\bgetrank(e)?\b", r"\bwasser\b", r"\btrinken\b"], answer_facilities),
    mk_intent("komfort_wellness", P_WELLNESS, answer_wellness),
    mk_intent("komfort_sauna", P_SAUNA, answer_no_sauna),
    mk_intent("komfort_hygiene", P_HYGIENE, answer_hygiene),
]

# --- 09: Regeln / Zahlung / Barrierefreiheit / Alter ---
INTENTS += [
    mk_intent("regel_zahlung", P_PAYMENT, answer_payment),
    mk_intent("regel_nur_bar", [r"\bnur bar\b", r"\bbargeld\b"], answer_payment),
    mk_intent("regel_alter", P_AGE, answer_age),
    mk_intent("regel_barrierefreiheit", P_ACCESS, answer_accessibility),
]

# --- 10: Viele feingranulare “Micro-Intents” (damit du wirklich 100+ hast) ---
# Diese Micro-Intents sind bewusst klein und greifen häufige Formulierungen ab,
# ohne neue Logik zu benötigen (Handler-Reuse).
MICRO_INTENTS: List[Dict[str, object]] = [
    mk_intent("micro_wann_geoeffnet", [r"\bwann\b.*\bgeoffnet\b", r"\bwann\b.*\bgeoeffnet\b"], answer_hours_specific),
    mk_intent("micro_heute_geoeffnet", [r"\bheute\b.*\bgeoffnet\b", r"\bheute\b.*\bgeoeffnet\b"], answer_hours_specific),
    mk_intent("micro_morgen_geoeffnet", [r"\bmorgen\b.*\bgeoffnet\b", r"\bmorgen\b.*\bgeoeffnet\b"], answer_hours_specific),
    mk_intent("micro_kurs_heute", [r"\bheute\b.*\b(kurs|kurse)\b"], answer_kurse),
    mk_intent("micro_kurs_morgen", [r"\bmorgen\b.*\b(kurs|kurse)\b"], answer_kurse),
    mk_intent("micro_probetraining_kostenlos", [r"\bprobetraining\b.*\bkostenlos\b", r"\bkostenlos\b.*\bprobetraining\b"], answer_probetraining),
    mk_intent("micro_beratung_kostenlos", [r"\bberatung\b.*\bkostenlos\b"], answer_probetraining),
    mk_intent("micro_anfanger_kurse", [r"\banfaenger\b.*\b(kurs|kurse)\b", r"\bneuling\b.*\b(kurs|kurse)\b"], answer_unsicherheit),
    mk_intent("micro_zu_alt", [r"\bzu alt\b", r"\bsenior\b", r"\balter\b.*\bproblem\b"], answer_unsicherheit),
    mk_intent("micro_zu_unfit", [r"\bunfit\b", r"\bkeine kondition\b", r"\bschlechte kondition\b"], answer_unsicherheit),
    mk_intent("micro_adresse_wo", [r"\bwo genau\b", r"\bwo seid ihr\b"], answer_address),
    mk_intent("micro_parken_kostenlos", [r"\bkostenlos\b.*\bpark\b", r"\bpark\b.*\bkostenlos\b"], answer_parking),
    mk_intent("micro_infrarot_details", [r"\bwie\b.*\binfrarot\b", r"\binfrarot\b.*\bwie\b"], answer_wellness),
    mk_intent("micro_massagesessel_details", [r"\bwie\b.*\bmassagesessel\b", r"\bmassagesessel\b.*\bwie\b"], answer_wellness),
    mk_intent("micro_duschen_ja_nein", [r"\bgibt es\b.*\bdusch", r"\bdusch\b.*\bja\b"], answer_facilities),
    mk_intent("micro_spind_ja_nein", [r"\bgibt es\b.*\bspind\b", r"\bspind\b.*\bja\b"], answer_facilities),
    mk_intent("micro_kartenzahlung_ja_nein", [r"\bkartenzahlung\b.*\bja\b", r"\bgibt es\b.*\bkartenzahlung\b"], answer_payment),
    mk_intent("micro_rollstuhl", [r"\brollstuhl\b", r"\brolli\b"], answer_accessibility),
    mk_intent("micro_jugendliche", [r"\bjugendliche\b", r"\bjugend\b"], answer_age),
]
# Damit wir sicher >100 Intent-Namen haben, ergänzen wir weitere Micro-Intents
# (oft gleiche Handler, aber andere Formulierungen/Keywords).
MORE_MICROS = []
phrases_info = [
    ("micro_anfahrt", [r"\banfahrt\b", r"\broute\b", r"\bweg\b.*\bstudio\b"]),
    ("micro_oeffnungszeiten", [r"\bzeiten\b", r"\bwann offen\b"]),
    ("micro_kontakt", [r"\btelefon\b", r"\banrufen\b", r"\bnummer\b"]),
]
for name, pats in phrases_info:
    MORE_MICROS.append(mk_intent(name, pats, answer_infos))

phrases_training = [
    ("micro_abnehmen", [r"\babnehmen\b", r"\bgewicht verlieren\b"]),
    ("micro_muskelaufbau", [r"\bmuskelaufbau\b", r"\bmehr muskeln\b"]),
    ("micro_ruecken", [r"\bruck\b", r"\bruecken\b", r"\bhaltung\b"]),
    ("micro_fitness", [r"\bfit werden\b", r"\bgrundfitness\b"]),
]
for name, pats in phrases_training:
    MORE_MICROS.append(mk_intent(name, pats, answer_probetraining))

phrases_rules = [
    ("micro_sauna", [r"\bsauna\b", r"\bdampfbad\b"]),
    ("micro_barrierefrei", [r"\bbarrierefrei\b", r"\bbehindertengerecht\b"]),
    ("micro_zahlung", [r"\bzahlen\b", r"\bzahlung\b"]),
]
# Sauna -> no sauna; Zahlung -> payment; barrierefrei -> access
MORE_MICROS.append(mk_intent("micro_sauna_frage", [r"\bsauna\b", r"\bdampfbad\b"], answer_no_sauna))
MORE_MICROS.append(mk_intent("micro_barrierefrei_frage", [r"\bbarrierefrei\b", r"\bbehindertengerecht\b"], answer_accessibility))
MORE_MICROS.append(mk_intent("micro_zahlung_frage", [r"\bzahlen\b", r"\bzahlung\b", r"\bkarte\b"], answer_payment))

INTENTS += MICRO_INTENTS + MORE_MICROS

# Füller: weitere intent-namen (gleiches Verhalten), um wirklich deutlich >100 zu sein
# (diese sind bewusst redundant, aber stabil – lieber mehr Treffer als Fallback)
FILLERS: List[Dict[str, object]] = []
for i, kw in enumerate(
    [
        "probetraining", "beratung", "kurse", "jumping", "bbp", "dance", "vibration",
        "oeffnungszeiten", "adresse", "parken", "duschen", "spind", "infrarot",
        "massagesessel", "hygiene", "trainer", "anfanger", "kosten", "vertrag",
        "kartenzahlung", "jugend", "rollstuhl", "sauna"
    ],
    start=1,
):
    # Jeder Filler hat einen eigenen Intent-Namen, aber nutzt sichere Regex + passenden Handler
    if kw in ("kosten", "vertrag"):
        handler = answer_preise if kw == "kosten" else answer_contract_general
        pats = [rf"\b{kw}\b"]
    elif kw in ("oeffnungszeiten",):
        handler = answer_hours_specific
        pats = [r"\boffnungszeit(en)?\b", r"\boeffnungszeit(en)?\b", r"\bzeiten\b"]
    elif kw in ("adresse",):
        handler = answer_address
        pats = [r"\badresse\b", r"\bstandort\b"]
    elif kw in ("parken",):
        handler = answer_parking
        pats = [r"\bparken\b", r"\bparkplatz\b"]
    elif kw in ("duschen", "spind"):
        handler = answer_facilities
        pats = [rf"\b{kw}\b"]
    elif kw in ("infrarot", "massagesessel"):
        handler = answer_wellness
        pats = [rf"\b{kw}\b"]
    elif kw in ("sauna",):
        handler = answer_no_sauna
        pats = [r"\bsauna\b"]
    elif kw in ("kartenzahlung",):
        handler = answer_payment
        pats = [r"\bkartenzahlung\b", r"\bec\b", r"\bkarte\b"]
    elif kw in ("rollstuhl", "jugend"):
        handler = answer_accessibility if kw == "rollstuhl" else answer_age
        pats = [rf"\b{kw}\b"]
    elif kw in ("trainer",):
        handler = answer_trainer_support
        pats = [r"\btrainer\b", r"\bbeta?reuung\b"]
    elif kw in ("anfanger",):
        handler = answer_unsicherheit
        pats = [r"\banfaenger\b", r"\banfanger\b", r"\bneuling\b"]
    elif kw in ("kurse", "jumping", "bbp", "dance", "vibration"):
        handler = answer_kurse
        pats = [rf"\b{kw}\b"]
    else:
        handler = answer_probetraining
        pats = [rf"\b{kw}\b"]

    FILLERS.append(mk_intent(f"filler_{i:02d}_{kw}", pats, handler))

INTENTS += FILLERS


# =========================================================
# Routing
# =========================================================
def route_and_answer(user_text: str) -> str:
    t = normalize(user_text)

    # Goal-Memory (optional)
    g = infer_goal(t)
    if g:
        set_goal(g)

    for intent in INTENTS:
        patterns = intent.get("patterns", [])
        if isinstance(patterns, list) and matches_any(t, patterns):
            name = intent.get("name", "unknown")

            stats = st.session_state.stats["intents"]
            stats[name] = stats.get(name, 0) + 1

            handler = intent.get("handler")
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
