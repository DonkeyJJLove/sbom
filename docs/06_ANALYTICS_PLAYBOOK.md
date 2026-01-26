# 06_ANALYTICS_PLAYBOOK — praktyczne wnioskowanie nad strumieniem SBOM/SCAN/DELTA/GATE (Elastic LAB)

> Dokument jest „operacyjny”: opisuje **jak** z danych robić wnioski (kwerendy, korelacje, metryki, reguły), oraz **jak przygotować repozytorium sbom**, żeby generowało sensowne delty, a nie tylko „5 eventów dla zasady”.

**Kontekst LAB**: Jenkins → toolbox (Syft/Grype/JQ) → Elasticsearch → Kibana (Discover).  
SBOM traktujemy jako **strumień danych** i sensor stanu bytu (sigillum relationis), a nie jednorazowy raport. :contentReference[oaicite:0]{index=0} :contentReference[oaicite:1]{index=1}

---

## 1. Co jest „źródłem prawdy” i gdzie fizycznie leży SBOM

### 1.1 Źródła prawdy w LAB
1) **Implementacja pipeline**: `lab/jenkins/pipeline_one.pipeline` (definicja etapów, payloadów i warunków).  
2) **Artefakty builda**: `.lab_out/*` (w Jenkins: Archive Artifacts).  
3) **Strumień zdarzeń**: indeks `sbom-test` + data view `sbom-test*` + pole czasu `@timestamp`.

### 1.2 Gdzie znaleźć SBOM „tu i teraz”
- **Plik SBOM** po buildzie:  
  `Jenkins → Build → Artifacts → .lab_out/sbom.cdx.json` (CycloneDX JSON z Syft).
- **W Elasticsearch**:
  - `event_type: "sbom"` **zawiera tylko summary** jeśli `FULL_PAYLOAD=false` (to jest u Ciebie teraz).
  - pełny dokument SBOM w indeksie pojawi się dopiero, gdy `FULL_PAYLOAD=true` (albo gdy wdrożysz osobny event/indeks na pełne SBOMy).  
To jest dokładnie kompromis „S1/S2/S3” (pełny SBOM w analityce vs metadane + link do artefaktu). :contentReference[oaicite:2]{index=2} :contentReference[oaicite:3]{index=3}

---

## 2. Model danych: minimalny schemat do wnioskowania

### 2.1 Stabilna tożsamość (AID)
Utrzymuj `aid.*` jako **oś korelacji**:
- `aid.repo` (najważniejsze w LAB)
- `aid.env` (lab/dev/test/prod)
- `aid.app_id`
- `aid.vcs_ref` (commit / tag / hash)
- `aid.app_version`
- `aid.owner_team`

> Zasada: jeśli nie ma stabilnej osi `aid.*`, to nie ma porządnej korelacji w czasie.

### 2.2 Typy obserwacji (event_type)
Masz już pięć kluczowych klas zdarzeń:
- `sbom_snapshot` — migawka listy komponentów (dla delt)
- `sbom` — SBOM „w sensie semantycznym” (u Ciebie na razie summary-only)
- `scan` — metryki ryzyka (Critical/High + opcjonalnie pełny raport)
- `delta` — różnice pomiędzy przebiegami (added/removed)
- `gate` — decyzja progowa (GO/STOP + uzasadnienie)

To jest klasyczna pętla obserwacja → orientacja → decyzja → akcja (OODA) w wersji DevSecOps. :contentReference[oaicite:4]{index=4}

---

## 3. Najprostsze wnioskowanie (Kibana Discover): pytania, które musisz umieć zadać

