# Środowiska testowe — LAB do analizy SBOM (Jenkins + backend: Elastic/Kibana **lub** Splunk)

Ten katalog jest „poligonem” dla całego repo: tu uruchamiasz lokalne środowisko, podłączasz aplikację (repo/artefakt), generujesz SBOM, skanujesz podatności, liczysz delty zmian i oglądasz to w analityce tak, jak robi się to produkcyjnie: wieloperspektywowo (dev, AppSec, SOC, compliance, ops). Celem nie jest „ładny SBOM”, tylko sterowanie: pomiar → próg → akcja, gdzie SBOM jest pieczęcią relacji (*Sigillum Relationis*), a AID jest tożsamością bytu, która spina wszystko w czasie.

Kluczowa zasada architektury LAB: **Jenkins + toolbox są wspólnym rdzeniem**, a analityka jest wybierana jako **alternatywny backend** — uruchamiasz albo profil `elastic` (Elastic + Kibana), albo profil `splunk` (Splunk + HEC). Pliki nie dublują funkcji, tylko jedna konfiguracja `docker-compose.lab.yml` steruje wariantami.

## Co dostajesz z tego LAB-u

Po uruchomieniu masz działający „core” (Jenkins + toolbox) oraz wybrany backend analityki:

Jeżeli wybierzesz `elastic`, dostajesz Elasticsearch (API na 9200) i Kibana (UI na 5601) oraz widok w Discover, gdzie widzisz zdarzenia z `aid.*` (AID_CONTRACT) i `event_type`. To jest minimalna baza pod dalszą analizę: możesz filtrować, agregować, budować dashboardy i alerty.

Jeżeli wybierzesz `splunk`, dostajesz Splunk Web (UI na 8000) i HEC (ingest na 8088). Dane widzisz w wyszukiwarce Splunk (SPL), a pola AID i `event_type` analizujesz przez `spath` lub ekstrakcje (w LAB najprościej przez `spath`).

Docelowo LAB obsługuje cztery strumienie danych dla każdej aplikacji: SBOM (skład), SCAN (podatności/licencje), DELTA (zmiany pomiędzy kolejnymi stanami), oraz GATE (decyzja/progi i wyjątki). To nie są „raporty” — to obserwacje bytu w czasie.

## Słownik pojęć w tym repo

SBOM to „odcisk relacji” artefaktu. Nie interesuje nas tylko to, co jest w środku, ale to, co z tego wynika: ryzyko, zgodność, dryf, trendy.

AID_CONTRACT to minimalna tożsamość bytu. AID nie jest „dla ozdoby”. Jest kluczem korelacji i sterowania: bez niego SBOM/scan/delta są anonimowe, a proces nie jest sterowalny.

`event_type` jest prostym rozróżnieniem rodzaju obserwacji: `sbom` (skład), `scan` (podatności/licencje), `delta` (różnice), `gate` (decyzja).

`@timestamp` to czas zdarzenia w UTC (Kibana używa go do filtrów czasu, trendów i alertów; w Splunk też warto mieć go w evencie, nawet jeśli Splunk ma własne `_time`).

## Standard danych (AID + koperta zdarzenia)

W tym LAB-u każde zdarzenie ma stałą „kopertę”. Minimalnie:

```json
{
  "@timestamp": "2026-01-25T19:13:49.574Z",
  "event_type": "sbom",
  "aid": {
    "app_id": "sbom",
    "owner_team": "K82M",
    "env": "lab",
    "vcs_ref": "local",
    "app_version": "0.0.0",
    "repo": "DonkeyJJLove/sbom"
  },
  "msg": "human-readable note",
  "payload": {}
}
```

W Elastic/Kibana filtrujesz po `aid.*` i `event_type` natywnie. W Splunk najprościej traktujesz event jako JSON i używasz `spath` do wydobycia pól. `payload` trzymasz jako „materiał” (pełny SBOM, raport skanera, delta, decyzja gate) albo jako streszczenie (liczniki, top-N), zależnie od tego, jak ciężkie dane chcesz indeksować.

## Start LAB: wybór backendu (profil)

W tym katalogu uruchamiasz zawsze `docker-compose.lab.yml`, wybierając backend profilem. Najpierw upewnij się, że jesteś w `środowiska-testowe/`.

Elastic + Kibana:

```bash
docker compose -f docker-compose.lab.yml --profile elastic up -d
docker compose -f docker-compose.lab.yml ps
```

Splunk:

```bash
docker compose -f docker-compose.lab.yml --profile splunk up -d
docker compose -f docker-compose.lab.yml ps
```

