# Kryptologia informacyjna – SBOM

<p align="center">
  <img src="img/kryptologia-informacyjna-sbom.png" alt="Kryptologia informacyjna – SBOM" width="800"><br>
  <em>Rys. 1. Kryptologia informacyjna – SBOM</em>
</p>


## Abstrakt

SBOM (Software Bill of Materials) jest dziś jednym z kluczowych artefaktów inżynierii bezpieczeństwa łańcucha dostaw oprogramowania: formalnym, maszynowo przetwarzalnym zapisem komponentów i relacji, które konstytuują byt software’owy w chwili kompilacji. W przeciwieństwie do opisów projektu na poziomie repozytorium czy deklaracji zależności na poziomie kodu źródłowego, SBOM opisuje **artefakt wdrożeniowy** jako realny, gotowy do dystrybucji obiekt – obraz kontenera, paczkę, binarium – i ujawnia jego genealogię: z jakich elementów powstał, w jakich wersjach, z jakimi licencjami, oraz jak te elementy są ze sobą powiązane w grafie zależności (w tym zależności tranzytywne). W tym sensie SBOM jest nie tylko „listą”, ale **operacyjnym markerem strukturalnym**: pozwala przejść od intuicji o złożoności do mierzalnego, porównywalnego opisu kompozycji, który można analizować w czasie i w skali całej organizacji.

Tekst rozwija ujęcie SBOM jako markera strukturalnego oraz **ontologicznej pieczęci relacji** (*Sigillum Relationis*). „Pieczęć” nie jest tu metaforą estetyczną, lecz skrótem funkcjonalnym: byt software’owy ujawnia swoją tożsamość poprzez relacje (komponent–komponent, komponent–wersja, komponent–licencja, komponent–źródło), a SBOM jest formalnym odciskiem tych relacji w chwili budowy. Z tak rozumianej ontologii wynika epistemologia praktyczna: SBOM jest artefaktem wiedzy o systemie, który umożliwia automatyczne wnioskowanie o ryzyku – o ile zostanie spięty z bazami podatności (CVE/NVD), politykami licencyjnymi oraz regułami organizacyjnymi. W konsekwencji SBOM staje się kluczowym elementem analizy strukturalnej (co system „ma w środku”) i analizy delt (co się w nim zmienia między wydaniami), a więc narzędziem do wykrywania dryfu architektonicznego, przyrostu powierzchni ataku, wprowadzania niepożądanych zależności i skuteczności remediacji.

Jednocześnie fundamentem niniejszego opracowania jest rozróżnienie między **wiedzą** a **sterowaniem**. SBOM sam w sobie nie „steruje” bezpieczeństwem – dostarcza pomiaru stanu, lecz nie dostarcza decyzji ani konsekwencji. Sterowanie pojawia się dopiero wtedy, gdy SBOM zostaje włączony w cybernetyczną pętlę sprzężenia zwrotnego: *pomiar → próg → akcja*. W praktyce oznacza to progi decyzyjne (np. brak podatności krytycznych, zakaz określonych licencji, allow-list komponentów, limity ryzyka), mechanizmy konsekwencji (fail pipeline, alert, ticket, wyjątek z akceptacją) oraz warstwę analityki i obserwowalności, która utrzymuje historię, koreluje zdarzenia i umożliwia szybkie reagowanie na asynchronicznie pojawiające się informacje o nowych zagrożeniach. Dlatego w tekście SBOM jest konsekwentnie osadzany w architekturze DevSecOps: CI/CD generuje i skanuje SBOM (Syft/Grype lub analogi), wyniki trafiają do analityki (np. Splunk), a następnie uruchamiają workflow (np. Jira) i działania zespołów (Dev, AppSec, SOC).

Warunkiem wiarygodności tego modelu jest kryptografia integralności i dowód pochodzenia: jeżeli SBOM ma być podstawą decyzji, musi być zaufanym świadectwem (hash, podpis, attestation, kontrola transportu i źródeł). Bez tego marker strukturalny może stać się wektorem manipulacji, a analityka – repozytorium fałszywej pewności. Z tego powodu opracowanie łączy zagadnienia ontologii relacji i analizy strukturalnej z praktyką zabezpieczeń (podpisy, łańcuch dowodów) oraz ze standardami formatów i wymiany danych (SPDX, CycloneDX, SWID i powiązane modele), które umożliwiają interoperacyjność w narzędziach i między organizacjami. W efekcie powstaje spójna teza: SBOM jest pieczęcią relacji i markerem strukturalnym, ale realna wartość ujawnia się dopiero wtedy, gdy zostaje potraktowany jako element sterowalnego systemu – z progami, pętlą sprzężenia zwrotnego, obserwowalnością i dowodami zaufania.

---

## 1. Wprowadzenie: oprogramowanie jako kompozycja i problem widoczności

Współczesne oprogramowanie jest złożone z setek komponentów i bibliotek, często pochodzących z otwartego oprogramowania. Analizy pokazują, że 98% badanych baz kodu zawiera komponenty open source, a 81% zawiera przynajmniej jedną znaną podatność. Taka złożoność łańcucha dostaw oprogramowania tworzy rozległą i trudną do zabezpieczenia powierzchnię ataku. Luka w dowolnym ogniwie łańcucha może skaskadować od punktu początkowego przez kolejne warstwy, aż do produktu końcowego i użytkownika, potencjalnie powodując katastrofalne skutki. Jedynym sposobem ograniczenia tego ryzyka jest utrzymanie pełnej widoczności komponentów i zależności oraz szybkie reagowanie na zagrożenia.

