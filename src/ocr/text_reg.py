from PIL import Image
import torch

from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg

import os
import time 

def get_predictor():
    config = Cfg.load_config_from_name('vgg_transformer')
    config['cnn']['pretrained'] = False
    config['device'] = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    return Predictor(config)

def predict_detections(detections):
    """
    Nhận danh sách các detections (crop + box) và chạy OCR.
    Returns: List of {"text": str, "box": list}
    """
    detector = get_predictor()
    results = []
    
    for det in detections:
        img = det["crop"]
        text = detector.predict(img)
        print(f"OCR: {text}")
        results.append({
            "text": text,
            "box": det["box"]
        })
        
    return results

def predict(crop_path):
    detector = get_predictor()
    ss = []

    # Đảm bảo sắp xếp file theo tên (hoặc theo tọa độ nếu có thể đọc từ metadata)
    files = sorted(os.listdir(crop_path))
    for p in files:
        path = os.path.join(crop_path, p)
        img = Image.open(path)
        s = detector.predict(img)
        print(s)
        ss.append(s)

    return ss


if __name__ == "__main__":
    start = time.time()
    predict("cropped_predictions")
    end = time.time()
    print(f"Time: {end - start}")