Warto pamiętać o podstawie: w Elasticsearch port `9300` to transport klastra (nie HTTP), więc przeglądarka i curl „łamią protokół”. Do API używasz `9200`. Kibana jest zwykle na `5601`. Splunk Web jest na `8000`, HEC na `8088`.

Jeżeli przełączasz backend, zatrzymaj poprzedni wariant zanim wystartujesz kolejny. Najprościej:

```bash
docker compose -f docker-compose.lab.yml stop elasticsearch kibana
docker compose -f docker-compose.lab.yml --profile splunk up -d
```

lub odwrotnie:

```bash
docker compose -f docker-compose.lab.yml stop splunk
docker compose -f docker-compose.lab.yml --profile elastic up -d
```

## Konfiguracja analityki: Elastic (Kibana) lub Splunk

### Elastic + Kibana (profil `elastic`)

Szybki test Elasticsearch:

```powershell
Invoke-RestMethod http://localhost:9200
Invoke-RestMethod "http://localhost:9200/_cluster/health?pretty"
```

W Kibanie tworzysz Data View dla indeksów, które będziesz zasilał. Na start możesz mieć `sbom-test`, docelowo polecam wzorzec `sbom-*`. W Data View ustaw `@timestamp` jako pole czasu. Jeżeli nie widzisz pól po świeżym ingest, odśwież „field list” w Data View.

W Discover filtruj np.:

```kql
aid.owner_team : "K82M" and event_type : "sbom"
```

### Splunk (profil `splunk`)

Wejdź do Splunk Web: `http://localhost:8000`. HEC jest na `http://localhost:8088/services/collector/event`. W LAB najprościej wysyłać eventy JSON do HEC i w wyszukiwaniu używać `spath`.

Test HEC (z toolbox):

```bash
curl -sS http://splunk:8088/services/collector/event   -H "Authorization: Splunk $SPLUNK_HEC_TOKEN"   -H "Content-Type: application/json"   -d '{
    "event": {
      "@timestamp": "2026-01-25T23:15:00.000Z",
      "event_type": "sbom",
      "aid": { "app_id":"sbom","owner_team":"K82M","env":"lab","vcs_ref":"local","app_version":"0.0.0","repo":"DonkeyJJLove/sbom" },
      "msg":"splunk hec test ok"
    }
  }'
```

W Splunk Search:

```spl
index=* "splunk hec test ok"
```

A potem filtr po AID przez `spath`:

```spl
index=* 
| spath
| search aid.owner_team="K82M" event_type="sbom"
```

## Podłączenie aplikacji: trzy praktyczne warianty

W LAB masz trzy „realne” sposoby podpięcia aplikacji. Wybór zależy od tego, czy analizujesz kod, paczkę, czy obraz kontenera.

Wariant A: obraz kontenera (najprostszy do SBOM i skanu). Budujesz image i skanujesz go.

Wariant B: katalog repo (source SBOM). Generujesz SBOM z systemu plików repo.

Wariant C: artefakt binarny (zip/jar/deb/msi). Generujesz SBOM z paczki.

W każdym wariancie wynik sprowadza się do tego samego: powstaje `sbom.json`, powstaje `scan.json`, powstaje `delta.json`, a potem leci to do wybranego backendu jako zdarzenia z AID.

## Narzędzia (referencyjnie): Syft + Grype

Syft generuje SBOM (np. CycloneDX JSON), Grype skanuje podatności. To jest minimalistyczny, powtarzalny duet.

Przykłady (Linux/WSL lub agent Jenkins na Linux):

SBOM dla obrazu:

```bash
syft myapp:1.2.3 -o cyclonedx-json > sbom.cdx.json
```

Skan podatności na podstawie SBOM:

```bash
grype sbom:sbom.cdx.json -o json > scan.grype.json
```

Jeżeli Twoje skany są offline lub w sieci restrykcyjnej, pamiętaj, że część skanerów potrzebuje aktualizacji bazy (to ma wpływ na czas i stabilność pipeline).

## Ingest: trzy poziomy ciężaru danych (dla obu backendów)

To jest decyzja architektoniczna, która determinuje koszty i komfort analizy, niezależnie czy backendem jest Elastic czy Splunk.

Tryb S1 (pełny payload): indeksujesz pełne JSON-y SBOM i pełne raporty skanów. Najlepsze na małą skalę (LAB), najcięższe w produkcji.

Tryb S2 (streszczenie + link): indeksujesz streszczenie (liczniki, top-y, meta) i link do pliku SBOM przechowywanego jako artefakt (np. Jenkins artifacts lub repo artefaktów). Najlżejsze i najłatwiejsze do skalowania.