SBOM (Software Bill of Materials) stanowi podstawę takiej widoczności. Jest to lista składników oprogramowania, zawierająca wszystkie biblioteki, moduły i zależności budujące dany produkt, często wraz z informacjami o wersjach, sumach kontrolnych i licencjach. Innymi słowy, SBOM jest jak spis materiałów użytych do stworzenia aplikacji. Dzięki SBOM organizacje mogą skuteczniej identyfikować podatne komponenty, dbać o zgodność licencyjną i zwiększać bezpieczeństwo łańcucha dostaw oprogramowania.

W praktyce SBOM odpowiada na pytanie, które długo pozostawało „zbyt drogie” operacyjnie: **z czego dokładnie zrobiony jest byt wdrożeniowy**? Nie „z jakiego repo”, nie „jak się nazywa projekt”, tylko: jakie pakiety, jakie wersje, jakie relacje zależności, jakie licencje, jakie identyfikatory bezpieczeństwa. Gdy system jest kompozycją, bezpieczeństwo jest problemem kompozycji – a nie pojedynczego pliku.

---

## 2. Ontologia relacji: SBOM jako *Sigillum Relationis*

### 2.1. Ślad bytu i relacyjna tożsamość artefaktu

SBOM to więcej niż zwykła lista bibliotek – to odcisk relacji, które konstytuują dany byt oprogramowania. Każdy artefakt (np. aplikacja, kontener, biblioteka) niesie w SBOM ślad wszystkich komponentów i zależności użytych przy jego budowie. W filozoficznym ujęciu SBOM jest ontologiczną pieczęcią: formalnym zapisem bytu poprzez pryzmat jego powiązań z innymi komponentami. SBOM ujawnia, co z czym współbytowało w momencie kompilacji – można go nazwać „świadkiem chwili builda”. Systemowo pełni on rolę sensora stanu procesu wytwarzania – sam nie steruje procesem, ale dostarcza informacji o aktualnej strukturze produktu, pozwalając porównywać stany w czasie.

Ta pieczęć relacji ma cechy analogiczne do kryptograficznego hasha – jest unikatowym odciskiem całości oprogramowania. Podobnie jak hash, kompletny SBOM kusi pozorną prostotą: wydaje się, że mając pełną listę komponentów, zyskujemy pełną kontrolę nad bezpieczeństwem. Jednak taka pełna transparentność może być złudna. Sam spis komponentów (prawda o przeszłości) nie podpowiada jeszcze, co zrobić z tą wiedzą w przyszłości. Najdłuższa nawet lista zależności nie gwarantuje bezpieczeństwa – stanowi jedynie archiwum stanu projektu. Bez kontekstu i mechanizmów reagowania SBOM może dać fałszywe poczucie kontroli. Dlatego SBOM nie powinien pozostać martwym dokumentem; aby był użyteczny, musi zostać włączony w procesy decyzyjne i ochronne organizacji.

### 2.2. SBOM jako byt epistemologiczny

SBOM jest artefaktem wiedzy o oprogramowaniu – formalnym zapisem wszystkich komponentów wchodzących w skład produktu programistycznego wraz z relacjami między nimi. Innymi słowy, SBOM pełni rolę technicznego śladu po procesie budowania systemu: enumeruje wszystkie biblioteki, moduły i pakiety (zarówno własne, jak i zewnętrzne) włączone do aplikacji, tworząc mapę ontologiczną komponentów. Każdy komponent jest traktowany nie tylko jako plik czy nazwa, ale jako byt relacyjny – element powiązany z innymi elementami w pewnej strukturze zależności.

Taka reprezentacja oznacza, że SBOM opisuje skład oprogramowania w kategoriach bytów i relacji między nimi. SBOM dokumentuje nie tylko co wchodzi w skład aplikacji, ale także jak poszczególne części są powiązane. Jeśli aplikacja używa biblioteki A, która z kolei używa biblioteki B, to SBOM ujmie zarówno A, jak i B, wskazując zależność (A zależy od B). W ten sposób SBOM oddaje hierarchię komponentów i ich powiązania (zarówno zależności bezpośrednie, jak i tranzytywne) zamiast traktować każdy plik w izolacji.

---

## 3. Analiza strukturalna: co SBOM „opisuje” o artefakcie

SBOM z natury jest strukturą hierarchiczną – odzwierciedla drzewo zależności (graf komponentów) budujących system. Analiza strukturalna SBOM polega na przetwarzaniu tej listy i relacji między komponentami w celu wykrycia potencjalnych problemów. Główne obszary analizy to:

1. **Wyszukiwanie podatności i błędów** – porównanie komponentów z bazami CVE i znanych luk bezpieczeństwa. Na podstawie SBOM można zidentyfikować, czy aplikacja zawiera komponenty z podatnościami.
2. **Sprawdzenie zgodności licencyjnej** – SBOM zawiera informacje o licencjach komponentów; analiza pozwala wykryć ewentualne niezgodne z polityką licencje (np. licencje wirusowe GNU GPL w komercyjnym produkcie).
3. **Jakość i metryki** – analiza może objąć metryki jakości (np. wykrycie komponentów oznaczonych jako przestarzałe, nierozwijane) czy inne atrybuty (np. pochodzenie komponentu – czy pochodzi z zaufanego źródła).

### 3.1. Reprezentacja właściwości komponentów

SBOM dostarcza szczegółowy obraz właściwości komponentów w projekcie. Minimalny zakres danych obejmuje m.in.: dostawcę komponentu, nazwę, wersję, znacznik czasu, autora SBOM oraz relacje zależności między komponentami, a także unikalne identyfikatory. Standardowe formaty SBOM (SPDX, CycloneDX, SWID) są zorientowane maszynowo, co umożliwia automatyczne przetwarzanie tych informacji.

**Wersje komponentów.** Każdy komponent jest opisany swoją wersją. To podstawa korelacji z CVE oraz oceny ryzyka.

**Zależności.** SBOM explicite przedstawia zależności między komponentami. Komponenty są wymienione wraz z listą innych komponentów, od których zależą. Dzięki temu można zrekonstruować hierarchiczny graf zależności całego systemu.

