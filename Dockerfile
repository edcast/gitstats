FROM python:3.7-alpine

RUN apk add g++ && apk add git

WORKDIR /var/app/

COPY requirements.txt /var/app/

RUN cd /var/app

RUN pip3 install -r requirements.txt

RUN ["cat"]
