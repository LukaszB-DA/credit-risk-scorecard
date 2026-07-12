<!-- 🇵🇱 Polski · 🇬🇧 [English version](README.md) -->

# Credit Scoring Model — Scorecard w Excelu (WoE/IV + regresja logistyczna MLE)

> Kompletny pipeline scoringu kredytowego zbudowany **od zera w Excelu**: ręczny binning WoE/IV,
> estymacja regresji logistycznej metodą największej wiarygodności (MLE) przez Solver,
> skalowanie karty scoringowej i pełny zestaw walidacyjny (AUC, KS, Gini, PSI).

*(Uzupełnij pola oznaczone `TODO:` przed publikacją.)*

---

## 1. Cel projektu

Zbudowanie interpretowalnej karty scoringowej (scorecard) przewidującej prawdopodobieństwo
niespłacenia kredytu (PD, *probability of default*) na podstawie danych aplikacyjnych,
wraz z pełną walidacją zgodną z praktyką modelowania ryzyka kredytowego.

Projekt świadomie **nie korzysta z gotowych bibliotek ML** — każdy etap (binning, WoE, IV,
funkcja wiarygodności, ROC, KS, PSI) jest policzony jawnie w arkuszu, żeby pokazać zrozumienie
mechaniki, a nie tylko wywołanie `sklearn`.

## 2. Dane

- **Źródło:** zbiór *German Credit* (`credit-g`) z OpenML, pobrany w Pythonie funkcją
  `sklearn.datasets.fetch_openml("credit-g", version=1)`.
- **Wielkość:** 1000 obserwacji, 20 zmiennych objaśniających + zmienna celu `class`.
- **Kodowanie targetu:** `good → 0`, `bad → 1`, więc **zdarzeniem modelowanym (1) jest default**.
  Determinuje to kierunek WoE (`WoE = ln(GoodDist / BadDist)` → wyższy WoE = niższe ryzyko).
- **Pipeline pozyskania:** skrypt [`fetch_data.py`](fetch_data.py) pobiera dane, przekodowuje
  target i zapisuje surowy plik → CSV zaimportowany do Excela. Surowe dane są dołączone do repo
  jako [`credit_data.csv`](credit_data.csv) (1000 × 21, bez braków danych).
- **Podział train/test (700 / 300):** wykonany ręcznie w Excelu — dodano pomocniczą kolumnę z
  liczbami losowymi na wszystkich 1000 wierszach, posortowano po niej, a następnie podzielono na
  pierwsze 700 (train) i pozostałe 300 (test). Powoduje to przetasowanie rekordów względem
  oryginalnej kolejności z CSV — stąd porządek w `Dev_sample` różni się od pliku źródłowego.
