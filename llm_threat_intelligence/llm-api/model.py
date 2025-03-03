from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

MODEL_NAME = "meta-llama/Llama-3.3-70B-Instruct"

def load_model():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, torch_dtype=torch.float16, device_map="auto")
    return model, tokenizer

model, tokenizer = load_model()
