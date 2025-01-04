import cv2
import face_recognition
import pickle
import os

def findEncodings(imgList):
    encodeList = []
    for img in imgList:
        # Change color space to RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList

if __name__ == "__main__":
    folderPath = "images"
    pathList = os.listdir(folderPath)
    imgList = []
    studentIds = []
    for path in pathList:
        imgList.append(cv2.imread(os.path.join(folderPath, path)))
        studentIds.append(os.path.splitext(path)[0])  # Import student IDs from image names

    print("Encoding Started...")
    encodeListKnow = findEncodings(imgList)
    encodeListKnowWithIds = [encodeListKnow, studentIds]
    print("Encoding Complete")

    with open("EncodeFile.p", 'wb') as file:
        pickle.dump(encodeListKnowWithIds, file)

    print("File Saved")
