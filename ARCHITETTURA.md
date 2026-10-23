# Architettura e infrastruttura

## Struttura

JARVIS è un'applicazione Python locale, composta da una GUI desktop e da un'interfaccia vocale da terminale. Non usa un server applicativo o container: i due ingressi condividono i servizi applicativi in `src` e chiamano API esterne quando la funzione lo richiede.

```text
JarvisGUI/main.py ─► UI (dashboard/chat) ─┐
                                         ├─► CommandRouter ─► servizi AI, sistema, mail, news, meteo
src/main.py ─► microfono ────────────────┘                          │
       ▲                                                             ├─► API Groq / Gmail / RSS / Open-Meteo
       └──────── voce Edge TTS ◄── risposta ◄───────────────────────┤
                                                                     └─► SQLite locale
```

## Moduli e responsabilità

| Percorso | Responsabilità |
|---|---|
| `src/main.py` | Composizione e ciclo dell'assistente vocale. |
| `src/core/command_router.py` | Dispatcher condiviso per richieste testuali, vocali e GUI; le dipendenze sono iniettate nel costruttore. |
| `src/core/text.py` | Normalizzazione di maiuscole e accenti per confrontare i comandi. |
| `src/core/weather.py` | Interpretazione di date e città nelle richieste meteo. |
| `src/actions/system_actions.py` | Azioni desktop, apertura browser/programmi, ricerca e data/ora; espone una facciata compatibile per il meteo. |
| `src/actions/weather_actions.py` | Geolocalizzazione, geocodifica e richieste meteo a ipwho.is/Open-Meteo; descrizioni meteo condivise. |
| `src/actions/system_actions_audio.py` | Rilevamento comandi e controllo volume master Windows tramite pycaw/COM. |
| `src/actions/email_actions.py` | Elenco e lettura dei messaggi Gmail, oltre all'invio di risposte nel thread originale tramite OAuth. |
| `src/actions/news_actions.py` | Lettura dei feed RSS ANSA e Sky TG24. |
| `src/ai/llm_client.py` | Client Groq, prompt, gestione della conversazione e operazioni sui fatti. |
| `src/interface/` | Cattura microfono e sintesi/riproduzione vocale. |
| `src/memory/` | Accesso SQLite a cronologia e fatti persistenti; la GUI recupera gli ultimi messaggi con timestamp locale. |
| `JarvisGUI/main.py` | Configura il percorso dei moduli condivisi e avvia la GUI. |
| `JarvisGUI/services.py` | Composition root GUI: crea i servizi e il dispatcher condiviso. |
| `JarvisGUI/ui/app.py` | Finestra principale, navigazione animata e contenitore delle viste. |
| `JarvisGUI/ui/dashboard.py` | Dashboard HUD, orologio e scorciatoie che aprono la chat con il comando già avviato. |
| `JarvisGUI/ui/chat_view.py` | Chat testo/voce con storico, fumetti e indicatore animato; sincronizza nuovi messaggi da SQLite ed esegue rete e microfono in worker. |

`src/voice_assistant.py` resta come entry point compatibile con il vecchio avvio e riesporta gli helper meteo, ma delega il ciclo a `src/main.py`.

## Pattern applicati

- **Separazione per responsabilità**: UI, dispatcher, azioni esterne, AI e persistenza sono in moduli distinti.
- **Dependency injection**: `CommandRouter` riceve AI e servizi d'azione dall'esterno; GUI e voce possono usarlo senza duplicare il routing.
- **Composition root**: ciascun punto d'ingresso compone i servizi necessari (`main.py` per la voce, `JarvisGUI/services.py` per la GUI).
- **Facade e compatibilità**: `SystemActions` mantiene l'interfaccia esistente e inoltra le operazioni meteo a `WeatherActions`; il vecchio modulo vocale inoltra al nuovo entry point.
- **Lazy initialization**: Gmail autentica al primo comando email, evitando browser OAuth all'avvio dell'app.

## Flusso delle richieste

1. La voce è trascritta da Google Speech Recognition; la GUI accetta testo o dettatura. Entrambi passano la frase al `CommandRouter`.
2. Il router normalizza gli accenti e instrada comandi specifici a volume, Gmail, news, meteo o azioni Windows. Le altre richieste passano a `LLMClient`.
3. `LLMClient` usa Groq per interpretare le richieste e formulare risposte; il router registra anche le risposte delle azioni dirette. Cronologia e fatti sono nel database SQLite locale.
4. La GUI interroga periodicamente le nuove righe SQLite: i comandi pronunciati nel processo vocale compaiono così nella chat desktop senza riavviarla.
4. La GUI visualizza la risposta; l'interfaccia vocale può leggerla con Edge TTS.

## Persistenza e credenziali

- `src/storage/jarvis.db`: tabelle SQLite per cronologia e fatti personali.
- `.env`: chiave `GROQ_API_KEY`; `.env.example` contiene il nome della variabile senza un valore segreto.
- `src/client_secret.json` e `src/token.json`: credenziali OAuth Google, ora esclusi da `.gitignore`.
- Il database locale e il file MP3 temporaneo sono esclusi dal controllo versione.

L'audio inviato a Google per la trascrizione e il testo/contesto inviato a Groq escono dal computer. La posta è consultabile dalla chat o dall'interfaccia vocale tramite riepiloghi Gmail; la GUI non contiene più una schermata dedicata alla posta. Conversazioni e fatti rimangono nel file SQLite locale.

## Servizi esterni

| Servizio | Uso |
|---|---|
| Groq | Interpretazione della memoria e conversazione (`openai/gpt-oss-20b`). |
| Google Speech Recognition | Trascrizione vocale italiana. |
| Edge TTS | Sintesi vocale (`it-IT-IsabellaNeural`). |
| Gmail API | Riepilogo delle email non lette su richiesta, con consenso OAuth. La GUI non include una vista Gmail dedicata. |
| Feed ANSA/Sky TG24 | Titoli di notizie. |
| ipwho.is / Open-Meteo | Localizzazione indicativa, geocodifica e previsioni. |

## Avvio

Per la voce: da `src`, eseguire `python main.py`. Per la GUI: dalla radice, eseguire `python JarvisGUI/main.py`. L'ambiente deve avere le dipendenze di `requirements.txt`, compreso `customtkinter`.