### 3.1 Bazowe filtry KQL (kanoniczne)
„Tylko ten byt”:
```kql
aid.repo : "DonkeyJJLove/sbom" and aid.env : "lab"
````

„Tylko decyzje bramki”:

```kql
event_type : "gate"
```

„Tylko skany”:

```kql
event_type : "scan"
```

„Tylko delty”:

```kql
event_type : "delta"
```

### 3.2 Najczęstszy błąd: filtrowanie po `_index` i `event_type` w niewłaściwej składni

W Kibanie filtruj po polach dokumentu (np. `event_type:"sbom"`), a `_index` zostaw jako wybór Data View (`sbom-test*`).
Jeśli w Discover widzisz „No results”, to zwykle:

* zły zakres czasu (Last 15 minutes vs realny timestamp),
* zły Data View (np. nie `sbom-test*`),
* zapytanie w KQL ma złą składnię.

---

## 4. Z czego robi się „analiza”, a nie tylko listing: metryki i relacje

### 4.1 Metryki stanu (per przebieg)

Z `scan` i `gate`:

* `payload.summary.critical`
* `payload.summary.high`
* `payload.decision`, `payload.reason`
* `payload.policy.fail_on`

Z `delta`:

* `payload.summary.added`
* `payload.summary.removed`

Z `sbom_snapshot`:

* długość `payload.components_snapshot[]` (to jest z grubsza „liczba zależności”)

> To są metryki, które później budują KPI procesu (ryzyko, dryf, skuteczność sterowania). 

### 4.2 Metryki zmiany (delta jako sygnał)

Kluczowy jest **DeltaRate** (tempo zmiany):

* `added + removed` w oknie czasu
* i korelacja: czy po dużej delcie rośnie ryzyko (Critical/High)

To jest fundament „SBOM jako strumień”: nie interesuje Cię tylko stan, ale **wektor zmiany**.  

### 4.3 Korelacja przyczynowa (heurystyczna, ale użyteczna)

W praktyce robisz 3 klasy korelacji:

1. **delta ↔ scan**: nowe komponenty → nowe podatności (albo spadek, jeśli aktualizacja naprawiła CVE).
2. **scan ↔ gate**: bramka jako funkcja progu i severity.
3. **delta ↔ gate**: duża delta → większa szansa STOP (nawet jeśli dziś CVE=0 — bo jutro feed CVE może się zmienić).

---

## 5. Kibana: minimalny dashboard, który ma sens (5 paneli)

> Celem nie jest „ładny wykres”, tylko szybka odpowiedź: *czy proces działa i co mówi o ryzyku*.

### Panel 1 — „Gate decisions over time”

* Lens: histogram `@timestamp`
* Breakdown: `payload.decision` (GO/STOP)

### Panel 2 — „Critical/High over time”

* Lens: histogram `@timestamp`
* Metrics: max/avg `payload.summary.critical`, max/avg `payload.summary.high` (dla `event_type:scan`)

### Panel 3 — „Delta volume”

* Lens: histogram `@timestamp`
* Metric: sum(`payload.summary.added`) + sum(`payload.summary.removed`) (dla `event_type:delta`)

### Panel 4 — „Tabela ostatnich przebiegów (pakiet zdarzeń)”

* Data table: `@timestamp`, `aid.vcs_ref`, `event_type`, `payload.decision`, `payload.summary.critical`, `payload.summary.high`
* Filter: `aid.repo`, `aid.env`

### Panel 5 — „Spójność strumienia”

* Pie/Bar: count by `event_type`
* Cel: czy każda iteracja generuje komplet (sbom_snapshot/sbom/scan/delta/gate)

---

## 6. Reguły (Alerting) — jak zamienić wnioski na akcję

### 6.1 Reguły „twarde” (pipeline gate)

To już masz: `FAIL_ON = none|critical|high` → GO/STOP.
To jest kontrola w strefie build (najszybsza pętla). 

### 6.2 Reguły „miękkie” (Kibana alerting)

Przykładowe reguły analityczne:

1. **Nowy STOP**: `event_type:gate AND payload.decision:STOP`

   * akcja: webhook/email (później Jira)
2. **Ryzyko rośnie**: `event_type:scan AND payload.summary.critical > 0`
3. **Delta skokowa**: `event_type:delta AND (payload.summary.added + payload.summary.removed) >= X`

   * to nie jest „vuln”, ale sygnał zwiększonej niepewności

> W dojrzałym modelu: bramka w CI jest strażnikiem, a alerting w SIEM/Elastic jest „drugą głową” — wykrywa trendy i zależności między zdarzeniami. 

---

## 7. Jak zrobić, żeby repo sbom generowało „ciekawe delty” (przykład kontrolowany)

Obecnie `TARGET_KIND=repo` w LAB potrafi dać płytki snapshot (albo pusty) — bo skanujesz katalog, a nie artefakt z realnymi zależnościami runtime. Żeby analiza miała sens, repo musi zawierać **wytwarzane artefakty**, a pipeline powinien umieć je skanować.

### 7.1 Docelowy wzorzec w repo: „3 warstwy zależności”

Dodaj do repo trzy minimalne, ale realne komponenty:

**A) Python (pip)**

* `examples/python-app/requirements.txt`
* minimalny kod (np. `app.py`)
* Cel: dependency graph + CVE (Grype ma dobre pokrycie dla wielu pakietów)

**B) Node (npm)**

* `examples/node-app/package.json`
* Cel: duży ekosystem, częste delty, szybka demonstracja

**C) Container image**

* `examples/container/Dockerfile` (np. bazowy `debian:12-slim` + instalacje)
* Cel: SBOM z pakietów OS (dpkg) + ryzyko z base image

### 7.2 Scenariusz testowy „dwa commity, jedna teza”

1. Commit #1: wersje „bezpieczne” (albo neutralne) — baseline.
2. Commit #2: kontrolowana zmiana:

   * dodaj 1 nową zależność,
   * zaktualizuj 1 zależność,
   * zmień base image (albo doinstaluj pakiet systemowy).

Efekt oczekiwany w danych:

* `delta.added` > 0 i/lub `delta.removed` > 0
* potencjalny wzrost `high/critical` (jeśli trafi się podatność)
* inny `aid.vcs_ref` → możesz korelować przebiegi

### 7.3 Jak wymusić „niebanalne CVE” bez sabotażu repo

Najbezpieczniejsza metoda: **zmiana base image** na starszą (albo dodanie pakietu systemowego, który ma znane CVE), ale w środowisku LAB tylko jako demonstracja, potem revert.
To jest klasyczny wzorzec PoC/pilot: kontrolowana podatność → dowód, że pętla działa.  

---

## 8. Głębsze wnioskowanie: „marker → próg → decyzja” (logika progowa)

W Twojej definicji procesu:

* markerami są: `sbom`, `scan`, `delta`, `gate`
* progi: `FAIL_ON`, plus (w przyszłości) progi dla delty i trendów
* decyzje: GO/STOP (dziś), docelowo też HOLD (wymaga rozbudowy)

To dokładnie ta idea: SBOM jako „pieczęć relacji” ma sens dopiero, gdy staje się sygnałem sterującym w pętli — inaczej jest tylko lustrem przeszłości.  

### 8.1 Jak dodać stan HOLD (kiedy chcesz, a nie musisz)

HOLD ma sens, gdy:

* ryzyko nie jest krytyczne, ale
* sygnał zmiany lub trend wskazuje rosnącą niepewność

Przykładowe reguły HOLD:

* `critical=0 AND high>0` → HOLD (wymaga akceptacji)
* `delta_rate > X` → HOLD (przegląd zmiany zależności)
* `wzrost high przez 3 kolejne buildy` → HOLD (trend negatywny)

---

## 9. Plan działań (konkretne zadania i zmiany)

### 9.1 Zadania „dane”

1. Rozbudować repo (`examples/python-app`, `examples/node-app`, `examples/container`).
2. Dodać do pipeline możliwość skanowania:

   * `TARGET_KIND=repo` (jak jest),
   * oraz **TARGET_KIND=file** (np. skan wygenerowanego artefaktu: `tar.gz`, `wheel`, `zip`),
   * oraz **TARGET_KIND=image** (skan obrazu Dockera, jeśli budujesz image w pipeline).

### 9.2 Zadania „analityka”

3. Ustalić strategię SBOM w ES:

   * **S2** (default): w ES tylko metryki + link do `.lab_out/sbom.cdx.json`
   * **S1/S3** (opcjonalnie): pełny SBOM w ES dla wybranych buildów (np. nightly lub release) 
4. Zbudować dashboard 5-panelowy (sekcja 5).
5. Dodać 3 reguły alertów (STOP, critical>0, delta skokowa).

### 9.3 Zadania „proces”

6. Wprowadzić minimalny runbook:

   * co robi Dev, gdy STOP,
   * co robi AppSec, gdy STOP,
   * kiedy dopuszczasz wyjątek,
   * jak rejestrować wyjątki (docelowo Jira).

---

## Status dokumentu

**Operacyjny**: opisuje praktyczne metody wnioskowania nad kanałem `sbom_snapshot/sbom/scan/delta/gate` w Elastic LAB.
**Następny krok**: rozbudować repo i uruchomić 2–3 kontrolowane iteracje, żeby zobaczyć delty i korelacje, a nie tylko komplet eventów.




