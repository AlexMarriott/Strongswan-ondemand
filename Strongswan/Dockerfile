FROM ubuntu
WORKDIR /

ENV FLASK_APP main.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_RUN_PORT 80

RUN apt update && apt install -y python3 python3-pip ansible

COPY webserver/ .
RUN pip3 install -r requirements.txt

CMD [ "python3", "main.py"]