Tryb S3 (hybryda): pełny SBOM tylko dla wydań releasowanych (np. `env=prod` lub tag release), a dla pozostałych tylko streszczenia. To jest zwykle „złoty środek”.

W LAB możesz zacząć od S1 (bo chcesz eksplorować), a potem przejść na S3.

## Minimalna analiza: pięć perspektyw „postrzegania danych” (Elastic i Splunk)

Perspektywa 1: Tożsamość i genealogia bytu (AID). Tu sprawdzasz, czy widzisz spójny strumień dla aplikacji, czy wersje i commity tworzą ciąg.

Kibana KQL:

```kql
aid.app_id:"myapp" and aid.env:"lab"
```

Splunk SPL:

```spl
index=* | spath | search aid.app_id="myapp" aid.env="lab"
```

Perspektywa 2: Bezpieczeństwo (AppSec/SOC). Tu pytasz: ile jest High/Critical, co jest nowe, co wraca.

Kibana KQL (przykład pod streszczenia):

```kql
event_type:"scan" and aid.app_id:"myapp" and payload.summary.critical > 0
```

Splunk SPL:

```spl
index=* | spath | search event_type="scan" aid.app_id="myapp" payload.summary.critical>0
```

Perspektywa 3: Zmiana struktury (delta). Tu jest serce epistemiki: co doszło, co ubyło, co zmieniło wersję.

Kibana KQL:

```kql
event_type:"delta" and aid.app_id:"myapp"
```

Splunk SPL:

```spl
index=* | spath | search event_type="delta" aid.app_id="myapp"
```

Perspektywa 4: Zgodność (licencje/polityki). Tu nie interesuje Cię CVE, tylko to, czy skład łamie politykę.

Kibana KQL:

```kql
event_type:"scan" and payload.licenses.deny_count > 0
```

Splunk SPL:

```spl
index=* | spath | search event_type="scan" payload.licenses.deny_count>0
```

Perspektywa 5: Operacje (stabilność pipeline i ingest). Tu pytasz: czy pipeline działa i czy są STOPy.

Kibana KQL:

```kql
aid.app_id:"myapp" and event_type:"gate" and payload.decision:"STOP"
```

Splunk SPL:

```spl
index=* | spath | search aid.app_id="myapp" event_type="gate" payload.decision="STOP"
```

Ważne: te zapytania zakładają, że w `payload` trzymasz chociaż streszczenia. Dlatego w kolejnych krokach dodamy minimalny schemat `payload.summary`.

## Jenkins: konfigurujemy to „porządnie” (rdzeń wspólny dla obu backendów)

W Jenkinsie celem jest pipeline, który robi cztery rzeczy i zawsze kończy się danymi w wybranym backendzie: Build → SBOM → Scan → Delta → Gate → Ingest.

W „General” włączasz zakaz równoległych buildów (LAB), ustawiasz rotację buildów, włączasz parametryzację. W parametrach dodajesz minimum: `AID_ENV`, `AID_APP_ID` oraz parametry backendu. Dla Elastic będą to `ES_URL` i `ES_INDEX`. Dla Splunk będą to `SPLUNK_HEC_URL` i `SPLUNK_HEC_TOKEN`. Tokeny i sekrety trzymaj w Jenkins Credentials, nie w skrypcie.

### Jenkinsfile: minimalny „heartbeat” do backendu

Zaczynasz od heartbeat, bo to eliminuje 80% problemów „nie widzę danych”. Ten krok ma sens dla obu backendów: generujesz jeden event zgodny z AID_CONTRACT i wysyłasz go tam, gdzie aktualnie działa analityka.

Jeżeli w LAB ustawiasz `BACKEND=elastic` lub `BACKEND=splunk`, pipeline nie musi zgadywać. Jeżeli ustawiasz `BACKEND=auto`, pipeline może sprawdzić dostępność endpointu i wybrać kanał. W tym repo trzymamy zasadę: najpierw deterministycznie, potem automatyzacja.

Po heartbeat dołączasz Syft/Grype oraz zaczynasz zasilać `event_type:scan`, potem deltę i bramki.

## Jak robić „analizę zmiany” (delta) w praktyce

Najprostsza delta, która daje ogrom wartości, to trzy liczby i trzy listy: ile komponentów doszło, ile ubyło, ile zmieniło wersję oraz top-ryzykowne zmiany.

W LAB można liczyć deltę w pipeline i wysyłać jako osobny event `event_type:"delta"`. W produkcji można to robić w pipeline (najprościej) lub w analityce (gdy chcesz centralne porównania).

Docelowo delta jest epistemiczną operacją: to nie „raport”, tylko sygnał: co się zmieniło w strukturze bytu i czy zmiana wnosi ryzyko.
