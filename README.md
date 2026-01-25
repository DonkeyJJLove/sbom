# SBOM LAB — Elastic-only DevSecOps Playground

Ten repozytorium to **laboratorium analizy SBOM** zbudowane w duchu:
**pomiar → próg → decyzja**,
gdzie **SBOM jest odciskiem relacji bytu (Sigillum Relationis)**, a **AID jest jego tożsamością w czasie**.

To nie jest demo „listy bibliotek”.
To jest **system wnioskowania o oprogramowaniu** oparty o:

* Jenkins (kontroler),
* toolbox (runtime narzędzi: syft / grype),
* Elasticsearch + Kibana (pamięć i analityka).

---

## Co tu znajdziesz (w skrócie)

* **LAB Elastic-only** — bez Splunka, bez SIEM-owych skrótów myślowych
* **Pipeline SBOM**: Build → SBOM → Scan → Delta → Gate → Ingest
* **Jednolity kontrakt danych** (AID + koperta zdarzenia)
* **Gotowe zapytania KQL** do pierwszego wnioskowania
* **Powtarzalne środowisko Docker Compose**

---

## Szybki start (5 minut)

### 1. Wymagania

* Docker + Docker Compose v2
* 8–12 GB RAM (Elastic)

### 2. Uruchom LAB

```bash
cd środowiska-testowe
docker compose -f docker-compose.lab.yml up -d --build
```

### 3. Sprawdź usługi

* Elastic: [http://localhost:9200](http://localhost:9200)
* Kibana: [http://localhost:5601](http://localhost:5601)
* Jenkins: [http://localhost:8080](http://localhost:8080)

---

## Pierwszy realny pomiar SBOM (najważniejsze)

1. Wejdź do **Jenkins → sbom-aid-lab → Build with Parameters**
2. Ustaw:

   * `TARGET_KIND = repo`
   * `TARGET_REF = .`
   * `AID_APP_ID = sbom`
   * `AID_REPO = DonkeyJJLove/sbom`
   * `AID_ENV = lab`
   * `FAIL_ON = none`
   * `FULL_PAYLOAD = false`
3. Uruchom **Build**

To tworzy **pierwszy byt repozytorium w analityce**.

---

## Gdzie są dane?

### Kibana → Discover

Utwórz **Data View**:

* Index pattern: `sbom-*`
* Time field: `@timestamp`
* Kliknij **Refresh field list**

Podstawowe KQL:

```kql
event_type : "sbom" and aid.repo : "DonkeyJJLove/sbom"
```

Jeśli to widzisz — **LAB działa end-to-end**.

---

## Jak wnioskować (minimalny zestaw)

* **Tożsamość bytu**

  ```kql
  aid.app_id : "sbom" and aid.env : "lab"
  ```

* **Skład (SBOM)**

  ```kql
  event_type : "sbom"
  ```

* **Podatności (SCAN)**

  ```kql
  event_type : "scan" and payload.summary.critical > 0
  ```

* **Zmiana (DELTA)**

  ```kql
  event_type : "delta"
  ```

* **Decyzje (GATE)**

  ```kql
  event_type : "gate"
  ```

---

## Struktura repo (czytaj jak mapę)

```text
.
├─ README.md                  ← to jest punkt wejścia
├─ docs/
│  ├─ 01_AID_CONTRACT.md      ← kontrakt tożsamości bytu
│  ├─ 02_LAB_SETUP_ELASTIC.md ← Elastic-only LAB (szczegóły)
│  ├─ 03_JENKINS_PIPELINE.md  ← pipeline + Jenkinsfile
│  ├─ 04_DATA_MODEL.md        ← koperta zdarzeń i pola
│  ├─ 05_KIBANA_QUERIES.md    ← wnioskowanie i KQL
│  └─ 90_APPENDIX_KRYPTOLOGIA.md
├─ lab/
│  ├─ jenkins/                ← Dockerfile Jenkinsa
│  └─ toolbox/                ← Dockerfile narzędzi (syft/grype)
├─ img/                        ← obrazy szkoleniowe
└─ środowiska-testowe/
   ├─ docker-compose.lab.yml  ← DOMYŚLNY LAB
   ├─ .env.lab
   └─ out/                     ← artefakty LAB
```

---

## Filozofia projektu (krótko)

* **SBOM** nie jest raportem, tylko **próbką stanu bytu**
* **Delta** jest ważniejsza niż stan absolutny
* **Gate** to akt decyzyjny, nie alert
* **Elastic** to pamięć epistemiczna, nie tylko logi
* **Jenkins** nie „wie” — Jenkins tylko **uruchamia obserwację**




