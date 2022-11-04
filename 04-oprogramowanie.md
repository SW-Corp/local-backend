# Komponenty oprogramowania:

    Backend server 
    Postgres
    InfluxDB
    Authenticator
    Connector
    Frontend

Wszystkie komponenty poza frontendem są skonteneryzowane przy użyciu Dockera.

## Backend server 
Serwer HTTPS, będący głównym komponentem systemu spajającym wszystko w całość. Udostępnia REST API pozwalające na zarządzanie zasobami, sterowanie stacją oraz pobieranie informacji o stacji i systemie. Dodatkowo serwis ten udostępnia również websockety dla zadań o charakterze asynchronicznym.

Stack technologiczny: Python 3.9, FastAPI

## Postgres
Relacyjna baza danych przechowująca specyfikację stacji, użytkowników i ich przywileje.

## Influx
Baza danych przebiegów czasowych przechowująca surowe dane zbieranie z czujników (np. ciśnienie w zbiornikach, napięcie w pompach) ale także wartości wyliczone z surowych danych (np. poziom wody, stan pompy włączona/wyłączona)

## Authenticator 
Mikroserwis służący do autoryzacji i uwierzytelniania użytkowników.

Stack technologiczny: Python 3.9

## Connector
Serwis będący łącznikiem między mikrokontrolerem (Arduino) komunikującym się bezpośrednio ze stacją, a Backend serwerem.

## Frontend 
Aplikacja webowa
//TODO

## Schemat przepływu danych
https://lucid.app/lucidchart/3b34f2a0-714b-4b3c-9c2b-add233da9218/edit?viewport_loc=-305%2C7%2C2198%2C1067%2C0_0&invitationId=inv_3eabc9c2-0e27-46bf-bd7e-bdf3ca0a2648

# Autoryzacja:
## Uprawnienia
    Użytkownik ma przypisany poziom uprawnień jakie posiada.
    Uprawnienia: read, write, manage_users. Każdy kolejny poziom uprawnień zawiera w sobie poprzedni.
    
    Read - podstawowy poziom, pozwala na pobieranie informacji ze stacji

    Write - pozwala na sterowanie stacją oraz kalibrowanie czujników

    Manager_users (admin) - pozwala na nadawanie uprawnień innym użytkownikom, usuwanie użytkowników oraz wyłączenie całej stacji.


# Backend API

## Endpointy HTTP

### Zaloguj sie POST /login
    
    Waliduje dane logowania. Sesja jest przechowywana w pliku cookie.

    body :
    {
        "email": "user@email.com",
        "password": "password"
    }

    Wymagane uprawnienia: -

### Zarejestruj się POST /signup
    Tworzy nowego użytkownika.Nowy użytkownik ma jedynie uprawnienia do odczytu,
    body :
    {
        "email": "user@email.com",
        "password": "password"
    }

    Wymagane uprawnienia: -

### Wyloguj się GET /logout
    Usuwa sesję.

    Wymagane uprawnienia: -

### Pobierz nazwy wszystkich stacji GET /workstations
    Wymagane uprawnienia: read

### Pobierz informacje o stacji GET /workstation/{nazwa stacji}
    Wymagane uprawnienia: read

### Dodaj nowe zadanie POST /task/{nazwa stacji}
    Wysyła polecenie do stacji np zamknij zawór x. Jest możliwość dodania warunków które muszą zostać spełnione żeby polecenie zostało wykonane.

    body:{
        "action": "is_open",
        "target": "valve1",
        "value": 1,
        "conditions":{
            "operator": "and",
            "conditionlist": [
                {
                    "type": "more",
                    "measurement": "water_level",
                    "field": "tank1",
                    "value": 100
                },
                {
                    "type": "more",
                    "measurement": "water_level",
                    "field": "tank2",
                    "value": 100
                }
            ]
        }
    }

    is_open dla zaworów (0/1)
    is_on dla pomp (0/1)        

    Wymagane uprawnienia: write


### Wyczyść kolejkę zadań POST /fushqueue/{nazwa stacji}
    Usuwa wszystkie polecenia czekające w kolejce, a także przerywa polecenie które aktualnie czeka na spełnienie warunków.

    Wymagane uprawnienia: write


### Pobierz listę zadań do wykonania GET /tasklist/{nazwa stacji} (nieużywany)
    Zwraca kolejkę zadań oczekujących na wykonanie
    
    Wymagane uprawnienia: read

