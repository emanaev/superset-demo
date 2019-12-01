FROM python:3.7
RUN apt-get -yqq update && \
    apt-get install -y unixodbc-dev odbc-postgresql
WORKDIR /
COPY requirements.txt /
RUN pip install -r requirements.txt
COPY odbcinst.ini /etc/odbcinst.ini
COPY *.py /
CMD ["python", "run.py"]