- Zbiory są **rozłączne** — części treningowa i testowa nie mają wspólnych rekordów (brak *leakage'u*).

```python
# fetch_data.py (skrót)
data = fetch_openml("credit-g", version=1, as_frame=True)
df = data.frame.copy()
df['class'] = df['class'].map({'good': 0, 'bad': 1})
df.to_csv("credit_data.csv", index=False)
```

> Uwaga metodyczna: tablice WoE/IV wyznaczono **wyłącznie na próbie treningowej**
> (arkusz `Dev_sample` = 700 rekordów rozwojowych), a następnie *zastosowano* do próby
> testowej. To poprawne podejście — brak leakage'u z testu do binningu.

## 3. Struktura pliku (arkusze)

| Arkusz | Zawartość |
|---|---|
| `Dev_sample` | Surowa próba rozwojowa (700 rek.) — podstawa wyznaczenia WoE/IV |
| `Binning_WOE_IV` | Ręczny binning: Good/Bad, GoodDist/BadDist, **WOE**, IV per bin, IV total; tablice mapujące kategorie na biny |
| `TRAIN_DATA` | 700 rek. treningowych: surowe cechy → WoE → score cząstkowy → PD → decyzja |
| `TEST_DATA` | 300 rek. testowych, ten sam pipeline scoringowy |
| `TRAIN_AUC` / `TEST_AUC` | Punkty krzywej ROC (TPR/FPR) i pole AUC metodą trapezów |
| `TRAIN_SUMMARY` / `TEST_SUMMARY` | Współczynniki β, log-likelihood, AUC, KS, Gini, statystyki PD |
| `TRAIN_Histogram` / `TEST_Histogram` | Rozkłady score / PD |
| `SCORECARD_SCALLING` | Parametry skalowania: PDO, Base score, Odds, Factor, Offset |
| `POINTS_TABLE` | Tablica punktów scorecardu per zmienna/bin |
| `PSI` | Population Stability Index (train vs test) po binach score |
| `Summary` | Polityka decyzyjna (progi), liczności i średnie PD w koszykach |
| `Documentation` | (do uzupełnienia) |

## 4. Metodyka

1. **Binning + WoE/IV.** Zmienne pogrupowane w biny; dla każdego binu:
   `WoE = ln(GoodDist / BadDist)`, `IV_bin = (GoodDist − BadDist) · WoE`, `IV_total = Σ IV_bin`.
2. **Regresja logistyczna (MLE).** Model liniowy na zmiennych WoE; parametry β0…β12
   wyznaczone przez **maksymalizację log-wiarygodności w Solverze** (12 predyktorów + wyraz wolny).
3. **Skalowanie scorecardu.** `Factor = PDO / ln(2)`, `Offset = Base − Factor · ln(Odds)`.
   Parametry: **PDO = 30, Base score = 600, Odds = 20:1**, stąd Factor ≈ 43.28, Offset ≈ 470.34.
   Interpretacja: przy score 600 szansa dobry:zły = 20:1; każde 30 pkt podwaja szansę.
4. **Polityka decyzyjna:** Reject `< 500` · Manual review `500–579` · Accept `≥ 580`.

## 5. Wyniki (zweryfikowane)

| Metryka | Train (700) | Test (300) |
|---|---|---|
| **AUC** | 0.804 | 0.815 |
| **KS** | 0.493 | 0.540 |
| **Gini** | 0.608 | 0.631 |

- **PSI (train vs test) = 0.064** → poniżej 0.10, populacje stabilne.
- Test nieznacznie lepszy od train — mieści się w szumie przy N_test = 300 i nie jest sygnałem
  ostrzegawczym (brak leakage'u potwierdzony rozłącznością zbiorów).

Rozkład decyzji:

| Koszyk | Train | Test |
|---|---|---|
| Accept | 124 | 40 |
| Manual review | 304 | 141 |
| Reject | 272 | 119 |

## 6. Jak otworzyć

> **Wymagany Microsoft Excel 2021 lub Microsoft 365** (ewentualnie Google Sheets).
> Model korzysta z funkcji `XLOOKUP` i `LET`. Są to standardowe funkcje współczesnego
> arkusza — w środowiskach docelowych (banki, korporacje) 365 jest normą. Starsze wersje
> Excela (≤ 2019) oraz LibreOffice tych funkcji nie obsługują i wyświetlą `#NAME?`.
> Otwórz plik w odpowiedniej wersji, aby logika modelu liczyła się poprawnie.

## 7. Ograniczenia

Model zbudowano na zbiorze `credit-g` (OpenML) — klasycznym benchmarku, którego właściwości
wyznaczają sposób interpretacji wyników. Jest to scorecard **aplikacyjny** (nie behawioralny,
bez segmentacji), zwalidowany na jednorazowym, losowym zbiorze testowym. Należy go traktować
jako demonstrację *procesu* modelowania, a nie gotowy komponent produkcyjny.

- **Mały zbiór.** 1000 obserwacji (~300 BAD) ogranicza ocenę stabilności, zwłaszcza dla rzadszej
  klasy BAD.
- **Brak walidacji out-of-time.** Podział jest losowy, nie czasowy — zachowanie modelu w czasie
  pozostaje nieznane.
- **Brak zmiennych behawioralnych.** Wyłącznie dane aplikacyjne; produkcyjne modele PD korzystają
  też z danych transakcyjnych i historii rachunku.
- **Brak segmentacji.** Jeden model dla całej populacji; w produkcji często stosuje się segmenty
  (produkt, przedział wieku, pre-scoring itd.).
- **Brak braków danych.** Zbiór jest kompletny, więc nie da się ocenić jakości imputacji ani wpływu
  missingów (część „braku" jest zakodowana jako kategoria, np. *no checking account*).
- **Logit bez regularyzacji.** W zasadzie podnosi to ryzyko overfittingu na małej próbie. Dwie
  przesłanki przeczą jednak *istotnemu* przeuczeniu: wynik na teście dorównuje/przewyższa train
  (AUC 0.815 vs 0.804), a samo grube binowanie WoE jest silnym regularyzatorem redukującym
  efektywne stopnie swobody. Dopasowanie z karą L2 pozostaje sensownym testem odporności.
- **Częściowe pokrycie driftu.** PSI policzono na poziomie score (0.064, stabilnie); stabilności
  per-zmienna (CSI) ani driftu w czasie nie badano.
- **Brak testów fairness.** Brak oceny biasu względem atrybutów wrażliwych (dane kodują płeć w
  `personal_status`, plus `age`) — coraz częściej oczekiwanej w modelach kredytowych w UE.
- **Brak walidacji produkcyjnej.** Model nie był testowany na danych operacyjnych ani w środowisku
  scoringowym.
- **Benchmarkowy charakter danych.** `credit-g` jest zbiorem edukacyjnym; zmienne są uproszczone
  i nie odzwierciedlają pełnej struktury danych kredytowych.

## 8. Odtwarzalność i dalsze kroki

Zbudowano i zweryfikowano na:

| Komponent | Wersja |
|---|---|
| Python | 3.14 |
| pandas | 3.0.3 |
| scikit-learn | 1.9.0 |

`fetch_openml("credit-g", version=1)` przypina wersję zbioru z OpenML, więc surowe pobranie jest
stabilne między środowiskami. Uwaga: podział 700/300 wykonano ręcznie w Excelu (bez ustalonego
ziarna), więc *dokładnej* partycji nie da się odtworzyć z samego skryptu — wynikowe arkusze
train/test są zapisane w skoroszycie.

Naturalne rozszerzenia: kalibracja PD, walidacja out-of-time, reject inference, CSI per-zmienna,
test fairness oraz porównanie z modelem regularyzowanym L2.

---

*Autor: [LukaszB-DA](https://github.com/LukaszB-DA) · Projekt portfolio — modelowanie ryzyka kredytowego / quantitative analytics.*
