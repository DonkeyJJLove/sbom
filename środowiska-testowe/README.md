# Środowiska testowe SBOM (Jenkins + Analiza)

Ten katalog zawiera dwa równoległe środowiska testowe, które realizują ten sam cel operacyjny: Jenkins generuje i przekazuje markery stanu bytu oprogramowania (SBOM, metadane buildu, wyniki skanu podatności/licencji), a następnie dane trafiają do centralnej analityki, gdzie można je przeglądać, filtrować, agregować i zamieniać na decyzje procesowe. Różnica polega wyłącznie na technologii warstwy analitycznej: w wariancie pierwszym jest to Splunk, w wariancie drugim Elastic (Elasticsearch + Kibana).

W obu przypadkach nazwa pliku YAML musi być inna, żeby dało się utrzymywać oba warianty obok siebie w jednym katalogu bez konfliktów i bez „przypadkowego” odpalania nie tego środowiska.

## Nazwy plików compose

Dla wariantu Splunk użyj pliku `docker-compose.splunk.yml`.

Dla wariantu Elastic użyj pliku `docker-compose.elastic.yml`.

Dzięki temu wprost wskazujesz wariant w komendzie `docker compose -f …` i nie mieszasz konfiguracji, wolumenów oraz portów.

## Wariant A: Splunk (on-prem PoC)

Ten wariant uruchamia Splunk oraz Jenkins. Jenkins dostaje zmienną środowiskową z adresem HEC widocznym w sieci dockerowej i może wysyłać eventy bezpośrednio do Splunk HEC. Splunk ma włączony HEC i healthcheck sprawdzający endpoint kolektora, co pozwala Jenkinsowi startować dopiero wtedy, gdy Splunk jest gotowy.

Jeżeli używasz przykładowego hasła i tokena HEC, traktuj to wyłącznie jako PoC do testów lokalnych i podmień wartości na własne w środowisku rzeczywistym.

Uruchomienie:

