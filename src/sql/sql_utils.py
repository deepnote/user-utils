def _deepnote_execute_sql(query, postgres_connection_string_env_var):
  class ExecuteSqlError(Exception):
    pass

  import psycopg2
  import pandas as pd
  import os

  if not postgres_connection_string_env_var:
    raise ExecuteSqlError('This SQL cell is not linked with an connected integration')

  connection_string = os.environ.get(postgres_connection_string_env_var)
  if not connection_string:
    raise ExecuteSqlError('This SQL cell is not linked with an connected integration')

  connection = None
  try:
    connection = psycopg2.connect(connection_string)
    return pd.io.sql.read_sql_query(query, connection)
  finally:
    if connection:
      connection.close()
