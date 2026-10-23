# Contribuire

## Flusso dei branch

`main` contiene la versione stabile. Le nuove funzionalita e le correzioni partono sempre da `develop` su un branch dedicato. Quando una modifica dipende da un'altra, le pull request sono impilate e vanno integrate in ordine:

```text
feature/nome-funzione  -> pull request -> develop
fix/nome-correzione    -> pull request -> develop
develop                -> pull request -> main (rilascio)
```

Non fare push diretti su `main` o `develop`. Non riscrivere la storia condivisa e non usare force push. Un rilascio va promosso con una pull request da `develop` a `main` dopo il superamento della CI.

Per il set di branch preparato in questo repository, l'ordine e: `feature/core-ai-productivity` → `feature/news-rss-resilience` → `feature/api-ddd-telemetry` → `feature/desktop-gui` → `chore/docs-ci`. Apri ogni PR verso `develop` solo dopo aver integrato la precedente: i branch successivi includono i prerequisiti dei precedenti.

## Controlli

La GitHub Action `Tests` installa le dipendenze su Windows/Python 3.12, esegue Ruff e la suite offline con `unittest`. Le pull request verso `develop` e `main` avviano il controllo; i push su `develop` e `main` lo avviano di nuovo. La configurazione lint è in `ruff.toml`, le dipendenze di sviluppo in `requirements-dev.txt`.

Prima di aprire una pull request, esegui localmente:

```powershell
$env:PYTHONPATH = "$PWD\src;$PWD"
python -m unittest discover -s tests -v
ruff check api gui src tests
```

## Dati e segreti

Non committare `.env`, credenziali OAuth, token, database locali o dump di conversazioni. Usa `.env.example` per documentare le variabili necessarie senza valori segreti.

## Protezione GitHub

La configurazione pronta da importare è `.github/rulesets/main-protection.json`. In GitHub apri **Settings → Rules → Rulesets → New ruleset → Import a ruleset**, seleziona il file e crea la regola. Protegge solo `main`, richiede una pull request e il controllo `unit-tests`, blocca force push e cancellazioni, richiede la risoluzione dei thread e non concede bypass agli amministratori.

Il controllo CI deve aver completato almeno una run prima che GitHub lo possa selezionare come required check. Il nome tecnico del job è `unit-tests`, uguale al contesto richiesto dalla regola. Il numero di approvazioni resta a zero per consentire il merge in un repository con un solo collaboratore; resta obbligatorio il passaggio dalla pull request e dalla CI.