**Licencje.** Dla każdego komponentu mogą być zawarte informacje o licencji. To podstawa audytu zgodności i sterowania ryzykiem prawnym.

**Identyfikatory komponentów (CPE, PURL).** SBOM często zawiera CPE lub PURL. CPE umożliwia jednoznaczne powiązanie z wpisami CVE w bazach podatności; PURL jest czytelnym identyfikatorem pakietu i bywa wykorzystywany do jednoznacznej identyfikacji w narzędziach.

**Kontekst użycia.** W CycloneDX komponent może mieć typ (aplikacja, biblioteka, kontener) oraz być osadzony w strukturze. Hierarchia zależności pokazuje miejsce komponentu w drzewie aplikacji.

### 3.2. Standardy i formaty: interoperacyjność jako warunek automatyzacji

Aby ułatwić analizę, SBOM powinien być w standardowym formacie i maszynowo przetwarzalny. Najczęściej spotkasz:

* **SPDX** (Linux Foundation; standard ISO/IEC 5962) – bogaty w meta-dane, silny w obszarze licencji.
* **CycloneDX** (OWASP) – lżejszy, praktyczny w pipeline’ach DevSecOps i narzędziach SCA.
* **SWID** – tagowanie identyfikacyjne oprogramowania.

Niezależnie od formatu, zaleca się generować co najmniej jeden SBOM dla każdego wydania. Warunek praktyczny jest prosty: **SBOM musi powstawać automatycznie w buildzie**, inaczej szybko staje się „piękną historią o wczoraj”.

---

## 4. Analiza delt: sekwencyjność, asynchroniczność, markery

Pojedynczy SBOM jest zapisem struktury bytu w chwili builda – migawką. W praktyce bezpieczeństwa taka migawka ma wartość dopiero wtedy, gdy staje się elementem **ciągu**: serii powtarzalnych pomiarów, które można porównywać. Właśnie w tym miejscu pojawia się fundamentalny zwrot epistemiczny: z „posiadania listy” przechodzimy do „rozumienia zmiany”. Jeśli patrzymy na SBOM jak na hash, to pojedynczy hash nie mówi, *co* się zmieniło – mówi jedynie, że coś jest „inne”. Dopiero analiza delt (różnic pomiędzy kolejnymi SBOM-ami) nadaje zmianie treść i pozwala ją sklasyfikować.

Analiza delt odpowiada na trzy pytania elementarne, które w praktyce tworzą jedną operację inżynierską: **co doszło, co zniknęło, co się przesunęło**. „Doszło” obejmuje nie tylko zależność dodaną jawnie przez dewelopera, lecz także komponenty tranzytywne, które pojawiły się jako konsekwencja aktualizacji innej biblioteki. „Zniknęło” może oznaczać redukcję powierzchni ataku, ale również ukryty regres: zniknięcie komponentu bywa skutkiem zamiany na inny, który ma gorsze właściwości bezpieczeństwa lub licencji. „Przesunęło się” – najczęściej – dotyczy wersji; i to właśnie wersje są głównym nośnikiem ryzyka, bo podatności są zazwyczaj wersjo-zależne.

Kluczowe jest rozumienie, że delta SBOM nie jest jedynie narzędziem raportowym. To narzędzie sterowania. Organizacja, która uczy się patrzeć na deltę, zdobywa świadomość trendów i potrafi uczyć się na swoich danych: widzi dryf architektoniczny, przyrost zależności, cykle „łatamy–psujemy–łatamy”, a także to, czy polityki działają, czy są obchodzone. W praktyce podejście to wpisuje się w cykl ciągłego doskonalenia: generuj czujnik (SBOM), obserwuj sygnały, kalibruj progi, reaguj i mierz efekty – tak by z każdą iteracją zwiększać poziom bezpieczeństwa.

### 4.1. Delta jako podstawowa operacja epistemiczna

Z punktu widzenia poznawczego (epistemologicznego) delta jest operacją, która redukuje niepewność w sposób użyteczny: zamiast pytać „czy system jest bezpieczny?”, pytamy „jak zmieniła się jego struktura i co ta zmiana implikuje?”. To przesunięcie jest krytyczne, bo bezpieczeństwo w systemach złożonych jest własnością dynamiczną, a nie statyczną. System może być „bezpieczny” tylko w relacji do znanego krajobrazu zagrożeń; ten krajobraz zmienia się asynchronicznie, niezależnie od naszej woli.

W praktyce delta powinna być liczona w kilku wymiarach jednocześnie:

* **Delta komponentów:** dodane/usunięte pakiety.
* **Delta wersji:** zmiany wersji (upgrade/downgrade), w tym „pozorne” aktualizacje, które tak naprawdę utrzymują podatną linię.
* **Delta licencji:** zmiany licencji lub warunków licencyjnych (w niektórych ekosystemach licencja bywa źle deklarowana i poprawiana w czasie).
* **Delta identyfikatorów:** zmiany CPE/PURL/bom-ref, które wpływają na jakość korelacji z CVE.
* **Delta grafu:** zmiany topologii zależności (np. komponent staje się tranzytywny zamiast bezpośredniego, co zmienia sposób remediacji).

### 4.2. Markery: od obserwacji do sterowania

W praktyce wyróżnia się trzy klasy markerów, które można wyprowadzić z delty – i które odpowiadają trzem poziomom zarządzania:

**(A) Markery tożsamości i dryfu.** Wskazują, czy byt wdrożeniowy pozostaje spójny ze swoją deklaracją (tożsamość) oraz czy nie rośnie niekontrolowanie (dryf). Markerami są m.in. przyrost zależności, nagłe pojawienie się komponentu spoza organizacyjnej allow-listy, „skoki” w grafie zależności oraz rozjazd między deklaracją a faktycznym składem artefaktu. Te markery są ważne, bo dryf jest mechanizmem, który powoli zwiększa powierzchnię ataku bez jednego spektakularnego zdarzenia.

