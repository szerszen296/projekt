# Instalacja wsl:
* W powershell:
  - wsl --install
  - wsl.exe --install Ubuntu-22.04
* Wyszukujemy w menu start Ubuntu-22.04
* Uruchamiamy ubuntu z menu start
# Instalacja potrzebnych programów:
* sudo apt update
* sudo apt install python3 python3-pip git
* sudo pip install flask
# Pobranie projektu:
git clone https://github.com/szerszen296/projekt.git
# Tworzenie środowiska:
* cd projekt
* python3 -m venv .venv
* . .venv/bin/activate
# Instalacja potrzebnych programów do środowiska:
* pip install requests pandas matplotlib openpyxl pytest-playwright pytest pytest-html pytest-xdist
* playwright install
* playwright install-deps
# Uruchomienie serwera:
* python3 app.py
# Sprawdzenie serwera:
* W przeglądarce wpisz adres: http://localhost:1111
# Testowanie serwera:
* Test serwera pozwala sprawdzić czy:
  - Jest tabela z pięcioma wynikami
  - Jest obrazek o wielkości 800x400
  - Przyciski pobierania działają poprawnie
  - Lista zmiany czasu działa poprawnie
  - Lista zmiany waluty działa poprawnie
* By uruchomić test serwera bedąc w głównym katalogu serwera należy wpisać komendy:
  - cd test
  - pytest test.py
* By uruchomić testy na wszystkich rdzeniach należy użyć komendy:
  - pytest -n auto test.py
* Zalecane jest używanie 2 rdzenieniów do testów:
  - pytest -n 2 test.py
* Raport generuje się w formacie html w katalogu gdzie znajdują się testy.


