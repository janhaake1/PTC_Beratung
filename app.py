import os
import streamlit as st

# Optional: OpenAI SDK
# pip install openai
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

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
}

COURSE_PLAN = """
Kursplan:
• Montag
  - 16:45–17:15 Vibrationstraining
  - 17:15–17:45 Fitness-Dance
  - 17:45–18:15 Bauch, Beine, Po
  - 18:15–18:45 Jumping

• Dienstag
  - 11:30–12:00 Vibrationstraining

• Mittwoch
  - 13:30–14:00 Vibrationstraining
  - 16:15–16:45 Vibrationstraining
  - 16:45–17:45 Jumping
  - 17:45–18:15 Bauch, Beine, Po

• Freitag
  - 15:30–16:00 Plattenkurs
"""

PRICE_POLICY = """
Die Beiträge können je nach Laufzeit und Angebot variieren.
Gerne beraten wir Sie persönlich und empfehlen das passende Paket
oder ein Probetraining – abgestimmt auf Ihr Ziel.
"""

# =========================================================
# SYSTEM PROMPT (SIE-FORM)
# =========================================================
SYSTEM_PROMPT = f"""
Sie sind der digitale Beratungsassistent des {STUDIO["name"]}.

REGELN:
- Siezen Sie konsequent.
- Antworten Sie freundlich, professionell und verständlich.
- Maximal 6–8 Sätze.
- Keine medizinische Beratung.
- Bei fehlenden Informationen: maximal 1 Rückfrage stellen.
- Am Ende jeder Antwort immer ein Call-to-Action:
  📞 {STUDIO["phone_display"]} ({STUDIO["phone_tel"]})

WISSENSBASIS:
Preise:
{PRICE_POLICY}

Kurse:
{COURSE_PLAN}

Öffnungszeiten:
{STUDIO["opening_hours"]}

Adresse:
{STUDIO["address"]}

AUFGABE:
Erkennen Sie, ob es um Preise, Probetraining, Kurse,
Öffnungszeiten/Anfahrt oder Trainingsziele (z.B. Rücken, Abnehmen)
geht und antworten Sie passend.
"""

# =========================================================
# INTENT ERKENNUNG (Fallback, ohne KI)
# =========================================================
def detect_intent(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["preis", "kosten", "beitrag", "mitglied", "abo", "vertrag"]):
        return "preise"
    if any(k in t for k in ["probetraining", "testen", "probe", "termin"]):
        return "probetraining"
    if any(k in t for k in ["kurs", "kurse", "jumping", "bauch", "beine", "po", "dance", "vibration"]):
        return "kurse"
    if any(k in t for k in ["öffnungszeit", "wann", "geöffnet", "adresse", "anfahrt", "wo"]):
        return "infos"
    if any(k in t for k in ["rücken", "abnehmen", "fett", "muskel", "fit", "stress"]):
        return "ziel"
    return "unklar"


def fallback_answer(intent: str) -> str:
    phone = f"📞 Telefon: {STUDIO['phone_display']} ({STUDIO['phone_tel']})"

    if intent == "preise":
        return (
            "Die Mitgliedsbeiträge können je nach Laufzeit und Angebot variieren. "
            "Am sinnvollsten ist eine kurze persönliche Beratung oder ein Probetraining, "
            "damit wir das passende Paket für Sie finden.\n\n" + phone
        )

    if intent == "probetraining":
        return (
            "Sehr gerne – ein Probetraining ist ideal, um unser Studio kennenzulernen. "
            "Sagen Sie mir einfach, an welchem Tag es Ihnen zeitlich am besten passt.\n\n" + phone
        )

    if intent == "kurse":
        return (
            "Gerne – hier ein Überblick über unseren aktuellen Kursplan:\n"
            f"{COURSE_PLAN}\n\n"
            "Wenn Sie möchten, empfehle ich Ihnen passende Kurse zu Ihrem Ziel.\n\n" + phone
        )

    if intent == "infos":
        return (
            f"Adresse:\n{STUDIO['address']}\n\n"
            f"Öffnungszeiten:\n{STUDIO['opening_hours']}\n\n" + phone
        )

    if intent == "ziel":
        return (
            "Das klingt gut. Damit wir Sie optimal beraten können: "
            "Wie oft möchten Sie pro Woche trainieren und haben Sie körperliche Einschränkungen?\n\n" + phone
        )

    return (
        "Gerne helfe ich Ihnen weiter. "
        "Geht es bei Ihnen um Preise, Probetraining, Kurse oder Öffnungszeiten?\n\n" + phone
    )

# =========================================================
# KI-ANTWORT (OPTIONAL)
# =========================================================
def llm_answer(messages):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        messages=messages,
        temperature=0.4,
        max_tokens=300,
    )

    return response.choices[0].message.content.strip()

# =========================================================
# STREAMLIT UI
# =========================================================
st.set_page_config(page_title="PTC Online-Beratung", page_icon="💬")

st.title("💬 Online-Beratung – PTC Fitnessstudio Hildesheim")
st.caption(
    "Guten Tag, ich bin der digitale Beratungsassistent des "
    "PTC Fitnessstudios Hildesheim. Wie kann ich Ihnen helfen?"
)

with st.expander("Datenschutz-Hinweis", expanded=False):
    st.write(
        "Bitte geben Sie keine sensiblen Gesundheitsdaten ein. "
        "Bei akuten Beschwerden wenden Sie sich an medizinisches Fachpersonal."
    )

if "chat" not in st.session_state:
    st.session_state.chat = [{"role": "system", "content": SYSTEM_PROMPT}]

for msg in st.session_state.chat:
    if msg["role"] == "system":
        continue
    with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
        st.write(msg["content"])

user_input = st.chat_input("Ihre Frage (z.B. Probetraining, Kurse, Preise)")
if user_input:
    st.session_state.chat.append({"role": "user", "content": user_input})

    answer = llm_answer(st.session_state.chat)

    if not answer:
        intent = detect_intent(user_input)
        answer = fallback_answer(intent)

    st.session_state.chat.append({"role": "assistant", "content": answer})

    with st.chat_message("assistant"):
        st.write(answer)

st.markdown("---")
st.markdown(
    f"**Direkter Kontakt:** "
    f"[{STUDIO['phone_display']}]({STUDIO['phone_tel']})"
)
