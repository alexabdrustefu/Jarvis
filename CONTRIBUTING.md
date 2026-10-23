# Contribuire

## Flusso dei branch

`main` contiene la versione stabile. Le nuove funzionalita e le correzioni partono sempre da `develop` su un branch dedicato:

```text
feature/nome-funzione  -> pull request -> develop
fix/nome-correzione    -> pull request -> develop
develop                -> pull request -> main (rilascio)
```

Non fare push diretti su `main` o `develop`. Non riscrivere la storia condivisa e non usare force push. Un rilascio va promosso con una pull request da `develop` a `main` dopo il superamento della CI.

## Controlli

La GitHub Action `Tests` installa le dipendenze su Windows/Python 3.12 ed esegue la suite offline con `unittest`. Le pull request verso `develop` e `main` avviano il controllo; i push su `develop` lo avviano di nuovo.

Prima di aprire una pull request, esegui localmente:

```powershell
$env:PYTHONPATH = "$PWD\src;$PWD"
python -m unittest discover -s tests -v
```

## Dati e segreti

Non committare `.env`, credenziali OAuth, token, database locali o dump di conversazioni. Usa `.env.example` per documentare le variabili necessarie senza valori segreti.

## Protezione GitHub

La regola di protezione va attivata nelle impostazioni del repository per `main`: richiedere pull request, richiedere il controllo `Unit tests (Windows / Python 3.12)` riuscito, vietare force push e cancellazione del branch e applicare la regola anche agli amministratori. Per mantenere possibile la revisione in un progetto con un solo collaboratore, il requisito di approvazioni può restare a zero; la modifica deve comunque passare da pull request e CI.
