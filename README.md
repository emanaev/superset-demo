# superset-demo
Apache Superset + Clickhouse + Import from Postgres (GreenPlum?) in Docker

# Usage
Clone the repo
```
git clone https://github.com/emanaev/superset-demo.git
cd superset-demo
```

Create local file `odbc.ini` for your Postgres (GreenPlum) datasource. Use the template replacing <VARIABLES> with your custom settings:
```
[<DSN_NAME>]
DRIVER = PostgreSQL ANSI
SERVERNAME = <POSTGRES_SERVER_DNS_OR_IP>
PORT = 5432
DATABASE = <POSTGRES_DATABASE_NAME>
USERNAME = <POSTGRES_LOGIN>
PASSWORD = <POSTGRES_PASSWORD>
```

Use `DRIVER = Postgres ANSI` for ANSI-encoded connections or `DRIVER = Postgres Unicode` for Unicode connections, see [`odbcinst.ini`](https://github.com/emanaev/superset-demo/blob/master/clickhouse/odbcinst.ini) for details

Create local file `dsn.env` (replace <DSN_NAME> with approppriate name, setted in `odbc.ini` earlier):
```
DSN=<DSN_NAME>
```
Adjust list of your Postgres (GreenPlum) tables you want to import in ClickHouse at the end of [`script/run.py`](https://github.com/emanaev/superset-demo/blob/master/script/run.py#L135):
```
tables = ['table1', 'table2', ...]
```
Start the core:
```
docker-compose build
docker-compose up -d postgres redis clickhouse
```
Start and init Superset. You will be prompted to create admin account. Remember the password:
```
docker-compose up -d superset
docker-compose exec superset superset-init
```
Run importer. It will copy table structure from Postgres (GreenPlum) to Clickhouse `default` database and fill it with data
```
docker-compose run script
```
Go to `http://<LOCAL_IP>:8088`, login with login/password settled earlier and create a database with type `Clickhouse` and server address `clickhouse`
Now you'll be able to see imported tables in `default` database. Use SQL Editor to surf them, or created your dashboards
