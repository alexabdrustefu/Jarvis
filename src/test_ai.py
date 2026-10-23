from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key or api_key == "inserisci_la_tua_chiave_qui":
    raise RuntimeError(
        "GROQ_API_KEY non configurata nel file .env"
    )

client = Groq(api_key=api_key)

response = client.chat.completions.create(
    # Verificheremo la disponibilità del modello
    # sulla console Groq se questo nome non è accettato.
    model="openai/gpt-oss-20b",
    messages=[
        {
            "role": "system",
            "content": (
                "Ti chiami JARVIS. Sei un assistente "
                "personale intelligente, preciso e "
                "collaborativo. Rispondi in italiano."
            ),
        },
        {
            "role": "user",
            "content": "Presentati e spiegami cosa puoi fare.",
        },
    ],
)

print("\nJARVIS:")
print(response.choices[0].message.content)