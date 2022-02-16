FROM 738572153508.dkr.ecr.us-east-1.amazonaws.com/gitstats:seed-v1

ARG D_CLIENT_ID
ARG D_SECRET_KEY

WORKDIR /var/app/

COPY . /var/app/

ENV DOMO_CLIENT_ID=$D_CLIENT_ID
ENV DOMO_CLIENT_SECRET=$D_SECRET_KEY

RUN cd /var/app

RUN pip3 install -r requirements.txt

RUN ["cat"]
