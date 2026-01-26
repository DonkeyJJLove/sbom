# 05_KIBANA_QUERIES — zapytania i workflow analityczne (LAB Elastic-only)

Ten rozdział to praktyczny „pakiet roboczy” do Kibany: **KQL do Discover**, gotowe **DSL do Dev Tools**, oraz przepisy na szybkie wizualizacje (Lens) dla strumienia zdarzeń generowanych przez pipeline SBOM.

Zakładamy, że pipeline indeksuje zdarzenia do Elasticsearch w indeksie (domyślnie): `sbom-test` i że w Kibanie masz data view `sbom-test*` z polem czasu `@timestamp`.

> Źródło danych: zdarzenia z pipeline (`event_type: sbom_snapshot | sbom | scan | delta | gate`) z polami `aid.*` oraz `payload.*`.

---

## 1) Pre-flight: ustawienia w Kibanie

### 1.1 Data view (konieczne)
**Stack Management → Data Views → Create data view**
- Name / pattern: `sbom-test*`
- Time field: `@timestamp`
- Save

Po zmianach mapowania pól: **Refresh field list**.

### 1.2 Okno czasu (częsta przyczyna „nie widzę danych”)
W Discover ustaw na start:
- **Last 24 hours** (albo Last 7 days)
- Dopiero potem schodź do Last 15 minutes

> Różnica: ES `_count` może pokazywać 6, a Discover 5 — zwykle 1 dokument jest poza oknem czasu.

---

## 2) Słownik pól (co masz w dokumentach)

### 2.1 Pola tożsamości (AID)
- `aid.app_id`
- `aid.env`
- `aid.owner_team`
- `aid.repo`
- `aid.vcs_ref`
- `aid.app_version`

### 2.2 Typ zdarzenia
- `event_type` ∈ `sbom_snapshot`, `sbom`, `scan`, `delta`, `gate`

### 2.3 Najważniejsze pola payload (summary-first)
**gate**
- `payload.decision` ∈ `GO`, `STOP`
- `payload.reason`
- `payload.policy.fail_on` ∈ `none`, `critical`, `high`
- `payload.summary.critical` (liczba)
- `payload.summary.high` (liczba)

**scan**
- `payload.summary.critical`
- `payload.summary.high`
- (opcjonalnie, gdy `FULL_PAYLOAD=true`): `payload.scan` (duży obiekt)

**delta**
- `payload.summary.added` (liczba)
- `payload.summary.removed` (liczba)
- (opcjonalnie) `payload.added[]`, `payload.removed[]` — jeśli utrzymujesz pełną listę w delta.json

**sbom_snapshot**
- `payload.components_snapshot[]` — tablica stringów (może być pusta)
  - przy pustej tablicy pole często **nie istnieje** w indeksie (ES nie indeksuje pustych wartości)

**sbom**
- przy `FULL_PAYLOAD=false`: `payload.summary.mode=summary_only`
- przy `FULL_PAYLOAD=true`: `payload.sbom` (duży obiekt)

---

## 3) Discover: KQL — szybki zestaw zapytań

### 3.1 „Czy w ogóle coś wpływa?”
```kql
_index : "sbom-test"
```

### 3.2 Wszystko dla konkretnego repo i środowiska
```kql
aid.repo : "DonkeyJJLove/sbom" and aid.env : "lab"
```

### 3.3 Tylko zdarzenia gate (decyzje)
```kql
event_type : gate
```

### 3.4 Gate: tylko STOP (blokady)
```kql
event_type : gate and payload.decision : "STOP"
```

### 3.5 Gate: polityka HIGH (fail_on=high)
```kql
event_type : gate and payload.policy.fail_on : "high"
```

### 3.6 Scan: gdzie są jakiekolwiek krytyczne
```kql
event_type : scan and payload.summary.critical >= 1
```

### 3.7 Scan: high lub critical > 0
```kql
event_type : scan and (payload.summary.critical >= 1 or payload.summary.high >= 1)
```

### 3.8 Delta: były zmiany komponentów
```kql
event_type : delta and (payload.summary.added >= 1 or payload.summary.removed >= 1)
```

### 3.9 Snapshot: niepusty snapshot komponentów (tylko gdy array ma wartości)
```kql
event_type : sbom_snapshot and payload.components_snapshot : *
```

