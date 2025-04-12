from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# Ollama API settings
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"  # Ollama runs locally at this endpoint

def query_ollama_llm(prompt):
    """Query local Ollama API for text generation with proper formatting and debugging."""
    payload = {
        "model": "tinyllama",  # Use the model you have installed
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,  # Adds variation
            "top_p": 0.95,  # Nucleus sampling
            "max_tokens": 500  # Maximum length of response
        }
    }
    
    print(f"🔹 Sending request to: {OLLAMA_API_URL}")
    print(f"🔹 Using model: tinyllama")
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        print(f"🔹 Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            response_json = response.json()
            print(f"🔹 Response received successfully")
            return response_json.get("response", "No response generated.")
        else:
            print(f"🔹 Response Error: {response.text}")
            return f"⚠️ Error: API returned status code {response.status_code}: {response.text}"
    except requests.exceptions.ConnectionError:
        return "⚠️ Error: Cannot connect to Ollama. Make sure the Ollama server is running."
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

@app.route('/ask_llm', methods=['POST'])
def ask_llm():
    """Query the Ollama LLM API and return a response."""
    data = request.json
    user_query = data.get("query", "")
    if not user_query:
        return jsonify({"error": "⚠️ Query is required."}), 400
    
    print(f"Received prompt: {user_query}")
    try:
        # Generate response using the local Ollama API
        response = query_ollama_llm(user_query)
        return jsonify({"query": user_query, "response": response})
    except Exception as e:
        return jsonify({"error": f"⚠️ Internal server error: {str(e)}"}), 500
    
if __name__ == '__main__':
    app.run(debug=True, port=8000)