```bash
docker compose -f docker-compose.splunk.yml up -d --build
````

Dostęp:

```text
Jenkins:    http://localhost:8080
Splunk Web: http://localhost:8000
HEC:        https://localhost:8088
```

## Wariant B: Elastic (Elasticsearch + Kibana) (on-prem PoC)

Ten wariant uruchamia Elasticsearch, Kibana oraz Jenkins. Jenkins dostaje zmienną środowiskową z adresem endpointu indeksowania w Elasticsearch i może wysyłać eventy przez HTTP wprost do indeksu, opcjonalnie przez ingest pipeline normalizujący.

W wersji PoC dla uproszczenia wyłączone jest bezpieczeństwo (security) w Elasticsearch i Kibana, żeby uniknąć narzutu konfiguracji certyfikatów i kluczy API. W środowisku realnym zwykle włączasz security, dodajesz TLS, a ingest prowadzisz przez Elastic Agent lub Logstash, ale tutaj trzymamy maksymalnie krótką ścieżkę testową.

Uruchomienie:

```bash
docker compose -f docker-compose.elastic.yml up -d --build
```

Dostęp:

```text
Jenkins:       http://localhost:8080
Kibana:        http://localhost:5601
Elasticsearch: http://localhost:9200
```

## Zasada wspólna dla obu wariantów: „marker → analityka → decyzja”

Oba środowiska są zbudowane tak, aby testować ten sam mechanizm sterowania, tylko na innej technologii. Jenkins wytwarza marker (zdarzenie opisujące „byt” buildu i jego relacje, np. SBOM lub skrót wyników skanu), wysyła go do warstwy analitycznej, a warstwa analityczna umożliwia progi, korelacje i konsekwencje procesowe (alert, ticket, bramka w CI/CD). Zmienia się tylko transport i składnia narzędzia, a nie sens sterowania.

## Procesowa analiza software: flow analityczny SBOM

Procesowa analiza software zaczyna się od przyjęcia, że pojedynczy build nie jest tylko „kompilacją”, ale zdarzeniem w łańcuchu produkcji. SBOM jest wtedy markerem relacji i kompozycji, a nie archiwum „listy bibliotek”. W praktyce budujesz strumień zdarzeń, w którym każdy etap dodaje kontekst, usuwa niejednoznaczność i umożliwia kolejne kroki automatyzacji. To daje dwa równoległe tryby pracy: tryb bieżący (reakcja i bramkowanie) oraz tryb historyczny (trend, regresja, audyt, dowód).

Flow analityczny można czytać jak prostą sekwencję, która jest asymetryczna i asynchroniczna. Asymetryczna, bo jeden węzeł (analityka) widzi wiele systemów budujących i porównuje je w jednym języku. Asynchroniczna, bo generacja (CI/CD) i interpretacja (analityka) nie muszą dziać się w tym samym czasie, a mimo to pozostają porównywalne, jeżeli trzymasz stabilny kontrakt pól i indeksowania.

Minimalny przepływ w PoC wygląda tak: Jenkins wytwarza artefakt i metadane (AID i kontekst buildu), generuje SBOM i wynik skanu, wysyła zdarzenie do centralnej analityki, analityka normalizuje zdarzenie do wspólnego schematu, zapisuje w indeksie, a następnie uruchamia zapytania, agregacje i reguły. Wynik reguły wraca do procesu jako sterowanie, czyli decyzja: przepuść, ostrzeż, wstrzymaj, utwórz ticket, wymuś upgrade zależności, zablokuj release.

Optymalizacja w tym modelu nie polega na „dodaniu więcej danych”, tylko na kontroli kształtu zdarzeń i ich retencji. W praktyce optymalizujesz objętość (nie zawsze wysyłasz pełny SBOM, czasem tylko streszczenie i hash), koszt indeksowania (stabilne mapowania, proste typy, mało pól tekstowych), koszt korelacji (konsekwentne klucze: app_id, app_version, vcs_ref, build_id, job) oraz koszt decyzji (progi i reguły, które są deterministyczne i odwracalne). Ten sam model ma też charakter dowodowy (audyt), predykcyjny (trend i ryzyko w czasie), ekonomiczny (koszt zależności i podatności) oraz operacyjny (SLA reakcji, bramki, zgodność).

## Runbook: bootstrap i „polowanie na dane” (Elastic)

W PowerShell nie używaj `curl` (to alias), tylko `curl.exe` albo `Invoke-RestMethod`. Komendy poniżej są zgodne z PowerShell.

### Sygnał życia (PowerShell)

```powershell
curl.exe -sS "http://localhost:9200"
curl.exe -sS "http://localhost:9200/_cluster/health?pretty"
curl.exe -sS "http://localhost:5601/api/status"
```

### Bootstrap (pipeline + template + indeksy) (PowerShell)

```powershell
$sbomPipe = @{
  description = "SBOM normalize"
  processors  = @(@{ set = @{ field = "@timestamp"; value = "{{_ingest.timestamp}}" } })
} | ConvertTo-Json -Compress -Depth 32

Invoke-RestMethod -Method Put -Uri "http://localhost:9200/_ingest/pipeline/sbom-normalize" -ContentType "application/json" -Body $sbomPipe

$vulnPipe = @{
  description = "VULN normalize"
  processors  = @(@{ set = @{ field = "@timestamp"; value = "{{_ingest.timestamp}}" } })
} | ConvertTo-Json -Compress -Depth 32

Invoke-RestMethod -Method Put -Uri "http://localhost:9200/_ingest/pipeline/vuln-normalize" -ContentType "application/json" -Body $vulnPipe

$sbomTpl = @{
  index_patterns = @("sbom-events-*")
  template = @{
    settings = @{ number_of_shards = 1; number_of_replicas = 0 }
    mappings = @{
      dynamic = $true
      properties = @{
        "@timestamp" = @{ type = "date" }
        app_id       = @{ type = "keyword" }
        app_version  = @{ type = "keyword" }
        vcs_ref      = @{ type = "keyword" }
        owner_team   = @{ type = "keyword" }
        type         = @{ type = "keyword" }
        source       = @{ type = "keyword" }
        build_id     = @{ type = "keyword" }
        job          = @{ type = "keyword" }
      }
    }
  }
} | ConvertTo-Json -Compress -Depth 32

