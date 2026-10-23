"""Console entry point for the voice assistant."""

import re

from actions.email_actions import EmailActions
from actions.news_actions import NewsActions
from actions.system_actions import SystemActions
from actions.system_actions_audio import SystemActions as AudioSystemActions
from ai.llm_client import LLMClient
from core.command_router import CommandRouter
from interface.voice_input import VoiceInput
from interface.voice_output import VoiceOutput


def main() -> None:
    router = CommandRouter(
        ai=LLMClient(),
        email=EmailActions(),
        news=NewsActions(),
        system=SystemActions(),
        audio=AudioSystemActions(),
    )
    listener = VoiceInput()
    speaker = VoiceOutput()
    speaker.speak(
        "Bentornato Boss, con cosa posso aiutarti oggi? "
        "Ti ricordo che per terminare la conversazione devi dire esci."
    )

    while True:
        try:
            text = listener.listen()
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
