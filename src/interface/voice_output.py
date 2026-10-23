import os
import asyncio
import tempfile
try:
    import edge_tts
except ImportError:
    edge_tts = None
try:
    from playsound import playsound
except ImportError:
    playsound = None

class VoiceOutput:
    """Riproduce la voce usando le voci neurali gratuite di Microsoft Edge (Edge-TTS)."""

    def __init__(self, voice="it-IT-IsabellaNeural", rate="+0%"):
        # Voce neurale femminile italiana calda e naturale
        self.voice = voice
        self.rate = rate

    async def _generate_audio(self, text: str, output_file: str):
        if edge_tts is None:
            raise RuntimeError("edge-tts non è installato.")
        communicate = edge_tts.Communicate(text, self.voice, rate=self.rate)
        await communicate.save(output_file)

    def speak(self, text: str):
        if not text or not text.strip():
            return
        if edge_tts is None or playsound is None:
            raise RuntimeError("Per la sintesi vocale installa edge-tts e playsound.")

        print(f"JARVIS: {text}")
        audio_file = None

        try:
            with tempfile.NamedTemporaryFile(
                prefix="jarvis_voice_", suffix=".mp3", delete=False
            ) as temporary_audio:
                audio_file = temporary_audio.name

            # Esegue la generazione asincrona dell'audio
            asyncio.run(self._generate_audio(text, audio_file))
            
            # Riproduce l'audio
            playsound(audio_file)

        except Exception as error:
            print(f"Errore nella riproduzione vocale: {error}")

        finally:
            if audio_file and os.path.exists(audio_file):
                try:
                    os.remove(audio_file)
                except PermissionError:
                    pass


if __name__ == "__main__":
    voice = VoiceOutput()
    voice.speak("Ciao... sono pronta. Ti ascolto, dimmi pure.")
