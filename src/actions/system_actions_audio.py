from ctypes import cast, POINTER
import re


def is_volume_command(text: str) -> bool:
    normalized_text = text.casefold()
    if any(word in normalized_text for word in ("muto", "muta", "silenzio")):
        return True

    if normalized_text.strip() in {
        "volume",
        "volume attuale",
        "quanto è il volume",
        "qual è il volume",
        "qual e il volume",
    }:
        return True

    if "volume" not in normalized_text:
        return False

    action_words = (
        "alza",
        "aumenta",
        "abbassa",
        "diminuisci",
        "riduci",
        "reduci",
        "imposta",
        "metti",
        "porta",
        "regola",
        "massimo",
    )
    return (
        any(word in normalized_text for word in action_words)
        or re.search(r"\bvolume\s+(?:a|al|su)\s*\d{1,3}\b", normalized_text) is not None
    )


class SystemActions:
    """Gestisce il controllo delle impostazioni di sistema come il volume audio."""

    def __init__(self):
        self.volume_interface = self._init_volume_interface()

    def _init_volume_interface(self):
        """Inizializza l'interfaccia audio predefinita di Windows."""
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from comtypes import CLSCTX_ALL
        except ImportError as error:
            print(
                "Controllo volume non disponibile: installa le dipendenze "
                f"con 'python -m pip install -r requirements.txt'. Dettaglio: {error}"
            )
            return None

        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None
            )
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            return volume
        except Exception as e1:
            try:
                enumerator = AudioUtilities.GetDeviceEnumerator()
                device = enumerator.GetDefaultAudioEndpoint(0, 1)
                interface = device.Activate(
                    IAudioEndpointVolume._iid_, CLSCTX_ALL, None
                )
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                return volume
            except Exception as e2:
                print(f"Errore nell'inizializzazione audio: {e1} / {e2}")
                return None

    def _get_current_volume_percent(self) -> int:
        """Restituisce il volume attuale in percentuale (0-100)."""
        if not self.volume_interface:
            return 0
        current_scalar = self.volume_interface.GetMasterVolumeLevelScalar()
        return int(round(current_scalar * 100))

    def _set_volume_percent(self, percent: int):
        """Imposta il volume ad una percentuale specifica (0-100)."""
        if not self.volume_interface:
            return
        percent = max(0, min(100, percent))
        scalar = percent / 100.0
        self.volume_interface.SetMasterVolumeLevelScalar(scalar, None)

    def adjust_volume(self, text: str) -> str:
        """Analizza il comando vocale, estrae la quantità (se presente) e regola il volume."""
        if not self.volume_interface:
            return "Non riesco ad accedere ai controlli audio del sistema."

        current_vol = self._get_current_volume_percent()
        text_lower = text.casefold()

        if any(word in text_lower for word in ("muta", "muto", "silenzio")):
            self._set_volume_percent(0)
            return "Audio disattivato."

        target_match = re.search(
            r"\b(?:imposta|metti|porta|regola)\s+(?:il\s+)?volume\s+"
            r"(?:a|al|su)\s*(\d{1,3})\b|\bvolume\s+(?:a|al|su)\s*(\d{1,3})\b",
            text_lower,
        )
        if target_match:
            target = int(next(value for value in target_match.groups() if value))
            new_vol = max(0, min(100, target))
            self._set_volume_percent(new_vol)
            return f"Volume impostato al {new_vol} percento."

        if "al massimo" in text_lower or "massimo" in text_lower:
            self._set_volume_percent(100)
            return "Volume impostato al massimo."

        numbers = re.findall(r"\d+", text_lower)
        amount = int(numbers[0]) if numbers else 10

        if any(
            phrase in text_lower
            for phrase in ("alza", "aumenta", "metti più alto")
        ):
            new_vol = min(100, current_vol + amount)
            self._set_volume_percent(new_vol)
            return f"Fatto, Volume aumentato al {new_vol} percento."

        if any(
            phrase in text_lower
            for phrase in ("abbassa", "diminuisci", "metti più basso", "riduci", "reduci")
        ):
            new_vol = max(0, current_vol - amount)
            self._set_volume_percent(new_vol)
            return f"Fatto, Volume abbassato al {new_vol} percento."

        return f"Il volume attuale è al {current_vol} percento."