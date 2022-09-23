# SWCorp Backend

## Komponenty
1. Baza danych Postgres - przechowuje informacje o stacji i użytkownikach
2. Baza danych Influx - przechowuje szeregi czasowe (dane z czujników na stacji)
4. Authenticator - mikroserwis autoryzujący i autentykujący użytkowników
5. Backend serwer - serwer zarządzający wszystkimi zasobami

## Zależności
Docker

docker-compose

## Uruchomienie
1. Edytuj plik konfiguracyjny
2. make all