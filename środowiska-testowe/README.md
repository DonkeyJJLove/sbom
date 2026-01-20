# Środowiska testowe SBOM (Jenkins + Analiza)

Ten katalog zawiera dwa równoległe środowiska testowe, które realizują ten sam cel operacyjny: Jenkins generuje/przekazuje zdarzenia (np. wynik skanu SBOM lub metadane builda), a następnie dane trafiają do centralnej analityki, gdzie można je przeglądać, filtrować i budować progi/korelacje. Różnica polega wyłącznie na technologii warstwy analitycznej: w wariancie pierwszym jest to Splunk, w wariancie drugim Elastic (Elasticsearch + Kibana).

W obu przypadkach nazwa pliku YAML musi być inna, żeby dało się utrzymywać oba warianty obok siebie w jednym katalogu bez konfliktów i bez „przypadkowego” odpalania nie tego środowiska.

## Nazwy plików compose

Dla wariantu Splunk użyj pliku `docker-compose.splunk.yml`.

Dla wariantu Elastic użyj pliku `docker-compose.elastic.yml`.

Dzięki temu wprost wskazujesz wariant w komendzie `docker compose -f …` i nie mieszasz konfiguracji, wolumenów oraz portów.

## Wariant A: Splunk (on-prem PoC)

Ten wariant uruchamia Splunk oraz Jenkins. Jenkins dostaje zmienną środowiskową z adresem HEC widocznym w sieci dockerowej i może wysyłać eventy bezpośrednio do Splunk HEC. Splunk ma włączony HEC i healthcheck sprawdzający endpoint kolektora, co pozwala Jenkinsowi startować dopiero wtedy, gdy Splunk jest gotowy.

Jeżeli używasz przykładowego hasła i tokena HEC, traktuj to wyłącznie jako PoC do testów lokalnych i koniecznie podmień wartości na własne w środowisku rzeczywistym.

Uruchomienie:

```bash
docker compose -f docker-compose.splunk.yml up -d --build
````

Dostęp:

```text
Jenkins: http://localhost:8080
Splunk Web: http://localhost:8000
HEC: https://localhost:8088
```

## Wariant B: Elastic (Elasticsearch + Kibana) (on-prem PoC)

Ten wariant uruchamia Elasticsearch, Kibana oraz Jenkins, a dodatkowo wykonuje jednorazowy „setup” (utworzenie minimalnego index template i ingest pipeline pod zdarzenia SBOM). Jenkins dostaje zmienną środowiskową z adresem endpointu indeksowania w Elasticsearch i może wysyłać eventy przez HTTP wprost do indeksu, opcjonalnie przez pipeline normalizujący.

W wersji PoC dla uproszczenia wyłączone jest bezpieczeństwo (security) w Elasticsearch i Kibana, żeby uniknąć narzutu konfiguracji certyfikatów i kluczy API. W środowisku realnym zwykle włączasz security, dodajesz TLS, a ingest prowadzisz przez Elastic Agent lub Logstash, ale tutaj trzymamy maksymalnie krótką ścieżkę testową.

Uruchomienie:

```bash
docker compose -f docker-compose.elastic.yml up -d --build
```

Dostęp:

```text
Jenkins: http://localhost:8080
Kibana: http://localhost:5601
Elasticsearch: http://localhost:9200
```

## Zasada wspólna dla obu wariantów: „marker → analityka → decyzja”

Oba środowiska są zbudowane tak, abyś mógł testować dokładnie ten sam mechanizm, tylko na innej technologii: Jenkins wytwarza marker (zdarzenie opisujące „byt” builda i jego relacje, np. SBOM lub skrót wyników skanu), wysyła go do warstwy analitycznej, a Ty budujesz na tym progi, korelacje oraz konsekwencje procesowe (alert, ticket, bramka w CI/CD).

Jeżeli przenosisz pipeline między wariantami, zmienia się tylko adres endpointu ingestu i ewentualnie format payloadu, natomiast sens sterowania pozostaje identyczny.

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
