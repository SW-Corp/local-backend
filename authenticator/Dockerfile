FROM python:3.9-alpine
EXPOSE 8000/tcp

RUN apk add build-base libffi-dev
COPY ./authenticator.py /opt/
COPY ./requirements.txt /opt/
WORKDIR /opt

RUN pip install -r requirements.txt

CMD ["python", "-u", "authenticator.py", "--port", "8000"]
