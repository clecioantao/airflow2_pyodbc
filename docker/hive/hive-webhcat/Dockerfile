FROM jaehue/hive-base:latest

COPY startup.sh .

ENV PYTHON_CMD=/usr/bin/python

USER root

RUN chmod +x startup.sh

EXPOSE 50111

CMD [ "./startup.sh" ]