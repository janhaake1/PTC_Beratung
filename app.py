import re
import unicodedata
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
    "Wellness",
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

def matches_any(text: str, patterns: list[str]) -> bool:
    for p in patterns:
        if re.search(p, text):
            return True
    return False

# =========================================================
# Session-Memory (optional, wirkt „mitdenkend“)
# =========================================================
def init_memory():
    if "memory" not in st.session_state:
        st.session_state.memory = {"goal": None}

def set_goal(goal: str | None):
    st.session_state.memory["goal"] = goal

def get_goal() -> str | None:
    return st.session_state.memory.get("goal")

def goal_phrase() -> str:
    g = get_goal()
    return f"Da Ihr Ziel „{g}“ ist, " if g else ""

# =========================================================
# Ziel-Erkennung (leicht erweiterbar)
# =========================================================
GOAL_PATTERNS = [
    ("abnehmen", [r"\babnehmen\b", r"\bgewicht\b", r"\bfett\b", r"\bfigur\b", r"\bkalorien\b"]),
    ("muskelaufbau", [r"\bmuskel\b", r"\bkraft\b", r"\baufbau\b", r"\bhypertroph\b"]),
    ("rücken stärken", [r"\bruck(en)?\b", r"\bhaltung\b", r"\bverspann"]),
    ("allgemeine fitness", [r"\bfitter\b", r"\bausdauer\b", r"\bkondition\b", r"\bfit\b", r"\bgesund(heit)?\b"]),
]

def infer_goal(text_norm: str) -> str | None:
    for goal, pats in GOAL_PATTERNS:
        if matches_any(text_norm, pats):
            return goal
    return None

def recommend_for_goal(goal: str) -> list[str]:
    # neutral, keine Versprechen/Guarantees
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
# Antwort-Handler (hier steckt die „Intelligenz“)
# =========================================================
def answer_unsicherheit(_text_norm: str) -> str:
    return (
        "Das ist überhaupt kein Problem.\n\n"
        "Wir legen großen Wert auf einen ruhigen, gut betreuten Einstieg und passen das Training individuell an – ohne Überforderung.\n\n"
        "Ein persönliches Beratungsgespräch oder ein kostenloses Probetraining ist dafür ideal.\n\n"
        f"{cta_short()}"
    )

def answer_orientierung(_text_norm: str) -> str:
    return (
        "Das geht vielen so – und ist überhaupt kein Problem.\n\n"
        "Wir unterstützen Sie dabei, einen passenden Einstieg zu finden: ruhig, strukturiert und mit persönlicher Betreuung.\n\n"
        "Am besten eignet sich dafür ein persönliches Beratungsgespräch oder ein kostenloses Probetraining.\n\n"
        f"{cta_short()}"
    )

def answer_preise(text_norm: str) -> str:
    # No-Go: keine Zahlen nennen
    goal = infer_goal(text_norm) or get_goal()
    if goal:
        set_goal(goal)

    parts = [
        "Die Mitgliedsbeiträge können je nach Laufzeit und Trainingsumfang variieren.",
        "Am sinnvollsten ist ein kurzes persönliches Beratungsgespräch oder ein kostenloses Probetraining, damit wir gemeinsam das passende Angebot für Sie finden.",
    ]
    if goal:
        parts.append(f"{goal_phrase()}können wir im Probetraining/Beratungsgespräch genau passend starten.")

    parts.append(probetraining_block())
    parts.append("Für die Anmeldung melden Sie sich am besten kurz telefonisch.")
    parts.append(cta_full())
    return "\n\n".join(parts)

def answer_medizin(text_norm: str) -> str:
    # No-Go: keine medizinische Aussage
    goal = infer_goal(text_norm) or get_goal()
    if goal:
        set_goal(goal)

    return (
        "Bei Beschwerden ist ein gut betreuter Einstieg besonders wichtig.\n\n"
        "Hinweis: Ich kann keine medizinische Einschätzung geben. Wenn Sie akute oder starke Beschwerden haben, lassen Sie das bitte ärztlich abklären.\n\n"
        "Am besten eignet sich dafür ein persönliches Beratungsgespräch oder ein kostenloses Probetraining – dann können wir in Ruhe besprechen, wie ein sinnvoller Einstieg aussehen kann.\n\n"
        f"{cta_short()}"
    )

def answer_infos(_text_norm: str) -> str:
    return (
        "Gern – hier die wichtigsten Infos:\n\n"
        f"📍 Adresse: {STUDIO['address']}\n\n"
        f"🕒 Öffnungszeiten:\n{STUDIO['opening_hours']}\n\n"
        f"🚗 Parken: {STUDIO['parking']}\n\n"
        "Wenn Sie möchten, können Sie direkt ein persönliches Beratungsgespräch oder ein kostenloses Probetraining vereinbaren.\n\n"
        f"{cta_short()}"
    )

def answer_probetraining(text_norm: str) -> str:
    goal = infer_goal(text_norm) or get_goal()
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

def answer_features(_text_norm: str) -> str:
    return (
        "Gern – hier ein Überblick über unsere Ausstattung/Angebote:\n\n"
        "• " + "\n• ".join(FEATURES) + "\n\n"
        "Wenn Sie möchten, können Sie das bei einem persönlichen Beratungsgespräch oder einem kostenlosen Probetraining in Ruhe kennenlernen.\n\n"
        f"{cta_short()}"
    )

