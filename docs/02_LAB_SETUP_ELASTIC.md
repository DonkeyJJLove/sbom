# 02_LAB_SETUP_ELASTIC — uruchomienie LAB-u (Elastic-only)

## Cel dokumentu

Ten dokument opisuje **jak uruchomić i zweryfikować LAB SBOM oparty wyłącznie o Elasticsearch + Kibana**.  
Celem LAB-u nie jest logowanie, lecz **wnioskowanie**: pomiar → próg → decyzja.

Zakładamy:
- **Elastic** jako pamięć i analitykę,
- **Kibana** jako interfejs wnioskowania,
- **Jenkins + toolbox** jako generator obserwacji (SBOM/SCAN/DELTA/GATE).

---

## Wymagania

- Docker + Docker Compose v2
- 8–12 GB RAM (Elastic)
- Dostęp do portów:
  - `9200` (Elasticsearch)
  - `5601` (Kibana)
  - `8080` (Jenkins)

---

## Struktura uruchomieniowa

LAB uruchamiany jest z katalogu:

```text
środowiska-testowe/
├─ docker-compose.lab.yml
├─ .env.lab          (opcjonalnie)
└─ out/              (artefakty LAB)
````

> **Uwaga**
> Ścieżki `build.context` w compose są liczone **względem `środowiska-testowe/`**.

---

## Uruchomienie LAB-u

### Krok 1 — start kontenerów

```bash
cd środowiska-testowe
docker compose -f docker-compose.lab.yml up -d --build
```

### Krok 2 — weryfikacja usług

```bash
curl -s http://localhost:9200
curl -s http://localhost:5601/api/status
```

Oczekiwane:

* Elastic zwraca JSON z `cluster_name` i `version`
* Kibana odpowiada statusem `available`

---

## Elasticsearch — zasady pracy w LAB

### Tryb pracy

* `single-node`
* `xpack.security.enabled=false`
* brak TLS i auth (LAB)

### Indeksy

* rekomendowany wzorzec: `sbom-*`
* domyślny indeks LAB: `sbom-test`

Elastic jest **jedynym źródłem prawdy** dla:

* historii bytu,
* delty zmian,
* decyzji gate.

---

## (WAŻNE) Kontrakt indeksu — index template

Aby uniknąć:

* analizowania tokenów (`sbom` ≈ `sbom-test-manual`),
* niejednoznacznych filtrów w Kibanie,

**należy wgrać index template** przed właściwą analizą.

### Template (minimalny)

```json
PUT _index_template/sbom-lab-template
{
  "index_patterns": ["sbom-*"],
  "template": {
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
        },
        "payload": { "type": "object", "enabled": true }
      }
    }
  }
}
```

Wgraj:

```bash
curl -X PUT http://localhost:9200/_index_template/sbom-lab-template \
  -H "Content-Type: application/json" \
  -d @index-template-sbom.json
```

> **Dlaczego to ważne**
> Bez template Kibana filtruje po `text`, a nie po tożsamości bytu.

---

## Kibana — konfiguracja Data View

### Krok 1 — utwórz Data View

* **Index pattern:** `sbom-*`
* **Time field:** `@timestamp`

### Krok 2 — odśwież pola

Po pierwszym ingest:

* **Stack Management → Data Views → sbom-* → Refresh field list**

To przełącza Discover z „surowych dokumentów” w **dane strukturalne**.

---

## Test ingestu (sanity check)

Wyślij ręcznie zdarzenie testowe:

```bash
curl -X POST http://localhost:9200/sbom-test/_doc?refresh=true \
  -H "Content-Type: application/json" \
  -d '{
    "@timestamp":"2026-01-25T21:00:00Z",
    "event_type":"sbom",
    "aid":{
      "app_id":"sbom",
      "owner_team":"K82M",
      "env":"lab",
      "vcs_ref":"manual",
      "app_version":"0.0.0",
      "repo":"DonkeyJJLove/sbom"
    },
    "msg":"elastic sanity check"
  }'
```

W Kibanie → Discover:

```kql
event_type : "sbom" and aid.app_id : "sbom"
```

Jeśli widzisz dokument → **Elastic + Kibana są gotowe**.

---

## Co NIE jest celem tego etapu

* ❌ analiza podatności
* ❌ dashboardy
* ❌ polityki gate

Ten etap kończy się, gdy:

* Elastic przyjmuje zdarzenia,
* Kibana widzi pola `aid.*`,
* filtry `.keyword` działają jednoznacznie.

---

## Następny krok

Po poprawnym setupie Elastic:

➡ **`03_JENKINS_PIPELINE.md`**
Konfiguracja joba Jenkins i pierwsza realna obserwacja repozytorium (SBOM z `TARGET_KIND=repo`).

---

## Status dokumentu

**Operacyjny / normatywny dla LAB-u Elastic-only.**
Każdy pipeline i tutorial zakłada wykonanie tych kroków.

---
