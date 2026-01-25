# AID_CONTRACT — tożsamość bytu (SBOM jako Sigillum Relationis)

AID (Application Identity Descriptor) jest minimalnym kontraktem tożsamości, który musi towarzyszyć każdemu artefaktowi obserwacji i sterowania: SBOM, wynikowi skanu, delcie oraz decyzji bramki (gate). AID nie jest metadanym „dla wygody”, tylko markerem strukturalnym, który spina byt wdrożeniowy z pomiarem, korelacją i akcją w pętli DevSecOps.

Wymagane pola AID (MUST):
AID_APP_ID        — stały identyfikator bytu/aplikacji/produktu; nie zmienia się między buildami.
AID_OWNER_TEAM    — właściciel odpowiedzialności; zespół, który dostaje ticket i ma mandat do remediacji.
AID_ENV           — środowisko, w którym wykonano pomiar lub w którym byt jest osadzony (np. lab/dev/test/prod).
AID_VCS_REF       — referencja do źródła: commit/tag; jeżeli brak Gita, wartość “local”.
AID_APP_VERSION   — wersja bytu (SemVer lub build-id); jeżeli nieznana, “0.0.0”.

Pole opcjonalne (SHOULD):
AID_REPO          — identyfikator repozytorium, np. "DonkeyJJLove/sbom".

Inwarianty kontraktu:
AID jest stały w obrębie jednego cyklu pomiarowego i jest propagowany 1:1 przez cały łańcuch: pomiar → próg → akcja.
AID_VCS_REF musi dać się odtworzyć (weryfikowalność). Gdy repo jest gitowe, preferowany jest skrót commita; gdy nie, “local”.
AID_APP_ID ma być krótki, bez spacji, stabilny, w stylu slug (np. "sbom", "router-page", "akmf-sandbox").

Reprezentacja w zdarzeniach (zalecany schemat JSON):

W każdym evencie (SBOM, scan, delta, gate) umieszczamy obiekt:
aid: {
  app_id, owner_team, env, vcs_ref, app_version, repo
}
oraz ewentualne pochodne pola wyliczalne (np. aid_fingerprint), ale AID nie zależy od narzędzia ani formatu SBOM.

Cel operacyjny:

Dzięki AID każde zdarzenie daje się jednoznacznie przypisać do bytu oraz powiązać z dokumentem „Kryptologia informacyjna – SBOM” jako formalnym opisem reguł i sensu pomiaru.
