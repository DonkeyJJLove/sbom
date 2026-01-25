# Środowiska testowe — LAB do analizy SBOM (Jenkins + Elastic/Kibana + opcjonalnie Splunk)

Ten katalog jest „poligonem” dla całego repo: tu uruchamiasz lokalne środowisko, podłączasz aplikację (repo/artefakt), generujesz SBOM, skanujesz podatności, liczysz delty zmian i oglądasz to w analityce tak, jak robi się to produkcyjnie: wieloperspektywowo (dev, AppSec, SOC, compliance, ops). Celem nie jest „ładny SBOM”, tylko sterowanie: pomiar → próg → akcja, gdzie SBOM jest pieczęcią relacji (*Sigillum Relationis*), a AID jest tożsamością bytu, która spina wszystko w czasie.

## Co dostajesz z tego LAB-u

Po pierwszym uruchomieniu masz działający Elastic (API na 9200) i Kibana (UI na 5601) oraz widok w Discover, gdzie widzisz zdarzenia z `aid.*` (AID_CONTRACT) i `event_type`. To jest minimalna baza pod dalszą analizę: możesz już filtrować, agregować, budować dashboardy i alerty.

Docelowo LAB ma obsłużyć trzy strumienie danych dla każdej aplikacji:
SBOM (skład), SCAN (podatności/licencje), DELTA (zmiany pomiędzy kolejnymi stanami). Czwarty strumień to GATE (decyzja/progi i wyjątki).

## Słownik pojęć w tym repo

SBOM to „odcisk relacji” artefaktu. Nie interesuje nas tylko to, co jest w środku, ale to, co z tego wynika: ryzyko, zgodność, dryf, trendy.

AID_CONTRACT to minimalna tożsamość bytu. AID nie jest „dla ozdoby”. Jest kluczem korelacji i sterowania: bez niego SBOM/scan/delta są anonimowe, a proces nie jest sterowalny.

`event_type` jest prostym rozróżnieniem rodzaju obserwacji:
`sbom` (skład), `scan` (podatności/licencje), `delta` (różnice), `gate` (decyzja).

`@timestamp` to czas zdarzenia w UTC (Kibana używa go do filtrów czasu, trendów i alertów).

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
  "payload": { }
}
````

W Kibanie filtrujesz po `aid.*` i `event_type`, a `payload` trzymasz jako „materiał” (pełny SBOM, raport skanera, delta, decyzja gate) albo jako streszczenie (liczniki, top-N), zależnie od tego, jak ciężkie dane chcesz indeksować.

## Start LAB: Elastic + Kibana

Uruchamiasz Elastic/Kibanę docker-compose (w tym katalogu). Jeżeli masz już klaster postawiony, ten krok pomiń.

Po uruchomieniu pamiętaj o podstawie: port `9300` to transport klastra (nie HTTP), więc przeglądarka i curl „łamią protokół”. Do API używasz `9200`. Kibana jest zwykle na `5601`.

Szybki test:

```powershell
Invoke-RestMethod http://localhost:9200
```

Jeżeli dostajesz JSON z `cluster_name` i `version`, to jest OK.

## Konfiguracja Kibany (żeby „widzisz dane”)

W Kibanie tworzysz Data View dla indeksów, które będziesz zasilał. Na start możesz mieć `sbom-test`, docelowo polecam wzorzec `sbom-*`.

W Data View ustaw `@timestamp` jako pole czasu. Jeśli część zdarzeń jest bez czasu, twórz drugi Data View bez time field, ale docelowo trzymaj się `@timestamp` zawsze.

W Discover filtruj np.:

```kql
aid.owner_team : "K82M" and event_type : "sbom"
```

Jeżeli nie widzisz pól po świeżym ingest, odśwież „field list” w Data View.

## Podłączenie aplikacji: trzy praktyczne warianty

W LAB masz trzy „realne” sposoby podpięcia aplikacji. Wybór zależy od tego, czy analizujesz kod, paczkę, czy obraz kontenera.

Wariant A: obraz kontenera (najprostszy do SBOM i skanu). Budujesz image i skanujesz go.

Wariant B: katalog repo (source SBOM). Generujesz SBOM z systemu plików repo.

Wariant C: artefakt binarny (zip/jar/deb/msi). Generujesz SBOM z paczki.

