import streamlit as st
import cv2
import os
import requests
from ultralytics import YOLO
import torch.cuda

n8n_webhook_url = "http://94.131.101.111:5678/webhook/store-video"
output_path = "/app/output/output_video.mp4"
model = YOLO("best.pt") # Моделька. подойдет любая йолка


# Функция обработки видео. Принимает путь до файла, обрабтывает его и сохраняет
# в  переменную output_path то есть например здесь cv2.VideoWriter(output_path...) нужно вставить именно этот путь
# Позже этот файл отправится и удалится
def process_video(input_path):
    cap = cv2.VideoCapture(input_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height), isColor=True)
    if not out.isOpened():
        raise RuntimeError("Failed to create VideoWriter!")
    while cap.isOpened():
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
                    last_detect.append((x1, y1, x2, y2, label, conf))  # каждое повреждение заносится в массив

        for x1, y1, x2, y2, label, conf in last_detect:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0, 255),
                          2)  # рисуночек на кадре из последнего обрабатываемого кадра
            cv2.putText(frame, f"{label}{conf:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        out.write(frame)

    cap.release()
    out.release()

# Функция отправки файла
def send_to_n8n(file_path):
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'video/mp4')}
            auth = ("admin", "strongpassword")
            response = requests.post(
                n8n_webhook_url,
                files=files,
                auth=auth,
                timeout=10
            )
        return response.status_code
    except Exception as e:
        st.error(f"Upload failed: {str(e)}")
        return 500

# Функция очистки временных файлов
def cleanup_files(*paths):
    for path in paths:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception as e:
            st.warning(f"Couldn't delete {path}: {e}")


st.title("🎞️ Video Processor")

uploaded_file = st.file_uploader("Upload video", type=["mp4", "avi"])
if uploaded_file:
    input_path = os.path.join("/app/output", uploaded_file.name)
# Прием видео
    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.video(input_path)
    st.write("Processing...")
# Обработка видео
    process_video(input_path)
    st.write("The video is ready to be sent")
# Отправка видео в бд
    status = send_to_n8n(output_path)
    st.success("Video sent to n8n!" if status == 200 else f"Failed to send to n8n. Status: {status}")
# Очистка временных файлов
    cleanup_files(input_path, output_path)