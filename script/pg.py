from clickhouse_driver import Client
import pyodbc
import os
from collections import namedtuple

PgColumn = namedtuple('PgColumn', ['name', 'isNullable', 'baseType', 'isArray', 'ext', 'pkCol'])

DSN = os.environ['DSN']
CH_DB = 'default'
CH_BUF_DB = 'import'

conn = pyodbc.connect('DSN=%s' % DSN)

getPgColumns_SQL = """
select
  a.attname,
  not a.attnotnull,
  a.atttypid::regtype::text,
  substring(format_type(a.atttypid, a.atttypmod) from '\((.*)\)') as ext,
  coalesce(ai.attnum, 0) as pk_attnum
from pg_class c
  inner join pg_namespace n on n.oid = c.relnamespace
  inner join pg_attribute a on a.attrelid = c.oid
  left join pg_index i on i.indrelid = a.attrelid and i.indisprimary
  left join pg_attribute ai on ai.attrelid = i.indexrelid and ai.attname = a.attname and ai.attisdropped = false
where
  n.nspname = ?
  and c.relname = ?
  and a.attnum > 0
  and a.attisdropped = false
order by
  a.attnum
"""

def getPgColumns(tblSchema, tblName):
  cur = conn.cursor()
  def rowToPgColumn(row):
    colName, isNullable, baseType, ext, pkCol = row
    if baseType[-2:]=='[]':
      baseType = baseType[:-2]
      isArray = True
    else:
      isArray = False
    if ext:
      ext = list(map(int, ext.split(',')))
    res = PgColumn(colName, int(isNullable), baseType, isArray, ext, pkCol)
#    print(res)
    return res

  cur.execute(getPgColumns_SQL, [tblSchema, tblName])
  res = list(map(rowToPgColumn, cur.fetchall()))
  cur.close()
  return res


pgToChMap = {
  "smallint": "Int16",
  "integer": "Int32",
  "bigint": "Int64",
  "character varying": "String",
  "varchar": "String",
  "text": "String",
  "real": "Float32",
  "double precision": "Float64",
  "interval": "Int32",
  "boolean": "UInt8",
  "decimal": "Decimal",
  "numeric": "Decimal",
  "character": "FixedString",
  "char": "FixedString",
  "jsonb": "String",
  "json": "String",
  "uuid": "UUID",
  "bytea": "Array(UInt8)",
  "inet": "Int64",
  "timestamp": "DateTime",
  "timestamp with time zone": "DateTime",
  "timestamp without time zone": "DateTime",
  "time": "UInt32",
  "time with time zone": "UInt32",
  "time without time zone": "UInt32",
  "date": "Date"
}


def toChType(col):
  chType = pgToChMap[col.baseType]
  if col.baseType == "numeric":
    chType = "%s(%d, %d)" % (chType, col.ext[0], col.ext[1])
  elif col.baseType == "character":
    chType = "%s(%d)" % (chType, col.ext[0])

  if col.isArray:
    chType = "Array(%s)" % (chType)
  elif col.isNullable:
    chType = "Nullable(%s)" % (chType)

  return chType


def getChDDL(tblName, pgColumns):
  pkColumns = {}
  for col in pgColumns:
    if col.pkCol:
      pkColumns[col.pkCol] = col.name
  pkColumns = [pkColumns[idx] for idx in sorted(pkColumns.keys())]
  return "CREATE TABLE IF NOT EXISTS %s (\n%s\n) Engine = %s(%s)\nORDER BY (%s)" % (
    tblName,
    ",\n".join(map(lambda col: " %s %s" % (col.name, toChType(col)), pgColumns)),
    "MergeTree",
    "",
    ",".join(pkColumns))


client = Client('clickhouse')

def execute(sql):
  print(sql)
  client.execute(sql)

tables = [
  "categories",
  "tournaments",
  "events",
  "player",
  "player_bonus",
  "payments",
  "bet",
  "bet_item"
]


for tblName in tables:
  execute("DROP TABLE IF EXISTS buf_%s" % tblName)
  execute("DROP TABLE IF EXISTS %s" % tblName)

execute("CREATE DATABASE import")
for tblName in tables:
   chDDL = getChDDL( tblName, getPgColumns('public', tblName) )
   execute(chDDL)
   bufName = "buf_%s" % tblName
   execute( "CREATE TABLE import.%s AS default.%s ENGINE=Buffer(default, %s, 16, 2, 20, 1000, 10000, 1000000, 10000000)" % (bufName, tblName, tblName) )
   execute( "INSERT INTO import.%s SELECT * FROM odbc('DSN=%s','','%s')" % (bufName, DSN, tblName) )