### 3.10 SBOM: tylko wpisy summary-only
```kql
event_type : sbom and payload.summary.mode : "summary_only"
```

### 3.11 Najnowszy przebieg „kompletny” (pakiet 5 zdarzeń w jednym czasie)
W praktyce wszystkie 5 eventów ma bardzo zbliżony timestamp. Użyj:
```kql
aid.repo : "DonkeyJJLove/sbom" and aid.env : "lab"
```
i posortuj po `@timestamp desc`, a potem filtruj w tabeli po `event_type`.

---

## 4) Workflow triage: „co się stało w ostatnim buildzie?”

### 4.1 Najpierw gate
KQL:
```kql
aid.repo : "DonkeyJJLove/sbom" and event_type : gate
```
Dodaj kolumny:
- `payload.decision`
- `payload.reason`
- `payload.policy.fail_on`
- `payload.summary.critical`
- `payload.summary.high`

Interpretacja:
- `decision=STOP` → pipeline zakończy się błędem (exit 10)
- `fail_on=high` → STOP gdy `high>0` lub `critical>0`
- `fail_on=critical` → STOP tylko gdy `critical>0`

### 4.2 Potem scan (co wygenerowało stop)
KQL:
```kql
aid.repo : "DonkeyJJLove/sbom" and event_type : scan
```

Jeśli włączysz `FULL_PAYLOAD=true`, będziesz mieć pełny `payload.scan` (duży). Wtedy w Discover zwykle analizujesz pola z `payload.summary.*`, a szczegóły bierzesz z JSON/Dev Tools.

### 4.3 Potem delta (czy zmiana w komponentach wystąpiła)
KQL:
```kql
aid.repo : "DonkeyJJLove/sbom" and event_type : delta
```

Dodaj kolumny:
- `payload.summary.added`
- `payload.summary.removed`

---

## 5) Dev Tools (DSL): gotowe zapytania ES

> W Kibanie: **Dev Tools → Console**

### 5.1 Ostatnie zdarzenia dla repo (downstream do debug)
```http
GET sbom-test/_search
{
  "size": 50,
  "sort": [{ "@timestamp": "desc" }],
  "query": {
    "bool": {
      "filter": [
        { "term": { "aid.repo": "DonkeyJJLove/sbom" } },
        { "term": { "aid.env": "lab" } }
      ]
    }
  }
}
```

### 5.2 Ostatni gate (najważniejszy)
```http
GET sbom-test/_search
{
  "size": 1,
  "sort": [{ "@timestamp": "desc" }],
  "query": {
    "bool": {
      "filter": [
        { "term": { "event_type": "gate" } },
        { "term": { "aid.repo": "DonkeyJJLove/sbom" } },
        { "term": { "aid.env": "lab" } }
      ]
    }
  }
}
```

### 5.3 Ostatni scan (summary)
```http
GET sbom-test/_search
{
  "size": 1,
  "sort": [{ "@timestamp": "desc" }],
  "_source": ["@timestamp","aid","event_type","payload.summary"],
  "query": {
    "bool": {
      "filter": [
        { "term": { "event_type": "scan" } },
        { "term": { "aid.repo": "DonkeyJJLove/sbom" } },
        { "term": { "aid.env": "lab" } }
      ]
    }
  }
}
```

### 5.4 Ostatnia delta (czy były zmiany)
```http
GET sbom-test/_search
{
  "size": 1,
  "sort": [{ "@timestamp": "desc" }],
  "_source": ["@timestamp","aid","event_type","payload.summary","payload.added","payload.removed"],
  "query": {
    "bool": {
      "filter": [
        { "term": { "event_type": "delta" } },
        { "term": { "aid.repo": "DonkeyJJLove/sbom" } },
        { "term": { "aid.env": "lab" } }
      ]
    }
  }
}
```

### 5.5 Ostatni snapshot komponentów (jeśli niepusty)
```http
GET sbom-test/_search
{
  "size": 1,
  "sort": [{ "@timestamp": "desc" }],
  "_source": ["@timestamp","aid","event_type","payload.components_snapshot"],
  "query": {
    "bool": {
      "filter": [
        { "term": { "event_type": "sbom_snapshot" } },
        { "term": { "aid.repo": "DonkeyJJLove/sbom" } },
        { "term": { "aid.env": "lab" } }
      ]
    }
  }
}
```

