"""Console entry point for the voice assistant."""

import re

from composition import create_application
from interface.voice_input import VoiceInput
from interface.voice_output import VoiceOutput


def build_router():
    """Backward-compatible voice entry point backed by the shared composition root."""
    return create_application().router


def main() -> None:
    application = create_application()
    router = application.router
    listener = VoiceInput()
    speaker = VoiceOutput()
    speaker.speak(
        "Bentornato Boss, con cosa posso aiutarti oggi? "
        "Ti ricordo che per terminare la conversazione devi dire esci."
    )

    while True:
        try:
            text = listener.listen()
            due_reminders = router.local_commands.store.take_due()
            for _reminder_id, title, _due_at in due_reminders:
                message = f"Promemoria: {title}."
                print(f"\nJ.A.R.V.I.S.: {message}")
                speaker.speak(message)
            if not text:
                continue

            print(f"\nTu: {text}")
            if text.strip().casefold() in {
                "esci", "termina", "spegni jarvis", "chiudi jarvis",
            }:
                speaker.speak("Va bene. A presto!")
                break

            response = router.handle(text)
            clean_response = re.sub(r"\*\*(.*?)\*\*", r"\1", response)
            clean_response = re.sub(r"\*(.*?)\*", r"\1", clean_response)
            clean_response = re.sub(r"`([^`]*)`", r"\1", clean_response)
            print(f"JARVIS: {clean_response}")
            speaker.speak(clean_response)
        except KeyboardInterrupt:
            print("\nChiusura di JARVIS.")
            break
        except Exception as error:
            print(f"Si è verificato un errore: {error}")
            speaker.speak("Si è verificato un problema. Riprova.")


if __name__ == "__main__":
    main()
