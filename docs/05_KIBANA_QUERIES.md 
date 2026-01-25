# 05_KIBANA_QUERIES — wnioskowanie w Kibanie (KQL) dla LAB SBOM

## Cel dokumentu

Ten dokument daje **minimalny, ale kompletny zestaw kwerend KQL** do wnioskowania o Twoim oprogramowaniu w LAB-ie Elastic-only.

Kwerendy są ułożone tak, aby:
- najpierw potwierdzić tożsamość bytu (AID),
- potem sprawdzić skład (SBOM),
- potem ryzyko (SCAN),
- potem zmianę (DELTA),
- na końcu sterowanie (GATE).

Nie zaczynamy od „czy są CVE”, tylko od: **czy byt istnieje i ma ciąg obserwacji**.

---

## Warunek wstępny (1 minuta)

### Data View
- index pattern: `sbom-*` (lub `sbom-test`)
- time field: `@timestamp`
- po pierwszym ingest: **Refresh field list**

Jeśli nie widzisz `aid.*` i `event_type`, najpierw to napraw.

---

## 0) Sanity check: „czy LAB w ogóle ma dane?”

```kql
event_type : *
````

Oczekujesz dokumentów w Discover. Jeśli pusto: pipeline nie ingeruje lub indeks inny.

---

## 1) Byt i genealogia (AID)

### 1.1. Wszystkie zdarzenia jednego bytu (najważniejsze)

```kql
aid.repo : "DonkeyJJLove/sbom" and aid.env : "lab"
```

To jest filtr bazowy do całego LAB-u.

### 1.2. Jeden byt po app_id

```kql
aid.app_id : "sbom" and aid.env : "lab"
```

### 1.3. Konkretna wersja/commit (genealogia)

```kql
aid.repo : "DonkeyJJLove/sbom" and aid.vcs_ref : "a1b2c3d"
```

W praktyce `a1b2c3d` bierzesz z pola `aid.vcs_ref` w ostatnim buildzie.

### 1.4. Sprawdzenie „czy to jest ciąg w czasie”

```kql
aid.repo : "DonkeyJJLove/sbom" and event_type : "gate"
```

Jeśli widzisz sekwencję gate w czasie, masz stabilny strumień obserwacji.

---

## 2) Skład (SBOM)

### 2.1. Wszystkie zdarzenia SBOM

```kql
event_type : "sbom" and aid.repo : "DonkeyJJLove/sbom"
```

Interpretacja:

* jeśli SBOM jest „summary_only”, zobaczysz tylko `payload.summary.note`
* jeśli `FULL_PAYLOAD=true`, zobaczysz `payload.sbom`

### 2.2. Snapshot komponentów (pod deltę)

```kql
event_type : "sbom_snapshot" and aid.repo : "DonkeyJJLove/sbom"
```

Kliknij dokument i zobacz `payload.components_snapshot`.
To jest Twoja minimalna reprezentacja „świata zależności”.

### 2.3. Pytanie epistemiczne #1: „Czy repo ma w ogóle zależności?”

W Discover:

* otwórz `sbom_snapshot`
* sprawdź, czy `payload.components_snapshot` ma >0 elementów

Jeśli 0, wniosek jest ważny: repo może być dokumentacyjne / brak lockfile / brak ekosystemu zależności wykrywalnego przez Syft.

---

## 3) Ryzyko (SCAN)

### 3.1. Wszystkie skany

```kql
event_type : "scan" and aid.repo : "DonkeyJJLove/sbom"
```

### 3.2. Krytyczne podatności

```kql
event_type : "scan" and aid.repo : "DonkeyJJLove/sbom" and payload.summary.critical > 0
```

### 3.3. Wysokie lub krytyczne

```kql
event_type : "scan" and aid.repo : "DonkeyJJLove/sbom" and (payload.summary.critical > 0 or payload.summary.high > 0)
```

### 3.4. Pytanie epistemiczne #2: „Czy ryzyko jest powtarzalne?”

Porównuj dwa kolejne buildy:

* filtruj po `aid.vcs_ref`
* porównaj `payload.summary.*`

Jeśli ryzyko jest niestabilne bez zmian w bycie, masz błąd pomiaru lub źródeł (np. różna baza CVE).

---

## 4) Zmiana (DELTA)

### 4.1. Wszystkie delty

```kql
event_type : "delta" and aid.repo : "DonkeyJJLove/sbom"
```

### 4.2. „Nowe komponenty” (added)

```kql
event_type : "delta" and aid.repo : "DonkeyJJLove/sbom" and payload.summary.added > 0
```

### 4.3. „Ubytek komponentów” (removed)

```kql
event_type : "delta" and aid.repo : "DonkeyJJLove/sbom" and payload.summary.removed > 0
```

### 4.4. Pytanie epistemiczne #3: „Czy delta jest sensowna?”

* delta wymaga wcześniejszego `sbom_snapshot`
* jeśli `added/removed` jest zawsze 0 mimo zmian w repo, to znaczy, że snapshot jest pusty lub repo nie jest poprawnie skanowane (`TARGET_REF`).

---

## 5) Sterowanie (GATE)

### 5.1. Wszystkie decyzje gate

```kql
event_type : "gate" and aid.repo : "DonkeyJJLove/sbom"
```

### 5.2. STOP (blokady)

```kql
event_type : "gate" and aid.repo : "DonkeyJJLove/sbom" and payload.decision : "STOP"
```

### 5.3. GO (dopuszczenia)

```kql
event_type : "gate" and aid.repo : "DonkeyJJLove/sbom" and payload.decision : "GO"
```

### 5.4. Pytanie epistemiczne #4: „Czy próg jest właściwy?”

* porównaj `payload.policy.fail_on`
* porównaj `payload.summary.critical/high`
* sprawdź, czy STOP jest „częsty” i czy ma sens (to jest tuning polityki, nie błąd).

---

## 6) Diagnostyka typowych anomalii (KQL)

### 6.1. „Widziałem dokumenty manualne/testowe”

```kql
aid.vcs_ref : "manual" or msg : "*hello*"
```

Usuń szum, żeby nie mieszać testów z bytem.

### 6.2. „Nie mam delty”

```kql
event_type : "sbom_snapshot" and aid.repo : "DonkeyJJLove/sbom"
```

Jeśli brak snapshotów, delta będzie bez sensu.

### 6.3. „Nie widzę pól aid.*”

To nie jest KQL. To jest problem Data View.

* Data View → Refresh field list

---

## 7) Minimalny rytuał wnioskowania (kolejność)

1. **Czy byt istnieje?**

```kql
aid.repo : "DonkeyJJLove/sbom"
```

2. **Czy jest ciąg obserwacji?**

```kql
aid.repo : "DonkeyJJLove/sbom" and event_type : "gate"
```

3. **Czy skład jest niepusty?**

```kql
aid.repo : "DonkeyJJLove/sbom" and event_type : "sbom_snapshot"
```

4. **Czy ryzyko istnieje?**

```kql
aid.repo : "DonkeyJJLove/sbom" and event_type : "scan"
```

5. **Czy zmiana jest wykrywana?**

```kql
aid.repo : "DonkeyJJLove/sbom" and event_type : "delta"
```

6. **Czy decyzje są spójne z ryzykiem?**

```kql
aid.repo : "DonkeyJJLove/sbom" and event_type : "gate"
```

---

## Status dokumentu

Operacyjny.
To jest minimalny zestaw kwerend pozwalający przejść z „LAB działa” do „wnioskuję o bycie”.

---