**(B) Markery ryzyka bezwzględnego.** To klasyczny pomiar „tu i teraz”: ile jest CVE, jakiej są krytyczności, czy naruszamy politykę licencji, czy używamy komponentów wycofanych lub z nieznanego źródła. Jednak nawet tu delta ma znaczenie: to, czy ryzyko rośnie lub maleje, jest ważniejsze niż sama liczba w danym dniu.

**(C) Markery efektywności sterowania.** Mierzą zdolność organizacji do reakcji: MTTR dla krytycznych luk, „żywotność” podatności (ile wydań z rzędu luka pozostaje), udział wyjątków od polityki, a także czas od pojawienia się CVE do zniknięcia podatnego komponentu ze wszystkich SBOM-ów w organizacji. Ta klasa markerów jest najbardziej dojrzała, bo przenosi rozmowę z „mamy podatności” na „jak szybko i konsekwentnie je wygaszamy”.

### 4.3. Asynchroniczność zagrożeń: delta w czasie CVE

Najtrudniejszy aspekt praktyczny polega na tym, że sekwencja SBOM-ów (build po buildzie) nie jest zsynchronizowana z sekwencją informacji o podatnościach (CVE publikowane kiedy indziej, z różną dynamiką, z korektami). Oznacza to, że sterowanie musi obejmować dwa rodzaje zdarzeń:

1. **Zmiana kompozycji** (nowy build → nowy SBOM → delta),
2. **Zmiana wiedzy o ryzyku** (nowe CVE / nowe oceny / nowe exploitability).

W dojrzałym systemie oba strumienie spotykają się w analityce: nowy CVE jest „przykładany” do historycznych SBOM-ów i natychmiast buduje się mapa ekspozycji. To właśnie dlatego pojedynczy SBOM jest za mało: organizacja potrzebuje serii „odcisków” oraz zdolności do ich przeszukania i korelacji wstecz.

---

## 5. Splunk jako mechanizm wnioskowania: od danych do decyzji

SBOM w formacie maszynowym (np. CycloneDX JSON) może być bezpośrednio przetwarzany przez narzędzia analityczne takie jak Splunk. Splunk umożliwia parsowanie i indeksowanie SBOM, co przekształca statyczny spis komponentów w dynamiczne źródło wiedzy operacyjnej.

### 5.1. Parsowanie, indeksacja, eksplozja komponentów

Przy właściwej konfiguracji (JSON extractions i odpowiednie limity rozmiaru zdarzeń) Splunk może:

* przechowywać SBOM jako event,
* wyciągać pola (`components.name`, `components.version`, `licenses`, `cpe`, `purl`),
* rozwinąć listę komponentów do wielu rekordów (np. `mvexpand`), tak aby każdy komponent był obserwacją.

W praktyce oznacza to, że Splunk nie „czyta dokumentu”, tylko buduje z niego **model danych** umożliwiający pytania w stylu:

* które aplikacje zawierają `log4j-core` w wersji < 2.16?
* które buildy wniosły nowy komponent X?
* gdzie naruszono politykę licencji?

### 5.2. Korelacja z podatnościami

Splunk może wnioskować o podatnościach na dwa sposoby:

1. **Feed CVE/NVD w Splunk** + korelacja po CPE/PURL.
2. **Wysyłanie do Splunk wyników SCA** (np. raport Grype), które już zawierają dopasowania CVE.

W obu wariantach Splunk staje się mechanizmem proaktywnej oceny: zanim zobaczysz exploit w runtime, możesz zobaczyć, że w buildzie zaszła zmiana strukturalna zwiększająca ryzyko.

---

## 6. DevSecOps jako cybernetyka: pomiar → próg → akcja (zamknięcie pętli kryptografią)

W klasycznej logice cybernetycznej sterowanie wymaga sprzężenia zwrotnego: **pomiar → próg → decyzja/akcja → nowy pomiar**. W kontekście bezpieczeństwa łańcucha dostaw „pomiar” nie oznacza tylko testów funkcjonalnych, lecz przede wszystkim pomiar struktury bytu wdrożeniowego: jego kompozycji i ryzyk wynikających z tej kompozycji. SBOM jest tu sensorem stanu, natomiast kryptografia (podpis, attestation, weryfikacja) jest mechanizmem, który zapewnia, że sensor nie kłamie i że sygnał pochodzi z właściwej tożsamości. Bez kryptografii pętla cybernetyczna pozostaje pętlą „soft” – działa na deklaracjach; z kryptografią staje się pętlą „twardą” – działa na dowodach.

### 6.1. Topologia pętli: gdzie powstaje dowód i gdzie jest weryfikowany

W dojrzałym modelu DevSecOps SBOM nie jest generowany „na końcu”, lecz jest elementem samego procesu budowy, a jego wiarygodność jest wymuszana przez **punkty weryfikacji**. Najprostsza topologia ma cztery miejsca, w których kryptografia zamyka pętlę:

1. **Po buildzie, przed publikacją artefaktu** – pipeline generuje SBOM i podpisuje go oraz generuje attestation wiążące SBOM z artefaktem (digest), wejściem (VCS ref) i środowiskiem. To jest moment tworzenia dowodu.

2. **Przed wysłaniem do analityki (SIEM/observability)** – pipeline wysyła nie tylko SBOM i raport SCA, ale również metadane umożliwiające weryfikację: digest artefaktu, identyfikator podpisu, ewentualnie wynik lokalnej weryfikacji podpisu. To redukuje ryzyko, że do Splunka trafi materiał niepowiązany z rzeczywistym bytem wdrożeniowym.

