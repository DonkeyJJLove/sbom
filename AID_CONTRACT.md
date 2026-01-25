# AID_CONTRACT — tożsamość bytu (SBOM jako *Sigillum Relationis*)

AID (*Application Identity Descriptor*) jest minimalnym kontraktem tożsamości, który musi towarzyszyć każdemu artefaktowi obserwacji i sterowania w tym repozytorium: SBOM, wynikowi skanu, delcie oraz decyzji bramki (*gate*). AID nie jest metadanym „dla wygody”. To marker strukturalny, który spina byt wdrożeniowy z pomiarem, korelacją i akcją w pętli DevSecOps (pomiar → próg → akcja).

W praktyce AID robi jedną, krytyczną rzecz: sprawia, że różne obserwacje (SBOM/scan/delta/gate) dają się jednoznacznie przypisać do *tego samego bytu* i powiązać w czasie, niezależnie od narzędzia, formatu i kanału transportu (Elastic/Splunk/CI).

## Dlaczego AID jest potrzebny

Sam SBOM to „treść o składnikach”. Hash/podpis/attestation to „dowód integralności i pochodzenia”. AID to „adres i mandat” — mówi *czego dotyczą dane* w sensie operacyjnym: jaka aplikacja/produkt, jakie środowisko, jaki snapshot źródła, jaka wersja i kto odpowiada.

Bez AID analityka staje się archiwum (widzisz biblioteki, ale nie masz pewności, do którego bytu to przypisać). Z AID analityka staje się sterowaniem (wiesz, do kogo należy ryzyko i co dokładnie ma zostać zablokowane, przepuszczone, oticketowane lub zeskalowane).

## Minimalny standard danych w projekcie: „koperta zdarzenia”

Żeby AID działał jako wzorzec dla YAML/CI, dane w repo przyjmują postać zdarzeń, gdzie AID jest częścią *koperty*, a właściwa treść (SBOM, wynik skanu, delta) jest *payloadem*. Koperta jest stała, payload może się różnić.

Rekomendowana koperta zdarzenia (Elastic/Kibana, ale neutralna narzędziowo):

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
  "msg": "hello from sbom-lab",
  "payload": { }
}
````

W LAB (Elastic/Kibana) kluczowe jest, że `aid.*` staje się zestawem pól indeksowalnych i filtrowalnych w Discover, a `@timestamp` pozwala użyć filtra czasu i wizualizacji trendów.

## Pola AID (normatywnie: MUST / SHOULD)

Wymagane (MUST):

`AID_APP_ID` — stały identyfikator bytu/aplikacji/produktu. Nie zmienia się między buildami. To „imię bytu”, np. `sbom`.

`AID_OWNER_TEAM` — właściciel odpowiedzialności. Zespół, który dostaje ticket i ma mandat do remediacji. W tym projekcie kanonicznie: `K82M`.

`AID_ENV` — środowisko, w którym wykonano pomiar lub gdzie byt jest osadzony, np. `lab/dev/test/prod`.

`AID_VCS_REF` — referencja do źródła: commit/tag. Gdy brak Gita albo pomiar jest lokalny: `local`.

`AID_APP_VERSION` — wersja bytu (SemVer lub build-id). Gdy nieznana: `0.0.0`.

Opcjonalne (SHOULD):

`AID_REPO` — identyfikator repozytorium, np. `DonkeyJJLove/sbom`.

## Inwarianty kontraktu (to jest „twarda prawda” AID)

AID jest stały w obrębie jednego cyklu pomiarowego i jest propagowany 1:1 przez cały łańcuch: pomiar → próg → akcja. To oznacza, że SBOM, scan, delta i gate dla „tej samej iteracji” muszą mieć identyczne wartości AID.

`AID_VCS_REF` musi dać się odtworzyć. Gdy repo jest gitowe, preferowany jest skrót commita; gdy nie — `local`, ale wtedy zdarzenie ma charakter diagnostyczny (lab), a nie produkcyjny.

`AID_APP_ID` ma być krótki, stabilny, bez spacji, w stylu slug. Zmiana `AID_APP_ID` to zmiana bytu (nowa tożsamość), a nie „kolejna wersja”.

`AID_OWNER_TEAM` jest mandatem. Jeżeli nie wiadomo, kto odpowiada, to system sterowania traci sens. Dlatego ten atrybut nie jest opcjonalny.

## Reprezentacja AID w implementacji (YAML / CI / LAB)

W repo AID jest traktowany jako zestaw zmiennych środowiskowych (`AID_*`), a następnie mapowany do obiektu `aid{...}` w zdarzeniu. To jest najprostszy i najbardziej przenośny wzorzec: YAML nie „wymyśla” AID, tylko go propaguje, a narzędzia generujące zdarzenia zawsze doklejają `aid.*` do koperty.

Minimalny plik środowiskowy (wzorzec do `.sbom/aid.env.example`):

```bash
AID_APP_ID=sbom
AID_OWNER_TEAM=K82M
AID_ENV=lab
AID_VCS_REF=local
AID_APP_VERSION=0.0.0
AID_REPO=DonkeyJJLove/sbom
```

W docker-compose (wzorzec): jedno źródło AID i jedno wstrzyknięcie do wszystkich usług, które generują lub transportują zdarzenia. Dzięki temu toolbox/Jenkins/forwarder zawsze „mówią tym samym językiem”.

## Jak to się czyta w Kibanie (LAB)

W Kibanie (Discover) AID działa jak klucz filtrów i korelacji. Typowe zapytania KQL:

```kql
event_type : "sbom"
```

```kql
aid.owner_team : "K82M"
```

```kql
aid.app_id : "sbom" and aid.env : "lab" and event_type : "sbom"
```

To jest dokładnie powód, dla którego AID ma postać pól: nie chcesz wyszukiwać w treści SBOM (ciężkiej i zmiennej), tylko sterować procesem po stabilnym identyfikatorze bytu i mandacie.

## Cel operacyjny (po co to finalnie jest)

Dzięki AID każde zdarzenie daje się jednoznacznie przypisać do bytu oraz powiązać z dokumentem „Kryptologia informacyjna – SBOM” jako formalnym opisem reguł i sensu pomiaru. AID jest mostem pomiędzy ontologicznym śladem relacji (SBOM jako *Sigillum Relationis*) a decyzją procesową (gate/ticket/alert), bo dostarcza stałego klucza: „to jest ten byt” oraz „to jest ten mandat”.


