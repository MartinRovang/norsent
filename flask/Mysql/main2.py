import sqlalchemy as sq
import pandas as pd 

engine = sq.create_engine('mysql+pymysql://root:password@localhost:3306/test')

df = pd.read_sql_table("student", engine)

query = "SELECT name FROM student"
df = pd.read_sql_query(query, engine)
print(df)