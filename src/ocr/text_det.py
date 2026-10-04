import cv2
import torch
from ultralytics import YOLO
import numpy as np
import os
from PIL import Image

DATA_PATH = "/home/truongkhanh/work/learn-by-me/cv/01-ocr-id-card/dataset/SROIE2019/data.yaml"

def train():
    model = YOLO('ckpt/detect_text/yolov8n.pt') 

        # 2. Bắt đầu huấn luyện
    results = model.train(
        data=DATA_PATH,    # Đường dẫn file yaml bạn vừa tạo
        epochs=100,          # Số vòng lặp huấn luyện
        imgsz=640,           # Kích thước ảnh đầu vào
        batch=8,            # Số lượng ảnh mỗi đợt (tùy vào VRAM của GPU)
        device=0,            # Chạy trên GPU (0) hoặc CPU ('cpu')
        name='my_yolo_model' # Tên thư mục lưu kết quả
    )

def predict():

    # img = cv2.imread("test-image/invoice.jpg")

    # Xoay 90 độ theo chiều kim đồng hồ
    # img_rotated = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)

    # Lưu hoặc đưa vào model
    # cv2.imwrite("output.jpg", img_rotated)

    model = YOLO('runs/detect/my_yolo_model2/weights/best.pt') 

    predictions = model("test-image/invoice.jpg")
    
    predictions[0].save("text.jpg")

def get_detections(image, model_path='ckpt/detect_text/best.pt', iou_nms_threshold=0.45):
    """
    Phát hiện text blocks, áp dụng NMS và trả về danh sách các crops cùng tọa độ.
    Returns: List of {"crop": Image, "box": [x1, y1, x2, y2]}
    """
    model = YOLO(model_path)
    results = model(image)
    result = results[0]
    
    raw_boxes = result.boxes.xyxy.cpu().numpy()
    scores = result.boxes.conf.cpu().numpy()
    
    # image = cv2.imread(image_path)
    if image is None:
        return []

    def xyxy_to_xywh(xyxy):
        x1, y1, x2, y2 = xyxy
        return [x1, y1, x2 - x1, y2 - y1]

    boxes_for_nms = [xyxy_to_xywh(box) for box in raw_boxes]
    keep_indices = cv2.dnn.NMSBoxes(boxes_for_nms, scores.tolist(), score_threshold=0.0, nms_threshold=iou_nms_threshold)
    
    detections = []
    if len(keep_indices) > 0:
        keep_indices = keep_indices.flatten()
        for idx in keep_indices:
            x1, y1, x2, y2 = raw_boxes[idx]
            x1, y1, x2, y2 = max(0, int(x1)), max(0, int(y1)), min(image.shape[1], int(x2)), min(image.shape[0], int(y2))
            
            if x2 <= x1 or y2 <= y1:
                continue
                
            crop_img = image[y1:y2, x1:x2]
            detections.append({
                "crop": Image.fromarray(cv2.cvtColor(crop_img, cv2.COLOR_BGR2RGB)),
                "box": [x1, y1, x2, y2],
                "score": float(scores[idx])
            })
    
    # Sắp xếp detections theo thứ tự đọc (y trước, x sau)
    # Điều này giúp parser dễ dàng xác định label đứng trước value
    detections.sort(key=lambda d: (d["box"][1], d["box"][0]))
    
    return detections

def split():
    image_path = "test-image/invoice.jpg"
    output_dir = 'cropped_predictions'
    os.makedirs(output_dir, exist_ok=True)
    
    detections = get_detections(image_path)
    for i, det in enumerate(detections):
        crop_name = f"crop_{i+1}_{det['score']:.2f}.jpg"
        crop_path = os.path.join(output_dir, crop_name)
        # Chuyển về BGR để cv2.imwrite
        cv2.imwrite(crop_path, cv2.cvtColor(np.array(det["crop"]), cv2.COLOR_RGB2BGR))
    
    print(f"Đã cắt và lưu {len(detections)} ảnh vào thư mục '{output_dir}'.")

if __name__ == "__main__":
    split()