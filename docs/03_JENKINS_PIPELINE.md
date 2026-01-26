# 03_JENKINS_PIPELINE — pełny samouczek (LAB Elastic-only)

Ten rozdział to **pełna ścieżka uruchomieniowa**: od startu labu, przez konfigurację Jenkinsa i wykonanie pierwszego pomiaru, aż po weryfikację danych w Elasticsearch i Kibanie oraz typowe awarie, które realnie napotkaliśmy i naprawiliśmy.

> **Źródło prawdy (kod pipeline):** `lab/jenkins/pipeline_one.pipeline`  
> Ten dokument **nie duplikuje** całego Jenkinsfile, żeby uniknąć driftu (rozjazdu dokumentacji i implementacji).

---

## 0) Co finalnie działa (stan końcowy)

Pipeline (Elastic-only) generuje i indeksuje do ES zestaw zdarzeń:

- `event_type: sbom_snapshot`
- `event_type: sbom`
- `event_type: scan`
- `event_type: delta`
- `event_type: gate`

W Kibanie (Discover) widzisz dokumenty w data view `sbom-test*` (np. 5 hitów w oknie czasu), a w ES `_count` potwierdza faktyczną liczbę dokumentów (np. 6).

---

## 1) Architektura LAB i pętla procesowa

**LAB Elastic-only:**  
**Jenkins → toolbox → Elasticsearch → Kibana**

### Rola komponentów
- **Jenkins** — orkiestracja uruchomień, parametryzacja, archiwizacja artefaktów `.lab_out/*`.
- **toolbox (`sbom-lab/toolbox:latest`)** — runtime narzędzi (`syft`, `grype`, `jq`), wykonywany przez `docker run`.
- **Elasticsearch** — „pamięć zdarzeń” (event store) i punkt odniesienia w czasie (snapshot → delta).
- **Kibana** — interfejs analityczny (Discover / filtry / dashboardy / alerting).

### Co pipeline wytwarza (artefakty / obserwacje)
- **SBOM** (CycloneDX JSON) → `.lab_out/sbom.cdx.json`
- **SCAN** (Grype JSON) → `.lab_out/scan.grype.json`
- **SNAPSHOT** komponentów (lista linii) → `.lab_out/components.snapshot.txt`
- **PREV** snapshot pobrany z ES → `.lab_out/components.prev.txt`
- **DELTA** (added/removed) → `.lab_out/delta.json`
- **GATE** (GO/STOP + powód) → `.lab_out/gate.vars`

> Snapshot może być pusty przy skanie `repo` bez manifestów zależności — to nie jest błąd, tylko informacja o braku składników wykrytych przez SBOM.

---

## 2) Struktura repo: pliki, które mają znaczenie

- `lab/jenkins/pipeline_one.pipeline` — **kod pipeline** (źródło prawdy)
- `środowiska-testowe/docker-compose.lab.yml` — compose dla LAB (Jenkins + toolbox + Elasticsearch + Kibana + Portainer)
- `środowiska-testowe/.env.lab` — parametry labu (opcjonalnie)
- `lab/jenkins/Dockerfile` — obraz Jenkinsa (docker-cli + curl/jq/git)
- `lab/toolbox/Dockerfile` — obraz toolboxa (syft + grype + jq)

**Ważne:** plik compose nie ma domyślnej nazwy `docker-compose.yml`, więc zawsze używaj `-f docker-compose.lab.yml`.

---

## 3) Uruchomienie LAB (Docker Desktop + WSL2)

### 3.1 Start środowiska (Elastic-only)
W katalogu `środowiska-testowe`:

```bash
docker compose -p sbom-lab -f docker-compose.lab.yml --profile elastic up -d --build
````

### 3.2 Aktualizacja kontenerów bez kasowania danych Jenkinsa

**Nie używaj** `docker compose down -v` (usuwa volume `jenkins_home` = joby/konfiguracja).

Zamiast tego:

```bash
docker compose -p sbom-lab -f docker-compose.lab.yml up -d --no-deps --force-recreate jenkins toolbox
```

Jeśli zmieniałeś Dockerfile:

```bash
docker compose -p sbom-lab -f docker-compose.lab.yml build jenkins toolbox
docker compose -p sbom-lab -f docker-compose.lab.yml up -d --no-deps --force-recreate jenkins toolbox
```

---

## 4) Krytyczny warunek: dostęp do `/var/run/docker.sock` (WSL)

W WSL sprawdziliśmy:

* `/var/run/docker.sock` ma grupę `docker`
* GID socketa w Twoim środowisku: **1000**

Sprawdzenie:

```bash
ls -l /var/run/docker.sock
stat -c '%g %a %n' /var/run/docker.sock
```

### 4.1 Compose: group_add + mount socketa

Dla usług używających dockera (`jenkins`, `toolbox`, opcjonalnie `portainer`) dopnij:

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
group_add:
  - "1000"   # GID z `stat -c %g /var/run/docker.sock`
```

