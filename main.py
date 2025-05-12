import streamlit as st
import cv2
import os
import requests

n8n_webhook_url = "http://localhost:5678/webhook/store-video"


def process_video(input_path):
    output_path = "/app/output/output_video.mp4"
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

        square_size = min(width, height) // 4
        center_x, center_y = width // 2, height // 2
        start_point = (center_x - square_size // 2, center_y - square_size // 2)
        end_point = (center_x + square_size // 2, center_y + square_size // 2)
        cv2.rectangle(frame, start_point, end_point, (0, 0, 255), 3)

        out.write(frame)

    cap.release()
    out.release()
    return output_path


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
    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.video(input_path)
    st.write("Processing...")

    processed_path = process_video(input_path)
    st.write("The video is ready to be sent")
    status = send_to_n8n(processed_path)
    st.success("Video sent to n8n!" if status == 200 else f"Failed to send to n8n. Status: {status}")
    cleanup_files(input_path, processed_path)