3. **W repozytorium artefaktów** – publikacja artefaktu jest dopuszczona tylko wtedy, gdy istnieją powiązane dowody (SBOM + podpis + attestation) oraz gdy przejdą one walidację. Repozytorium staje się strażnikiem kompletności dowodowej.

4. **Przed wdrożeniem (CD / release gate)** – środowisko docelowe (lub pipeline release) weryfikuje podpisy i attestation niezależnie od tego, co „mówi” upstream. To jest kluczowe, bo oddziela domenę wytwarzania od domeny wdrożeniowej i zmniejsza ryzyko kompromitacji pojedynczego etapu.

Te cztery punkty sprawiają, że kryptografia nie jest dodatkiem, ale integralnym elementem sterowania: w każdym miejscu pętli mamy warunek „dowód albo stop”.

### 6.2. Próg bezpieczeństwa jako reguła dowodowa, nie tylko reguła CVE

Najczęściej organizacje definiują progi wprost na ryzyku (CVE/CVSS, licencje). W modelu „dowodowym” dochodzi drugi wymiar progów: **progi wiarygodności**. Oznacza to, że pipeline może zablokować wydanie nie dlatego, że wykryto CVE, lecz dlatego, że brak dowodu, iż SBOM odpowiada artefaktowi.

W praktyce progi dzielą się na trzy klasy:

* **Progi kompozycji**: np. zakazane licencje, komponenty spoza allow-list, niepożądane źródła.
* **Progi podatności**: np. brak Critical, limit High, wymagane SLA naprawy.
* **Progi zaufania**: brak podpisu, brak attestation, niezgodność digest, niezweryfikowane źródło zdarzeń.

To jest moment, w którym kryptografia zamyka pętlę cybernetyczną: sama „wiedza o ryzyku” nie wystarczy, jeśli nie ma pewności, że wiedza dotyczy właściwego obiektu. Z perspektywy sterowania progi zaufania są równorzędne progom CVE.

### 6.3. Praktyczny łańcuch: Syft → podpis → attestation → SCA → HEC → Splunk → Jira → release gate

W typowym scenariuszu DevSecOps wygląda to następująco:

1. **Build** (Jenkins) wytwarza artefakt (np. obraz kontenera) i oblicza jego digest.
2. **SBOM** jest generowany (Syft) na podstawie artefaktu, a nie tylko repo.
3. **Podpis SBOM** jest wykonywany kluczem organizacji; równolegle generowane jest **attestation**, które wiąże: `VCS_REF`, `BUILD_ID`, `ARTIFACT_DIGEST`, `SBOM_HASH`, środowisko build.
4. **SCA** (Grype/Trivy) analizuje SBOM i generuje raport podatności.
5. **HEC push**: pipeline wysyła do Splunk zdarzenia SBOM/SCA wraz z metadanymi dowodowymi (digest, identyfikator podpisu, a najlepiej także status weryfikacji).
6. **Splunk** indeksuje i koreluje: buduje alerty oparte o progi podatności i progi zaufania.
7. **Jira** otrzymuje zadania/incydenty: zarówno dla CVE (remediacja), jak i dla naruszeń dowodowych (brak podpisu, rozjazd digest).
8. **Release gate** weryfikuje dowody niezależnie: jeśli brak podpisu/attestation lub weryfikacja nie przechodzi – wdrożenie jest blokowane nawet wtedy, gdy raport CVE wygląda „czysto”.

Ta sekwencja jest cybernetyczna w ścisłym sensie: każdy cykl builda produkuje pomiar i dowód, a każdy cykl wdrożenia wymaga weryfikacji dowodu i podjęcia decyzji.

### 6.4. Konkretna reguła w pipeline: gdzie dokładnie weryfikować podpisy

Weryfikacja powinna pojawić się w dwóch miejscach, aby zapewnić odporność na kompromitację etapu:

* **Weryfikacja w CI** – natychmiast po wygenerowaniu podpisu/attestation, jako test spójności procesu. To wykrywa błędy konfiguracji i brak dostępu do kluczy.
* **Weryfikacja w CD** – przed deploymentem, jako test spójności dostarczanego artefaktu. To wykrywa podmianę w repozytorium lub w kanale dystrybucji.

W praktyce wygląda to jak prosta zasada: *CI podpisuje; CD nie ufa CI, tylko weryfikuje*. To rozdzielenie jest fundamentalne w bezpieczeństwie łańcucha dostaw.

### 6.5. Splunk jako egzekutor progów: bezpieczeństwo jako dane

Gdy dowody są przesyłane do Splunka, analityka staje się nie tylko dashboardem, ale elementem sterowania organizacyjnego. Splunk może wykrywać:

* buildy bez podpisanego SBOM,
* rozjazd pomiędzy deklarowanym digest a digests w repozytorium,
* nagłe pojawienie się komponentów o wysokiej centralności lub z „czarnej listy”,
* podatności krytyczne oraz trend ich utrzymywania się w kolejnych wydaniach.

Kluczowe jest, że Splunk nie zastępuje pipeline’u w decyzji „fail build”, lecz uzupełnia sterowanie o wymiar organizacyjny: korelacje między projektami, alarmy globalne i automatyczne tworzenie pracy (Jira). To jest cybernetyka na poziomie całej domeny.

### 6.6. Wyjątki i rozliczalność: kontrolowane naruszenie progów

Ponieważ organizacje czasem muszą wdrażać mimo ryzyka, dojrzały model zawiera mechanizm wyjątków. Wyjątek jest dopuszczalny tylko wtedy, gdy spełnione są warunki dowodowe: mamy podpisane SBOM, wiemy dokładnie, co wdrażamy, i potrafimy opisać ryzyko. Wyjątek bez dowodu jest nie wyjątkiem, lecz utratą sterowalności.

Dlatego praktycznie wyjątki powinny:

