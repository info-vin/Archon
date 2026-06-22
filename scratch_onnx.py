import os
from huggingface_hub import hf_hub_download
import onnxruntime as ort
from transformers import AutoTokenizer
import numpy as np
import math

def sigmoid(x):
    return 1 / (1 + math.exp(-x))

def test_onnx():
    repo_id = "Xenova/ms-marco-MiniLM-L-6-v2"
    print("Downloading ONNX model from:", repo_id)
    
    # Download the ONNX model
    onnx_file = hf_hub_download(repo_id=repo_id, filename="onnx/model_quantized.onnx")
    print("Downloaded ONNX to:", onnx_file)
    
    # Load session
    session = ort.InferenceSession(onnx_file, providers=['CPUExecutionProvider'])
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(repo_id)
    
    # Tokenize input pairs
    pairs = [("What is the capital of France?", "Paris is the capital of France."), 
             ("What is the capital of France?", "The quick brown fox jumps over the lazy dog.")]
    
    inputs = tokenizer(pairs, padding=True, truncation=True, return_tensors="np")
    
    # Prepare inputs for ONNX
    onnx_inputs = {k: v.astype(np.int64) for k, v in inputs.items()}
    
    # Run inference
    outputs = session.run(None, onnx_inputs)
    logits = outputs[0]
    
    scores = [sigmoid(x[0]) for x in logits]
    print("Scores:", scores)

if __name__ == "__main__":
    test_onnx()