W każdym wariancie wynik sprowadza się do tego samego: powstaje `sbom.json`, powstaje `scan.json`, powstaje `delta.json`, a potem leci to do Elastic jako zdarzenia z AID.

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

## Ingest do Elastic: dwa poziomy ciężaru danych

To jest decyzja architektoniczna, która determinuje koszty i komfort analizy.

Tryb S1 (pełny payload): indeksujesz pełne JSON-y SBOM i pełne raporty skanów. Najlepsze na małą skalę (LAB), najcięższe w produkcji.

Tryb S2 (streszczenie + link): indeksujesz streszczenie (liczniki, top-y, meta) i link do pliku SBOM przechowywanego jako artefakt (np. w Jenkins artifacts lub repo artefaktów). Najlżejsze i najłatwiejsze do skalowania.

Tryb S3 (hybryda): pełny SBOM tylko dla wydań releasowanych (np. `env=prod` lub tag release), a dla pozostałych tylko streszczenia. To jest zwykle „złoty środek”.

W LAB możesz zacząć od S1 (bo chcesz eksplorować), a potem przejść na S3.

## Minimalna analiza w Kibanie: pięć perspektyw „postrzegania danych”

Perspektywa 1: Tożsamość i genealogia bytu (AID)
Tu sprawdzasz: czy w ogóle widzisz spójny strumień dla aplikacji, czy wersje i commity tworzą ciąg.

KQL:

```kql
aid.app_id:"myapp" and aid.env:"lab"
```

Perspektywa 2: Bezpieczeństwo (AppSec/SOC)
Tu pytasz: ile jest High/Critical, co jest nowe, co wraca, co ma exploitability.

KQL (przykład):

```kql
event_type:"scan" and aid.app_id:"myapp" and payload.summary.critical > 0
```

Perspektywa 3: Zmiana struktury (delta)
Tu jest serce „epistemiki”: co doszło, co ubyło, co zmieniło wersję, czy rośnie graf zależności.

KQL:

```kql
event_type:"delta" and aid.app_id:"myapp"
```

Perspektywa 4: Zgodność (licencje/polityki)
Tu nie interesuje Cię CVE, tylko to, czy skład łamie politykę licencyjną lub wewnętrzną.

KQL:

```kql
event_type:"scan" and payload.licenses.deny_count > 0
```

Perspektywa 5: Operacje (stabilność pipeline i ingest)
Tu pytasz: czy pipeline działa, czy ingest nie gubi zdarzeń, czy nie ma „dziur” w czasie.

KQL:

```kql
aid.app_id:"myapp" and event_type:"gate" and payload.decision:"STOP"
```

Ważne: te zapytania zakładają, że w `payload` trzymasz chociaż streszczenia. Dlatego w kolejnych krokach dodamy minimalny schemat `payload.summary`.

## Jenkins: konfigurujemy to „porządnie”

W Jenkinsie celem jest pipeline, który robi cztery rzeczy i zawsze kończy się danymi w Elastic:

Build → SBOM → Scan → Delta → Gate → Ingest.

### Konfiguracja joba (UI), czyli co klikasz

W „General” włączasz zakaz równoległych buildów (LAB), ustawiasz rotację buildów, włączasz parametryzację.

W parametrach dodajesz minimum:
`ES_URL`, `ES_INDEX`, `AID_ENV`, `AID_APP_ID`, opcjonalnie `AID_REPO`.

Tokeny i sekrety trzymasz w Jenkins Credentials, nie w skrypcie.

### Jenkinsfile: minimalny „heartbeat” (sprawdza łączność i schemat danych)

Najpierw uruchom pipeline, który tylko wysyła 1 zdarzenie do Elastic. Dopiero jak je widzisz w Kibanie, dodajesz Syft/Grype.

Poniżej wzorzec, który działa zarówno jako diagnostyka, jak i „kamień węgielny” dalszej automatyzacji:

