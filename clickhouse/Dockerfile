FROM yandex/clickhouse-server
RUN apt-get -yqq update && \
    apt-get install -y unixodbc odbc-postgresql
RUN ln -s /usr/lib/x86_64-linux-gnu/odbc/psqlodbca.so /usr/lib/x86_64-linux-gnu/psqlodbca.so && \
    ln -s /usr/lib/x86_64-linux-gnu/odbc/psqlodbcw.so /usr/lib/x86_64-linux-gnu/psqlodbcw.so
COPY odbcinst.ini /etc/odbcinst.ini
