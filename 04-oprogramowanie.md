# Komponenty oprogramowania:

- Backend server 
- Postgres
- InfluxDB
- Authenticator
- Connector
- Frontend

Wszystkie komponenty poza frontendem są skonteneryzowane przy użyciu Dockera.

## Backend server 
Serwer HTTPS, będący głównym komponentem systemu spajającym wszystko w całość, udostępnia REST API pozwalające na zarządzanie zasobami, sterowanie stacją oraz pobieranie informacji o stacji i systemie. Dodatkowo serwis ten udostępnia również websockety dla zadań o charakterze asynchronicznym.

Stack technologiczny: Python 3.9, FastAPI

## Postgres
Relacyjna baza danych przechowująca specyfikację stacji, użytkowników i ich przywileje.

## Influx
Baza przebiegów czasowych przechowująca surowe dane zbierane z czujników (np. ciśnienie w zbiornikach, napięcie i natężenie przepływające przez pompy) ale także wartości wyliczone z surowych danych (np. poziom wody, stan pompy włączona/wyłączona)

## Authenticator 
Mikroserwis służący do autoryzacji i uwierzytelniania użytkowników.

Stack technologiczny: Python 3.9

## Connector
Serwis będący łącznikiem między mikrokontrolerem (Arduino), komunikujący się bezpośrednio ze stacją, a Backend serwerem.

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

### Zaloguj się **POST /login**
    
    Waliduje dane logowania. Sesja jest przechowywana w pliku cookie.

    body :
    {
        "email": "user@email.com",
        "password": "password"
    }

    Wymagane uprawnienia: -

### Zarejestruj się **POST /signup**
Tworzy nowego użytkownika. Nowy użytkownik ma jedynie uprawnienia do odczytu.
```
    body:
    {
        "email": "user@email.com",
        "password": "password"
    }
```
Wymagane uprawnienia: brak

### Wyloguj się **GET /logout**
Usuwa sesję użytkownika. Powoduje wylogowanie z aplikacji webowej.

Wymagane uprawnienia: brak

### Pobierz nazwy wszystkich stacji **GET /workstations**
Wymagane uprawnienia: read

### Pobierz informacje o stacji **GET /workstation/{nazwa stacji}**
Wymagane uprawnienia: read

