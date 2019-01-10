#!/usr/bin/python

import os
import sys
import re
import cv2
from sklearn.svm import SVC
#need to install extra module: $pip install opencv-contrib-python
import numpy as np
import logging
from optparse import OptionParser

DATA_DIR = "C:\Users\dzi\Pictures"
HAAR_DIR = "C:\Python27\Lib\site-packages\cv2\data\haarcascade_frontalface_default.xml"

def ERR_EXIT(err=""):
    if err: 
        logging.error(err)
    sys.exit(-1)

class faceDetecter():
    def __init__(self,owner,picDir):
        self.pic_repo = picDir
        self.owner = owner
        self.haar = cv2.CascadeClassifier(HAAR_DIR)
        
    def catchFacesFromCamera(self,camera,mode="collect"):
        count = 0
        for n in range(30):
            success, image = camera.read()
            gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = self.haar.detectMultiScale(gray_img, scaleFactor = 1.15, minNeighbors = 5, minSize = (5,5))
            if not len(faces):
                print "No face detected!"
            if mode == "detect":
                return image, gray_img, faces
            for x, y, w, h in faces:
                count = count + 1
                cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.imwrite(os.path.join(self.pic_repo,"train_image_{0}_{1}.jpg".format(self.owner,count)), cv2.resize(gray_img[y:y + h, x:x + w],(200,200)))
            cv2.imshow('image', image)
            cv2.waitKey(0)
        #cv2.destroyAllWindows()

    def catchFacesFromPicture(self,pic):
        pic_path = pic
        if not ("/" in pic or "\\" in pic):
            pic_path = os.path.join(self.pic_repo,pic)
        image = cv2.imread(pic_path)
        gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.haar.detectMultiScale(gray_img, scaleFactor = 1.15, minNeighbors = 5, minSize = (5,5))
        if not len(faces):
            print "No face detected!"
        return image,gray_img,faces

    def getTrainData(self):
        self.train_X = []
        self.train_Y = []
        self.labelDict = {}
        label_n = 0
        for root, dirs, files in os.walk(self.pic_repo):
            for filename in files:
                try:
                    owner = re.findall(r"train_image_(.*?)_[1-9]\d*\.jpg",filename)[0]
                except:
                    continue
                if not self.labelDict.has_key(owner):
                    label_n = label_n + 1
                    self.labelDict[owner] = label_n 
                file_path = os.path.join(root, filename)
                face_img = cv2.imread(file_path,cv2.IMREAD_GRAYSCALE)
                face_img = cv2.resize(face_img,(200,200))
                self.train_X.append(face_img)
                self.train_Y.append(label_n)
        self.train_X, self.train_Y = np.asarray(self.train_X), np.asarray(self.train_Y)

    def train(self):
        
        #self.model = cv2.face.LBPHFaceRecognizer_create()
        #self.model.train(np.asarray(self.train_X),np.asarray(self.train_Y))
        self.model = SVC(C=1.0, kernel="linear", probability=True)
        self.model.fit(self.train_X.reshape(self.train_X.shape[0],-1), self.train_Y)

    def detect(self,source="",camera="",pic="",video=False):
        if source == "camera":
            image, gray_img, faces = self.catchFacesFromCamera(camera,"detect")
        elif source == "picture":
            image, gray_img, faces = self.catchFacesFromPicture(pic)
        pred_dict = dict([(v,k) for k,v in self.labelDict.items()])
        for x, y, w, h in faces:
            target = cv2.resize(gray_img[y:y + h, x:x + w],(200,200)).reshape(1,-1)
            pred = self.model.predict(target)
            pred_proba = self.model.predict_proba(target)[0][pred[0]-1]
            pred_name = pred_dict[pred[0]]
            show_text = pred_name + " %.2f%%" % (100*float(pred_proba))
            print pred,pred_proba
            cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(image,show_text,(x,y-20),cv2.FONT_HERSHEY_SIMPLEX,1,255,2)
        cv2.imshow('image', image)
        if video:
            if not cv2.waitKey(10) == -1:
                return False
        else:
            cv2.waitKey(0)
        return True

if __name__ == '__main__':
    parser = OptionParser() 
    parser.add_option("-c", "--collect", action="store_true", 
                  dest="collect", 
                  default=False, 
                  help="collect face data") 
    parser.add_option("-n", "--name", 
                  dest="name",
                  default="", 
                  help="face owner")
    parser.add_option("-d", "--detect", action="store_true", 
                  dest="detect", 
                  default=False, 
                  help="detect face")
    parser.add_option("-p", "--pic",
                  dest="pic",
                  default="",
                  help="picture input") 
    parser.add_option("-v", "--video", action="store_true",
                  dest="video",
                  default=False,
                  help="detect in video stream") 
    (options, args) = parser.parse_args() 
    if not (options.collect ^ options.detect):
        ERR_EXIT("require either --collect/-c or --detect/-d specified !")
    if options.collect:
        if not options.name:
            ERR_EXIT("require --name/-n specified!")
        detecter = faceDetecter(options.name, DATA_DIR)
        cmr = cv2.VideoCapture(0)
        detecter.catchFacesFromCamera(cmr)
        cmr.release()
    if options.detect:
        detecter = faceDetecter("", DATA_DIR)
        detecter.getTrainData()
        detecter.train()
        if options.pic:
            detecter.detect("picture",pic=options.pic)
        else:
            cmr = cv2.VideoCapture(0)
            if options.video:
                while 1:
                    if not detecter.detect("camera",camera=cmr,video=True):
                        break
            else:
                detecter.detect("camera",camera=cmr)
            cmr.release()
