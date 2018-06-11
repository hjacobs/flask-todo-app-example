FROM alpine:3.7
MAINTAINER Henning Jacobs <henning@jacobs1.de>

EXPOSE 8080

RUN apk add --no-cache python3 py3-gevent && python3 -m ensurepip

WORKDIR /
RUN pip3 install Flask Flask-Dance 

COPY app.py /
COPY templates /templates

ENTRYPOINT ["/usr/bin/python3", "app.py"]

