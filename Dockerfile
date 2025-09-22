FROM python:3.13.1

WORKDIR /app

RUN pip install poetry==1.8.5

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-root --only main

COPY . .
