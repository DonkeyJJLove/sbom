# Pipeline SBOM LAB – konfiguracja Jenkins

Ten pipeline realizuje pełny cykl sterowania bezpieczeństwem artefaktu:
**Build → SBOM → Scan → Delta → Gate → Ingest**.

Nie generujemy „ładnych raportów”.  
Generujemy **zdarzenia sterujące**, spójne w czasie przez AID.

---

## Cel pipeline

Pipeline ma zawsze zakończyć się:
- wysłaniem danych do Elastic,
- decyzją `GO / STOP`,
- zapisem śladu bytu (SBOM jako *Sigillum Relationis*).

Każdy run jest obserwacją stanu systemu.

---

## Założenia środowiskowe

Agent Jenkins:
- Linux / WSL (shell `sh`)
- Dostępne narzędzia:
  - `syft`
  - `grype`
  - `jq`
  - `curl`

Elastic:
- API dostępne po HTTP (`9200`)
- Indeks typu `sbom-*`

---

## Konfiguracja joba (UI)

### General

- **Do not allow concurrent builds**  
  Zapewnia jedną, spójną sekwencję stanów (delta ma sens).

- **Do not allow pipeline to resume after controller restart**  
  Przerwany pomiar = nieważny pomiar.

- **Discard old builds**  
  Jenkins nie jest archiwum. Historią jest Elastic.

---

## Parametry pipeline

### Parametry ingestu

| Parametr | Znaczenie |
|--------|-----------|
| `ES_URL` | Adres Elasticsearch |
| `ES_INDEX` | Indeks docelowy |

Sterują **gdzie trafia zdarzenie**.

---

### Parametry AID (tożsamość bytu)

| Parametr | Znaczenie |
|-------|----------|
| `AID_APP_ID` | Stały identyfikator aplikacji |
| `AID_OWNER_TEAM` | Właściciel odpowiedzialności |
| `AID_ENV` | Środowisko (`lab/dev/test/prod`) |
| `AID_REPO` | Repozytorium |
| `AID_VCS_REF` | Commit (nadpisywany z git) |
| `AID_APP_VERSION` | Wersja (nadpisywana z git/tag) |

AID spina wszystkie zdarzenia (`sbom`, `scan`, `delta`, `gate`) w jeden byt.

---

### Parametry skanowania

| Parametr | Znaczenie |
|--------|-----------|
| `TARGET_KIND` | Co skanujemy (`repo/image/file`) |
| `TARGET_REF` | Ścieżka / obraz / artefakt |

Pipeline jest **agnostyczny względem źródła**.

---

### Parametry polityki (gate)

| Parametr | Znaczenie |
|--------|-----------|
| `FAIL_ON` | Próg blokady (`none/critical/high`) |
| `FULL_PAYLOAD` | Czy indeksować pełne JSON-y |

To jest **sterowanie**, nie konfiguracja na sztywno.

---

## Triggery

- **GitHub hook trigger for GITScm polling** – **ON**
- Brak cronów, brak zależności od innych jobów

Zdarzeniem inicjującym jest **zmiana bytu**, nie zegar.

---

## Co pipeline robi technicznie

### 1. Derive AID
Jeśli repo jest git:
- pobiera commit (`vcs_ref`)
- wyznacza wersję (`tag` lub `commit`)

### 2. SBOM
- `syft` generuje CycloneDX JSON
- powstaje snapshot komponentów

### 3. Scan
- `grype` skanuje SBOM
- liczone są severity

### 4. Delta
- porównanie snapshotów
- powstaje zdarzenie `event_type=delta`

### 5. Gate
- decyzja `GO / STOP`
- powstaje zdarzenie `event_type=gate`

### 6. Ingest
- każde zdarzenie trafia do Elastic
- Jenkins **nie jest źródłem prawdy**

---

## Zdarzenia w Elastic

Pipeline generuje:

- `sbom_snapshot` – lekki, pod deltę  
- `sbom` – skład  
- `scan` – podatności  
- `delta` – zmiany  
- `gate` – decyzja

Każde zdarzenie ma:
- `@timestamp`
- `event_type`
- `aid.*`
- `payload`

---

## Dlaczego tak

- Jenkins = generator obserwacji  
- Elastic = pamięć operacyjna  
- AID = tożsamość w czasie  
- SBOM = odcisk relacji  
- Gate = akt decyzyjny  

To **cybernetyczna pętla sterowania**, nie raport bezpieczeństwa.

---

## Następne kroki

- Dashboardy w Kibanie (5 perspektyw)
- Reguły alertowe
- Integracja z Jira / SOAR
- Wersja prod (S3 payload)

LAB jest punktem startu, nie celem.
