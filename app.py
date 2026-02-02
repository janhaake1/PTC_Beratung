import re
import unicodedata
import streamlit as st

# =========================================================
# KONFIGURATION – PTC FITNESSSTUDIO HILDESHEIM
# =========================================================
STUDIO = {
    "name": "PTC Fitnessstudio Hildesheim",
    "phone_display": "05121 2819760",
    "phone_tel": "tel:+4951212819760",
    "opening_hours": (
        "Montag, Mittwoch, Freitag: 08:00–20:00 Uhr\n"
        "Dienstag & Donnerstag: 09:00–20:00 Uhr\n"
        "Samstag: 10:00–14:00 Uhr\n"
        "Sonntag: 11:00–15:00 Uhr"
    ),
    "address": "Rudolf-Diesel-Straße 8, 31137 Hildesheim",
    "parking": "Direkt am Studio stehen ausreichend kostenlose Parkplätze zur Verfügung.",
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

PROBETRAINING = {
    "duration": "in der Regel 60 Minuten",
    "included": "mit persönlicher Betreuung",
    "options": "je nach Wunsch Geräte-Training und/oder Kurse",
    "price": "kostenlos",
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
# HILFSFUNKTIONEN (Textbausteine)
# =========================================================
def cta_short() -> str:
    return f"📞 Telefon: {STUDIO['phone_display']} ({STUDIO['phone_tel']})"

def cta_full() -> str:
    return (
        f"📞 Telefon: {STUDIO['phone_display']} ({STUDIO['phone_tel']})\n"
        f"📍 Adresse: {STUDIO['address']}\n"
        f"🕒 Öffnungszeiten:\n{STUDIO['opening_hours']}"
    )

def probetraining_block() -> str:
    return (
        "Probetraining:\n"
        f"• Dauer: {PROBETRAINING['duration']}\n"
        f"• Betreuung: {PROBETRAINING['included']}\n"
        f"• Inhalt: {PROBETRAINING['options']}\n"
        f"• Kosten: {PROBETRAINING['price']}"
    )

def parking_block() -> str:
    return f"🚗 Parken: {STUDIO['parking']}"

def normalize(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text

def safety_note_if_needed(user_text: str) -> str:
    t = normalize(user_text)
    medical_markers = [
        "diagnose", "arzt", "operation", "bandscheibe", "herz", "blutdruck",
        "schmerz", "schmerzen", "verletzung", "physio", "krankheit"
    ]
    if any(m in t for m in medical_markers):
        return (
            "Hinweis: Ich kann keine medizinische Einschätzung geben. "
            "Wenn Sie akute oder starke Beschwerden haben, lassen Sie das bitte ärztlich abklären. "
        )
    return ""

# =========================================================
# INTENT-ERKENNUNG (robust, Multi-Intent)
# =========================================================
INTENT_PATTERNS = {
    # NEU: Unsicherheit/Einstiegshürde (sehr wichtig)
    "einstieg_unsicherheit": [
        r"lange(r)? keinen sport",
        r"lange(r)? nicht trainiert",
        r"lange(r)? keinen sport gemacht",
        r"unsportlich",
        r"anfanger",
        r"anfaenger",
        r"neuling",
        r"wieder anfangen",
        r"wieder starten",
        r"lange pause",
    ],
    # NEU: Orientierungslosigkeit („wo anfangen?“)
    "orientierungslosigkeit": [
        r"weiss nicht wo ich anfangen soll",
        r"weiß nicht wo ich anfangen soll",
        r"wo anfangen",
        r"wie anfangen",
        r"wie starte ich",
        r"keine ahnung wie starten",
        r"unsicher wie anfangen",
    ],

    "preise": [
        r"\bpreis(e)?\b", r"\bkosten\b", r"\bbeitrag\b", r"\bmitglied(schaft)?\b", r"\babo\b", r"\bvertrag\b", r"\btarif\b"
    ],
    "probetraining": [
        r"\bprobetraining\b", r"\bprobe\b", r"\btesten\b", r"\btermin\b", r"\bkennenlernen\b", r"\berst(es)? mal\b"
    ],
    "kurse": [
        r"\bkurse?\b", r"\bjumping\b", r"\bbauch\b", r"\bbeine\b", r"\bpo\b", r"\bdance\b", r"\bvibration\b", r"\bplattenkurs\b"
    ],
    "infos": [
        r"\boffnungszeit(en)?\b", r"\böffnungszeit(en)?\b", r"\bgeoffnet\b", r"\bgeöffnet\b", r"\bwann\b", r"\buhr\b",
        r"\badresse\b", r"\banfahrt\b", r"\bwo\b", r"\bparken\b", r"\bparkplatz\b"
    ],

    "ziel_abnehmen": [
        r"\babnehmen\b", r"\bgewicht\b", r"\bfett\b", r"\bkalorien\b", r"\bfigur\b"
    ],
    "ziel_ruecken": [
        r"\brucken\b", r"\brücken\b", r"\bhaltung\b", r"\bverspann\b"
    ],
    "ziel_muskel": [
        r"\bmuskel\b", r"\bkraft\b", r"\bhypertroph\b", r"\baufbau\b"
    ],
    "ziel_fitness": [
        r"\bfitter\b", r"\bausdauer\b", r"\bkondition\b", r"\bgesund(heit)?\b", r"\bstress\b"
    ],
}

# Priorität: erst Unsicherheit/Orientierung, dann Ziele, dann Kurse/Infos, dann Probetraining/Preise
INTENT_PRIORITY = [
    "einstieg_unsicherheit",
    "orientierungslosigkeit",
    "ziel_ruecken",
    "ziel_abnehmen",
    "ziel_muskel",
    "ziel_fitness",
    "kurse",
    "infos",
    "probetraining",
    "preise",
]

def detect_intents(user_text: str) -> list[str]:
    t = normalize(user_text)
    hits = []
    for intent, patterns in INTENT_PATTERNS.items():
        for p in patterns:
            if re.search(p, t):
                hits.append(intent)
                break

    hits = list(dict.fromkeys(hits))
    hits.sort(key=lambda x: INTENT_PRIORITY.index(x) if x in INTENT_PRIORITY else 999)

    # Top-2 reichen, damit es kurz bleibt
    return hits[:2] if hits else ["unklar"]

# =========================================================
# SESSION-MEMORY (wirkt „mitdenkend“)
# =========================================================
def init_memory():
    if "memory" not in st.session_state:
        st.session_state.memory = {
            "goal": None,
            "asked_price": False,
            "asked_courses": False,
            "asked_infos": False,
            "asked_probetraining": False,
        }

def set_goal_from_intents(intents: list[str]):
    if "ziel_abnehmen" in intents:
        st.session_state.memory["goal"] = "abnehmen"
    elif "ziel_ruecken" in intents:
        st.session_state.memory["goal"] = "rücken stärken"
    elif "ziel_muskel" in intents:
        st.session_state.memory["goal"] = "muskelaufbau"
    elif "ziel_fitness" in intents:
        st.session_state.memory["goal"] = "allgemeine fitness"

def goal_phrase() -> str:
    g = st.session_state.memory.get("goal")
    return f"Da Ihr Ziel „{g}“ ist, " if g else ""

# =========================================================
# KURS-EMPFEHLUNG (ohne Kurszeiten, außer wenn explizit gefragt)
# =========================================================
def recommend_courses_for_goal(goal: str) -> list[str]:
    if goal == "abnehmen":
        return ["Jumping", "Bauch, Beine, Po", "Fitness-Dance"]
    if goal == "rücken stärken":
        return ["Vibrationstraining (ruhiger Einstieg)", "Rumpfstabilität im Geräte-Training (angepasst)"]
    if goal == "muskelaufbau":
        return ["Freihantelbereich (Technik & Progression mit Betreuung)", "Körperanalyse zur Verlaufskontrolle"]
    if goal == "allgemeine fitness":
        return ["Fitness-Dance", "Jumping", "Vibrationstraining"]
    return []

def course_plan_compact() -> str:
    lines = []
    for day, items in COURSE_PLAN.items():
        for time, title in items:
            lines.append(f"• {day}: {time} {title}")
    return "\n".join(lines)

# =========================================================
# ANTWORT-ENGINE (kurz, beratend, No-Gos sicher)
# =========================================================
def build_answer(user_text: str, intents: list[str]) -> str:
    init_memory()
    set_goal_from_intents(intents)

    # Flags
    if "preise" in intents:
        st.session_state.memory["asked_price"] = True
    if "kurse" in intents:
        st.session_state.memory["asked_courses"] = True
    if "infos" in intents:
        st.session_state.memory["asked_infos"] = True
    if "probetraining" in intents:
        st.session_state.memory["asked_probetraining"] = True

    safety = safety_note_if_needed(user_text)
    goal = st.session_state.memory.get("goal")

    # 0) Einstiegshürde / Unsicherheit (immer kurz, keine Kurszeiten)
    if "einstieg_unsicherheit" in intents:
        return (
            "Das ist überhaupt kein Problem.\n\n"
            "Wir legen großen Wert auf einen ruhigen, gut betreuten Einstieg und passen das Training individuell an – ohne Überforderung.\n\n"
            "Dafür eignet sich ein kostenloses Probetraining mit persönlicher Betreuung sehr gut. "
            "So können Sie in Ruhe starten und herausfinden, was für Sie passt.\n\n"
            f"{cta_short()}"
        ).strip()

    # 0b) Orientierungslosigkeit („wo anfangen?“) – ebenfalls kurz, keine Kurszeiten
    if "orientierungslosigkeit" in intents:
        return (
            "Das geht vielen so – und ist überhaupt kein Problem.\n\n"
            "Wir unterstützen Sie dabei, einen passenden Einstieg zu finden: ruhig, strukturiert und mit persönlicher Betreuung.\n\n"
            "Ein kostenloses Probetraining ist dafür ideal. So können Sie in Ruhe starten und wir besprechen gemeinsam, was am besten zu Ihrem Alltag passt.\n\n"
            f"{cta_short()}"
        ).strip()

    # 1) Ziele (kurz + Empfehlung, aber KEINE Kurszeiten unless „kurse“ gefragt)
    if any(i.startswith("ziel_") for i in intents) and goal:
        parts = []
        parts.append(
            f"{safety}{goal_phrase()}kann ein ruhiger, gut betreuter Einstieg sehr sinnvoll sein. "
            "Wir achten auf saubere Ausführung und steigern nach und nach."
        )

        rec = recommend_courses_for_goal(goal)
        if rec:
            parts.append("Passend dazu kommen bei uns oft diese Optionen infrage: " + ", ".join(rec) + ".")

        # Probetraining als nächster Schritt
        parts.append("Wenn Sie möchten, können Sie das bei einem kostenlosen Probetraining in Ruhe kennenlernen.")
        parts.append(probetraining_block())
        parts.append("Für die Anmeldung melden Sie sich am besten kurz telefonisch.")
        parts.append(cta_full())
        return "\n\n".join(parts).strip()

    # 2) Kurse (hier sind Zeiten erlaubt)
    if "kurse" in intents:
        parts = []
        parts.append("Gern – hier ein Überblick über unseren aktuellen Kursplan:")
        parts.append(course_plan_compact())

        if goal:
            rec = recommend_courses_for_goal(goal)
            if rec:
                parts.append(f"{goal_phrase()}würden sich z. B. diese Optionen anbieten: " + ", ".join(rec) + ".")

        parts.append("Wenn Sie möchten, können Sie Kurse auch im Rahmen eines kostenlosen Probetrainings ausprobieren.")
        parts.append(probetraining_block())
        parts.append("Für die Anmeldung melden Sie sich am besten kurz telefonisch.")
        parts.append(cta_full())
        return "\n\n".join(parts).strip()

    # 3) Infos (Öffnungszeiten, Adresse, Parken)
    if "infos" in intents:
        parts = []
        parts.append("Gern – hier die wichtigsten Infos:")
        parts.append(f"📍 Adresse: {STUDIO['address']}")
        parts.append("🕒 Öffnungszeiten:\n" + STUDIO["opening_hours"])
        parts.append(parking_block())
        parts.append("Wenn Sie möchten, können Sie direkt ein kostenloses Probetraining vereinbaren.")
        parts.append("Für die Anmeldung melden Sie sich am besten kurz telefonisch.")
        parts.append(cta_full())
        return "\n\n".join(parts).strip()

    # 4) Probetraining (klar, kurz)
    if "probetraining" in intents:
        parts = []
        parts.append("Sehr gern – ein Probetraining ist ideal, um unser Studio kennenzulernen.")
        parts.append(probetraining_block())
        if goal:
            parts.append(f"{goal_phrase()}können wir im Probetraining genau passend starten – ohne Überforderung.")
        parts.append("Für die Anmeldung melden Sie sich am besten kurz telefonisch.")
        parts.append(cta_full())
        return "\n\n".join(parts).strip()

    # 5) Preise (keine Zahlen, neutral)
    if "preise" in intents:
        parts = []
        parts.append(
            f"{safety}Die Beiträge können je nach Laufzeit und Angebot variieren. "
            "Damit Sie das passende Modell bekommen, empfehle ich Ihnen ein kurzes telefonisches Gespräch oder ein kostenloses Probetraining."
        )
        if goal:
            parts.append(f"{goal_phrase()}wäre ein Probetraining mit Betreuung ein guter Einstieg, um den passenden Rahmen zu finden.")
        else:
            parts.append("Wenn Sie mir Ihr Ziel nennen (z. B. Abnehmen, Rücken stärken, Muskelaufbau), kann ich Ihnen die sinnvollste Option bei uns einordnen.")
        parts.append(probetraining_block())
        parts.append("Für die Anmeldung melden Sie sich am besten kurz telefonisch.")
        parts.append(cta_full())
        return "\n\n".join(parts).strip()

    # 6) Unklar → 1 kurze Rückfrage
    return (
        "Gern helfe ich Ihnen weiter. Geht es bei Ihnen eher um Kurse, Probetraining, Öffnungszeiten/Anfahrt oder Mitgliedschaft?\n\n"
        "Alternativ erreichen Sie uns direkt telefonisch.\n\n"
        f"{cta_full()}"
    ).strip()

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
        st.session_state.memory = {"goal": None, "asked_price": False, "asked_courses": False, "asked_infos": False, "asked_probetraining": False}
        st.rerun()

with col2:
    st.link_button("📞 Anrufen", STUDIO["phone_tel"])

with col3:
    g = st.session_state.memory.get("goal")
    if g:
        st.info(f"Merke ich mir: Ziel = {g}")

# Verlauf anzeigen
for msg in st.session_state.chat:
    with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
        st.write(msg["content"])

# Input
user_input = st.chat_input("Ihre Frage (z.B. Probetraining, Kurse, Öffnungszeiten, Mitgliedschaft)")
if user_input:
    st.session_state.chat.append({"role": "user", "content": user_input})

    intents = detect_intents(user_input)
    answer = build_answer(user_input, intents)

    st.session_state.chat.append({"role": "assistant", "content": answer})

    with st.chat_message("assistant"):
        st.write(answer)

st.markdown("---")
st.markdown(f"**Direkter Kontakt:** [{STUDIO['phone_display']}]({STUDIO['phone_tel']})")
