instalacja wsl.
w powershell:
wsl --install
wsl.exe --install Ubutnu-22.04
Wyszukujemy w menu start Ubuntu-22.04
w ubuntu:
przy pierwszym uruchomieniu tworzymy uzytkownika.
apt update
apt install python3 python3-pip git flask
Pobieramy projekt.
git clone https://github.com/szerszen296/projekt.git
cd projekt
python3 -m venv .venv
. .venv/bin/activate
Pobieramy potrzebne programy
pip install requests pandas matplotlib
By uruchomic serwer:
python3 app.py

