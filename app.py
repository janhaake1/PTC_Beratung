import re
import unicodedata
import json
import os
from threading import Lock
from datetime import datetime
from typing import Optional, List, Dict

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
# GLOBAL STATS (für alle Nutzer) – einfache Gesamtauswertung
# =========================================================
STATS_FILE = "ptc_global_stats.json"


def _load_global_stats() -> Dict[str, object]:
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "intents" not in data or "fallback" not in data:
                raise ValueError("Invalid stats shape")
            return data
        except Exception:
            pass
    return {"intents": {}, "fallback": 0, "updated_at": None}


def _save_global_stats(data: Dict[str, object]) -> None:
    data["updated_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    tmp = STATS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATS_FILE)


@st.cache_resource
def get_global_stats_store() -> Dict[str, object]:
    return {"lock": Lock(), "data": _load_global_stats()}


def inc_global_intent(name: str) -> None:
    store = get_global_stats_store()
    with store["lock"]:
        intents = store["data"]["intents"]
        intents[name] = int(intents.get(name, 0)) + 1
        _save_global_stats(store["data"])


def inc_global_fallback() -> None:
    store = get_global_stats_store()
    with store["lock"]:
        store["data"]["fallback"] = int(store["data"].get("fallback", 0)) + 1
        _save_global_stats(store["data"])


# =========================================================
# LOGGING – ALLE FRAGEN (global)
# =========================================================
QUESTIONS_LOG = "ptc_questions_log.jsonl"


def sanitize_for_log(text: str) -> str:
    """
    Minimales Hardening:
    - Länge begrenzen (verhindert Abuse)
    - offensichtliche Emails/Telefonnummern grob maskieren
    """
    t = (text or "").strip()
    t = t[:800]  # Limit
    t = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[email]", t)
    t = re.sub(r"\b(\+?\d[\d\s\-\/]{7,}\d)\b", "[telefon]", t)
    return t


@st.cache_resource
def get_log_lock() -> Lock:
    return Lock()


def log_question(raw_text: str, intent: str, goal: Optional[str]) -> None:
    entry = {
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "intent": intent,
        "goal": goal,
        "text": sanitize_for_log(raw_text),
    }
    lock = get_log_lock()
    with lock:
        with open(QUESTIONS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_questions_log(limit: int = 200) -> List[Dict[str, object]]:
    if not os.path.exists(QUESTIONS_LOG):
        return []
    rows: List[Dict[str, object]] = []
    with open(QUESTIONS_LOG, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    # letzte zuerst
    return rows[-limit:][::-1]


# =========================================================
# Ziel-Erkennung
# =========================================================
GOAL_PATTERNS = [
    ("abnehmen", [r"\babnehmen\b", r"\bgewicht\b", r"\bfett\b", r"\bfigur\b", r"\bkalorien\b"]),
    ("muskelaufbau", [r"\bmuskel\b", r"\bkraft\b", r"\baufbau\b", r"\bhypertroph\b"]),
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
# Antwort-Handler
# =========================================================
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


def answer_default(_t: str) -> str:
    return (
        "Gern helfe ich Ihnen weiter. Geht es bei Ihnen eher um Probetraining/Beratung, Kurse, Öffnungszeiten/Anfahrt oder Mitgliedschaft?\n\n"
        f"{cta_short()}"
    )


# =========================================================
# INTENTS (Reihenfolge = Priorität)
# =========================================================
INTENTS: List[Dict[str, object]] = [
    {
        "name": "medizin_beschwerden",
        "patterns": [
            r"\bruckenschmerz(en)?\b", r"\bruck(en)?\b", r"\brücken\b", r"\brückenschmerz(en)?\b",
            r"\bschmerz(en)?\b", r"\bbeschwerden\b", r"\bverletzung\b", r"\bbandscheibe\b",
            r"\bphysio\b", r"\barzt\b", r"\boperation\b", r"\bkrankheit\b", r"\bblutdruck\b", r"\bherz\b",
        ],
        "handler": answer_medizin,
    },
    {
        "name": "preise_kosten",
        "patterns": [
            r"\bpreis(e)?\b", r"\bkosten\b", r"\bbeitrag\b", r"\bmitglied(schaft)?\b", r"\babo\b",
            r"\bvertrag\b", r"\btarif\b", r"wie viel", r"wieviel", r"monat", r"monatlich", r"pro monat",
            r"euro", r"€",
            r"\bkündigen\b", r"\bkuendigen\b", r"kündigungsfrist", r"kuendigungsfrist",
            r"\bstudent\b", r"\bstudenten\b", r"\bazubi\b",
        ],
        "handler": answer_preise,
    },
    {
        "name": "duschen_umkleide_spinde_getraenke",
        "patterns": [
            r"\bdusch(e|en)\b", r"\bduschen vorhanden\b", r"\bgibt es duschen\b", r"\bduschmoglichkeit\b", r"\bduschmöglichkeit\b",
            r"\bumkleide\b", r"\bumkleiden\b", r"\bumziehen\b",
            r"\bspind(e)?\b", r"\bschliessfach\b", r"\bschließfach\b", r"\bschliessfaecher\b", r"\bschließfächer\b",
            r"\babschliessbar\b", r"\babschließbar\b",
            r"\bgetrank(e)?\b", r"\bgetränk(e)?\b", r"\bwasser\b", r"\btrinken\b",
        ],
        "handler": answer_facilities,
    },
    {
        "name": "wellness_infrarot_massagesessel",
        "patterns": [
            r"\bwellness\b", r"\binfrarot\b", r"\binfrarotkabine\b",
            r"\bmassage\b", r"\bmassagesessel\b", r"\bmassagestuhl\b",
        ],
        "handler": answer_wellness,
    },
    {
        "name": "zahlung_kartenzahlung",
        "patterns": [
            r"\bkartenzahlung\b", r"\bec\b", r"\bgirocard\b", r"\bvisa\b", r"\bmastercard\b",
            r"\bapple pay\b", r"\bgoogle pay\b", r"\bkontaktlos\b", r"\b(nur )?bar\b",
            r"zahlungsmoglichkeiten", r"zahlungsmöglichkeiten",
        ],
        "handler": answer_payment,
    },
    {
        "name": "mindestalter_nach_absprache",
        "patterns": [
            r"\bmindestalter\b", r"ab wieviel jahren", r"ab wie viel jahren",
            r"\bjugend\b", r"\bjugendliche\b", r"\bschüler\b", r"\bschueler\b", r"\bnach absprache\b",
        ],
        "handler": answer_age,
    },
    {
        "name": "barrierefreiheit",
        "patterns": [
            r"\bbarrierefrei\b", r"\brollstuhl\b", r"\baufzug\b", r"\bstufen\b", r"\btreppe\b",
        ],
        "handler": answer_accessibility,
    },
    {
        "name": "einstieg_unsicherheit",
        "patterns": [
            r"lange(r)? keinen sport", r"lange(r)? nicht trainiert", r"lange(r)? keinen sport gemacht",
            r"unsportlich", r"anfanger", r"anfaenger", r"neuling", r"wieder anfangen", r"wieder starten", r"lange pause",
        ],
        "handler": answer_unsicherheit,
    },
    {
        "name": "orientierung",
        "patterns": [
            r"weiß nicht wo ich anfangen soll", r"weiss nicht wo ich anfangen soll",
            r"wo anfangen", r"wie anfangen", r"wie starte ich", r"keine ahnung", r"unsicher wie anfangen",
        ],
        "handler": answer_orientierung,
    },
    {
        "name": "probetraining_beratung",
        "patterns": [
            r"\bprobetraining\b", r"\bprobe\b", r"\btesten\b", r"\bkennenlernen\b",
            r"\bberatung\b", r"\bberatungsgespraech\b", r"\bberatungsgespräch\b",
        ],
        "handler": answer_probetraining,
    },
    {
        "name": "infos_anfahrt_parken_zeiten",
        "patterns": [
            r"\boffnungszeit(en)?\b", r"\böffnungszeit(en)?\b", r"\bgeoffnet\b", r"\bgeöffnet\b",
            r"\badresse\b", r"\banfahrt\b", r"\bwo\b", r"\bparken\b", r"\bparkplatz\b", r"\bsonntag\b", r"\bsamstag\b",
        ],
        "handler": answer_infos,
    },
    {
        "name": "kurse",
        "patterns": [
            r"\bkurse?\b", r"\bjumping\b", r"\bfitt?ness[- ]dance\b", r"\bbauch\b", r"\bbeine\b", r"\bpo\b",
            r"\bvibration\b", r"\bplattenkurs\b",
        ],
        "handler": answer_kurse,
    },
    {
        "name": "ausstattung",
        "patterns": [
            r"\bausstattung\b", r"\bgera(te|ete)\b", r"\bgeräte\b", r"\bmaschinen\b", r"\bfrei?hantel\b",
            r"\bkorperanalyse\b", r"\bkörperanalyse\b", r"\bvibration\b", r"\bwellness\b", r"\binfrarot\b", r"\bmassagesessel\b",
        ],
        "handler": answer_features,
    },
]


def route_and_answer(user_text: str) -> str:
    t_norm = normalize(user_text)

    g = infer_goal(t_norm)
    if g:
        set_goal(g)

    # Intent finden
    for intent in INTENTS:
        patterns = intent.get("patterns", [])
        if isinstance(patterns, list) and matches_any(t_norm, patterns):
            name = str(intent.get("name", "unknown"))

            # Session-Stats
            stats = st.session_state.stats["intents"]
            stats[name] = stats.get(name, 0) + 1

            # Global-Stats
            inc_global_intent(name)

            # ALLE FRAGEN loggen (mit Intent)
            log_question(raw_text=user_text, intent=name, goal=get_goal())

            handler = intent.get("handler")
            if callable(handler):
                return handler(t_norm)

    # Fallback
    st.session_state.stats["fallback"] += 1
    inc_global_fallback()

    # ALLE FRAGEN loggen (Fallback)
    log_question(raw_text=user_text, intent="fallback", goal=get_goal())

    return answer_default(t_norm)


# =========================================================
# STREAMLIT UI
# =========================================================
st.set_page_config(page_title="PTC Online-Beratung", page_icon="💬", layout="centered")

# --- Modern App Look (PTC-Rot) ---
st.markdown("""
<style>
.block-container { max-width: 980px; padding-top: 1.2rem; padding-bottom: 2.2rem; }
header[data-testid="stHeader"] { display: none; }
div[data-testid="stToolbar"] { display: none; }
footer { display: none; }

div[data-testid="stVerticalBlockBorderWrapper"]{
  background: #ffffff;
  border: 1px solid rgba(0,0,0,.06);
  border-radius: 18px;
  padding: 14px 16px;
  box-shadow: 0 10px 25px rgba(0,0,0,.04);
}

.stButton button, .stLinkButton a{
  border-radius: 14px !important;
  padding: 0.65rem 1rem !important;
  font-weight: 600 !important;
}

div[data-baseweb="input"] input{
  border-radius: 14px !important;
}

[data-testid="stChatMessage"]{
  border-radius: 18px;
  padding: 6px 2px;
}

.ptc-accent {
  height: 4px;
  width: 64px;
  background: #b22222;
  border-radius: 999px;
  margin: 8px 0 14px 0;
}
</style>
""", unsafe_allow_html=True)

# --- Moderner Header ---
st.markdown(f"""
<div style="display:flex; flex-direction:column; gap:6px; margin-bottom: 8px;">
  <div style="font-size:28px; font-weight:800; letter-spacing:-0.02em;">
    Online-Beratung
  </div>
  <div style="font-size:14px; color:#555;">
    {STUDIO["name"]} · Schnell Antworten zu Probetraining, Kursen, Öffnungszeiten & Mitgliedschaft
  </div>
  <div class="ptc-accent"></div>
</div>
""", unsafe_allow_html=True)

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

# --- Actionbar als Card ---
with st.container(border=True):
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

# =========================================================
# ADMIN-BEREICH (nur über ?admin=1)
# =========================================================
admin = st.query_params.get("admin") == "1"
if admin:
    with st.expander("📈 Gesamt-Statistik (alle Nutzer) – Admin", expanded=True):
        store = get_global_stats_store()
        data = store["data"]

        intents = data.get("intents", {})
        fallback = data.get("fallback", 0)
        updated_at = data.get("updated_at")

        if intents:
            st.write("**Top-Intents (gesamt):**")
            for k, v in sorted(intents.items(), key=lambda x: x[1], reverse=True):
                st.write(f"• {k}: {v}")
        else:
            st.write("Noch keine Daten.")

        st.write("---")
        st.write(f"❓ Fallback (gesamt): {fallback}")
        if updated_at:
            st.caption(f"Letztes Update: {updated_at}")

        st.download_button(
            "📥 Gesamt-Stats als JSON",
            data=json.dumps(data, ensure_ascii=False, indent=2),
            file_name="ptc_global_stats.json",
            mime="application/json",
        )

    with st.expander("🧾 Fragen-Log (alle Anfragen) – Admin", expanded=True):
        rows = read_questions_log(limit=300)
        if not rows:
            st.write("Noch keine geloggten Fragen.")
        else:
            st.caption("Neueste Einträge zuerst. Emails/Telefonnummern werden im Log grob maskiert.")
            for r in rows:
                ts = r.get("ts", "")
                intent = r.get("intent", "")
                goal = r.get("goal", None)
                text = r.get("text", "")
                label = f"{ts} · intent={intent}"
                if goal:
                    label += f" · goal={goal}"
                st.write(f"**{label}**")
                st.write(text)
                st.write("---")

        # Download des kompletten Logs
        if os.path.exists(QUESTIONS_LOG):
            with open(QUESTIONS_LOG, "r", encoding="utf-8") as f:
                log_data = f.read()
            st.download_button(
                "📥 Fragen-Log als JSONL",
                data=log_data,
                file_name="ptc_questions_log.jsonl",
                mime="application/jsonl",
            )

# Chat-Verlauf
for msg in st.session_state.chat:
    with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
        st.write(msg["content"])

# Input
user_input = st.chat_input("Ihre Frage (z.B. Probetraining, Kurse, Öffnungszeiten, Mitgliedschaft)")
if user_input:
    st.session_state.chat.append({"role": "user", "content": user_input})

    answer = route_and_answer(user_input)
    st.session_state.chat.append({"role": "assistant", "content": answer})

    st.rerun()

st.markdown("---")
st.markdown(f"**Direkter Kontakt:** [{STUDIO['phone_display']}]({STUDIO['phone_tel']})")
