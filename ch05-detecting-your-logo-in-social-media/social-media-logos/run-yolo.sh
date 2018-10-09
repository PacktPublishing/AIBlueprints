#!/bin/sh

cd ~/yolo-darknet
exec ./darknet detector test ~/smartcode/ch05-detecting-your-logo-in-social-media/flickrlogo47.data ~/smartcode/ch05-detecting-your-logo-in-social-media/yolov3_logo_detection.cfg backup/yolov3_logo_detection_final.weights

