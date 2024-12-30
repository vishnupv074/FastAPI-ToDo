FROM python:3.11.11-alpine3.21
LABEL maintainer="vishnupv074"

ENV PYTHONBUFFERED 1

# Install sqlite3 
RUN apk add --no-cache sqlite

COPY ./requirements.txt /tmp/requirements.txt
COPY . /app
WORKDIR /app
EXPOSE 8000

RUN apk add --no-cache bash && \
    python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    rm -rf /tmp && \
    adduser \
        --disabled-password \
        --no-create-home \
        fast-user

ENV PATH="/py/bin:$PATH"

USER fast-user