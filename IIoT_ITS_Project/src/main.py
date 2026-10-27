import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import cv2
import numpy as np
from modules.traffic_analyzer import TrafficAnalyzer
from modules.mqtt_client import IIoTPublisher

def main():
    video_path = "../data/raw_videos/traffic_sample.mp4" 
    cap = cv2.VideoCapture(video_path)

    cv2.namedWindow("IIoT ITS - Edge Gateway Node", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("IIoT ITS - Edge Gateway Node", 960, 540)

    roi_polygon = np.array([[100, 300], [1100, 300], [1200, 700], [50, 700]], np.int32)

    analyzer = TrafficAnalyzer(model_path='yolov8n.pt', roi_polygon=roi_polygon)
    iiot_pub = IIoTPublisher(broker="broker.emqx.io", topic="iiot/traffic/junction_01")

    frame_count = 0
    PUBLISH_INTERVAL = 15

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        processed_frame, analytics_data = analyzer.process_frame(frame)

        if frame_count % PUBLISH_INTERVAL == 0:
            iiot_pub.publish_telemetry(analytics_data)

        cv2.imshow("IIoT ITS - Edge Gateway Node", processed_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    iiot_pub.disconnect()

if __name__ == "__main__":
    main()