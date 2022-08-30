build:
	docker build -t ${tag} .
clean:
	docker rmi -f ${tag}
run:
	docker run -d -p ${port}:${port} --name ${name} ${tag}

all:
	docker-compose up --build

all-nobase:
	docker-compose up --build server authenticator

clean:
	docker-compose down

db:
	docker-compose up --build -d postgres

enviroment:
	docker-compose up --build -d postgres influx authenticator

venvserver:
	backend -c src/backend/venv.conf
