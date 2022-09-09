FROM python:3.10-alpine

COPY src/twitter_api.py /bots/
COPY src/dalle_api.py /bots/
COPY src/credential.py /bots/
COPY requirements.txt /bots/

WORKDIR /bots

RUN pip3 install -r requirements.txt

RUN mkdir /bots/images/

LABEL maintainer="Zekeriya AY <zekeriya@zekeriyaay.com>"

CMD [ "python3", "twitter_api.py" ]
