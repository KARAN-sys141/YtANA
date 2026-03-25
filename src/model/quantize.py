import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import tensorflow as tf
import tf_keras
from src.model.architecture import build_multitask_model

MODEL_PATH = "saved_models/youtube_intelligence_v1.h5"
TFLITE_PATH = "saved_models/youtube_intelligence_quantized.tflite"
MAX_LEN = 64

def quantize_model():
    print(f"Loading heavy model from {MODEL_PATH}...")
    
    model = build_multitask_model(max_len=MAX_LEN)
    model.load_weights(MODEL_PATH)
    print("Model weights loaded successfully.")

    print("Starting TFLite conversion (this takes 1-2 mins)...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    
    converter.target_spec.supported_ops = [
        tf.lite.OpsSet.TFLITE_BUILTINS, 
        tf.lite.OpsSet.SELECT_TF_OPS    
    ]
    
    tflite_model = converter.convert()
    
    with open(TFLITE_PATH, "wb") as f:
        f.write(tflite_model)
        
    print(f"\nQuantized model saved to: {TFLITE_PATH}")
    
    original_size = os.path.getsize(MODEL_PATH) / (1024 * 1024)
    quantized_size = os.path.getsize(TFLITE_PATH) / (1024 * 1024)
    
    print(f"Original Size:  {original_size:.2f} MB")
    print(f"Quantized Size: {quantized_size:.2f} MB")
    print(f"Compression:    {original_size / quantized_size:.1f}x smaller! 🚀")

if __name__ == "__main__":
    quantize_model()