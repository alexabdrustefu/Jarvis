# Funzionamento e funzionalità

J.A.R.V.I.S. è un assistente personale Python per Windows. Offre una GUI desktop e un'interfaccia vocale da terminale; entrambe usano lo stesso router dei comandi, lo stesso client AI e la stessa memoria SQLite.

## Funzionalità

- Conversazione in italiano con il modello openai/gpt-oss-20b tramite API Groq.
- Memoria della cronologia e dei fatti personali in SQLite.
- GUI desktop con dashboard HUD animata e chat multilinea. La chat carica la cronologia recente, mostra gli orari, permette di copiare le risposte e si aggiorna anche quando i comandi arrivano dall'interfaccia vocale.
- Dettatura tramite Google Speech Recognition e lettura facoltativa delle risposte tramite Edge TTS.
- Riepilogo delle email Gmail non lette, invocabile dalla chat o dalla voce. La GUI non contiene una sezione Gmail dedicata.
- Meteo attuale e previsioni tramite Open-Meteo; la posizione può essere rilevata tramite IP o specificata nella richiesta.
- Notizie da feed RSS ANSA con Sky TG24 come ripiego.
- Apertura di siti e programmi, ricerche web, data e ora, controllo del volume master di Windows.

## Interfacce

### GUI desktop

Avvio dalla radice del progetto:

~~~powershell
python .\JarvisGUI\main.py
~~~

La finestra si apre sulla chat. Ctrl+Invio invia un messaggio, PARLA avvia la dettatura e LEGGI RISPOSTE attiva la sintesi vocale. PULISCI cancella la cronologia conversazionale previa conferma; i fatti salvati restano disponibili. La dashboard offre azioni rapide per meteo, notizie e informazioni di sistema.

Non è presente una vista per aprire singole email o comporre risposte. Per ottenere un riepilogo della posta non letta puoi chiedere in chat “leggi le email”.

### Assistente vocale

Avvio dalla radice del progetto:

~~~powershell
python .\src\main.py
~~~

VoiceInput registra dal microfono e invia la trascrizione a Google Speech Recognition in italiano. VoiceOutput legge la risposta con Edge TTS. Per chiudere pronuncia “esci”, “termina”, “spegni Jarvis” o “chiudi Jarvis”; Ctrl+C interrompe il ciclo.

### Interfaccia testuale interattiva

~~~powershell
python .\src\test_core.py
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
3. I comandi riconosciuti vengono inoltrati alla relativa azione; le altre richieste passano a LLMClient e Groq.
4. Le conversazioni e i fatti vengono letti o salvati nel database SQLite locale.
5. La GUI visualizza la risposta; l'assistente vocale può leggerla con Edge TTS.

## Dati, rete e privacy

- Cronologia e fatti: src/storage/jarvis.db.
- Configurazione AI: .env nella radice, variabile GROQ_API_KEY.
- OAuth Google: src/client_secret.json e src/token.json, se si usano i comandi Gmail.
- Le richieste AI vengono inviate a Groq; la dettatura usa Google Speech Recognition; la sintesi Edge TTS richiede Internet.
- Meteo, notizie e Gmail contattano servizi esterni.
- La cronologia e i fatti restano nel database locale. Le credenziali, il token e il database non vanno pubblicati.

Per installare dipendenze e configurare le chiavi consulta INSTALLAZIONE.md. Per componenti, responsabilità e infrastruttura consulta ARCHITETTURA.md.
