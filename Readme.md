# SWCorp Backend

## Komponenty
Baza danych Postgres - przechowuje informacje o stacji i użytkownikach
Baza danych Influx - przechowuje szeregi czasowe (dane z czujników na stacji)
Authenticator - mikroserwis autoryzujący i autentykujący użytkowników
Backend serwer - serwer zarządzający wszystkimi zasobami

## Zależności
Docker
docker-compose

## Uruchomienie
1. Edytuj plik konfiguracyjny
2. make all