FROM 738572153508.dkr.ecr.us-east-1.amazonaws.com/gitstats:seed-v1

WORKDIR /var/app/

COPY requirements.txt /var/app/

RUN cd /var/app

RUN pip3 install -r requirements.txt

RUN ["cat"]
