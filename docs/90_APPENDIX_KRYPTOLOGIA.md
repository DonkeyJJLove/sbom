# 90_APPENDIX_KRYPTOLOGIA — SBOM jako kryptologia informacyjna bytu

## Status dokumentu

**Appendix / esej techniczno-epistemologiczny.**  
Ten dokument **nie opisuje procedur** ani konfiguracji. Rozwija ramę pojęciową, w której SBOM, AID i zdarzenia LAB-u są traktowane jak elementy **kryptologii informacyjnej**: systemu odcisków, skrótów i relacji umożliwiających wnioskowanie o bycie w czasie.

---

## Teza główna

> **SBOM nie jest listą.  
> SBOM jest skrótem relacyjnym bytu.**

Tak jak kryptograficzny hash:
- nie opisuje treści wprost,
- ale **jednoznacznie ją reprezentuje** w danej przestrzeni.

SBOM jest hashem **nie pliku**, lecz **struktury relacji**:
- komponentów,
- zależności,
- wersji,
- źródeł pochodzenia.

---

## Kryptologia informacyjna vs kryptografia

### Kryptografia
- chroni treść,
- zapewnia poufność, integralność, autentyczność,
- operuje na bitach i kluczach.

### Kryptologia informacyjna (w tym LAB-ie)
- **nie ukrywa treści**,
- redukuje ją do **znaczącego odcisku**,
- umożliwia porównanie stanów bez pełnej rekonstrukcji.

SBOM nie szyfruje.  
SBOM **kompresuje wiedzę o bycie**.

---

## SBOM jako odcisk relacji (Sigillum Relationis)

Klasyczna lista zależności mówi:
> „A używa B w wersji C”.

SBOM jako sigillum mówi:
> „Ten byt **istniał** w takim układzie relacji”.

To zasadnicza różnica:
- lista → opis statyczny,
- odcisk → **świadectwo stanu w czasie**.

Dlatego w LAB-ie:
- SBOM jest zdarzeniem,
- nie artefaktem archiwalnym.

---

## AID jako klucz domenowy

W kryptografii:
- hash bez kontekstu jest bezużyteczny.

W LAB-ie:
- SBOM bez AID jest bezużyteczny.

**AID pełni rolę klucza domenowego**, który:
- nadaje znaczenie odciskowi,
- wiąże go z bytem, właścicielem i środowiskiem,
- umożliwia korelację w czasie.

Bez AID:
- nie ma historii,
- nie ma delty,
- nie ma sterowania.

---

## Delta jako operacja kryptologiczna

Delta nie jest „różnicą plików”.

Delta jest:
- porównaniem dwóch odcisków relacyjnych,
- wykrywaniem **zmiany bytu**, nie zmiany tekstu.

W tym sensie:
- `sbom_snapshot` ≈ skrót relacyjny,
- `delta` ≈ różnica skrótów.

Dlatego delta jest:
- tańsza niż pełne SBOM,
- bardziej informacyjna niż pojedynczy stan.

---

## Asynchroniczność prawdy

Istotna cecha kryptologii informacyjnej:

> **Prawda o bycie nie pojawia się synchronicznie.**

- SBOM powstaje w momencie builda,
- podatność może zostać odkryta miesiące później,
- decyzja gate może nastąpić jeszcze później.

Dzięki temu, że SBOM jest odciskiem:
- nowa wiedza (np. CVE) może zostać **zastosowana wstecz**,
- bez przebudowy bytu.

To fundamentalna przewaga nad raportami.

---

## Gate jako akt woli systemu

W klasycznych systemach:
- alert = sygnał,
- decyzja = człowiek.

W LAB-ie:
- gate = **formalny akt sterowania**,
- oparty na odcisku bytu i jego historii.

Gate nie mówi:
> „jest błąd”.

Gate mówi:
> „ten byt **nie przechodzi dalej** w tym stanie”.

To różnica ontologiczna, nie stylistyczna.

---

## Minimalizm jako warunek prawdy

Kryptologia informacyjna wymaga redukcji.

Dlatego w LAB-ie:
- `payload.summary` jest preferowany,
- pełne dane są opcjonalne,
- model danych jest stabilny.

Nadmiar informacji:
- zaciemnia zmianę,
- zwiększa szum,
- utrudnia wnioskowanie.

Prawda operacyjna jest **skondensowana**.

---

## SBOM a iluzja kontroli

Częsty błąd:
> „Mamy SBOM, więc wiemy wszystko”.

To fałsz.

SBOM:
- nie gwarantuje bezpieczeństwa,
- nie zastępuje decyzji,
- nie przewiduje przyszłości.

SBOM daje:
- **zdolność reagowania**,
- **zdolność porównania**,
- **zdolność sterowania**.

Reszta to polityka i odpowiedzialność.

---

## Konsekwencje praktyczne (dla LAB-u)

Z tej ramy wynikają twarde zasady:
- SBOM **zawsze jako zdarzenie**, nie plik,
- AID **zawsze obecny**,
- delta **ważniejsza niż stan**,
- gate **ważniejszy niż alert**,
- Elastic **ważniejszy niż raport**.

---

## Konkluzja

SBOM w tym repozytorium nie jest narzędziem compliance.  
Jest elementem **systemu kryptologii informacyjnej**, w którym:

- byt zostawia ślad,
- ślad jest porównywalny,
- porównanie prowadzi do decyzji.

To wystarcza, by sterować złożonością.

---
