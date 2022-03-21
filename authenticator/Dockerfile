FROM python:3.9-alpine
EXPOSE 8080/tcp

RUN apk add libpq-dev libffi-dev gcc musl-dev
COPY ./* /opt/

WORKDIR /opt

RUN pip install -r requirements.txt

CMD ["python", "-u", "authenticator.py", "--port", "8080"]
