import mysql.connector
from datetime import datetime

# Connect to MySQL
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",              # no password
    database="face_attendance_db"  # the name of the DB we have
)

mycursor = mydb.cursor()

#Inserting our students data
data = {
    "112": {
        "name": "Mufti Menk",
        "major": "Islamic Studies",
        "starting_year": 2021,
        "total_attendance": 7,
        "standing": "A",
        "year": 3,
        "last_attendance_time": "2025-01-04 00:54:34"
    },
    "123": {
        "name": "Mohammad Ali",
        "major": "Boxing",
        "starting_year": 2021,
        "total_attendance": 12,
        "standing": "A",
        "year": 1,
        "last_attendance_time": "2024-12-11 00:54:34"
    },
    "456": {
        "name": "Elon Musk",
        "major": "Physics",
        "starting_year": 2020,
        "total_attendance": 7,
        "standing": "B",
        "year": 2,
        "last_attendance_time": "2024-12-09 00:54:34"
    }
}

# Here we Upsert each student into the 'students' table
for student_id, value in data.items():
    name = value["name"]
    major = value["major"]
    standing = value["standing"]
    year = value["year"]
    starting_year = value["starting_year"]
    total_attendance = value["total_attendance"]
    last_attendance_time = value["last_attendance_time"]

    # Convert last_attendance_time to a proper datetime object
    last_attendance_time_dt = datetime.strptime(last_attendance_time, "%Y-%m-%d %H:%M:%S")

    # Query to either insert or update the existing record
    # We'll have a simple approach to it: try to insert; if there's a duplicate, then update
    sql = """
    INSERT INTO students (id, name, major, standing, year, starting_year, total_attendance, last_attendance_time)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        name = VALUES(name),
        major = VALUES(major),
        standing = VALUES(standing),
        year = VALUES(year),
        starting_year = VALUES(starting_year),
        total_attendance = VALUES(total_attendance),
        last_attendance_time = VALUES(last_attendance_time)
    """

    val = (
        student_id,
        name,
        major,
        standing,
        year,
        starting_year,
        total_attendance,
        last_attendance_time_dt
    )

    mycursor.execute(sql, val)
    mydb.commit()

mycursor.close()
mydb.close()

print("Data inserted/updated successfully!") # To let us know everything went smoothlyy
