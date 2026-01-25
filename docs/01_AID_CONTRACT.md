# AID_CONTRACT — kontrakt tożsamości bytu (Application Identity Descriptor)

## Cel dokumentu

AID (Application Identity Descriptor) jest **minimalnym kontraktem tożsamości**, który **musi** towarzyszyć każdemu zdarzeniu generowanemu w LAB-ie SBOM.

AID:
- spina zdarzenia w czasie,
- umożliwia korelację SBOM / SCAN / DELTA / GATE,
- jest warunkiem sterowalności procesu (pomiar → próg → decyzja).

Bez AID zdarzenia są **anonimowe** i **niesterowalne**.

---

## Definicja bytu

**Byt aplikacyjny** to logiczny obiekt, który:
- ma tożsamość,
- istnieje w czasie (kolejne obserwacje),
- podlega zmianie (delta),
- może być oceniany i blokowany (gate).

Bytem może być:
- repozytorium kodu,
- obraz kontenera,
- artefakt binarny,
- model / pipeline (w LAB-ie).

AID nie opisuje *jak* byt działa.  
AID opisuje *kim* jest byt w systemie obserwacji.

---

## Struktura AID (MUST)

Każde zdarzenie **MUSI** zawierać obiekt `aid` o następującej strukturze:

```json
"aid": {
  "app_id": "sbom",
  "owner_team": "K82M",
  "env": "lab",
  "vcs_ref": "a1b2c3d",
  "app_version": "v0.1.0",
  "repo": "DonkeyJJLove/sbom"
}
````

### Znaczenie pól

| Pole          | Typ    | Wymagane | Znaczenie                                                         |
| ------------- | ------ | -------- | ----------------------------------------------------------------- |
| `app_id`      | string | MUST     | **Stały identyfikator bytu**. Nie zmienia się między buildami.    |
| `owner_team`  | string | MUST     | Zespół odpowiedzialny za byt (adresat decyzji).                   |
| `env`         | enum   | MUST     | Kontekst środowiska: `lab`, `dev`, `test`, `prod`.                |
| `vcs_ref`     | string | MUST     | Referencja wersji (commit, tag). Nadpisywana automatycznie z VCS. |
| `app_version` | string | MUST     | Wersja logiczna bytu.                                             |
| `repo`        | string | SHOULD   | Identyfikator źródła (repozytorium).                              |

---

## Niezmienność i zmienność

### Niezmienne w czasie

* `app_id`
* `owner_team`
* `repo`

Zmiana tych pól oznacza **inny byt**.

### Zmienne w czasie

* `vcs_ref`
* `app_version`
* `env`

Zmiana tych pól oznacza **inną obserwację tego samego bytu**.

---

## AID a zdarzenia

AID **nie istnieje samodzielnie** — zawsze występuje w kopercie zdarzenia.

Każde zdarzenie w LAB-ie należy do jednego z typów:

```text
sbom   — skład bytu
scan   — podatności / licencje
delta  — zmiana między obserwacjami
gate   — decyzja (GO / STOP)
```

AID jest kluczem, po którym te zdarzenia są łączone.

---

## Kontrakt koperty zdarzenia

Minimalna koperta zdarzenia:

```json
{
  "@timestamp": "2026-01-25T19:13:49.574Z",
  "event_type": "sbom",
  "aid": { ... },
  "msg": "human-readable note",
  "payload": { }
}
```

### Zasady

* `@timestamp` — czas obserwacji w UTC (MUST)
* `event_type` — jeden z dozwolonych typów (MUST)
* `aid` — zgodny z tym kontraktem (MUST)
* `payload` — dane właściwe zdarzenia (MAY być puste lub streszczone)

---

## AID jako klucz korelacji

W Elastic/Kibana:

* **nie korelujemy po indeksie**
* **nie korelujemy po nazwie joba**
* **nie korelujemy po nazwie pliku**

Korelujemy **wyłącznie po `aid.*` + `event_type`**.

Przykład:

```kql
aid.app_id : "sbom" and aid.env : "lab"
```

---

## AID a sterowanie (Gate)

Decyzje typu `gate` **nie są alertami**.
Są **aktami sterowania** dotyczącymi konkretnego bytu.

```json
"event_type": "gate",
"aid": { ... },
"payload": {
  "decision": "STOP",
  "reason": "critical>0"
}
```

Bez AID:

* nie wiadomo **czego** dotyczy decyzja,
* nie wiadomo **kto** jest właścicielem,
* nie da się śledzić skutków w czasie.

---

## Zasady walidacji AID (LAB)

W LAB-ie:

* brak pola AID → **błąd kontraktu**
* zmiana `app_id` → **nowy byt**
* brak spójności AID między zdarzeniami → **brak delty**

Pipeline powinien:

* generować AID automatycznie,
* nadpisywać `vcs_ref` i `app_version` z VCS,
* nie pozwalać na ręczne „dryfowanie” `app_id`.

---

## Dlaczego AID jest kluczowy

AID:

* zamienia logi w dane,
* zamienia dane w wiedzę,
* zamienia wiedzę w decyzje.

Bez AID:

* SBOM jest tylko listą,
* SCAN jest tylko raportem,
* DELTA nie istnieje,
* GATE nie ma adresata.

Z AID:

* byt istnieje,
* byt ma historię,
* byt podlega sterowaniu.

---

## Status dokumentu

**Normatywny.**
Ten kontrakt obowiązuje wszystkie pipeline’y, narzędzia i zdarzenia w LAB-ie.

Zmiany w kontrakcie AID wymagają:

* świadomej decyzji architektonicznej,
* migracji zapytań i dashboardów.

---