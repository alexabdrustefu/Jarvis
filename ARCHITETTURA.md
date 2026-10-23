# Architettura e infrastruttura

## Panoramica

J.A.R.V.I.S. è un'applicazione desktop e vocale locale. Non usa un server applicativo o container. La GUI e il programma vocale costruiscono le proprie dipendenze e condividono CommandRouter, servizi e memoria tramite i moduli in src.

~~~mermaid
flowchart LR
    GUI[JarvisGUI: dashboard e chat] --> GUIComposition[GUI composition root]
    Voice[src/main.py: interfaccia vocale] --> VoiceComposition[Voice composition root]
    GUIComposition --> Router[CommandRouter]
    VoiceComposition --> Router
    Router --> AI[LLMClient]
    Router --> Actions[Azioni applicative]
    AI --> Memory[(SQLite)]
    Actions --> External[Groq, Gmail, RSS, Open-Meteo, Windows]
    VoiceComposition --> Audio[Microfono e Edge TTS]
    GUIComposition --> Audio
~~~

## Struttura dei moduli

| Percorso | Responsabilità |
|---|---|
| src/main.py | Compone AI, router, azioni e interfacce vocali; avvia il ciclo dell'assistente. |
| src/core/command_router.py | Riconosce i comandi specifici e inoltra le richieste AI generiche. |
| src/core/text.py | Normalizza testo e accenti per il confronto dei comandi. |
| src/core/weather.py | Interpreta date e città nelle richieste meteo. |
| src/actions/system_actions.py | Apre programmi e siti, esegue ricerche e fornisce data/ora; espone la facciata meteo. |
| src/actions/system_actions_audio.py | Riconosce i comandi audio e controlla il volume master Windows tramite pycaw/COM. |
| src/actions/weather_actions.py | Rileva la posizione, geocodifica città e interroga Open-Meteo. |
| src/actions/news_actions.py | Recupera e formatta notizie da feed RSS. |
| src/actions/email_actions.py | Integra Gmail API per i riepiloghi email e le operazioni email del core tramite OAuth. |
| src/ai/llm_client.py | Invia richieste a Groq, gestisce contesto conversazionale e memoria dei fatti. |
| src/interface/ | Acquisisce la voce e riproduce la sintesi vocale. |
| src/memory/ | Gestisce cronologia e fatti nel database SQLite locale. |
| JarvisGUI/main.py | Inserisce src nel percorso Python e avvia JarvisApp. |
| JarvisGUI/services.py | Composition root della GUI: crea i servizi e il CommandRouter condiviso. |
| JarvisGUI/ui/app.py | Crea la finestra, la navigazione e il ciclo di vita delle viste desktop. |
| JarvisGUI/ui/dashboard.py | Mostra HUD, orologio e scorciatoie che inviano richieste alla chat. |
| JarvisGUI/ui/chat_view.py | Gestisce chat, cronologia, input vocale e aggiornamento delle risposte. |

La GUI non ha una vista Gmail dedicata. Il core mantiene il router email per i comandi di riepilogo disponibili dalla chat o dalla voce.

## Ingressi e composizione

- JarvisGUI/main.py configura il path dei moduli in src e avvia JarvisApp.
- JarvisGUI/services.py crea LLMClient, EmailActions, NewsActions e le azioni di sistema/audio, quindi li passa a CommandRouter.
- src/main.py compone gli stessi tipi di servizi e avvia VoiceInput/VoiceOutput.
- src/voice_assistant.py mantiene compatibilità con il vecchio punto di ingresso e delega al nuovo ciclo.

Le dipendenze sono passate al router dal composition root. Questo evita che il router costruisca direttamente API client o widget grafici.

## Flusso delle richieste

1. Chat, microfono o interfaccia testuale passano il testo a CommandRouter.
2. CommandRouter normalizza il testo e riconosce i comandi specifici per audio, Gmail, news, meteo, data/ora, apertura e ricerca.
3. Le azioni dirette chiamano il relativo servizio; le richieste generiche arrivano a LLMClient e poi a Groq.
4. LLMClient usa LongTermMemory e FactsMemory per leggere o aggiornare lo stato conversazionale locale.
5. Le risposte vengono mostrate nella GUI o nel terminale; VoiceOutput può leggerle ad alta voce.
6. La chat GUI sincronizza periodicamente le nuove righe della cronologia SQLite, incluse quelle aggiunte dal processo vocale.

## Persistenza e servizi esterni

- src/storage/jarvis.db: cronologia e fatti personali, conservati localmente.
- .env: variabili locali, inclusa GROQ_API_KEY.
- src/client_secret.json e src/token.json: credenziali e token OAuth Google per Gmail, se configurato.
- Groq: conversazione AI e interpretazione di richieste.
- Google Speech Recognition: trascrizione vocale italiana.
- Edge TTS: sintesi vocale, con voce italiana configurata nel client.
- Gmail API: riepilogo dei messaggi non letti su richiesta.
- Feed RSS: notizie.
- ipwho.is e Open-Meteo: posizione approssimativa, geocodifica e previsioni.
- Windows/COM: avvio di programmi e controllo audio.

Le credenziali, il token OAuth e il database locale sono esclusi dal controllo versione tramite .gitignore. Il testo inviato al modello AI, l'audio inviato al riconoscimento vocale e le richieste rivolte ai provider esterni lasciano il computer.

## Pattern e responsabilità

- **Separazione per responsabilità**: interfacce, router, azioni, client AI e persistenza hanno moduli distinti.
- **Dependency injection**: CommandRouter riceve i servizi dal composition root.
- **Facade**: SystemActions espone le azioni desktop e inoltra le richieste meteo a WeatherActions.
- **Lazy initialization**: l'autenticazione Gmail viene avviata al primo comando email e non all'apertura della GUI.
- **Condivisione dei servizi**: i due ingressi usano lo stesso router e lo stesso database, mantenendo una cronologia comune.

## Avvio e controlli

I comandi di installazione e avvio sono in INSTALLAZIONE.md. L'applicazione è orientata a Windows; il controllo del volume dipende da librerie Windows e l'audio può richiedere dipendenze compatibili con la versione Python installata.
