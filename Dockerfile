FROM alpine:3.7
MAINTAINER Henning Jacobs <henning@jacobs1.de>

EXPOSE 8080

RUN apk add --no-cache python3 py3-gevent && python3 -m ensurepip

WORKDIR /
RUN pip3 install Flask Flask-Dance redis

COPY app.py /
COPY static /static
COPY templates /templates

ENTRYPOINT ["/usr/bin/python3", "app.py"]

