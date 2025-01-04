import os
import pickle
import numpy as np
import cv2
import face_recognition
import cvzone
import mysql.connector
from datetime import datetime

# Connect to MySQL
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="face_attendance_db"
)
mycursor = mydb.cursor(dictionary=True)

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

imgBackground = cv2.imread('res/background.png')

# Importing the mode images into a list
folderModePath = 'res/Modes'
modePathList = os.listdir(folderModePath)
imgModeList = [cv2.imread(os.path.join(folderModePath, path)) for path in modePathList]

print("Loading Encode File ...")
with open('EncodeFile.p', 'rb') as file:
    encodeListKnownWithIds = pickle.load(file)
encodeListKnown, studentIds = encodeListKnownWithIds
print("Encode File Loaded")

modeType = 0  # 0=default, 1=Show info, 2=marked (confirmation) , 3=already marked
counter = 0
studentInfo = None
imgStudent = None

while True:
    success, img = cap.read()
    if not success:
        print("Could not read from webcam. Exiting...")
        break

    # Downscale and convert for face_recognition
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

    # Put the live webcam feed onto the background
    imgBackground[162:162 + 480, 55:55 + 640] = img

    # If no face is detected, we go to default
    if not faceCurFrame:
        modeType = 0
        counter = 0
        studentInfo = None
        imgStudent = None
        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[0]
        cv2.imshow("Face Attendance", imgBackground)
        cv2.waitKey(1)
        continue

    # Faces found then we check each face
    for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
        matchIndex = np.argmin(faceDis)

        if matches[matchIndex]:
            student_id = studentIds[matchIndex]

            # Scale bounding box back up to original size becuase we downscaled it up in the code (0.25)
            y1, x2, y2, x1 = faceLoc
            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
            bbox = (55 + x1, 162 + y1, x2 - x1, y2 - y1)
            imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)

            # We only fetch from DB once per detection cycle
            if counter == 0:
                mycursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
                studentInfo = mycursor.fetchone()

                if studentInfo is not None:
                    # Convert BLOB image or use just default image
                    blobData = studentInfo['photo']
                    if blobData:
                        array = np.frombuffer(blobData, np.uint8)
                        imgStudent = cv2.imdecode(array, cv2.IMREAD_COLOR)
                    else:
                        imgStudent = cv2.imread('res/1.png')

                    # Resize the student's photo cz we allow the images folder to accept any size image
                    imgStudent = cv2.resize(imgStudent, (216, 216))
                    imgBackground[175:175 + 216, 909:909 + 216] = imgStudent

                    # Check last attendance time
                    last_attendance_time = studentInfo['last_attendance_time']
                    if last_attendance_time is None:
                        last_attendance_time = datetime.min

                    # Make sure we handle string -> datetime if needed
                    if isinstance(last_attendance_time, str):
                        last_attendance_time = datetime.strptime(last_attendance_time, "%Y-%m-%d %H:%M:%S")

                    secondsElapsed = (datetime.now() - last_attendance_time).total_seconds()

                    # If more than 24 hours => new attendance
                    if secondsElapsed > 86400:
                        # Update attendance right away
                        new_total = studentInfo['total_attendance'] + 1
                        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        update_sql = """
                            UPDATE students
                            SET total_attendance = %s, last_attendance_time = %s
                            WHERE id = %s
                        """
                        mycursor.execute(update_sql, (new_total, now_str, studentInfo['id']))
                        mydb.commit()

                        # Refresh studentInfo['total_attendance'] in memory
                        studentInfo['total_attendance'] = new_total
                        studentInfo['last_attendance_time'] = now_str

                        # modeType=1 => Show student info
                        modeType = 1
                    else:
                        # Within 24 hours => Show "already marked"
                        modeType = 3

                    counter = 1
                else:
                    print("Student not found in DB.")
                    modeType = 0
                    counter = 0

    # If we have a mode to display
    if studentInfo is not None and counter > 0:
        if modeType == 1:
            # Show STUDENT INFO (imgModeList[1])

            imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[1]

            # Display all the text info for about ~10 frames
            if counter <= 10:
                # Overlay the student image
                if imgStudent is not None:
                    imgBackground[175:175 + 216, 909:909 + 216] = imgStudent
                # Then display all their information
                cv2.putText(imgBackground, str(studentInfo['total_attendance']), (861, 125),
                            cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                cv2.putText(imgBackground, str(studentInfo['major']), (1006, 550),
                            cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(imgBackground, str(studentInfo['id']), (1006, 493),
                            cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(imgBackground, str(studentInfo['standing']), (910, 625),
                            cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                cv2.putText(imgBackground, str(studentInfo['year']), (1025, 625),
                            cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                cv2.putText(imgBackground, str(studentInfo['starting_year']), (1125, 625),
                            cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)

                (w, h), _ = cv2.getTextSize(studentInfo['name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                offset = (414 - w) // 2
                cv2.putText(imgBackground, str(studentInfo['name']), (808 + offset, 445),
                            cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)


            # After 10 frames, switch to modeType=2 => "Marked" screen
            elif 10 < counter <= 20:

                # Show "MARKED SUCCESSFULLY" (imgModeList[2])
                modeType = 2
                imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[2]

            # If counter > 20 => reset
            elif counter > 20:
                modeType = 0
                counter = 0
                studentInfo = None
                imgStudent = None
                imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[0]

            counter += 1

        elif modeType == 2:
            # If we've manually switched to modeType=2 above
            # We Show "marked" for a few frames
            imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[2]
            counter += 1

            # After a short while, revert to default
            if counter > 20:
                modeType = 0
                counter = 0
                studentInfo = None
                imgStudent = None
                imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[0]

        elif modeType == 3:
            
            # Show "ALREADY MARKED" (imgModeList[3])
            imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[3]
            counter += 1

            # Show for ~20 frames
            if counter > 20:
                modeType = 0
                counter = 0
                studentInfo = None
                imgStudent = None
                imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[0]

    else:
        # If there's no valid student or we've reset
        modeType = 0
        counter = 0
        studentInfo = None
        imgStudent = None
        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[0]

    cv2.imshow("Face Attendance", imgBackground)
    cv2.waitKey(1)