Bez tego pojawia się błąd:
`permission denied while trying to connect to the docker API at unix:///var/run/docker.sock`

---

## 5) Obraz Jenkinsa: jakie narzędzia MUSZĄ być dostępne

Przerabialiśmy to praktycznie: pipeline używa `jq` i `curl` w stage’ach fetch/delta/ingest.

Minimalnie Jenkins powinien mieć:

* `docker` (docker-ce-cli)
* `curl`
* `jq`
* `git`
* `bash` + coreutils

Objaw braku: `command -v jq` kończy stage `Prep` błędem (exit 127).

---

## 6) Konfiguracja joba Jenkins (UI) — rekomendowany wariant

### 6.1 Utwórz job

**New Item → Pipeline**

### 6.2 Opcje w `options { ... }` (w pipeline)

W samym pliku pipeline używamy m.in.:

* `disableConcurrentBuilds()` (delta ma sens tylko sekwencyjnie)
* `durabilityHint('MAX_SURVIVABILITY')` (większa trwałość kosztem wydajności)
* `buildDiscarder(logRotator(...))`
* `timestamps()`

> Uwaga: Jenkins może wyświetlić komunikat typu „Resume disabled … switching to … low-durability mode”, jeśli w UI wyłączyłeś resume dla uruchomienia. To nie psuje logiki pipeline, tylko zmienia tryb trwałości wykonania.

### 6.3 Definition: Pipeline script from SCM (najlepsze)

* **Definition:** Pipeline script from SCM
* SCM: Git (Twoje repo)
* **Script Path:** `lab/jenkins/pipeline_one.pipeline`

To rozwiązuje problem „posypało się na brakującej klamrze }” — bo nie wklejasz ręcznie długiego kodu do UI.

### 6.4 Parametry joba

Upewnij się, że masz parametry zgodne z pipeline (minimum):

**Elastic**

* `ES_URL` = `http://elasticsearch:9200` (z perspektywy sieci docker)
* `ES_INDEX` = `sbom-test`

**AID (tożsamość)**

* `AID_ENV` = `lab`
* `AID_APP_ID` = `sbom`
* `AID_OWNER_TEAM` = `K82M`
* `AID_REPO` = `DonkeyJJLove/sbom`
* `AID_VCS_REF`, `AID_APP_VERSION` — mogą zostać domyślne; pipeline ustala best-effort z gita

**Target**

* `TARGET_KIND` = `repo` (na start)
* `TARGET_REF` = `.`

  * repo: `.`
  * image: `myapp:1.2.3`
  * file: `./ścieżka/do/pliku.zip`

**Gate**

* `FAIL_ON` = `none` (na start)
* `FULL_PAYLOAD` = `false` (na start)

---

## 7) Pierwszy realny pomiar repo (krok po kroku)

1. Jenkins → **Build with Parameters**
2. Ustaw:

   * `TARGET_KIND=repo`
   * `TARGET_REF=.`
   * `FAIL_ON=none`
   * `FULL_PAYLOAD=false`
3. Start.

### Artefakty

Po buildzie, w archiwum artefaktów powinny pojawić się pliki `.lab_out/*` (m.in. SBOM/SCAN/DELTA/GATE).

> W praktyce upewniliśmy się, że toolbox zapisuje do **tego samego jenkins_home volume**, a nie do bind-mount ścieżek, które existują tylko wewnątrz kontenera Jenkinsa.

---

## 8) Weryfikacja: Elasticsearch (czy ingest wszedł)

### 8.1 Windows PowerShell — szybki check

```powershell
$EsHost="http://localhost:9200"
$Index="sbom-test"

# indeksy
curl.exe -sS "$EsHost/_cat/indices?v"

# count
Invoke-RestMethod -Method GET -Uri "$EsHost/$Index/_count?pretty" | ConvertTo-Json -Depth 20

# ostatni gate
$body = @{
  size = 1
  sort = @(@{ "@timestamp" = "desc" })
  query = @{ bool = @{ filter = @(@{ term = @{ event_type = "gate" } }) } }
} | ConvertTo-Json -Depth 20

Invoke-RestMethod -Method POST -Uri "$EsHost/$Index/_search?pretty" -ContentType "application/json" -Body $body |
  ConvertTo-Json -Depth 20
```