* być rejestrowane (Jira, CMDB, rejestr ryzyka),
* mieć właściciela (OWNER_TEAM),
* mieć termin (expiry),
* być mierzalne (ile wyjątków, jak długo trwają),
* być widoczne w analityce (dashboard ryzyka).

W ten sposób pętla sterowania pozostaje domknięta także wtedy, gdy organizacja chwilowo „łamie” swoje progi.

### 6.7. Wniosek: kryptografia domyka sterowanie

Z perspektywy cybernetycznej SBOM jest czujnikiem, ale kryptografia jest mechanizmem, który sprawia, że sygnał czujnika jest wiarygodny i przypisany do konkretnego bytu. Weryfikacja podpisów i attestation w pipeline oraz w release gate zamienia SBOM w dowód, a progi – w egzekwowalne reguły. Dopiero wtedy bezpieczeństwo łańcucha dostaw przestaje być kontemplacją raportów, a staje się sterowaniem procesem.

---

## 7. Sieć kaskadowa zależności i propagacja ryzyka

SBOM ujawnia sieć powiązań – jest mapą, która pokazuje, z jakich części składa się artefakt i jak te części są ze sobą połączone. W pojedynczym produkcie ta mapa ma postać grafu zależności: węzłami są komponenty, a krawędziami relacje „zależy od”. Jednak prawdziwa skala zjawiska ujawnia się dopiero wtedy, gdy SBOM traktuje się nie jako dokument pojedynczego projektu, lecz jako element infrastruktury wiedzy całej organizacji. Wówczas zbiór SBOM-ów z wielu produktów tworzy meta‑graf łańcucha dostaw – sieć, w której te same komponenty występują w wielu usługach, bibliotekach i obrazach kontenerów.

W tej sieci ryzyko nie rozkłada się równomiernie. Pojawia się asymetria typowa dla systemów złożonych: niewielka liczba komponentów o wysokiej centralności (frameworki webowe, biblioteki kryptograficzne, logowanie, serializacja, parsowanie) jest wykorzystywana przez ogromną liczbę zależności. Z perspektywy bezpieczeństwa oznacza to, że pojedyncza luka w komponencie „hubie” ma skutki multiplikatywne – jej propagacja odbywa się nie przez jedną aplikację, lecz przez setki bytów wdrożeniowych, które komponent odziedziczyły (często tranzytywnie, bez świadomej decyzji zespołu). To właśnie mechanizm kaskady: mały obiekt w sensie kodu staje się wielkim obiektem w sensie zasięgu ryzyka.

Analiza kaskady ma dwa wymiary: (1) identyfikację miejsc, gdzie komponent występuje, oraz (2) priorytetyzację interwencji. Pierwszy wymiar jest czysto informacyjny: jeśli organizacja posiada centralne repozytorium SBOM (np. indeks w Splunku), może błyskawicznie odpowiedzieć na pytanie „gdzie mamy X?”. Drugi wymiar jest stricte cybernetyczny: skoro nie da się aktualizować wszystkiego natychmiast, trzeba wiedzieć, które wystąpienia są krytyczne. Priorytetyzacja wynika z połączenia danych z SBOM z danymi kontekstowymi: ekspozycja usługi (Internet/DMZ/intranet), rola biznesowa, krytyczność danych, a także sygnały z SOC (czy obserwujemy próby eksploatacji).

SBOM umożliwia też rozróżnienie między zależnościami bezpośrednimi a tranzytywnymi, co jest kluczowe dla remediacji. Luka w zależności bezpośredniej może być naprawiona przez zmianę deklaracji w projekcie. Luka w zależności tranzytywnej często wymaga innej strategii: aktualizacji komponentu nadrzędnego, zmiany wersji frameworka, zastosowania override w menedżerze pakietów lub wręcz refaktoryzacji. Bez grafu zależności organizacja widzi jedynie „bibliotekę X jest podatna”; z grafem widzi „biblioteka X jest wciągnięta przez Y i Z w tej ścieżce” – a to jest informacja o tym, jak wykonać naprawę w rzeczywistym świecie SDLC.

Kaskadowość ma jeszcze jeden, często pomijany aspekt: zaufanie między podmiotami. Gdy dostawca udostępnia SBOM odbiorcy, przekazuje mu nie tylko listę komponentów, ale możliwość niezależnej oceny ryzyka. Jeśli SBOM jest podpisany, odbiorca może zweryfikować autentyczność i zestawić skład z własnymi politykami (np. komponenty zabronione, licencje, minimalne wersje). W ten sposób SBOM działa jak paszport bezpieczeństwa w łańcuchu dostaw: umożliwia rozmowę opartą o dane, a nie o deklaracje.

W praktyce organizacyjnej sieć kaskadowa wymusza zmianę sposobu pracy: zamiast modelu, w którym każdy zespół sam „odkrywa” zagrożenie w swoim kodzie, pojawia się model centralnej inteligencji. Nowe CVE jest analizowane raz, a następnie sygnał jest propagowany do wszystkich bytów dotkniętych poprzez SBOM. To redukuje opóźnienie reakcji i zwiększa spójność. W tym sensie SBOM jest narzędziem nie tylko technicznym, ale organizacyjnym: umożliwia przejście od lokalnych reakcji do sterowania na poziomie całej domeny.

---

## 7. Studium przypadku: Log4Shell jako demonstracja przewagi SBOM

Log4Shell (CVE-2021-44228) pokazał, że problemem nie jest tylko sama podatność, lecz brak odpowiedzi na pytanie: **czy i gdzie używamy log4j?**. Organizacje bez widoczności zależności traciły czas na przeszukiwanie kodu i serwerów. Organizacje z SBOM mogły w minutach uzyskać mapę ekspozycji: wyszukać `log4j` w indeksie SBOM i wskazać zespoły odpowiedzialne.

To studium jest ważne nie jako „historia o Log4j”, tylko jako dowód mechanizmu: w kryzysie liczy się zdolność do szybkiego wnioskowania o strukturze systemu.

