#%%
import mysql.connector as con


mydb = con.connect(
    host = 'localhost',
    user = 'root',
    password = 'password',
    database = 'test',
)

my_cursor = mydb.cursor()
#my_cursor.execute("CREATE DATABASE testdb")

# my_cursor.execute("SHOW DATABASES")
# for db in my_cursor:
#     print(db[0])

# sqlstuff = "INSERT INTO student (student_id, name, major, gpa) VALUES (%s, %s, %s, %s)"

# record1 = (12, "Martin", "fysikk", 6.02)

# my_cursor.execute(sqlstuff, record1)
# mydb.commit()

# sqlstuff = "INSERT INTO student (student_id, name, major, gpa) VALUES (%s, %s, %s, %s)"
# records = [(199, "Martins", "lar23e", 0.02), (121, "Martinsen", "larve", 1.02), (100, "MLarven", "tester", 5.02),]

# my_cursor.executemany(sqlstuff, records)
# mydb.commit()

# my_cursor.execute("CREATE TABLE users (name VARCHAR(255), email VARCHAR(255), age INTEGER(10), user_id INTEGER AUTO_INCREMENT PRIMARY KEY)")
# my_cursor.execute("SHOW TABLES")
# for i in my_cursor:
#     print(i)


# sqlstuff = "INSERT INTO users (name, email, age) VALUES (%s %s %s)"
# records = [("Tim, larve@test.com", 90), ("Hest, le@test.com", 40), ("Larvemannen, terster@test.com", 90),]

# my_cursor.executemany(sqlstuff, records)
# mydb.commit()

import pandas as pd
my_cursor.execute("SELECT * FROM student")
result = my_cursor.fetchall()

data = pd.DataFrame(result)

print(data)

