# 04_DATA_MODEL — model danych LAB SBOM (Elastic-only)

## Cel dokumentu

Ten dokument definiuje **kanoniczny model danych** używany w LAB-ie SBOM.  
Model nie jest „formatem logów”, lecz **modelem obserwacji bytu w czasie**.

Dane są projektowane tak, aby:
- umożliwiać korelację,
- umożliwiać analizę zmiany (delta),
- umożliwiać decyzje (gate),
- być stabilne w Elasticsearch i Kibanie.

---

## Zasada nadrzędna

> **Nie indeksujemy wszystkiego.  
> Indeksujemy to, co jest potrzebne do wnioskowania.**

Dlatego:
- rdzeń (`aid`, `event_type`, `@timestamp`) jest zawsze obecny,
- `payload` ma tryb **summary-first**,
- pełne dane są opcjonalne (`FULL_PAYLOAD=true`).

---

## Typy zdarzeń (event_type)

Każde zdarzenie w LAB-ie **MUSI** mieć jednoznaczny `event_type`.

| event_type | Znaczenie | Rola w analizie |
|-----------|----------|-----------------|
| `sbom` | Skład bytu | Stan strukturalny |
| `scan` | Podatności / licencje | Ryzyko |
| `delta` | Zmiana między stanami | Dynamika |
| `gate` | Decyzja sterująca | Sterowanie |
| `sbom_snapshot` | Migawka komponentów | Podstawa delty |

---

## Kanoniczna koperta zdarzenia

Każde zdarzenie **MUSI** spełniać ten kontrakt:

```json
{
  "@timestamp": "2026-01-25T19:13:49.574Z",
  "event_type": "sbom",
  "aid": { ... },
  "msg": "human-readable note",
  "payload": { }
}
````

### Znaczenie pól

| Pole         | Typ     | Wymagane | Uwagi                                       |
| ------------ | ------- | -------- | ------------------------------------------- |
| `@timestamp` | date    | MUST     | Czas obserwacji (UTC)                       |
| `event_type` | keyword | MUST     | Typ zdarzenia                               |
| `aid`        | object  | MUST     | Tożsamość bytu (patrz `01_AID_CONTRACT.md`) |
| `msg`        | string  | SHOULD   | Krótka notatka dla człowieka                |
| `payload`    | object  | MAY      | Dane właściwe zdarzenia                     |

---

## Model AID (przypomnienie)

AID jest **kluczem korelacji** i nie jest powtarzany w `payload`.

```json
"aid": {
  "app_id": "sbom",
  "owner_team": "K82M",
  "env": "lab",
  "vcs_ref": "a1b2c3d",
  "app_version": "v0.1.0",
  "repo": "DonkeyJJLove/sbom"
}
```

Zmiana `app_id` = **nowy byt**
Zmiana `vcs_ref` = **nowa obserwacja**

---

## Zdarzenie: sbom

### Cel

Opisuje **skład bytu w danym momencie**.

### Payload (summary-first)

```json
"payload": {
  "summary": {
    "note": "sbom generated",
    "mode": "summary_only"
  }
}
```

### Payload (FULL_PAYLOAD=true)

```json
"payload": {
  "sbom": { ... pełny CycloneDX JSON ... }
}
```

> **Zasada:**
> `sbom` odpowiada na pytanie *„z czego byt się składa”*.

---

## Zdarzenie: sbom_snapshot

### Cel

Lekka migawka komponentów, używana **wyłącznie do liczenia delty**.

```json
"payload": {
  "components_snapshot": [
    "pkg:npm/lodash@4.17.21",
    "pkg:pypi/requests@2.31.0"
  ]
}
```

* bez zagnieżdżeń,
* lista stringów,
* tanie w indeksowaniu.

---

## Zdarzenie: scan

### Cel

Opisuje **ryzyko** wynikające ze składu.

### Payload (summary)

```json
"payload": {
  "summary": {
    "critical": 0,
    "high": 2,
    "medium": 5
  }
}
```

### Payload (FULL_PAYLOAD=true)

```json
"payload": {
  "summary": { ... },
  "scan": { ... pełny raport Grype ... }
}
```

> `scan` odpowiada na pytanie *„czy skład jest bezpieczny”*.

---

## Zdarzenie: delta

### Cel

Opisuje **zmianę bytu w czasie**.

```json
"payload": {
  "summary": {
    "added": 2,
    "removed": 1
  },
  "added": [
    "pkg:npm/axios@1.6.0"
  ],
  "removed": [
    "pkg:npm/request@2.88.2"
  ]
}
```

> **Delta jest ważniejsza niż stan absolutny.**

---

## Zdarzenie: gate

### Cel

Reprezentuje **decyzję sterującą**, nie alert.

```json
"payload": {
  "policy": {
    "fail_on": "high"
  },
  "summary": {
    "critical": 0,
    "high": 1
  },
  "decision": "STOP",
  "reason": "high_or_critical>0"
}
```

### Semantyka

* `GO` → obserwacja dopuszczona
* `STOP` → byt **zablokowany decyzją**

> Gate **musi** mieć adresata → `aid.owner_team`.

---

## Relacje czasowe

Dla jednego builda oczekiwany ciąg:

```text
sbom_snapshot → sbom → scan → delta → gate
```

Brak któregoś elementu:

* brak `sbom_snapshot` → brak delty
* brak `gate` → brak sterowania

---

## Mapowanie w Elasticsearch (wymagane)

Kluczowe pola **MUSZĄ** być `keyword`:

* `event_type`
* `aid.*`

Bez tego:

* filtrowanie w Kibanie jest niejednoznaczne,
* korelacja jest błędna.

Zobacz `02_LAB_SETUP_ELASTIC.md` (index template).

---

## Minimalne zapytania wnioskowania

* **Tożsamość bytu**

  ```kql
  aid.app_id : "sbom" and aid.env : "lab"
  ```

* **Ryzyko**

  ```kql
  event_type : "scan" and payload.summary.critical > 0
  ```

* **Zmiana**

  ```kql
  event_type : "delta" and payload.summary.added > 0
  ```

* **Decyzje**

  ```kql
  event_type : "gate" and payload.decision : "STOP"
  ```

---

## Czego ten model celowo NIE robi

* ❌ nie przechowuje pełnych artefaktów jako default
* ❌ nie dubluje AID w payload
* ❌ nie miesza semantyki zdarzeń

To **model do sterowania**, nie archiwum.

---

## Status dokumentu

**Normatywny.**
Każde narzędzie i pipeline w LAB-ie musi produkować dane zgodne z tym modelem.

Zmiana modelu = zmiana zasad wnioskowania.

---
