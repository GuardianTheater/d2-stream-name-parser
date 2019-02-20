FROM ubuntu:bionic

ARG github_token
ARG github_name
ARG github_email

RUN apt-get update && apt-get install -y software-properties-common
RUN add-apt-repository ppa:alex-p/tesseract-ocr
RUN apt-get update && apt-get install -y \
    git \
    python-pip \
    tesseract-ocr-grc

RUN git config --global url."https://$github_token:@github.com/".insteadOf "https://github.com/"
RUN git config --global user.name "$github_name"
RUN git config --global user.email "$github_email"

WORKDIR /usr/src/app
COPY . /usr/src/app

RUN pip install --trusted-host pypi.python.org -r requirements.txt --upgrade

CMD ["python", "d2screens.py"]