### Odtwórz scenariusz POST /scenario/{nazwa stacji}/{nazwa scenariusza}
    Odtwarza jeden z wcześniej stworzonych scenariuszy. Scenariusz jest listą poleceń.

    Wymagane uprawnienia: write

### Dodaj scenariusz POST /scenario/{nazwa scenariusza}
    Dodaje nowy scenariusz.

    body: schemat scenariusza (Patrz sekcja scenariusze) 

    Wymagane uprawnienia: write


### Edytuj scenariusz POST /scenario/{nazwa scenariusza}
    Edytuje istniejący scenariusz

    body: schemat scenariusza (Patrz sekcja scenariusze) 

    Wymagane uprawnienia: write


### Usuń scenariusz DELETE /scenario/{nazwa scenariusza}
    Usuwa scenariusz.
    
    Wymagane uprawnienia: write


### Pobierz metryki GET /metrics/{nazwa stacji} (nieużywany)
    Zwraca zestaw metryk bazy danych. Metryki są zebrane z czujników na stacji

    Wymagane uprawnienia: read


### Wyślij metryki POST /metrics/
    Zapisuje metryki do bazy danych. Ten endpoint jest używany tylko przez Connectora

    body: {
        "workstation_name": "testworkstation",
        "metrics": [
            {
                "measurement": "water_level",
                "field": "tank1",
                "value": 10
            },
            {
                "measurement": "water_level",
                "field": "tank2",
                "value": 10
            }
        ]
    }

    Wymagane uprawnienia: write


### Pobierz listę użytkowników GET /users
    Zwraca użytkowników wraz z ich uprawnieniami

    Wymagane uprawnienia: manage_users

### Nadaj uprawnienia POST /permission
    Zmienia uprawnienia użytkownika

    body : {
    "user": "user2@email.com",
    "permission": "write"
    }

    Wymagane uprawnienia: manage_users

### Pobierz logi GET /logs
    Pobierz listę logów operacji wykonywanych na stacji.

    Wymagane uprawienia: read

# Komunikacja przez websockety
Websockety są używane do komunikacji backend->frontend dla dwóch przypadków

    Przesyłanie powiadomień
    Przesyłanie stanu stacji

## Powiadomienia 
Backend przesyła powiadomienia w następujących sytuacjach:

1. Potwierdzenie wykonania zadania (operacji na komponencie stacji), bądź też błąd podczas wykonywania zadania.
2. Rozpoczęcie oraz zakończenie scenariusza.
3. Niespełnienie warunków zadania lub początkowych warunków scenariusza.

## Przesyłanie stanu stacji
Connector cyklicznie przesyła do Backendu informacje z czujników stacji. W momencie odebrania danych Backend przetwarza je, zapisuje do bazy danych oraz rozsyła aktualny stan stacji do wszystkich podłączonych websocketów.

Struktura danych stanu stacji przesyłana do Frontendu.

    {
        "pumps": {
            "P1": {
                "voltage": 12, 
                "current": 1000,
                "is_on": true
            },
            <pozostałe pompy>
        },
        "valves": {
            "V3": {
                "voltage": 12,
                "current": 1000,
                "is_open": true
            },
            <pozostałe zawory>
        },
        "tanks": {
            "C1": {
                "pressure": 1000,
                "offset": -1.5, # offset wyliczony w procesie kalibracji
                "water_level": 8.5,
                "float_switch_up": false, # stan pływaka
                "water_volume": 1683
            },
            <pozostałe zbiorniki>

        },
        "currentScenario": "", #aktualnie wykonywany scenariusz
        "type": "state" #metadane
    }

# System scenariuszy

## Format przykładowego scenariusza
//TODO

    {
        "initial_conditions":{
            "operator": "and",
            "conditionlist": [
                {
                    "type": "more",
                    "measurement": "water_level",
                    "field": "C1",
                    "value": 5
                },
                {
                    "type": "less",
                    "measurement": "water_level",
                    "field": "C3",
                    "value": 2
                }
            ]
        }
        ,
        "description": "Opis": [
            {
                "action": "is_on",
                "target": "P2",
                "value": 1
            },
            {
                "action": "is_on",
                "target": "P2",
                "value": 0,
                "ttl": 30,
                "conditions": {
                    "operator": "and",
                    "conditionlist": [
                        {
                            "type": "more",
                            "measurement": "water_level",
                            "field": "C3",
                            "value": 5
                        }
                    ]
                }
            }

        ]
    }