### 8.2 Yellow na indeksie (1 node)

W 1-node indeks bywa `yellow`, bo replika nie ma gdzie się przypisać.
Ustaw:

```http
PUT sbom-test/_settings
{
  "index": { "number_of_replicas": 0 }
}
```

---

## 9) Weryfikacja: Kibana (Discover)

### 9.1 Data View

Kibana → Stack Management → Data Views:

* Pattern: `sbom-test*`
* Time field: `@timestamp`

### 9.2 Discover: czas i KQL

* Time picker: **Last 24 hours** (na start)
* KQL:

```kql
aid.repo : "DonkeyJJLove/sbom"
```

lub:

```kql
event_type : gate
```

> Jeśli Discover pokazuje mniej hitów niż `_count`, to zwykle kwestia okna czasu (np. „Last 15 minutes”).

---

## 10) Stabilizacja mapowania pól (ważne dla delty)

Pipeline pobiera „previous snapshot” przez `term` na:

* `event_type`
* `aid.app_id`, `aid.env`, `aid.repo`

Żeby `term` działał deterministycznie, pola powinny być **keyword**.

### 10.1 Sprawdź field_caps

```http
GET sbom-test/_field_caps?fields=event_type,aid.app_id,aid.env,aid.repo
```

### 10.2 Template dla `sbom-test*` (zalecane w LAB)

```http
PUT _index_template/sbom-lab-template
{
  "index_patterns": ["sbom-test*"],
  "priority": 200,
  "template": {
    "settings": { "number_of_shards": 1, "number_of_replicas": 0 },
    "mappings": {
      "properties": {
        "@timestamp": { "type": "date" },
        "event_type": { "type": "keyword" },
        "aid": {
          "properties": {
            "app_id": { "type": "keyword" },
            "owner_team": { "type": "keyword" },
            "env": { "type": "keyword" },
            "vcs_ref": { "type": "keyword" },
            "app_version": { "type": "keyword" },
            "repo": { "type": "keyword" }
          }
        }
      }
    }
  }
}
```

Jeśli chcesz zastosować template „na czysto”:

```http
DELETE sbom-test
```

i uruchom pipeline ponownie, potem w Data View odśwież pola.

---

## 11) Typowe awarie — czego się nauczyliśmy (case studies)

### 11.1 `NoSuchMethodError: readProperties`

Powód: brak pluginu Pipeline Utility Steps.
Rozwiązanie: nie używać `readProperties`; AID wyliczać przez `sh(returnStdout:true)`.

### 11.2 `RejectedAccessException: new java.util.Properties`

Powód: Script Security sandbox blokuje konstrukcje Javy w Groovy.
Rozwiązanie: jw. — bez `new Properties()`.

### 11.3 `Bad substitution`

Powód: `sh` w Jenkins używa `/bin/sh` (dash), a nie bash; bash-owe `${VAR/.../...}` nie działa.
Rozwiązanie: budować JSON zapytań przez `jq -n ...`.

### 11.4 `permission denied docker.sock`

Powód: brak uprawnień do `/var/run/docker.sock`.
Rozwiązanie: `group_add` z GID socketa + mount socketa.

### 11.5 `no configuration file provided`

Powód: compose file nie nazywa się domyślnie.
Rozwiązanie: zawsze `-f docker-compose.lab.yml`.

### 11.6 Brak plików `.lab_out/*` po toolbox

Powód: `$WORKSPACE` z kontenera Jenkinsa nie jest ścieżką hosta — bind-mount nie działa jak oczekiwano.
Rozwiązanie: toolbox montuje **ten sam volume** `jenkins_home` co Jenkins (wykryty przez `docker inspect sbom-lab-jenkins`).

### 11.7 Snapshot pusty

Powód: repo nie ma zależności wykrywalnych przez syft (brak manifestów).
Rozwiązanie: snapshot może być pusty; pipeline nie powinien failować na `-s` dla snapshotu.

### 11.8 `jq: Unknown option --argfile`

Powód: `jq` nie ma `--argfile`.
Rozwiązanie: `--slurpfile` dla JSON, a TXT→JSON przez `jq -R -s`.

---
