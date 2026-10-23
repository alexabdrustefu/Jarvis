# Installazione e configurazione

Questa guida descrive l'installazione su Windows dalla cartella principale del repository.

## Prerequisiti

- Windows 10 o 11.
- Python 3.10 o superiore e Python Launcher (py). Le funzioni audio e il controllo del volume dipendono da componenti Windows e possono richiedere pacchetti compatibili con la versione di Python installata.
- Connessione Internet.
- Ollama per la chat AI gratuita e locale. Groq è facoltativo.
- Microfono e altoparlanti/cuffie per le funzioni vocali.
- Facoltativamente, un progetto Google Cloud con Gmail API e credenziali OAuth desktop per i comandi email.

## Ambiente virtuale e dipendenze

Apri PowerShell nella cartella del repository:

~~~powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
~~~

Se l'attivazione viene bloccata dalla policy di PowerShell, abilitala per la sessione corrente:

~~~powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
~~~

Puoi anche evitare l'attivazione e usare direttamente **.venv\Scripts\python.exe** al posto di **python**.

## Modello locale gratuito

Installa Ollama dal sito ufficiale [ollama.com/download](https://ollama.com/download), quindi apri PowerShell:

~~~powershell
ollama pull qwen3:4b
ollama run qwen3:4b
~~~

Il modello viene scaricato sul PC e le richieste successive sono elaborate localmente, senza chiavi o costo per chiamata. RAM e spazio disco richiesti dipendono dal modello scelto.

### LM Studio locale facoltativo

Installa [LM Studio](https://lmstudio.ai/) e scarica un modello compatibile con il tuo PC. Nella scheda **Developer** avvia il server locale sulla porta predefinita 1234 e carica un modello. J.A.R.V.I.S. lo rileva per le richieste più complesse. Non è richiesto un account o un servizio a pagamento per l'inferenza locale. Per scegliere un modello specifico, imposta `LM_STUDIO_MODEL` nel file `.env` usando l'identificatore restituito da `/v1/models`.

## Provider Groq facoltativo

Crea il file locale .env partendo dal modello:

~~~powershell
Copy-Item .env.example .env
notepad .env
~~~

Imposta la variabile senza virgolette o spazi aggiuntivi:

~~~dotenv
GROQ_API_KEY=la_tua_chiave_groq
~~~

In modalità **Automatico**, JARVIS usa Ollama per richieste normali o personali e LM Studio per richieste complesse se il server locale è attivo; altrimenti resta su Ollama. Automatico non invia messaggi ai servizi cloud. Groq viene usato solo se lo selezioni esplicitamente dalle preferenze GUI. Le quote gratuite dei servizi ospitati possono cambiare. Non pubblicare `.env`.

## Gmail facoltativo

La GUI non ha una schermata Gmail. I comandi email disponibili dal router vocale/chat possono fornire un riepilogo dei messaggi non letti.

1. Crea o seleziona un progetto in Google Cloud e abilita Gmail API.
2. Configura il consenso OAuth e crea credenziali per un'applicazione desktop.
3. Salva il JSON scaricato come **src/client_secret.json**.
4. Al primo comando email, completa il consenso Google nel browser. Il token locale viene salvato in **src/token.json**.

Le credenziali OAuth sono facoltative; senza di esse le altre funzioni continuano a essere disponibili. Non condividere client_secret.json o token.json.

## Avvio

Dalla radice del repository, con l'ambiente virtuale attivo, avvia la GUI desktop:

~~~powershell
python .\gui\main.py
~~~

### Installer Windows

Scarica `JARVIS-Setup-*.exe` dalle [release GitHub](https://github.com/alexabdrustefu/Jarvis/releases/latest) e avvialo. L'installer non richiede privilegi amministrativi. Avvia J.A.R.V.I.S. dal menu Start; per la chat AI locale installa Ollama e il modello `qwen3:4b` come descritto sopra.

L'installer distribuito dal progetto non è firmato con un certificato commerciale: Windows può mostrare un avviso SmartScreen. Ogni release include `SHA256SUMS.txt` per verificare che installer e archivio siano integri.

L'installer conserva database, preferenze e credenziali in `%LOCALAPPDATA%\JARVIS`, separati dai file di programma. Per usare Groq, copia `%LOCALAPPDATA%\JARVIS\config.example.env` in `%LOCALAPPDATA%\JARVIS\.env` e aggiungi `GROQ_API_KEY`. Gmail OAuth è facoltativo: posiziona `client_secret.json` nella stessa cartella dati e autorizza l'accesso al primo comando email.

La build portatile `JARVIS-Portable-*.zip` non richiede installazione: estraila in una cartella utente e avvia `JARVIS.exe`. Per configurare Groq dalla build portatile, crea `%LOCALAPPDATA%\JARVIS` se manca e copia `config.example.env` dalla cartella estratta in quella directory rinominandolo `.env`.

Avvia l'assistente vocale da terminale:

~~~powershell
python .\src\main.py
~~~

Avvia l'interfaccia testuale interattiva:

~~~powershell
python .\tests\manual_memory_console.py
~~~

Nella GUI la chat è la schermata iniziale. Ctrl+Invio invia il messaggio; il pulsante PARLA attiva la dettatura e LEGGI RISPOSTE abilita la sintesi vocale. La dashboard offre scorciatoie per meteo, notizie e informazioni di sistema. Pronuncia “esci” per terminare la sessione vocale; nell'interfaccia testuale usa /exit.

## API HTTP e socket per un client web

Dalla GUI apri **Pianificazione** e avvia il bridge locale, oppure esegui:

~~~powershell
python .\api\main.py
~~~

L'avvio apre automaticamente Swagger UI nel browser su `http://127.0.0.1:8765/docs`; lo schema OpenAPI è disponibile su `/openapi.json`. Per avviare senza aprire il browser usa `python .\api\main.py --no-browser`.

- `GET http://127.0.0.1:8765/health` restituisce lo stato.
- `POST http://127.0.0.1:8765/api/chat` riceve `{"message":"Ciao"}` e restituisce `{"reply":"..."}`.
- WebSocket `ws://127.0.0.1:8765/ws` scambia gli stessi oggetti JSON ed è pronto per un client JavaScript nel browser.
- `127.0.0.1:8766` accetta JSON delimitato da newline, una richiesta per riga.

Il bridge usa solo la libreria standard Python ed è raggiungibile dal PC locale.

## Comandi di esempio

- Che tempo fa domani a Milano?
- Dimmi le notizie
- Leggi le email o Controlla la posta in arrivo
- Che ore sono? o Dimmi la data
- Apri calcolatrice, Apri Gmail
- Cerca ricette vegetariane
- Alza il volume, Abbassa il volume di 10, Imposta il volume al 40, Muta
- Ricordati che il mio colore preferito è blu
- Cosa ti ricordi di me?

## Verifiche e test

I test automatici non richiedono rete e usano memoria SQLite temporanea. Dalla cartella principale:

~~~powershell
python -m unittest discover -s tests -t . -p "test_*.py" -v
~~~

tests/manual_memory_console.py è un'interfaccia interattiva. tests/test_ai.py è un controllo manuale live: eseguito direttamente contatta Groq e può consumare richieste API; l'importazione durante la discovery è sicura e non invia richieste.

## Problemi comuni

- **Ollama non disponibile**: avvia Ollama, verifica `ollama list` e scarica il modello con `ollama pull qwen3:4b`.
- **Problemi con PyAudio o il microfono**: controlla il dispositivo audio predefinito e la compatibilità della versione di PyAudio con Python e Windows.
- **Errore OAuth o credenziali mancanti**: controlla src/client_secret.json, l'abilitazione di Gmail API e lo stato del consenso OAuth.
- **Problemi SSL con Google**: verifica proxy, VPN o antivirus con ispezione HTTPS. J.A.R.V.I.S. non disabilita la verifica TLS.
- **Meteo o notizie non disponibili**: le funzioni dipendono da Internet e da servizi esterni; riprova dopo aver controllato la connessione.
- **Nessun audio in uscita**: controlla il dispositivo audio e la connessione; Edge TTS richiede Internet.

Per l'organizzazione dei moduli e i flussi tra GUI, router e servizi consulta ARCHITETTURA.md. Per il riepilogo delle funzioni consulta FUNZIONAMENTO.md.
