build:
	docker build -t ${tag} .
clean:
	docker rmi -f ${tag}
run:
	docker run -d -p ${port}:${port} --name ${name} ${tag}

up:
	docker compose up

all:
	bash ./shutdown_service/init_shutdown_service.sh
	docker-compose up --build -d

clean:
	docker-compose down

enviroment:
	docker-compose up --build -d postgres influx authenticator

venvserver:
	backend -c src/backend/venv.conf
