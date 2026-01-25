# LAB: Automatyczna analiza SBOM w CI/CD (Jenkins + Elastic)

## 0. Cel LAB-u
Sterowanie ryzykiem przez obserwację struktury bytu aplikacji.
SBOM jako Sigillum Relationis, AID jako tożsamość.

![SBOM intro](../img/01_intro_sbom.png)

---

## 1. Czym SBOM jest w tym LAB-ie
Nie lista bibliotek, tylko próbka stanu bytu.
(event_type = sbom)

![Automated SBOM](../img/02_automated_sbom_ci_cd.png)

---

## 2. Strumienie danych
- SBOM – skład
- SCAN – podatności/licencje
- DELTA – zmiana
- GATE – decyzja

---

## 3. Fazy wdrożenia w LAB
PoC → Pilot → Rollout → Operacje

![Phased DevSecOps](../img/03_phased_devsecops_sbom.png)

---

## 4. Workflow techniczny
Jenkins → Syft/Grype → Elastic → Kibana → (Gate)

![Workflow](../img/04_workflow_sbom_ci_cd.png)

---

## 5. Architektura logiczna
On-prem, hybryda, kolektory, indeksy

![Architecture](../img/05_hybrid_architecture_sbom.png)

---

## 6. Kontrakt danych (AID + koperta)
[tu wklejasz dokładnie JSON, który już masz]

---

## 7. Minimalne zapytania w Kibanie
(event_type, aid.*, payload.summary)

---

## 8. Co dalej
Delta, progi, automatyczne gate, SOC / AppSec
