# JARVIS: funzionamento e funzionalità

## Panoramica

JARVIS è un assistente personale in Python per Windows, disponibile con interfaccia vocale da terminale e GUI desktop. Le due interfacce condividono il dispatcher dei comandi e i servizi applicativi. Le richieste non riconosciute vengono inoltrate a un modello linguistico tramite Groq.

## Cosa può fare

- **Conversare** in italiano con il modello `openai/gpt-oss-20b` tramite l'API Groq.
- **Ricordare informazioni e conversazioni** nel database SQLite `src/storage/jarvis.db`. La memoria conversazionale conserva gli ultimi messaggi usati come contesto; la memoria dei fatti consente di salvare, aggiornare, consultare e dimenticare informazioni.
- **Consultare Gmail**: dalla chat o dall'interfaccia vocale puoi chiedere un riepilogo delle email non lette. La GUI non include più una sezione dedicata alla posta.
- **Leggere titoli di notizie** da feed RSS ANSA, con Sky TG24 come ripiego se il feed primario non restituisce notizie.
- **Fornire meteo** attuale o previsioni fino a circa 15 giorni, con posizione dedotta dall'indirizzo IP o con città indicata nella richiesta. Usa i servizi web ipwho.is e Open-Meteo.
- **Aprire siti e programmi**: Google, YouTube, Gmail, Wikipedia, Blocco note, Calcolatrice, Esplora file e Chrome, oltre a effettuare ricerche Google.
- **Leggere data e ora** e regolare il volume principale di Windows (incluso muto, percentuale e incrementi).

La GUI (`python .\JarvisGUI\main.py` dalla cartella principale) offre una dashboard HUD animata con scorciatoie operative, chat multilinea, dettatura e lettura vocale facoltativa. La chat ripristina gli ultimi 60 messaggi salvati, mostra orari e permette di copiare le risposte. `Ctrl+Invio` invia il testo; **PULISCI** cancella la cronologia previa conferma, conservando i fatti memorizzati. Le chiamate AI e al microfono girano in background. Il comando «aiuto» elenca le funzioni disponibili sia nell'interfaccia vocale sia nella chat.

## Flusso di una richiesta vocale

1. `src/main.py` inizializza AI, input/output vocale e azioni; `JarvisGUI/main.py` avvia la GUI usando gli stessi servizi.
2. `VoiceInput` acquisisce l'audio dal microfono e invia la trascrizione al servizio Google Speech Recognition in italiano (`it-IT`).
3. `src/core/command_router.py` riconosce prima i comandi specifici (volume, email, notizie, meteo, ora/data, apertura e ricerca). Le altre frasi passano a `LLMClient`.
4. `LLMClient` invia richieste al modello Groq e usa `LongTermMemory` e `FactsMemory` per il contesto. Le conversazioni e i fatti vengono memorizzati localmente in SQLite.
5. `VoiceOutput` crea un MP3 temporaneo con Edge TTS (voce `it-IT-IsabellaNeural`), lo riproduce e tenta di eliminarlo.

Per terminare, pronuncia **«esci»**, **«termina»**, **«spegni Jarvis»** o **«chiudi Jarvis»**. `Ctrl+C` interrompe il ciclo. Per il modulo testuale alternativo descritto in `src/test_core.py`, usa `python test_core.py` dalla cartella `src`.

## Requisiti e limiti operativi

- Windows, microfono, uscita audio e Python 3.10 o superiore (il codice usa annotazioni `str | None`; le dipendenze audio sono orientate a Windows).
- Connessione Internet per Groq, riconoscimento vocale, Edge TTS, RSS, meteo e flusso OAuth Gmail.
- Chiave API Groq nel file `.env`; credenziali OAuth desktop Gmail in `src/client_secret.json` se si desidera usare le email.
- Le funzioni meteo, news, AI, email e voce dipendono da servizi esterni e possono non funzionare senza rete o se il servizio cambia.
- `src/test_ai.py` effettua una richiesta reale a Groq all'importazione/esecuzione: non è una suite di test offline.

## Posta Gmail dalla chat o dalla voce

La GUI non ha una schermata Gmail. Puoi comunque chiedere a JARVIS un riepilogo delle email non lette dalla chat o dall'interfaccia vocale; per questa azione serve il consenso OAuth Gmail. Il modulo conserva nel core le integrazioni Gmail, ma l'apertura dei messaggi e la composizione delle risposte non sono disponibili nell'interfaccia desktop.

## Dati e credenziali

La cronologia e i fatti sono in `src/storage/jarvis.db`. Le credenziali OAuth vengono salvate in `src/token.json`; `src/client_secret.json` contiene il segreto client scaricato da Google Cloud. Questi file e `.env` sono locali e sensibili: non condividerli. Sono esclusi dal controllo versione. L'accesso Gmail viene autenticato al primo comando email.
