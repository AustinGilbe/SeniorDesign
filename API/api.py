from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Hugging Face API credentials (store securely as an environment variable)
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN") # Load from environment

if not HUGGINGFACE_API_TOKEN:
    raise ValueError("⚠️ Hugging Face API token is missing! Set HUGGINGFACE_API_TOKEN as an environment variable.")

def query_huggingface_llm(prompt):
    """Query Hugging Face API for text generation with proper formatting and debugging."""
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": prompt,  # Correct format for API request
        "parameters": {
            "max_length": 200,
            "temperature": 0.7,  # Adds variation
            "top_p": 0.95,  # Nucleus sampling
            "do_sample": True  # Enables sampling instead of greedy decoding
        }
    }

    print(f"🔹 Sending request to: {HUGGINGFACE_API_URL}")
    print(f"🔹 Using token: {HUGGINGFACE_API_TOKEN[:10]}*****")  # Mask token for security

    response = requests.post(HUGGINGFACE_API_URL, headers=headers, json=payload)

    print(f"🔹 Response Status Code: {response.status_code}")
    print(f"🔹 Response Text: {response.text}")

    # Handle API response
    if response.status_code == 200:
        return response.json()[0].get("generated_text", "No response generated.")
    elif response.status_code == 503:
        return "⚠️ Error: Hugging Face API is overloaded or down. Try again later."
    elif response.status_code == 401:
        return "⚠️ Error: Invalid Hugging Face API token."
    else:
        return f"⚠️ Error: {response.text}"

@app.route('/ask_llm', methods=['POST'])
def ask_llm():
    """Query the Hugging Face LLM API and return a response."""
    data = request.json
    user_query = data.get("query", "")

    if not user_query:
        return jsonify({"error": "⚠️ Query is required."}), 400

    try:
        # Generate response using the API instead of a local model
        response = query_huggingface_llm(user_query)
        return jsonify({"query": user_query, "response": response})

    except Exception as e:
        return jsonify({"error": f"⚠️ Internal server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)

