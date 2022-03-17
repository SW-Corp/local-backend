FROM python:3.9-alpine
EXPOSE 8000/tcp

COPY ./authenticator.py /opt/
WORKDIR /opt

#RUN pip install -r requirements.txt

CMD ["python", "-u", "authenticator.py", "--port", "8000"]
