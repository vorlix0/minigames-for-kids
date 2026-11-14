# Minigry dla dzieci

Zbiór prostych minigier w Pythonie. Pierwszą grą jest labirynt.

## Uruchomienie

Potrzebny jest Python 3.8 lub nowszy z biblioteką Tkinter. W katalogu
projektu uruchom:

```powershell
py main.py
```

W systemach, w których Python jest dostępny jako `python3`, można użyć
`python3 main.py`. Tkinter jest zwykle częścią instalacji Pythona; w niektórych
dystrybucjach Linuksa wymaga osobnego pakietu.

## Labirynt

Wybierz kolor mazaka i poziom, a następnie kliknij mazak na starcie i prowadź
go do mety, trzymając lewy przycisk myszy. Po puszczeniu przycisku możesz
kontynuować od końca narysowanej ścieżki.

- **Łatwy:** mazak może wychodzić poza ścieżkę.
- **Trudny:** wyjście poza ścieżkę powoduje wyczyszczenie rysunku i powrót na start.

Przycisk „Od nowa” rozpoczyna grę ponownie. Zmiana poziomu również zaczyna
nową grę. Przycisk „Menu” pozwala wrócić do wyboru minigry.

## Rozbudowa i testy

Każda gra ma własny katalog w `games`; nową grę można dodać do menu w
`main.py`. Logika labiryntu jest oddzielona od interfejsu Tkintera.

```powershell
py -m unittest discover
```
