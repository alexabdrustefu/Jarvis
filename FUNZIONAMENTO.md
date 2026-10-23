# Funzionamento e funzionalità

J.A.R.V.I.S. è un assistente personale Python per Windows. Offre una GUI desktop e un'interfaccia vocale da terminale; entrambe usano lo stesso router dei comandi, lo stesso client AI e la stessa memoria SQLite.

## Funzionalità

- Conversazione locale gratuita con Ollama (`qwen3:4b`) e LM Studio; Groq è facoltativo.
- Selezione automatica del provider in base a complessità e privacy del messaggio.
- API HTTP e socket TCP locali per futuri client web.
- Memoria della cronologia e dei fatti personali in SQLite.
- GUI desktop con dashboard HUD animata e chat multilinea. La chat carica la cronologia recente, mostra gli orari, permette di copiare le risposte e si aggiorna anche quando i comandi arrivano dall'interfaccia vocale.
- Dettatura tramite Google Speech Recognition e lettura facoltativa delle risposte tramite Edge TTS.
- Riepilogo delle email Gmail non lette, invocabile dalla chat o dalla voce. La GUI non contiene una sezione Gmail dedicata.
- Meteo attuale e previsioni tramite Open-Meteo; la posizione può essere rilevata tramite IP o specificata nella richiesta.
- Notizie da feed RSS ANSA con Sky TG24 come ripiego.
- Apertura di siti e programmi, ricerche web, data e ora, controllo del volume master di Windows.

## Promemoria, routine e impostazioni

La sezione **Pianificazione** della GUI gestisce promemoria e attività in SQLite. Puoi scrivere `ricordami di chiamare Luca tra 10 minuti`, `ricordami di comprare il latte domani alle 9` o `aggiungi attività inviare il documento`. Usa `mostra promemoria`, `completa 2` ed `elimina 2` in chat per consultarli e gestirli. La GUI mostra un avviso all'ora prevista mentre resta aperta; l'interfaccia vocale annuncia gli avvisi al successivo ciclo di ascolto.

Per una routine, inserisci un nome nel pannello, seleziona le azioni consentite e salva. La routine compare nella lista e può essere lanciata dalla chat, ad esempio `avvia modalità lavoro`. J.A.R.V.I.S. descrive il passaggio e aspetta una conferma esplicita (`sì` o `no`) prima di agire. Le routine sono composte da azioni integrate, non eseguono codice personalizzato.

Preferenze e routine vengono salvate localmente in `src/storage/jarvis.db`. Il pannello permette di scegliere provider AI, lettura delle risposte, voce Edge TTS, velocità e città meteo; mostra lo stato dei server locali e avvia il bridge web. In modalità automatica Ollama gestisce i turni normali e LM Studio le richieste complesse se il server è attivo; senza LM Studio resta tutto su Ollama. Il cloud Groq viene usato solo se selezionato esplicitamente.

## Interfacce

### GUI desktop

Avvio dalla radice del progetto:

~~~powershell
python .\gui\main.py
~~~

La finestra si apre sulla chat. Ctrl+Invio invia un messaggio, PARLA avvia la dettatura e LEGGI RISPOSTE attiva la sintesi vocale. PULISCI cancella la cronologia conversazionale previa conferma; i fatti salvati restano disponibili. La dashboard offre azioni rapide per meteo, notizie e informazioni di sistema.

Non è presente una vista per aprire singole email o comporre risposte. Per ottenere un riepilogo della posta non letta puoi chiedere in chat “leggi le email”.

### API HTTP e socket

Avvia dalla GUI con **Avvia bridge per web**, oppure dalla radice del progetto:

~~~powershell
python .\api\main.py
~~~

Swagger UI si apre automaticamente all'avvio terminale su `http://127.0.0.1:8765/docs` (`--no-browser` disabilita l'apertura) e lo schema OpenAPI è su `/openapi.json`. La REST API v1 espone `GET /api/v1/menu` per scoprire le funzioni e i link, `GET /api/v1/health`, `POST /api/v1/chat`, `GET/POST /api/v1/reminders`, `PATCH/DELETE /api/v1/reminders/{id}`, `GET /api/v1/routines` e `GET /api/v1/stats`. Le statistiche sono aggregate e non contengono testi della chat o valori dei fatti personali. Restano compatibili `POST /api/chat`, `GET /health`, WebSocket `ws://127.0.0.1:8765/ws` e socket TCP JSON per riga su `127.0.0.1:8766`. Tutti usano lo stesso router e ascoltano solo sul PC locale.

### Assistente vocale

Avvio dalla radice del progetto:

~~~powershell
python .\src\main.py
~~~

VoiceInput registra dal microfono e invia la trascrizione a Google Speech Recognition in italiano. VoiceOutput legge la risposta con Edge TTS. Per chiudere pronuncia “esci”, “termina”, “spegni Jarvis” o “chiudi Jarvis”; Ctrl+C interrompe il ciclo.

### Interfaccia testuale interattiva

~~~powershell
python .\tests\manual_memory_console.py
~~~

Questa interfaccia riutilizza il router senza microfono. Digita /exit per uscire.

## Comandi di esempio

- Meteo: “Che tempo fa domani a Milano?”
- Notizie: “Dimmi le notizie”
- Email: “Leggi le email non lette”
- Sistema: “Che ore sono?”, “Apri calcolatrice”, “Apri Gmail”
- Ricerca: “Cerca ricette vegetariane”
- Volume: “Alza il volume”, “Muta”, “Imposta il volume al 40”
- Memoria: “Ricordati che il mio colore preferito è blu”; “Cosa ti ricordi di me?”

“Aiuto” o “cosa puoi fare” mostra le capacità principali. I comandi deterministici sono riconosciuti dal router prima di inviare le richieste non riconosciute al modello AI.

## Flusso di una richiesta

1. La GUI, il microfono o il terminale forniscono il testo al CommandRouter.
2. Il router normalizza maiuscole e accenti e controlla i comandi per volume, email, notizie, meteo, orologio, programmi e ricerca web.
3. I comandi riconosciuti vengono inoltrati alla relativa azione; le altre richieste passano a LLMClient e al provider scelto.
4. Le conversazioni e i fatti vengono letti o salvati nel database SQLite locale.
5. La GUI visualizza la risposta; l'assistente vocale può leggerla con Edge TTS.

Le richieste AI limitano la cronologia nel prompt e la lunghezza della risposta. Le domande normali non passano da una chiamata separata per classificare la memoria; le operazioni semplici sui fatti sono locali. La stima dei token non richiede tokenizer o download.

## Dati, rete e privacy

- Cronologia e fatti: src/storage/jarvis.db.
- Ollama: modello locale gratuito `qwen3:4b`, scaricabile con `ollama pull qwen3:4b`.
- Groq facoltativo: configurazione in `.env` tramite GROQ_API_KEY.
- OAuth Google: src/client_secret.json e src/token.json, se si usano i comandi Gmail.
- Con Ollama le richieste AI restano sul PC. Groq riceve il messaggio corrente senza fatti o cronologia salvati; dettatura e sintesi vocale usano servizi online.
- Meteo, notizie e Gmail contattano servizi esterni.
- La cronologia e i fatti restano nel database locale. Le credenziali, il token e il database non vanno pubblicati.

Per installare dipendenze e configurare le chiavi consulta INSTALLAZIONE.md. Per componenti, responsabilità e infrastruttura consulta ARCHITETTURA.md.