### 5.6 Histogram: trend critical/high (scan)
```http
GET sbom-test/_search
{
  "size": 0,
  "query": {
    "bool": {
      "filter": [
        { "term": { "event_type": "scan" } },
        { "term": { "aid.repo": "DonkeyJJLove/sbom" } },
        { "term": { "aid.env": "lab" } }
      ]
    }
  },
  "aggs": {
    "by_time": {
      "date_histogram": { "field": "@timestamp", "fixed_interval": "1m" },
      "aggs": {
        "crit_max": { "max": { "field": "payload.summary.critical" } },
        "high_max": { "max": { "field": "payload.summary.high" } }
      }
    }
  }
}
```

### 5.7 Zdarzenia STOP (gate)
```http
GET sbom-test/_search
{
  "size": 25,
  "sort": [{ "@timestamp": "desc" }],
  "query": {
    "bool": {
      "filter": [
        { "term": { "event_type": "gate" } },
        { "term": { "payload.decision": "STOP" } }
      ]
    }
  }
}
```

---

## 6) Przepisy Lens (wizualizacje, bez „wielkiej filozofii”)

### 6.1 „Ryzyko teraz”: ostatni scan (critical/high)
- Visualization: **Metric** (albo Gauge)
- Data view: `sbom-test*`
- KQL filter: `event_type : scan and aid.repo : "DonkeyJJLove/sbom" and aid.env : "lab"`
- Metric field: `payload.summary.critical` (lub `payload.summary.high`)
- Time range: Last 24h

### 6.2 „Decyzje gate w czasie”
- Visualization: **Bar / Line**
- Filter: `event_type : gate and aid.repo : "DonkeyJJLove/sbom"`
- Break down by: `payload.decision`
- X-axis: `@timestamp` date histogram

### 6.3 „Delta zmian komponentów”
- Filter: `event_type : delta and aid.repo : "DonkeyJJLove/sbom"`
- Y: `payload.summary.added` (sum albo max) i osobno `payload.summary.removed`
- X: `@timestamp`

> Jeśli `added/removed` są zawsze 0 (repo bez komponentów), przejdź na `TARGET_KIND=image` i testuj na obrazie kontenera.

---

## 7) Praktyczne wskazówki (co wyszło w praktyce)

### 7.1 Dlaczegoł „snapshot pusty” przy repo
To nie jest błąd pipeline, tylko efekt: `syft` nie zawsze wykrywa komponenty w repo, jeśli repo nie ma manifestów zależności.  
Wtedy delta będzie 0/0. To jest poprawne — ale oznacza, że sensowniejszy test SBOM/Delta uzyskasz dla:
- `TARGET_KIND=image` (np. obraz aplikacji),
- lub repo z realnymi manifestami (npm/pip/maven/gradle itp.).

### 7.2 1-node cluster: indeks „yellow”
Repliki nie mają gdzie się umieścić. Ustaw `number_of_replicas=0` na indeksie (lub w template).

### 7.3 Pola keyword (ważne dla term-query w pipeline)
Pipeline w fetch używa `term`. Jeśli pola typu `aid.repo`/`event_type` nie są keyword, fetch może nie trafiać w poprzedni snapshot.  
Dlatego w LAB warto użyć index template z mapowaniem keyword (opis w `03_JENKINS_PIPELINE.md`).

---

## 8) Minimalny „pakiet zapytań” do szybkiego debug (Discover)

1) Wszystko dla repo:
```kql
aid.repo : "DonkeyJJLove/sbom" and aid.env : "lab"
```

2) Ostatnie decyzje gate:
```kql
event_type : gate and aid.repo : "DonkeyJJLove/sbom"
```

3) Tylko STOP:
```kql
event_type : gate and payload.decision : "STOP"
```

4) Scan ryzyka:
```kql
event_type : scan and aid.repo : "DonkeyJJLove/sbom"
```

5) Delta zmian:
```kql
event_type : delta and aid.repo : "DonkeyJJLove/sbom"
```

---

## 9) Co dalej
W kolejnym kroku możemy:
- dodać „pakiety” filtrów pod dashboard (Lens) i Alerting,
- dołożyć widoki: „per repo / per env / per team”,
- przygotować „wzór indeksu” (template) pod dalsze pola (np. licencje, CVE, komponenty w delcie).

---

## Status
Dokument operacyjny (LAB Elastic-only) dla strumienia zdarzeń pipeline SBOM.