---

## 8. Kryptografia i dowód pochodzenia: dlaczego SBOM musi być zaufany

Skoro SBOM ma służyć jako zaufane źródło prawdy o składzie oprogramowania, kluczowe jest zapewnienie jego wiarygodności i integralności. W praktyce analityki bezpieczeństwa nie istnieje „neutralny” dokument: każde dane, które trafiają do centralnego indeksu (SIEM, data lake, Splunk), stają się podstawą decyzji, alarmów, blokad i wyjątków. Jeżeli więc SBOM może być podmieniony, sfałszowany albo „wybiórczo zniekształcony”, cała pętla sterowania ryzykiem zamienia się w pętlę sterowania iluzją. Kryptografia jest tu strażnikiem prawdziwości markera: spina opis (SBOM) z bytem (artefaktem) oraz z tożsamością procesu (pipeline, organizacja), a przez to umożliwia weryfikowalne rozróżnienie między „danymi deklarowanymi” a „danymi dowiedzionymi”.

Warto to ująć jednoznacznie: **kryptografia nie jest ozdobnikiem SBOM**, tylko warunkiem, by SBOM mógł stać się elementem sterowalnego systemu. Bez kryptografii SBOM pozostaje deklaracją; z kryptografią staje się dowodem.

### 8.1. Model zagrożeń: co dokładnie chronimy

Zanim dobierze się mechanizmy, trzeba zdefiniować, przed czym SBOM ma chronić system decyzyjny. Typowe klasy zagrożeń są trzy.

Po pierwsze, **modyfikacja treści**: ktoś podmienia SBOM po wygenerowaniu (usuwa komponent, zmienia wersję, dopisuje licencję „bezpieczną”), aby ukryć ryzyko lub wymusić błędną decyzję. Po drugie, **podszycie się pod źródło**: ktoś wysyła do analityki „fałszywe SBOM-y” udając pipeline, aby wytworzyć szum, zablokować wydania lub wyczyścić ślady. Po trzecie, **rozłączenie opisu od bytu**: SBOM jest poprawny, ale nie dotyczy tego artefaktu, który faktycznie wdrażamy (wtedy SBOM staje się prawdą, lecz o innym obiekcie).

Każda z tych klas wymaga innego elementu kryptograficznego: podpis chroni treść, uwierzytelnienie i autoryzacja chronią kanał i źródło, a dowód pochodzenia (attestation) wiąże SBOM z artefaktem i kontekstem builda.

### 8.2. Poziom artefaktu i pliku SBOM: hash, podpis, wiązanie z binarium

Najbardziej fundamentalna warstwa to wiązanie SBOM z konkretnym artefaktem. W praktyce realizuje się to przez dwa typy danych:

1. **identyfikatory zawartości** (hash artefaktu, hash komponentów, digest obrazu kontenera),
2. **identyfikatory pochodzenia** (kto wygenerował, jakim procesem, na jakim wejściu).

Każdy komponent wymieniony w SBOM może być opatrzony kryptograficzną sumą kontrolną (np. SHA-256), a sam plik SBOM powinien zostać podpisany cyfrowo kluczem prywatnym organizacji. Dzięki sumom hash wiążemy SBOM z konkretnymi binariami (weryfikujemy, że opis odpowiada rzeczywistemu artefaktowi), a dzięki podpisowi mamy pewność, że lista komponentów nie została zmieniona od czasu wygenerowania.

Podpisany SBOM działa jak notarialna pieczęć autentyczności: zapewnia, że SBOM pochodzi z zaufanego źródła (np. z naszego pipeline CI) i nie został sfałszowany po drodze. W praktyce implementuje się to przez infrastrukturę kluczy publicznych (GPG/X.509) albo przez systemy nowej generacji, takie jak Sigstore/cosign czy in-toto. W dojrzałych wdrożeniach podpis „pliku” jest uzupełniany przez **attestation**: podpisaną asercję o procesie builda (np. „ten SBOM pochodzi z tego pipeline’u, dla tego commit/ref, w tym środowisku, i dotyczy artefaktu o digest X”). Takie podejście redukuje ryzyko, że poprawny SBOM zostanie podstawiony do niewłaściwego artefaktu.

W praktyce warto rozdzielić dwa obiekty dowodowe:

* **SBOM as data** – dokument opisowy,
* **SBOM as evidence** – dokument + podpis + dowód powiązania z artefaktem.

Tylko drugi wariant nadaje się do automatycznego sterowania (gating), bo tylko on jest odporny na manipulacje w łańcuchu dystrybucji.

### 8.3. Zarządzanie kluczami: kto ma prawo „pieczętować byt”

Wielu wdrożeń nie psuje brak podpisu, lecz brak polityki kluczy. Jeśli SBOM ma być dowodem, trzeba odpowiedzieć na pytanie: *kto* może podpisywać i *jak* zabezpieczamy klucz prywatny. Dobre praktyki obejmują separację ról i minimalizację powierzchni dostępu:

* klucze prywatne trzymane w HSM lub w bezpiecznej usłudze KMS,
* rotacja kluczy w przewidywalnym cyklu,
* ograniczenie podpisywania do kontrolowanych etapów pipeline’u,
* rozdział środowisk (dev/test/prod) różnymi kluczami,
* zasada „least privilege” dla kont i agentów build.

Jeżeli klucz prywatny wycieknie, podpis przestaje oznaczać zaufanie – staje się narzędziem atakującego. Dlatego w dojrzałej architekturze podpis jest traktowany jak zdolność do wystawiania „paszportu bytu” i podlega politykom porównywalnym z politykami certyfikacji.

### 8.4. Poziom transportu i dostępów: kanał, źródło, autoryzacja

