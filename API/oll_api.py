from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# Ollama API settings
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"  # Ollama runs locally at this endpoint

def final_output(responses):
    prompt = ""
    for i, response in enumerate(responses):
        prompt += "Response "
        prompt += str(i)
        prompt += " "
        prompt += response
        prompt += "\n"
    prompt += "this is a collection of responses to a problem from multiple queries. Respond with the majority vote from the queries and a brief description of the problem, and nothing else. Keep the output to simply the result and description in one sentence, nothing else."
    print(prompt)
    return None

def multi_query(prompt):
    """Query the Ollama model multiple times"""
    responses = []
    prompt += ". The term i just gave you is a sequence of numbers. identify the number that does not belong, and respond with the number ONLY."
    for i in range(5):
        responses.append(query_ollama_llm(prompt))
    return responses

def query_ollama_llm(prompt):
    """Query local Ollama API for text generation with proper formatting and debugging."""
    payload = {
        "model": "gemma:2b-instruct-q2_K",  # Use the model you have installed
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,  # Adds variation
            "top_p": 0.95,  # Nucleus sampling
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
        responses = multi_query(user_query)
        final_output(responses)
        return jsonify({"query": user_query, "response": response})
    except Exception as e:
        return jsonify({"error": f"⚠️ Internal server error: {str(e)}"}), 500
    
if __name__ == '__main__':
    app.run(debug=True, port=8000)
