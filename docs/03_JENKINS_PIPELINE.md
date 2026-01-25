# 03_JENKINS_PIPELINE — konfiguracja i uruchomienie pipeline (LAB Elastic-only)

## Cel dokumentu

Ten dokument opisuje:
- konfigurację joba Jenkins w LAB-ie,
- parametry sterujące,
- sposób uruchomienia **pierwszego realnego pomiaru repozytorium**,
- minimalne warunki poprawności (co musi się wydarzyć w Elastic).

LAB jest Elastic-only: **Jenkins → toolbox → Elasticsearch → Kibana**.

---

## Założenia architektury (LAB)

### Role komponentów
- **Jenkins**: kontroler uruchomień (scheduler + parametry)
- **toolbox (sbom-lab/toolbox)**: runtime narzędzi (`syft`, `grype`, `jq`, `curl`, `git`)
- **Elasticsearch**: pamięć zdarzeń i baza wnioskowania
- **Kibana**: interfejs do wnioskowania

### Dlaczego toolbox
Nie instalujemy `jq/syft/grype` do Jenkinsa.  
Pipeline uruchamia je w **toolbox** przez `docker run` (Jenkins ma tylko docker-cli + socket).

---

## Wymagania pipeline

Jenkins container / agent:
- ma podmontowany docker socket: `/var/run/docker.sock`
- ma `docker` CLI
- ma dostęp do repo (bind mount do `/repo` albo checkout do workspace)

Toolbox image:
- `sbom-lab/toolbox:latest` istnieje (zbudowany przez compose)

---

## Konfiguracja joba w UI (Configure)

### 1) Type
- **New Item → Pipeline**

### 2) General
- **Do not allow concurrent builds** → ON  
  (delta ma sens tylko w sekwencji)
- **Do not allow the pipeline to resume if the controller restarts** → ON  
  (przerwany pomiar = pomiar nieważny)
- **Discard old builds** → ON (np. 30)
- **GitHub project** (opcjonalnie) → URL repo

### 3) This project is parameterized → ON

Dodaj parametry:

#### Ingest (Elastic)
- **Text**
  - `ES_URL` (domyślnie: `http://elasticsearch:9200` jeśli Jenkins jest w tej samej sieci docker)
  - `ES_INDEX` (domyślnie: `sbom-test`)

#### AID (tożsamość bytu)
- **Choice**
  - `AID_ENV`: `lab`, `dev`, `test`, `prod`
- **Text**
  - `AID_APP_ID` (np. `sbom`)
  - `AID_OWNER_TEAM` (np. `K82M`)
  - `AID_REPO` (np. `DonkeyJJLove/sbom`)
  - `AID_VCS_REF` (np. `local`, pipeline może nadpisać z git)
  - `AID_APP_VERSION` (np. `0.0.0`, pipeline może nadpisać z git)

#### Target (co analizujemy)
- **Choice**
  - `TARGET_KIND`: `repo`, `image`, `file`
- **Text**
  - `TARGET_REF`: `.`
    - `repo` → `.` (workspace/repo)
    - `image` → `myapp:1.2.3`
    - `file` → `./path/to/artifact.zip`

#### Gate (polityka)
- **Choice**
  - `FAIL_ON`: `none`, `critical`, `high`
- **Boolean**
  - `FULL_PAYLOAD` (domyślnie OFF)

### 4) Triggers
- **GitHub hook trigger for GITScm polling** → ON (opcjonalnie)
- reszta triggerów → OFF (LAB)

### 5) Pipeline
- **Definition** → `Pipeline script`
- Wklej Jenkinsfile (poniżej)

---

## Jenkinsfile (toolbox-runner, Elastic-only)

Ten Jenkinsfile:
- wykonuje SBOM/SCAN w toolbox
- liczy prostą deltę (added/removed) lokalnie
- zapisuje `sbom/scan/delta/gate` do Elastic
- w LAB-ie domyślnie nie wymaga FULL_PAYLOAD