### Dodaj nowe zadanie **POST /task/{nazwa stacji}**
Wysyła polecenie do stacji np zamknij zawór x. Jest możliwość dodania warunków które muszą zostać spełnione żeby polecenie zostało wykonane.

    body: {
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


### Wyczyść kolejkę zadań **POST /flushqueue/{nazwa stacji}**
Usuwa wszystkie polecenia czekające w kolejce, a także przerywa polecenie które aktualnie czeka na spełnienie warunków.

Wymagane uprawnienia: write


### Pobierz listę zadań do wykonania **GET /tasklist/{nazwa stacji}** (nieużywany)
Zwraca kolejkę zadań oczekujących na wykonanie
    
Wymagane uprawnienia: read

### Odtwórz scenariusz **POST /scenario/{nazwa stacji}/{nazwa scenariusza}**
Odtwarza jeden z wcześniej stworzonych scenariuszy. Scenariusz jest listą poleceń.

Wymagane uprawnienia: write

### Dodaj scenariusz **POST /scenario/{nazwa scenariusza}**
Dodaje nowy scenariusz.

    body: schemat scenariusza (Patrz sekcja scenariusze) 

Wymagane uprawnienia: write


### Edytuj scenariusz **POST /scenario/{nazwa scenariusza}**
    Edytuje istniejący scenariusz

    body: schemat scenariusza (Patrz sekcja scenariusze) 

    Wymagane uprawnienia: write


### Usuń scenariusz DELETE /scenario/{nazwa scenariusza}
    Usuwa scenariusz.
    
    Wymagane uprawnienia: write


### Pobierz metryki GET /metrics/{nazwa stacji} (nieużywany)
    Zwraca zestaw metryk bazy danych. Metryki są zebrane z czujników na stacji

    Wymagane uprawnienia: read


### Wyślij metryki POST /metrics
    Zapisuje metryki do bazy danych. Ten endpoint jest używany tylko przez Connector.

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
Websockety są używan0e do komunikacji backend->frontend dla dwóch przypadków

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
            "V1": {
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
        "currentScenario": "", # aktualnie wykonywany scenariusz
        "type": "state" # metadane
    }

# System scenariuszy

## Format przykładowego scenariusza

    {
        "initial_conditions": {
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
        "description": "Opis":
        "tasks": 
        [
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
                "drop_after_ttl": true,
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
            },
            {
                "action": "is_open",
                "target": "V1",
                "value": 1
            },
            {
                "action": "is_open",
                "target": "V1",
                "value": 0,
                "timeout": 5
            }

        ]
    }

# Struktura obiektu scenariusz

**initial_conditions** (opcjonalne) - obiekt conditons. Początkowe warunki które muszą zostać spełnione aby scenariusz został wykonany

**description** - opis scenariusza (widoczny w aplikacji internetowej)

**tasks** - lista obiektów task. Lista zadań składających się na scenariusz.

# Struktura obiektu task

    {
        "action": "is_on",
        "target": "P2",
        "value": 0,
        "timeout": 10,
        "ttl": 30,
        "drop_after_ttl": true,
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
    },

**action** - zadanie wykonywane w tasku: is_on dla pomp, is_open dla zaworów

**target** - komponent na którym zostanie wykonane zadanie: zawór (Vx) lub pompa (Px)

**value** - wartość zadania: 1 - włączenie pompy/otwarcie zaworu , 0 - wyłączenie pompy/zamknięcie zaworu

**timeout** (opcjonalne) - czas w sekundach po którym zadanie zostanie przetworzone. Podczas czekania na przeminięcie tego czasu kolejka zadań jest zablokowana. 

**conditions** (opcjonalne) - obiekt typu conditions. Warunki na spełnienie których będzie czekało zadanie zanim zostanie przetworzone. Czekanie na spełnienie warunków blokuje kolejkę zadań

**ttl** (opcjonalne, domyślnie **10s**) - czas w sekundach przez który system będzie czekał na spełnienie warunków taska.

**drop_after_ttl** (opcjonalne, domyślnie **false**) - określa czy zadanie zostanie wykonane czy porzucone po minięciu czasu **ttl** bez spełnienia warunków. **false**  - zadanie zostanie wykonane po czasie ttl

# Struktura obiektu conditions

    {
        "operator": "and",
        "conditionlist": [
            {
                "measurement": "water_level",
                "field": "C3",
                "value": 5
                "type": "more",
            }
        ]
    }

**operator** (and/or) - spójnik łączący warunki. And - wszystkie warunki muszą być spełnione, or - tylko jeden warunek musi zostać spełniony

**conditionlist** - lista obiektów typu condition. Lista warunków

# Struktura obiektu condition
Warunek pozwala na uwarunkowanie wykonania zadania na podstawie dowolnej wartości dowolnej metryki

    {
        "measurement": "water_level",
        "field": "C3",
        "value": 5
        "type": "more",
    }


**measurement** - typ metryki z której warunek będzie odczytywał wartość

**field** - komponent którego dotyczy metryka (pompa, zawór lub zbiornik)

**value** - wartość której oczekujemy

**type** - typ warunku, określa czy oczekujemy że wartość metryki będzie większa, mniejsza lub równa podanej przez nas wartości

### Typy pola measurement i komponenty których one dotyczą:

- **current** - pompy, zawory
- **voltage** - pompy, zawory
- **water_level** - zbiorniki
- **is_on** - pompy
- **is_open** - zawory
- **float_switch_up** - zbiorniki
- **pressure** - zbiorniki

### Wartości pola type:

- equal
- more
- less
- moreequal
- lessequal

## Przykładowe scenariusze

### Włącz pompę P1 na 10 sekund 

    {
        "description": "Opis":
        "tasks": 
        [
            {
                "action": "is_on",
                "target": "P1",
                "value": 1
            },
            {
                "timeout": 10
                "action": "is_on",
                "target": "P1",
                "value": 0
            }
        ]
    }

### Włącz zawór V1 na tak długo aż poziom wody w C2 spadnie do 5cm

    {
        "description": "Opis":
        "tasks": 
        [
            {
                "action": "is_open",
                "target": "V1",
                "value": 1
            },
            {
                "timeout": 10
                "action": "is_open",
                "target": "V1",
                "value": 0,
                "ttl": 30, # warunek bedzie czekał maks 30 sekund na spełnienie
                "conditions": {
                    "operator": "and",
                    "conditionlist": [
                    {
                            "type": "more",
                            "measurement": "water_level",
                            "field": "C2",
                            "value": 5
                        }
                    ]
                }

            }
        ]
    }

### Otwórz wszystkie zawory i zamknij je w odstępach czasowych 10s

Warunki początkowe: Poziom wody w zbiornikach C2, C3, C4 jest większy niż 5cm

    {
        "initial_conditions": {
            "operator": "and",
            "conditionlist": [
                {
                    "type": "more",
                    "measurement": "water_level",
                    "field": "C1",
                    "value": 5
                },
                {
                    "type": "more",
                    "measurement": "water_level",
                    "field": "C2",
                    "value": 5
                },
                {
                    "type": "more",
                    "measurement": "water_level",
                    "field": "C3",
                    "value": 5
                }
            ]
        }
        "description": "Opis":
        "tasks": 
        [
            {
                "action": "is_open",
                "target": "V1",
                "value": 1
            },
            {
                "action": "is_open",
                "target": "V2",
                "value": 1
            },
            {
                "action": "is_open",
                "target": "V3",
                "value": 1
            },
            {
                "timeout": 10, 
                "action": "is_open",
                "target": "V1",
                "value": 0
            },
            {
                "timeout": 10, # 20 sekund od startu scenariusza
                "action": "is_open",
                "target": "V2",
                "value": 0
            },
            {
                "timeout": 10, # 30 sekund od startu scenariusza
                "action": "is_open",
                "target": "V3",
                "value": 0
            },
        ]
    }

### Pompuj wodę do zbiornika C2 aż osiągnie poziom 10cm albo gdy poziom wody z którego pompujesz (C1) spanie poniżej 2cm 
Warunkiem początkowym oczywiście będzie poziom wody w C2<10cm, C1>2cm

    {
        "initial_conditions": {
            "operator": "and",
            "conditionlist": [
                {
                    "type": "less",
                    "measurement": "water_level",
                    "field": "C3",
                    "value": 2
                }
            ]
        }
        "description": "Opis":
        "tasks": 
        [
            {
                "action": "is_on",
                "target": "P1",
                "value": 1
            },
            {
                "action": "is_on",
                "target": "P1",
                "value": 0,
                "ttl": 1000, # dowolna duża wartość, czekamy aż warunki zostaną spełnione
                "conditions": {
                    "operator": "or",
                    "conditionlist": [
                        {
                            "type": "more",
                            "measurement": "water_level",
                            "field": "C2",
                            "value": 10
                        },
                        {
                            "type": "less",
                            "measurement": "water_level",
                            "field": "C1",
                            "value": 2
                        }
                    ]
                }
            }
        ]
    }
