import cv2
import threading
import torch.cuda
from ultralytics import YOLO
import glob
import os

device = 'cuda' if torch.cuda.is_available() else 'cpu'# для отладки
print(device)

nframes = 20 # обрабатываемый кадр
video_folder = "./videos"
videos = glob.glob(os.path.join(video_folder, "*.mp4"))
model = YOLO("best.pt") # Моделька. подойдет любая .pt

def process_video(video_path, window_name):
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    last_detect = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1

        if frame_count % nframes == 0:
            ''' на обрабатываемом кадре: 
            1. убираем старые поврежденния
            2. запоминаем новые'''
            results = model(frame)

            last_detect.clear()
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    label = result.names[int(box.cls[0])]
                    conf = float(box.conf[0])
                    last_detect.append((x1, y1, x2, y2, label, conf))# каждое повреждение заносится в массив

        for x1, y1, x2, y2, label, conf in last_detect:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0, 255), 2)# рисуночек на кадре из последнего обрабатываемого кадра
            cv2.putText(frame, f"{label}{conf:.2f}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.imshow(window_name, frame)# вывод потока (куда будет отправляться это еще под вопросом)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("process finished by user interrupt")
                cap.release()
                cv2.destroyWindow(window_name)

threads = []
for idx, video_path in enumerate(videos):
    window_name = f"Video {idx}: {os.path.basename(video_path)}"
    t = threading.Thread(target=process_video, args=(video_path, window_name))
    t.start()
    threads.append(t)

for t in threads:
    t.join()

cv2.destroyAllWindows()