Kryptografia chroni również przesyłanie SBOM i wyników analizy do centralnych systemów oraz kontroluje dostęp. Jeżeli SBOM i dane o podatnościach są wysyłane do SIEM, musi to odbywać się przez szyfrowane kanały (TLS) oraz z użyciem bezpiecznej autoryzacji. Token uwierzytelniający zdarzenia w centralnym indeksie (np. token Splunk HEC) jest przypisany do określonych uprawnień i stanowi mechanizm wymuszający: tylko uprawnione źródło może „mówić” do analityki.

To jest nie tylko ochrona poufności. To ochrona integralności całego systemu decyzyjnego: bez takiej warstwy atakujący może wstrzyknąć fałszywe SBOM-y lub raporty CVE do Splunka i spowodować błędne decyzje (maskowanie ryzyka albo generowanie szumu). Dlatego oprócz TLS stosuje się praktyki uzupełniające:

* mTLS (weryfikacja certyfikatu klienta),
* allow-listy źródeł i segmentację sieci,
* tokeny o minimalnym zakresie (per indeks / per sourcetype),
* rotację sekretów i monitoring nadużyć,
* kontrolę ekspozycji (HEC dostępny tylko z sieci CI, nie z całej domeny).

W tym modelu integralność kanału i integralność dokumentu (podpis) są komplementarne: kanał chroni przed podszyciem się i manipulacją w tranzycie, podpis chroni przed manipulacją „po drodze” i w archiwum.

### 8.5. Poziom historii: łańcuch dowodów, znaczniki czasu, niezmienność

Podpisy kryptograficzne umożliwiają budowę ciągłego łańcucha dowodów związanych z SBOM. Każdy kolejny SBOM (dla nowej wersji artefaktu) można podpisywać i opatrywać znacznikiem czasu. W ten sposób tworzymy historyczny łańcuch zaufania – chronologię, której nie da się zmienić bez pozostawienia śladu. Archiwizując SBOM-y wraz z podpisami, organizacja może po latach wykazać, że dany SBOM był autentyczny w danym czasie i że odpowiadał konkretnemu artefaktowi.

W praktyce znaczniki czasu mają znaczenie nie tylko audytowe. Umożliwiają rozróżnienie dwóch sytuacji, które w incydentach bywają mieszane: (1) „mieliśmy podatny komponent”, (2) „wiedzieliśmy o podatnym komponencie”. CVE jest wiedzą pojawiającą się asynchronicznie; podpisany i ostemplowany SBOM pozwala odtworzyć, *kiedy* dany skład był w użyciu, nawet jeśli informacja o podatności pojawiła się później. To porządkuje analizę ryzyka i odpowiedzialności.

Niektóre organizacje dopełniają ten model przez mechanizmy niezmienności przechowywania: repozytoria artefaktów z wersjonowaniem i retencją, obiekty WORM, a w nowszych podejściach – logi transparentności (rejestry, które utrudniają ukrycie faktu podpisania lub publikacji). Celem jest zawsze ten sam efekt: utrudnić manipulację historią po incydencie.

### 8.6. Weryfikacja po stronie konsumenta: podpis ma sens tylko wtedy, gdy jest sprawdzany

Podpis i attestation są użyteczne dopiero wtedy, gdy ich weryfikacja jest częścią procesu. W praktyce oznacza to, że:

* pipeline może weryfikować podpis SBOM przed publikacją lub przed deploymentem,
* odbiorca (inny zespół, klient, regulator) może weryfikować podpis w sposób automatyczny,
* analityka (np. Splunk) może odrzucać zdarzenia bez poprawnej autoryzacji źródła,
* polityki mogą rozróżniać ryzyko „znane i dowiedzione” od ryzyka „zadeklarowane bez dowodu”.

To jest krytyczne, bo inaczej podpis staje się elementem dekoracyjnym: istnieje, ale nie wpływa na decyzje.

### 8.7. Konsekwencje: kryptografia jako warunek sterowalności

Krótko mówiąc, kryptografia dostarcza języka zaufania dla SBOM: hash, podpis, certyfikat, token – to elementy, którymi system „mówi”: wiem, że ten ślad jest prawdziwy i pochodzi od właściwej tożsamości. Bez tych zabezpieczeń cała analiza SBOM mogłaby zostać podważona jednym zmanipulowanym bajtem, a system bezpieczeństwa – nawet jeśli bogaty w dashboardy – stałby się podatny na dezinformację. Dlatego w dojrzałym podejściu kryptografia nie jest „sekcją końcową”, tylko rdzeniem: to ona przekształca SBOM z opisowej listy w zaufany marker w pętli sterowania ryzykiem.

---

## 9. Podsumowanie: kryptologia informacyjna SBOM

SBOM jest fundamentem kryptologii informacyjnej w inżynierii bezpieczeństwa oprogramowania, bo:

* działa jak strukturalny marker tożsamości (odcisk relacji),
* umożliwia analizę kompozycji i delt,
* daje podstawę do automatycznego wnioskowania o ryzyku,
* wymaga kryptograficznego zabezpieczenia integralności,
* staje się sterowalny dopiero po spięciu z progami, alertami i workflow.

W praktyce SBOM nie jest „dokumentem”, lecz **interfejsem między bytem a decyzją**: z ontologii przechodzi do cybernetyki.

---

## Bibliografia i źródła robocze

Poniższy tekst został scalony i rozwinięty na podstawie trzech dokumentów roboczych (Word):

* **Kryptologia informacyjna – SBOM**
* **SBOM jako epistemologiczny artefakt w inżynierii oprogramowania i analiza zmian komponentów**
* **Architektura DevSecOps z SBOM i Analityką (Splunk, Jira, CI/CD)**

W samych dokumentach wskazano m.in. odniesienia do: OWASP CycloneDX, OWASP Cheat Sheet (Dependency Graph SBOM), Splunk Lantern, Black Duck oraz standardów i praktyk SBOM.
