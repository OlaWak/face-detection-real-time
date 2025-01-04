import os
import mysql.connector

# Connect to MySQL
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="face_attendance_db"
)
mycursor = mydb.cursor()

# Path to the local images from the folder
folderPath = "images"
pathList = os.listdir(folderPath)

for filename in pathList:
    if filename.lower().endswith((".png", ".jpg", ".jpeg")):
        student_id = os.path.splitext(filename)[0]
        file_path = os.path.join(folderPath, filename)

        # Read image in binary mode
        with open(file_path, 'rb') as f:
            blob_data = f.read()

        # Insert/Update the student photo in the 'students' table
        # (We assume the student record already exists; if not, we'll have to handle insert logic)
        sql = """
        UPDATE students
        SET photo = %s
        WHERE id = %s
        """
        val = (blob_data, student_id)
        mycursor.execute(sql, val)
        mydb.commit()

        print(f"Uploaded image for student_id={student_id}")

mycursor.close()
mydb.close()
