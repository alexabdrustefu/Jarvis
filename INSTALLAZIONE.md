# Installazione e comandi

Queste istruzioni sono per Windows e PowerShell. Esegui i comandi dalla cartella principale del progetto.

## 1. Prerequisiti

- Installa Python 3.10 o superiore e verifica che `py` sia disponibile nel terminale.
- Per input e output audio, collega microfono e altoparlanti/cuffie. `PyAudio` e `pycaw` potrebbero richiedere componenti compatibili con la versione di Python e Windows in uso.
- Prepara una chiave API Groq. Per le email, prepara anche un client OAuth di tipo **applicazione desktop** in Google Cloud, abilita Gmail API e scarica il JSON delle credenziali.

## 2. Ambiente Python e dipendenze

```powershell
py -3 -m venv .venv
\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Se PowerShell blocca l'attivazione, puoi richiedere l'uso dei virtual environment solo per la sessione corrente:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
\.venv\Scripts\Activate.ps1
```

In alternativa, senza attivare l'ambiente, usa `\.venv\Scripts\python.exe` al posto di `python` nei comandi successivi.

## 3. Configurazione Groq

Copia il modello nella cartella principale e inserisci la chiave:

```powershell
Copy-Item .env.example .env
notepad .env
```

Inserisci la chiave dopo `GROQ_API_KEY=`. Non incollarla in chat o in file che verranno condivisi. Il client usa il modello `openai/gpt-oss-20b` attraverso Groq.

## 4. Configurazione facoltativa di Gmail

1. In Google Cloud crea o seleziona un progetto, abilita Gmail API e configura la schermata di consenso OAuth.
2. Crea credenziali OAuth per un'applicazione desktop e salva il JSON scaricato come `src/client_secret.json`.
3. Avvia JARVIS: al primo accesso alla posta si aprirà il consenso Google nel browser per lettura e invio. Se avevi autorizzato la sola lettura, Google richiederà un nuovo consenso prima di poter rispondere; il token sarà salvato in `src/token.json`.

L'autenticazione Gmail parte solo quando chiedi di leggere la posta. Puoi usare voce o GUI senza configurare Gmail finché non invochi questa funzione.

Non condividere né aggiungere al controllo versione `src/client_secret.json` o `src/token.json`.

## 5. Avvio

La sezione Gmail richiede i permessi OAuth di lettura e invio. Se `src/token.json` e stato autorizzato in precedenza per la sola lettura, al primo accesso alla posta Google richiedera un nuovo consenso prima di poter inviare risposte.

Gli import del progetto sono organizzati per essere eseguiti dalla cartella `src`:

```powershell
Set-Location .\src
python .\main.py
```

Per l'assistente solo testuale (richiede comunque Groq):

```powershell
python .\test_core.py
```

Per avviare l'interfaccia grafica dalla cartella principale:

```powershell
python .\JarvisGUI\main.py
```

La chat è la schermata iniziale della GUI e supporta testo multilinea (`Ctrl+Invio` per inviare), storico persistente, risposte copiabili e il pulsante **PARLA** per dettatura. Si sincronizza con i comandi eseguiti dall'assistente vocale. Attiva **LEGGI RISPOSTE** per ascoltare le risposte. La dashboard include scorciatoie per meteo, notizie, email e ora.

Pronuncia «esci» per chiudere l'assistente vocale; nel test testuale usa `/exit`.

## Comandi vocali di esempio

- «Jarvis, che ore sono?»
- «Che tempo fa domani a Milano?»
- «Leggi le email» / «Controlla la posta in arrivo»
- «Dimmi le notizie»
- «Apri calcolatrice» / «Apri Gmail» / «Cerca ricette»
- «Alza il volume», «Abbassa il volume di 10», «Imposta il volume al 40», «Muta»
- «Ricordati che il mio colore preferito è blu»
- «Cosa ti ricordi di me?»

## Test esistente

Il test automatizzato presente nel progetto riguarda il riconoscimento e la regolazione del volume. Dalla cartella `src`:

```powershell
python -m unittest test_system_actions_audio -v
```

`test_ai.py` contatta Groq e non è un test offline. `test_core.py` è un programma interattivo, non un test automatizzato.

## Problemi comuni

- **`SSL: WRONG_VERSION_NUMBER` su Gmail**: controlla proxy di Windows, VPN o antivirus con ispezione HTTPS; JARVIS non disattiva la verifica TLS. Se la rete richiede un proxy, configurane correttamente l'accesso HTTPS.

- **`GROQ_API_KEY non trovata`**: controlla che `.env` sia nella radice del progetto e contenga la variabile con il nome esatto.
- **Errore microfono o `PyAudio`**: verifica il dispositivo predefinito di Windows e la compatibilità del pacchetto audio con la versione Python installata.
- **Errore OAuth/file mancante**: controlla il percorso `src/client_secret.json`, abilita Gmail API e completa il consenso OAuth.
- **Nessun audio in uscita**: verifica Internet e dispositivo audio; la sintesi Edge TTS richiede rete. Se la riproduzione non funziona, il testo resta visibile nel terminale.
- **Meteo o notizie non disponibili**: verifica la connessione Internet e riprova; le funzioni interrogano servizi esterni.
