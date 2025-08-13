# instalacja wsl:
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
* pip install requests pandas matplotlib openpyxl
# Uruchomienie serwera:
* python3 app.py
# Sprawdzenie serwera:
* w przeglądarce wpisz adres: http://localhost:1111

