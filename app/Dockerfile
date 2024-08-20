FROM python:alpine AS base
WORKDIR /app
COPY . /app
RUN pip3 install -r requirements.txt

CMD gunicorn -b 0.0.0.0:$PORT app:app
