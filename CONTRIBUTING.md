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

## Commit e pull request

Mantieni i commit piccoli e concentrati su un solo cambiamento. Usa messaggi leggibili, per esempio `feat(gui): add keyboard shortcut` o `fix(api): validate reminder input`. Evita commit che mescolano modifiche indipendenti. Compila il [template della pull request](.github/PULL_REQUEST_TEMPLATE.md) e indica sempre come hai verificato il cambiamento.

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

## Protezione GitHub e release

Le configurazioni sono in `.github/rulesets/main-protection.json` e `.github/rulesets/develop-protection.json`. Entrambi i branch richiedono una pull request e il check `unit-tests`, bloccano cancellazioni e force push e richiedono la risoluzione delle conversazioni. Non sono richieste approvazioni, così il maintainer singolo può integrare il proprio lavoro mantenendo CI e PR obbligatorie. I ruleset sono attivi sul repository GitHub.

Per pubblicare una versione, crea un tag `vMAJOR.MINOR.PATCH` su `main`. Il workflow `Windows release` crea l'app desktop, compila l'installer Inno Setup e l'archivio portatile, quindi pubblica gli asset nella GitHub Release.

Le pull request eseguono test e lint. I push ai branch `feature/*`, `fix/*`, `chore/*`, `develop` e `main` verificano anche il packaging Windows, così le dipendenze dinamiche della GUI vengono controllate prima di una release.
