# Installazione e configurazione

Questa guida descrive l'installazione su Windows dalla cartella principale del repository.

## Prerequisiti

- Windows 10 o 11.
- Python 3.10 o superiore e Python Launcher (py). Le funzioni audio e il controllo del volume dipendono da componenti Windows e possono richiedere pacchetti compatibili con la versione di Python installata.
- Connessione Internet.
- Una chiave API Groq per la chat e le richieste AI.
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

## Chiave Groq

Crea il file locale .env partendo dal modello:

~~~powershell
Copy-Item .env.example .env
notepad .env
~~~

Imposta la variabile senza virgolette o spazi aggiuntivi:

~~~dotenv
GROQ_API_KEY=la_tua_chiave_groq
~~~

Il client usa il modello **openai/gpt-oss-20b** tramite Groq. Non pubblicare .env e non inserire la chiave in un commit.

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
python .\JarvisGUI\main.py
~~~

Avvia l'assistente vocale da terminale:

~~~powershell
python .\src\main.py
~~~

Avvia l'interfaccia testuale interattiva:

~~~powershell
python .\src\test_core.py
~~~

Nella GUI la chat è la schermata iniziale. Ctrl+Invio invia il messaggio; il pulsante PARLA attiva la dettatura e LEGGI RISPOSTE abilita la sintesi vocale. La dashboard offre scorciatoie per meteo, notizie e informazioni di sistema. Pronuncia “esci” per terminare la sessione vocale; nell'interfaccia testuale usa /exit.

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

Il test automatizzato disponibile riguarda il riconoscimento dei comandi e la regolazione del volume. Dalla cartella principale:

~~~powershell
python -m unittest discover -s src -p "test_system_actions_audio.py" -v
~~~

src/test_core.py è un'interfaccia interattiva. src/test_ai.py contatta Groq: non è un test offline e può consumare richieste API.

## Problemi comuni

- **GROQ_API_KEY non trovata**: verifica che .env sia nella cartella principale e che il nome della variabile sia esattamente GROQ_API_KEY.
- **Problemi con PyAudio o il microfono**: controlla il dispositivo audio predefinito e la compatibilità della versione di PyAudio con Python e Windows.
- **Errore OAuth o credenziali mancanti**: controlla src/client_secret.json, l'abilitazione di Gmail API e lo stato del consenso OAuth.
- **Problemi SSL con Google**: verifica proxy, VPN o antivirus con ispezione HTTPS. J.A.R.V.I.S. non disabilita la verifica TLS.
- **Meteo o notizie non disponibili**: le funzioni dipendono da Internet e da servizi esterni; riprova dopo aver controllato la connessione.
- **Nessun audio in uscita**: controlla il dispositivo audio e la connessione; Edge TTS richiede Internet.

Per l'organizzazione dei moduli e i flussi tra GUI, router e servizi consulta ARCHITETTURA.md. Per il riepilogo delle funzioni consulta FUNZIONAMENTO.md.
