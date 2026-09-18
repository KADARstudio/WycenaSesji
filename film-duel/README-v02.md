# Seans 0.2 — prototyp mobilny

Adres aplikacji: https://raw.githack.com/KADARstudio/WycenaSesji/film-duel-prototype/film-duel/index.html

Zmiany: animowane pojedynki, zwycięzca zachowany w tym samym elemencie ekranu, licznik kolejnych zwycięstw, opcjonalne oryginalne dźwięki, animowany finał, statystyki rzeczywistych decyzji i czasu, historia do 200 sesji, oznaczanie obejrzanych, oceny 1–5 i eksport JSON.

Dźwięki są domyślnie wyłączone; włącza je ikona nuty. Ikona biblioteki otwiera historię i listę zapisanych filmów. Zachowano dotychczasowe ustawienia i zapisy w tej samej przeglądarce.

## Testowanie

Python 3.12, Node.js oraz Playwright 1.57.0:

```
python -m pip install playwright==1.57.0
python -m playwright install --with-deps chromium webkit
python film-duel/test-v02.py
```

Testy obejmują czyste funkcje turnieju i księgowania, pełne sesje w Chromium i WebKit oraz oddzielnie rzeczywisty publiczny adres, bez makiet odpowiedzi hostingu. Raporty: test-results-v02/report.json oraz public-test-results/report.json. Test przeglądarkowy nie zastępuje testu na fizycznym telefonie.

## Dane i ograniczenia

Brak kont i synchronizacji. Historia, oceny i wybory są zapisywane lokalnie; można je usunąć lub wyeksportować. Wybranie filmu, otwarcie platformy i potwierdzenie obejrzenia są rozdzielone. Czas dotyczy widocznego ekranu pojedynków; cofnięcie decyzji nie cofa rzeczywiście spędzonego czasu. Sesje ze starej wersji nie otrzymują zmyślonych pomiarów.

Katalog testowy obejmuje próbkę do 100 popularnych filmów na platformę, nie wszystkie tytuły. Dane PL dotyczą abonamentów. Aplikacja próbuje pobrać najnowszy opublikowany katalog z gałęzi film-duel-prototype; awaryjnie używa datowanej kopii i ostrzega o starszych danych. Nie gwarantuje dostępności filmu ani odświeżenia dokładnie co godzinę. Nieoficjalną integrację JustWatch trzeba zastąpić właściwą umową/API przed komercyjną premierą. Nie ma jeszcze trybu par ani rekomendacji AI.
