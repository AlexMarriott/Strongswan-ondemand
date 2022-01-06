FROM ubuntu
WORKDIR /

ENV FLASK_APP main.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_RUN_PORT 80
ARG DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y python3 python3-pip software-properties-common && mkdir -p /opt/flask && add-apt-repository --yes --update ppa:ansible/ansible && apt update && apt install ansible -y


COPY webserver/ /opt/flask
RUN pip3 install -r /opt/flask/requirements.txt
WORKDIR /opt/flask
CMD [ "python3", "main.py"]