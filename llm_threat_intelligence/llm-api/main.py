from flask import Flask, request, jsonify
from model import model, tokenizer
from prompt_engine import format_prompt

app = Flask(__name__)

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    log_entry = data.get("text", "")

    if not log_entry:
        return jsonify({"error": "No log entry provided"}), 400

    # Format the prompt with semantic priors
    prompt = format_prompt(log_entry)

    # Generate response from LLM
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    output = model.generate(**inputs, max_length=100)
    response = tokenizer.decode(output[0], skip_special_tokens=True)

    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
