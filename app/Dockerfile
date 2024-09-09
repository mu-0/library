FROM python:alpine AS base
WORKDIR /app
COPY requirements.txt /app
RUN apk add --no-cache poppler-utils
RUN pip3 install -r requirements.txt
COPY . /app

CMD gunicorn -b 0.0.0.0:$PORT app:app