def answer_kurse(text_norm: str) -> str:
    # Wenn spezifischer Kurs gefragt ist, trotzdem den Plan liefern (kurz)
    goal = infer_goal(text_norm) or get_goal()
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

def answer_default(_text_norm: str) -> str:
    return (
        "Gern helfe ich Ihnen weiter. Geht es bei Ihnen eher um Probetraining/Beratung, Kurse, Öffnungszeiten/Anfahrt oder Mitgliedschaft?\n\n"
        f"{cta_short()}"
    )

# =========================================================
# INTENT-REGISTRY (HIER pflegst du später nur Patterns)
# Reihenfolge = Priorität (oben wird zuerst geprüft)
# =========================================================
INTENTS = [
    {
        "name": "medizin_beschwerden",
        "patterns": [
            r"\bruckenschmerz(en)?\b", r"\bruck(en)?\b", r"\bschmerz(en)?\b", r"\bbeschwerden\b",
            r"\bverletzung\b", r"\bbandscheibe\b", r"\bphysio\b", r"\barzt\b", r"\boperation\b"
        ],
        "handler": answer_medizin,
    },
    {
        "name": "preise_kosten",
        "patterns": [
            r"\bpreis(e)?\b", r"\bkosten\b", r"\bbeitrag\b", r"\bmitglied(schaft)?\b", r"\babo\b", r"\bvertrag\b", r"\btarif\b",
            r"wie viel", r"wieviel", r"monat", r"monatlich", r"pro monat", r"euro", r"€"
        ],
        "handler": answer_preise,
    },
    {
        "name": "einstieg_unsicherheit",
        "patterns": [
            r"lange(r)? keinen sport", r"lange(r)? nicht trainiert", r"lange(r)? keinen sport gemacht",
            r"unsportlich", r"anfanger", r"anfaenger", r"neuling", r"wieder anfangen", r"wieder starten", r"lange pause"
        ],
        "handler": answer_unsicherheit,
    },
    {
        "name": "orientierung",
        "patterns": [
            r"weiß nicht wo ich anfangen soll", r"weiss nicht wo ich anfangen soll",
            r"wo anfangen", r"wie anfangen", r"wie starte ich", r"keine ahnung", r"unsicher wie anfangen"
        ],
        "handler": answer_orientierung,
    },
    {
        "name": "probetraining_beratung",
        "patterns": [r"\bprobetraining\b", r"\bprobe\b", r"\btesten\b", r"\bkennenlernen\b", r"\bberatung\b", r"\bberatungsgesprach\b", r"\bberatungsgespräch\b"],
        "handler": answer_probetraining,
    },
    {
        "name": "infos_anfahrt_parken_zeiten",
        "patterns": [
            r"\boffnungszeit(en)?\b", r"\böffnungszeit(en)?\b", r"\bgeoffnet\b", r"\bgeöffnet\b",
            r"\badresse\b", r"\banfahrt\b", r"\bwo\b", r"\bparken\b", r"\bparkplatz\b", r"\bsonntag\b", r"\bsamstag\b"
        ],
        "handler": answer_infos,
    },
    {
        "name": "kurse",
        "patterns": [r"\bkurse?\b", r"\bjumping\b", r"\bfitt?ness[- ]dance\b", r"\bbauch\b", r"\bbeine\b", r"\bpo\b", r"\bvibration\b", r"\bplattenkurs\b"],
        "handler": answer_kurse,
    },
    {
        "name": "ausstattung",
        "patterns": [r"\bwellness\b", r"\bsauna\b", r"\binfrarot\b", r"\bmassage\b", r"\bkorperanalyse\b", r"\bkörperanalyse\b", r"\bfrei?hantel\b", r"\bvibration\b", r"\bgera(te|ete)\b", r"\bgeräte\b"],
        "handler": answer_features,
    },
]

def route_and_answer(user_text: str) -> str:
    t = normalize(user_text)

    # Ziel merken, wenn es im Text vorkommt (ohne gleich zu antworten)
    g = infer_goal(t)
    if g:
        set_goal(g)

    # Intent first-match
    for intent in INTENTS:
        if matches_any(t, intent["patterns"]):
            return intent["handler"](t)

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

# Session init
if "chat" not in st.session_state:
    st.session_state.chat = []
init_memory()

# Top actions
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    if st.button("Neues Gespräch"):
        st.session_state.chat = []
        st.session_state.memory = {"goal": None}
        st.rerun()

with col2:
    st.link_button("📞 Anrufen", STUDIO["phone_tel"])

with col3:
    g = get_goal()
    if g:
        st.info(f"Merke ich mir: Ziel = {g}")

# Verlauf anzeigen (normaler Chat-Verlauf)
for msg in st.session_state.chat:
    with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
        st.write(msg["content"])

# Input
user_input = st.chat_input("Ihre Frage (z.B. Probetraining, Kurse, Öffnungszeiten, Mitgliedschaft)")
if user_input:
    st.session_state.chat.append({"role": "user", "content": user_input})
    answer = route_and_answer(user_input)
    st.session_state.chat.append({"role": "assistant", "content": answer})

    with st.chat_message("assistant"):
        st.write(answer)

st.markdown("---")
st.markdown(f"**Direkter Kontakt:** [{STUDIO['phone_display']}]({STUDIO['phone_tel']})")
