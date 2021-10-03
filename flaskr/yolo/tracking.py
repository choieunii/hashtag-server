import time
import cv2
import numpy as np

#from dbr import *
from .tracker import *

CONFIDENCE_THRESHOLD = 0.2
NMS_THRESHOLD = 0.4
COLORS = [(0, 255, 255), (255, 255, 0), (0, 255, 0), (255, 0, 0)]
tracker = EuclideanDistTracker()

# input : video? image?


def main(img):
    images = []
    count = 0

    net = cv2.dnn.readNet("yolov4-obj_last.weights", "yolov4-obj.cfg")
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    # net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA_FP16)
    # make darknet model
    model = cv2.dnn_DetectionModel(net)
    model.setInputParams(size=(416, 416), scale=1/255, swapRB=True)

    images = []

    print("START")

    data = np.fromfile(img, np.uint8)
    frame = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)  # 사진 읽어옴

    # 1. detect object and return output
    classes, scores, boxes = model.detect(
        frame, CONFIDENCE_THRESHOLD, NMS_THRESHOLD)

    # 2. Object Tracking
    # boxes_cids = [x, y, w, h, (class, id)]
    boxes_cids = tracker.update(classes, boxes, frame)
    barcode_data = []
    for box_cid in boxes_cids:
        x, y, w, h, class_id, decode_info = box_cid
        if class_id[0] == 0:
            id_name = "BARCODE " + decode_info
            barcode_data.append(decode_info)
        else:
            id_name = "PRODUCT"
        text = f"ID ={str(class_id[1])} {id_name}"
        text = f"ID ={str(class_id[1])} {id_name}"
        cv2.putText(frame, text, (x, y - 15),
                    cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 1)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1)

    print(barcode_data)
    return barcode_data

    cv2.imshow("detections", frame)
    images.append(frame)
    key = cv2.waitKey()

    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
