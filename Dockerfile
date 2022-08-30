FROM python:3.9-alpine
COPY . /backend
WORKDIR /backend

RUN mkdir "/backend/venv" && python3 -m venv "/backend/venv"
RUN apk add libpq-dev libffi-dev gcc musl-dev

# RUN echo ehhhh 
# RUN echo $PATH 


ENV PATH="$PATH:/backend/venv/bin"

RUN pip install -U pip && pip install -e .

ENTRYPOINT ["backend", "-c", "src/backend/config.conf"]