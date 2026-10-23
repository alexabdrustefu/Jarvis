
try:
    import speech_recognition as sr
except ImportError:
    sr = None


class VoiceInput:
    """Acquisisce la voce dal microfono e la converte in testo."""

    def __init__(self, language="it-IT"):
        self.recognizer = sr.Recognizer() if sr else None
        self.Microphone = sr.Microphone if sr else None
        self.language = language

    def listen(self):
        """Ascolta una frase e restituisce il testo riconosciuto."""
        if sr is None:
            raise RuntimeError("speech_recognition non è installato.")
        with sr.Microphone() as source:
            print("JARVIS: Ti ascolto...")
            self.recognizer.adjust_for_ambient_noise(
                source,
                duration=0.5,
            )
            try:
                audio = self.recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=10,
                )
            except sr.WaitTimeoutError:
                print("JARVIS: Non ho sentito nessuna voce.")
                return None

        try:
            text = self.recognizer.recognize_google(
                audio,
                language=self.language,
            )
            print(f"Tu (voce): {text}")
            return text

        except sr.UnknownValueError:
            print("JARVIS: Non sono riuscito a capire.")
            return None

        except sr.RequestError as error:
            print(f"JARVIS: Errore nel servizio di riconoscimento: {error}")
            return None


if __name__ == "__main__":
    voice = VoiceInput()
    print("Test microfono: parla dopo il segnale visivo.")
    result = voice.listen()
    print("Test completato:", result)
