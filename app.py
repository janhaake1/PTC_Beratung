import re
import unicodedata
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
            # App soll nicht crashen, sondern Fehler anzeigen
            st.error(f"Regex-Fehler im Pattern: {p}\n{e}")
    return False

# =========================================================
# Session-Memory
# =========================================================
def init_memory():
    if "memory" not in st.session_state:
        st.session_state.memory = {"goal": None}

def set_goal(goal: Optional[str]):
    st.session_state.memory["goal"] = goal

def get_goal() -> Optional[str]:
    return st.session_state.memory.get("goal")

def goal_phrase() -> str:
    g = get_goal()
    return f"Da Ihr Ziel „{g}“ ist, " if g else ""

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
        "Am sinnvollsten ist ein kurzes persönliches Beratungsgespräch oder ein kostenloses Probetraining, damit wir gemeinsam das passende Angebot für Sie finden.",
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
        "Hinweis: Ich kann keine medizinische Einschätzung geben. Wenn Sie akute oder starke Beschwerden haben, lassen Sie das bitte ärztlich abklären.\n\n"
        "Am besten eignet sich dafür ein persönliches Beratungsgespräch oder ein kostenloses Probetraining – dann können wir in Ruhe besprechen, wie ein sinnvoller Einstieg aussehen kann.\n\n"
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
        ],
        "handler": answer_preise,
    },
    {
        "name": "duschen_umkleide_spinde_getraenke",
        "patterns": [
            r"\bdusch(e|en)\b", r"\bduschen vorhanden\b", r"\bgibt es duschen\b", r"\bduschmoglichkeit\b", r"\bduschmöglichkeit\b",
            r"\bduschraum\b", r"\bmit dusche\b",
            r"\bumkleide\b", r"\bumkleiden\b", r"\bumkleideraum\b", r"\bkabine\b", r"\bumziehen\b", r"\bwo umziehen\b",
            r"\bspind(e)?\b", r"\bschliessfach\b", r"\bschließfach\b", r"\bschliessfaecher\b", r"\bschließfächer\b",
            r"\bspindschloss\b", r"\babschliessbar\b", r"\babschließbar\b", r"\bwerte wegschliessen\b", r"\bwerte wegschließen\b",
            r"\bgetrank(e)?\b", r"\bgetränk(e)?\b", r"\bwasser\b", r"\btrinken\b", r"\bgetrankeautomat\b", r"\bgetränkeautomat\b",
            r"\bflasche auffullen\b", r"\bflasche auffüllen\b", r"\bwasserstation\b", r"\bdrink\b",
            r"\bdusche und spind\b", r"\bumkleide und dusche\b", r"\bspind und dusche\b",
        ],
        "handler": answer_facilities,
    },
    {
        "name": "wellness_infrarot_massagesessel",
        "patterns": [
            r"\bwellness\b", r"\binfrarot\b", r"\binfrarotkabine\b", r"\bwaermekabine\b", r"\bwärmekabine\b",
            r"\bsauna\b", r"\bmassage\b", r"\bmassagesessel\b", r"\bmassagestuhl\b",
            r"\bentspann(en|ung)\b", r"\bregeneration\b", r"\brecovery\b", r"\berholen\b",
            r"\bwie funktioniert infrarot\b", r"\bwie funktioniert der massagesessel\b",
        ],
        "handler": answer_wellness,
    },
    {
        "name": "zahlung_kartenzahlung",
        "patterns": [
            r"\bkartenzahlung\b", r"\bkarte\b", r"\bec\b", r"\bgirocard\b", r"\bvisa\b", r"\bmastercard\b",
            r"\bapple pay\b", r"\bgoogle pay\b", r"\bkontaktlos\b", r"\b(nur )?bar\b", r"\bbarzahlung\b",
            r"\bkann ich mit karte zahlen\b", r"\bkann man mit karte zahlen\b", r"\bzahlungsmoglichkeiten\b", r"\bzahlungsmöglichkeiten\b",
        ],
        "handler": answer_payment,
    },
    {
        "name": "mindestalter_nach_absprache",
        "patterns": [
            r"\bmindestalter\b", r"\bab wieviel jahren\b", r"\bab wie viel jahren\b", r"\bab wann\b",
            r"\bjugendliche\b", r"\bjugend\b", r"\bkind\b", r"\bkinder\b",
            r"\bdarf ich als schuler\b", r"\bdarf ich als schüler\b", r"\bazubi\b", r"\bschuler\b", r"\bschüler\b",
            r"\bnach absprache\b",
        ],
        "handler": answer_age,
    },
    {
        "name": "barrierefreiheit",
        "patterns": [
            r"\bbarrierefrei\b", r"\brollstuhl\b", r"\brolli\b", r"\baufzug\b", r"\bstufen\b", r"\btreppe\b",
            r"\bbehindertengerecht\b", r"\b(zugaenglich|zugänglich)\b", r"\bebenerdig\b",
        ],
        "handler": answer_accessibility,
    },
    {
        "name": "ablauf_probetraining",
        "patterns": [
            r"\bablauf\b", r"\bwie laeuft\b", r"\bwie läuft\b", r"\bwie funktioniert probetraining\b",
            r"\bwie ist probetraining\b", r"\bwas passiert im probetraining\b", r"\bersttermin\b",
            r"\beinfuehrung\b", r"\beinführung\b", r"\beinweisung\b", r"\btrainer zeigt\b",
        ],
        "handler": lambda _t: (
            "Gern: Im Probetraining lernen Sie das Studio in Ruhe kennen und wir schauen gemeinsam, was zu Ihren Zielen passt.\n\n"
            f"{probetraining_block()}\n\n"
            "Für die Anmeldung melden Sie sich am besten kurz telefonisch.\n\n"
            f"{cta_short()}"
        ),
    },
    {
        "name": "mitbringen_probetraining",
        "patterns": [
            r"was (muss|soll) ich mitbringen", r"\bmitbringen\b", r"\bhandtuch\b", r"\bturnschuhe\b",
            r"\bsportsachen\b", r"\bkleidung\b", r"\bwas brauche ich\b", r"\bwas mitnehmen\b",
            r"\btrainingsschuhe\b", r"\bsaubere schuhe\b", r"\bgetrank\b", r"\bgetränk\b",
        ],
        "handler": lambda _t: (
            "Für ein Probetraining reichen in der Regel bequeme Sportsachen, saubere Hallenschuhe und ein Handtuch. "
            "Etwas zu trinken ist ebenfalls sinnvoll.\n\n"
            "Wenn Sie möchten, können Sie direkt ein persönliches Beratungsgespräch oder ein kostenloses Probetraining vereinbaren.\n\n"
            f"{cta_short()}"
        ),
    },
    {
        "name": "anmeldung_termin",
        "patterns": [
            r"\banmelden\b", r"\banmeldung\b", r"\btermin\b", r"\bbuchen\b", r"\breservier(en|ung)\b",
            r"\bprobetraining anmelden\b", r"\bwie anmelden\b", r"\bwie buche\b", r"\bwie reserviere\b",
            r"\bberatungstermin\b",
        ],
        "handler": lambda _t: (
            "Gern – am einfachsten vereinbaren Sie ein persönliches Beratungsgespräch oder ein kostenloses Probetraining telefonisch.\n\n"
            f"{cta_short()}"
        ),
    },
    {
        "name": "auslastung_stosszeiten",
        "patterns": [
            r"\bvoll\b", r"\bleer\b", r"\bauslastung\b", r"\bstosszeit(en)?\b", r"\bstoßzeit(en)?\b",
            r"\bwann ist wenig los\b", r"\bwann ist es ruhig\b", r"\bwann ist es voll\b",
            r"\bmorgens\b", r"\babends\b", r"\bmittags\b", r"\bfeierabend\b",
        ],
        "handler": lambda _t: (
            "Das hängt oft vom Wochentag und der Uhrzeit ab. Wenn Sie mir sagen, wann Sie typischerweise trainieren möchten, kann ich es besser einordnen.\n\n"
            "Gern können Sie auch ein kostenloses Probetraining/kurzes Beratungsgespräch vereinbaren – dann finden wir gemeinsam ein passendes Zeitfenster.\n\n"
            f"{cta_short()}"
        ),
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
            r"\badresse\b", r"\banfahrt\b", r"\bwo seid ihr\b", r"\bwo genau\b", r"\bstandort\b",
            r"\bparken\b", r"\bparkplatz\b", r"\bsonntag\b", r"\bsamstag\b",
        ],
        "handler": answer_infos,
    },
    {
        "name": "kurse",
        "patterns": [
            r"\bkurse?\b", r"\bjumping\b", r"\bjumping.*wann\b", r"\bwann.*jumping\b", r"\bzeiten.*jumping\b",
            r"\bfitt?ness[- ]dance\b", r"\bbauch\b", r"\bbeine\b", r"\bpo\b", r"\bvibration\b", r"\bplattenkurs\b",
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
    t = normalize(user_text)

    g = infer_goal(t)
    if g:
        set_goal(g)

    for intent in INTENTS:
        patterns = intent.get("patterns", [])
        if isinstance(patterns, list) and matches_any(t, patterns):
            handler = intent.get("handler")
            if callable(handler):
                return handler(t)

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