Invoke-RestMethod -Method Put -Uri "http://localhost:9200/_index_template/sbom-template" -ContentType "application/json" -Body $sbomTpl

$vulnTpl = @{
  index_patterns = @("vuln-events-*")
  template = @{
    settings = @{ number_of_shards = 1; number_of_replicas = 0 }
    mappings = @{
      dynamic = $true
      properties = @{
        "@timestamp" = @{ type = "date" }
        app_id       = @{ type = "keyword" }
        app_version  = @{ type = "keyword" }
        vcs_ref      = @{ type = "keyword" }
        owner_team   = @{ type = "keyword" }
        type         = @{ type = "keyword" }
        source       = @{ type = "keyword" }
        build_id     = @{ type = "keyword" }
        job          = @{ type = "keyword" }
        severity     = @{ type = "keyword" }
        cve          = @{ type = "keyword" }
      }
    }
  }
} | ConvertTo-Json -Compress -Depth 32

Invoke-RestMethod -Method Put -Uri "http://localhost:9200/_index_template/vuln-template" -ContentType "application/json" -Body $vulnTpl

Invoke-RestMethod -Method Put -Uri "http://localhost:9200/sbom-events-000001" | Out-Null
Invoke-RestMethod -Method Put -Uri "http://localhost:9200/vuln-events-000001" | Out-Null
```

### Test ingest (symulacja zdarzenia z Jenkinsa) (PowerShell)

```powershell
$doc = @{
  app_id      = "demo"
  app_version = "1.0.0"
  source      = "manual"
  job         = "test"
  build_id    = "b-1"
  msg         = "hello from PS"
} | ConvertTo-Json -Compress

Invoke-RestMethod -Method Post `
  -Uri "http://localhost:9200/sbom-events-000001/_doc?pipeline=sbom-normalize" `
  -ContentType "application/json" `
  -Body $doc
```

### Polowanie na dane (czy Jenkins coś wrzucił?) (PowerShell)

```powershell
curl.exe -sS "http://localhost:9200/_cat/indices?format=json"
curl.exe -sS "http://localhost:9200/sbom-events-*/_count?pretty"
curl.exe -sS "http://localhost:9200/vuln-events-*/_count?pretty"
curl.exe -sS "http://localhost:9200/sbom-events-*/_search?size=10&sort=@timestamp:desc&pretty"
curl.exe -sS "http://localhost:9200/vuln-events-*/_search?size=10&sort=@timestamp:desc&pretty"
```

Jeżeli widzisz dokumenty tylko „manual”, a nie z Jenkinsa, to znaczy, że Jenkins jeszcze nie publikuje zdarzeń w jobie/pipeline albo publikuje w innym formacie/indeksie. Wtedy tropem jest logika w Jenkinsfile (gdzie robisz POST) oraz to, czy Jenkins ma dostęp sieciowy do `http://elasticsearch:9200` w sieci dockerowej.

## Runbook: szybki test HEC (Splunk)

W PowerShell do testów Splunka używaj `curl.exe` albo `Invoke-RestMethod`, bo `curl` w PowerShell to alias.

```powershell
curl.exe -k "https://localhost:8088/services/collector/health"

$token = "00000000-0000-0000-0000-000000000000"
$headers = @{ Authorization = "Splunk $token"; "Content-Type" = "application/json" }
$body = @{ event = @{ msg = "hello"; source = "sbom-poc" }; sourcetype = "sbom:test" } | ConvertTo-Json -Compress

Invoke-RestMethod -Method Post -Uri "https://localhost:8088/services/collector/event" -Headers $headers -Body $body
```

## Szybkie sprzątanie po testach

Jeżeli chcesz usunąć kontenery i wolumeny danego wariantu, uruchom komendę dla konkretnego pliku compose:

```bash
docker compose -f docker-compose.splunk.yml down -v
```

albo:

```bash
docker compose -f docker-compose.elastic.yml down -v
```

To usuwa również wolumeny danych, więc traktuj to jako „reset środowiska”.

```
::contentReference[oaicite:0]{index=0}
```