```groovy
pipeline {
  agent any

  parameters {
    string(name: 'ES_URL', defaultValue: 'http://host.docker.internal:9200', description: 'Elasticsearch URL')
    string(name: 'ES_INDEX', defaultValue: 'sbom-test', description: 'Index for LAB events')
    choice(name: 'AID_ENV', choices: ['lab','dev','test','prod'], description: 'Environment')
  }

  environment {
    AID_APP_ID     = 'sbom'
    AID_OWNER_TEAM = 'K82M'
    AID_REPO       = 'DonkeyJJLove/sbom'
    AID_VCS_REF    = 'local'
    AID_APP_VERSION= '0.0.0'
  }

  stages {
    stage('Derive AID from git (if available)') {
      steps {
        script {
          if (isUnix()) {
            sh '''
              set -e
              if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
                echo "AID_VCS_REF=$(git rev-parse --short HEAD)" > aid_dynamic.env
                echo "AID_APP_VERSION=$(git describe --tags --always 2>/dev/null || git rev-parse --short HEAD)" >> aid_dynamic.env
              else
                echo "AID_VCS_REF=local" > aid_dynamic.env
                echo "AID_APP_VERSION=0.0.0" >> aid_dynamic.env
              fi
            '''
          } else {
            bat '''
              @echo off
              echo AID_VCS_REF=local> aid_dynamic.env
              echo AID_APP_VERSION=0.0.0>> aid_dynamic.env
            '''
          }

          def props = readProperties file: 'aid_dynamic.env'
          env.AID_VCS_REF = props['AID_VCS_REF']
          env.AID_APP_VERSION = props['AID_APP_VERSION']
        }
      }
    }

    stage('Send heartbeat to Elastic') {
      steps {
        script {
          if (isUnix()) {
            sh '''
              set -e
              ts=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")
              cat > event.json <<JSON
{
  "@timestamp":"$ts",
  "event_type":"sbom",
  "aid":{
    "app_id":"'"$AID_APP_ID"'",
    "owner_team":"'"$AID_OWNER_TEAM"'",
    "env":"'"$AID_ENV"'",
    "vcs_ref":"'"$AID_VCS_REF"'",
    "app_version":"'"$AID_APP_VERSION"'",
    "repo":"'"$AID_REPO"'"
  },
  "msg":"jenkins heartbeat ok"
}
JSON
              curl -sS -X POST "$ES_URL/$ES_INDEX/_doc?refresh=true" -H "Content-Type: application/json" --data-binary @event.json
            '''
          } else {
            powershell '''
              $ts = (Get-Date).ToUniversalTime().ToString("o")
              $body = @{
                "@timestamp" = $ts
                event_type = "sbom"
                aid = @{
                  app_id = "$env:AID_APP_ID"
                  owner_team = "$env:AID_OWNER_TEAM"
                  env = "$env:AID_ENV"
                  vcs_ref = "$env:AID_VCS_REF"
                  app_version = "$env:AID_APP_VERSION"
                  repo = "$env:AID_REPO"
                }
                msg = "jenkins heartbeat ok"
              } | ConvertTo-Json -Depth 6

              Invoke-RestMethod -Method Post -Uri "$env:ES_URL/$env:ES_INDEX/_doc?refresh=true" -ContentType "application/json" -Body $body | Out-Null
            '''
          }
        }
      }
    }
  }
}
```

Po tym buildzie w Kibanie zobaczysz zdarzenie z `msg = jenkins heartbeat ok` i pełnym `aid.*`.

### Kolejny krok (już po heartbeat): SBOM + Scan + Delta + Gate

W następnym etapie dołożymy:
generowanie SBOM (Syft), skan (Grype), minimalne streszczenia `payload.summary`, delta (porównanie z poprzednim stanem), oraz gate (decyzja i ewentualne wyjątki).

Tu świadomie zaczynamy od heartbeat, bo to eliminuje 80% problemów „nie widzę danych”.

## Jak robić „analizę zmiany” (delta) w praktyce

Najprostsza delta, która daje ogrom wartości, to trzy liczby i trzy listy:
ile komponentów doszło, ile ubyło, ile zmieniło wersję oraz top-ryzykowne zmiany.

W LAB można liczyć deltę lokalnie (skrypt w pipeline) i wysyłać jako osobny event `event_type:"delta"`. W produkcji możesz to robić albo w pipeline (najprościej), albo w analityce (gdy chcesz centralne porównania).

Docelowo delta jest epistemiczną operacją: to nie „raport”, tylko sygnał: co się zmieniło w strukturze bytu i czy zmiana wnosi ryzyko.