```groovy
pipeline {
  agent any

  options {
    disableConcurrentBuilds()
    durabilityHint('MAX_SURVIVABILITY')
    buildDiscarder(logRotator(numToKeepStr: '30'))
    timestamps()
  }

  parameters {
    string(name: 'ES_URL',   defaultValue: 'http://elasticsearch:9200', description: 'Elasticsearch URL (docker network)')
    string(name: 'ES_INDEX', defaultValue: 'sbom-test', description: 'Index for LAB events')

    choice(name: 'AID_ENV', choices: ['lab','dev','test','prod'], description: 'Environment')
    string(name: 'AID_APP_ID',     defaultValue: 'sbom', description: 'Stable application ID')
    string(name: 'AID_OWNER_TEAM', defaultValue: 'K82M', description: 'Owner team')
    string(name: 'AID_REPO',       defaultValue: 'DonkeyJJLove/sbom', description: 'Repo identifier')
    string(name: 'AID_VCS_REF',     defaultValue: 'local', description: 'VCS ref (pipeline may override)')
    string(name: 'AID_APP_VERSION', defaultValue: '0.0.0', description: 'App version (pipeline may override)')

    choice(name: 'TARGET_KIND', choices: ['repo','image','file'], description: 'What to scan')
    string(name: 'TARGET_REF', defaultValue: '.', description: 'repo path / image name / file path')

    choice(name: 'FAIL_ON', choices: ['none','critical','high'], description: 'Gate threshold')
    booleanParam(name: 'FULL_PAYLOAD', defaultValue: false, description: 'Index full JSONs (heavy)')
  }

  environment {
    OUT_DIR = '.lab_out'
    SBOM_CDX = "${OUT_DIR}/sbom.cdx.json"
    SCAN_JSON = "${OUT_DIR}/scan.grype.json"
    SNAPSHOT_TXT = "${OUT_DIR}/components.snapshot.txt"
    PREV_TXT = "${OUT_DIR}/components.prev.txt"
    DELTA_JSON = "${OUT_DIR}/delta.json"
    GATE_VARS = "${OUT_DIR}/gate.vars"
  }

  stages {

    stage('Prep') {
      steps {
        sh '''
          set -e
          mkdir -p "$OUT_DIR"
          command -v docker >/dev/null
        '''
      }
    }

    stage('Checkout (optional)') {
      steps {
        script {
          try { checkout scm } catch (e) { echo "checkout scm skipped: ${e}" }
        }
      }
    }

    stage('Derive AID from git (best-effort)') {
      steps {
        sh '''
          set -e
          VCS_REF="${AID_VCS_REF}"
          APP_VER="${AID_APP_VERSION}"

          if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
            VCS_REF="$(git rev-parse --short HEAD)"
            APP_VER="$(git describe --tags --always 2>/dev/null || git rev-parse --short HEAD)"
          fi

          echo "AID_VCS_REF=$VCS_REF" > "$OUT_DIR/aid_dynamic.env"
          echo "AID_APP_VERSION=$APP_VER" >> "$OUT_DIR/aid_dynamic.env"
        '''
        script {
          def props = readProperties file: "${env.OUT_DIR}/aid_dynamic.env"
          env.AID_VCS_REF = props['AID_VCS_REF']
          env.AID_APP_VERSION = props['AID_APP_VERSION']
        }
      }
    }

    stage('SBOM + SCAN in toolbox') {
      steps {
        sh '''
          set -e

          # toolbox robi syft+grype+jq (Jenkins nie ma tych narzędzi)
          docker run --rm \
            -v "$WORKSPACE:/work" -w /work \
            sbom-lab/toolbox:latest \
            bash -lc '
              set -e
              mkdir -p .lab_out

              # TARGET selection
              case "$TARGET_KIND" in
                repo)  T="$TARGET_REF" ;;
                image) T="$TARGET_REF" ;;
                file)  T="$TARGET_REF" ;;
                *) echo "Unknown TARGET_KIND=$TARGET_KIND"; exit 2 ;;
              esac

              syft "$T" -o cyclonedx-json > .lab_out/sbom.cdx.json
              grype "sbom:.lab_out/sbom.cdx.json" -o json > .lab_out/scan.grype.json

              # snapshot komponentów (dla delta): purl@version lub name@version
              jq -r "
                (.components // []) | .[] |
                (
                  (try .purl catch null) as \\$p |
                  (try .name catch null) as \\$n |
                  (try .version catch null) as \\$v |
                  if \\$p != null and \\$v != null then (\\$p + \\\"@\\\" + \\$v)
                  elif \\$p != null then \\$p
                  elif \\$n != null and \\$v != null then (\\$n + \\\"@\\\" + \\$v)
                  elif \\$n != null then \\$n
                  else empty end
                )
              " .lab_out/sbom.cdx.json | sort -u > .lab_out/components.snapshot.txt
            '
        '''
      }
    }

    stage('Fetch previous snapshot (Elastic)') {
      steps {
        sh '''
          set -e

          QUERY=$(cat <<'JSON'
{
  "size": 1,
  "sort": [{"@timestamp":"desc"}],
  "query": {
    "bool": {
      "filter": [
        {"term": {"event_type":"sbom_snapshot"}},
        {"term": {"aid.app_id":"__APP_ID__"}},
        {"term": {"aid.env":"__ENV__"}},
        {"term": {"aid.repo":"__REPO__"}}
      ]
    }
  }
}
JSON
)
          QUERY="${QUERY/__APP_ID__/$AID_APP_ID}"
          QUERY="${QUERY/__ENV__/$AID_ENV}"
          QUERY="${QUERY/__REPO__/$AID_REPO}"

          RESP=$(curl -sS -X POST "$ES_URL/$ES_INDEX/_search" -H "Content-Type: application/json" -d "$QUERY" || true)

          echo "$RESP" | jq -e '.hits.hits | length > 0' >/dev/null 2>&1 || { : > "$PREV_TXT"; exit 0; }
          echo "$RESP" | jq -r '.hits.hits[0]._source.payload.components_snapshot[]? // empty' | sort -u > "$PREV_TXT"
        '''
      }
    }

    stage('DELTA') {
      steps {
        sh '''
          set -e
          comm -23 "$SNAPSHOT_TXT" "$PREV_TXT" > "$OUT_DIR/added.txt" || true
          comm -13 "$SNAPSHOT_TXT" "$PREV_TXT" > "$OUT_DIR/removed.txt" || true

          ADDED_COUNT=$(wc -l < "$OUT_DIR/added.txt" | tr -d ' ')
          REMOVED_COUNT=$(wc -l < "$OUT_DIR/removed.txt" | tr -d ' ')

          jq -n \
            --argjson added_count "$ADDED_COUNT" \
            --argjson removed_count "$REMOVED_COUNT" \
            --slurpfile added "$OUT_DIR/added.txt" \
            --slurpfile removed "$OUT_DIR/removed.txt" \
            '{
              summary: { added: $added_count, removed: $removed_count },
              added: ($added[0] // []),
              removed: ($removed[0] // [])
            }' > "$DELTA_JSON"
        '''
      }
    }

    stage('GATE') {
      steps {
        sh '''
          set -e
          CRIT=$(jq '[.matches[]? | .vulnerability.severity? | select(.=="Critical")] | length' "$SCAN_JSON")
          HIGH=$(jq '[.matches[]? | .vulnerability.severity? | select(.=="High")] | length' "$SCAN_JSON")

          DECISION="GO"
          REASON="ok"

          if [ "$FAIL_ON" = "critical" ] && [ "$CRIT" -gt 0 ]; then DECISION="STOP"; REASON="critical>0"; fi
          if [ "$FAIL_ON" = "high" ] && { [ "$CRIT" -gt 0 ] || [ "$HIGH" -gt 0 ]; }; then DECISION="STOP"; REASON="high_or_critical>0"; fi

          echo "$CRIT $HIGH $DECISION $REASON" > "$GATE_VARS"
        '''
      }
    }

    stage('INGEST (Elastic events)') {
      steps {
        sh '''
          set -e
          TS=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")
          read CRIT HIGH DECISION REASON < "$GATE_VARS"

          # aid object
          AID=$(jq -n \
            --arg app_id "$AID_APP_ID" \
            --arg owner_team "$AID_OWNER_TEAM" \
            --arg env "$AID_ENV" \
            --arg vcs_ref "$AID_VCS_REF" \
            --arg app_version "$AID_APP_VERSION" \
            --arg repo "$AID_REPO" \
            '{app_id:$app_id, owner_team:$owner_team, env:$env, vcs_ref:$vcs_ref, app_version:$app_version, repo:$repo}'
          )

          # sbom_snapshot
          SNAP=$(jq -n \
            --arg ts "$TS" \
            --argjson aid "$AID" \
            --slurpfile comps "$SNAPSHOT_TXT" \
            '{
              "@timestamp": $ts,
              event_type: "sbom_snapshot",
              aid: $aid,
              msg: "components snapshot for delta",
              payload: { components_snapshot: ($comps[0] // []) }
            }'
          )
          curl -sS -X POST "$ES_URL/$ES_INDEX/_doc?refresh=true" -H "Content-Type: application/json" --data-binary "$SNAP" >/dev/null

          # sbom (summary-only by default)
          SBOM_PAYLOAD=$(jq -n \
            --argjson full "$FULL_PAYLOAD" \
            --argfile sbom "$SBOM_CDX" \
            'if $full then { sbom: $sbom } else { summary: { note:"sbom generated", mode:"summary_only" } } end'
          )
          SBOM_EVT=$(jq -n \
            --arg ts "$TS" --argjson aid "$AID" --argjson payload "$SBOM_PAYLOAD" \
            '{ "@timestamp":$ts, event_type:"sbom", aid:$aid, msg:"sbom generated", payload:$payload }'
          )
          curl -sS -X POST "$ES_URL/$ES_INDEX/_doc?refresh=true" -H "Content-Type: application/json" --data-binary "$SBOM_EVT" >/dev/null

          # scan
          SCAN_PAYLOAD=$(jq -n \
            --argjson full "$FULL_PAYLOAD" \
            --argfile scan "$SCAN_JSON" \
            --argjson critical "$CRIT" \
            --argjson high "$HIGH" \
            '{
              summary: { critical:$critical, high:$high },
              scan: (if $full then $scan else null end)
            }'
          )
          SCAN_EVT=$(jq -n \
            --arg ts "$TS" --argjson aid "$AID" --argjson payload "$SCAN_PAYLOAD" \
            '{ "@timestamp":$ts, event_type:"scan", aid:$aid, msg:"grype scan completed", payload:$payload }'
          )
          curl -sS -X POST "$ES_URL/$ES_INDEX/_doc?refresh=true" -H "Content-Type: application/json" --data-binary "$SCAN_EVT" >/dev/null

          # delta
          DELTA_PAYLOAD=$(cat "$DELTA_JSON")
          DELTA_EVT=$(jq -n \
            --arg ts "$TS" --argjson aid "$AID" --argjson payload "$(echo "$DELTA_PAYLOAD" | jq '.')" \
            '{ "@timestamp":$ts, event_type:"delta", aid:$aid, msg:"delta computed", payload:$payload }'
          )
          curl -sS -X POST "$ES_URL/$ES_INDEX/_doc?refresh=true" -H "Content-Type: application/json" --data-binary "$DELTA_EVT" >/dev/null

          # gate
          GATE_EVT=$(jq -n \
            --arg ts "$TS" --argjson aid "$AID" \
            --arg decision "$DECISION" --arg reason "$REASON" --arg fail_on "$FAIL_ON" \
            --argjson critical "$CRIT" --argjson high "$HIGH" \
            '{
              "@timestamp": $ts,
              event_type: "gate",
              aid: $aid,
              msg: "gate decision",
              payload: {
                policy: { fail_on: $fail_on },
                summary: { critical: $critical, high: $high },
                decision: $decision,
                reason: $reason
              }
            }'
          )
          curl -sS -X POST "$ES_URL/$ES_INDEX/_doc?refresh=true" -H "Content-Type: application/json" --data-binary "$GATE_EVT" >/dev/null

          # enforce gate
          if [ "$DECISION" = "STOP" ]; then
            echo "GATE STOP: $REASON"
            exit 10
          fi

          echo "GATE GO"
        '''
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: '.lab_out/*', allowEmptyArchive: true
    }
  }
}
````

---

## Pierwszy realny pomiar repo (krok po kroku)

W Jenkins → **Build with Parameters** ustaw:

* `TARGET_KIND = repo`
* `TARGET_REF = .`
* `AID_APP_ID = sbom`
* `AID_REPO = DonkeyJJLove/sbom`
* `AID_ENV = lab`
* `FAIL_ON = none`
* `FULL_PAYLOAD = false`

Uruchom build.

---

## Kryteria sukcesu (w Elastic)

W Kibanie / Discover:

```kql
aid.repo : "DonkeyJJLove/sbom"
```

Powinieneś zobaczyć **pakiet zdarzeń**:

* `event_type: sbom_snapshot`
* `event_type: sbom`
* `event_type: scan`
* `event_type: delta`
* `event_type: gate`

Jeśli widzisz tylko manual/heartbeat → pipeline nie doszedł do ingestu.

---

## Typowe awarie i szybkie diagnozy

### 1) `exit 127` w Jenkins

Brak `docker` CLI w Jenkinsie albo brak dostępu do socket.
Sprawdź w logu `Prep`:

* `command -v docker`

### 2) `docker run sbom-lab/toolbox:latest` nie działa

Toolbox image nie zbudowany / nie istnieje.
Zbuduj compose:

* `docker compose up -d --build`

### 3) Kibana widzi dokumenty, ale nie widzi pól `aid.*`

Odśwież Data View:

* **Stack Management → Data Views → Refresh field list**

### 4) Filtry łapią „tokeny”

Brak index template `keyword`.
Zastosuj template z `02_LAB_SETUP_ELASTIC.md`.

---

## Status dokumentu

**Operacyjny**: to jest domyślny pipeline LAB-u Elastic-only.
Każdy kolejny etap wnioskowania zakłada, że ten pipeline generuje pełen strumień `sbom/scan/delta/gate`.

---

