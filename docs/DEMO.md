# Demo guidata

La modalità demo mostra la chat e le azioni principali senza richiedere account, chiavi API, Ollama, rete o microfono. Le risposte sono dichiaratamente simulate e tutti i dati di prova vengono conservati in una cartella temporanea rimossa alla chiusura.

## Avvio

Dalla cartella del progetto, con le dipendenze installate:

```powershell
python .\gui\main.py --demo
```

La modalità demo è disponibile anche dalla build Windows:

```powershell
& "$env:LOCALAPPDATA\Programs\JARVIS\JARVIS.exe" --demo
```

## Percorso consigliato (90 secondi)

1. Guarda il messaggio iniziale: conferma che la demo è offline.
2. Scrivi `Che tempo fa oggi a Milano?` per vedere una previsione esplicitamente simulata.
3. Scrivi `Ricordami di fare una pausa tra 10 minuti` e apri **Pianificazione** per vedere il promemoria nel database temporaneo.
4. Torna alla chat e prova `Dimmi le notizie` o `Leggi le email`: J.A.R.V.I.S. spiega che in demo non contatta servizi esterni.
5. Apri **Centro di comando** per esplorare dashboard e scorciatoie.

Chiudi la finestra per eliminare la memoria e i promemoria dimostrativi. Per la chat AI reale, avvia l'app senza `--demo` e installa Ollama seguendo [INSTALLAZIONE.md](../INSTALLAZIONE.md).
