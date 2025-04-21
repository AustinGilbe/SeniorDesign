from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# Ollama API settings
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"  # Ollama runs locally at this endpoint

def read_examples():
    bd_path = "../DER Data/Logs/BD/bd_log_1.csv"
    clean_path = "../DER Data/Logs/CLEAN/clean_log_1.csv"
    dos_path = "../DER Data/Logs/DOS/dos_log_1.csv"
    gm_path = "../DER Data/Logs/GM/gm_log_1.csv"
    mitm_path = "../DER Data/Logs/MITM/mitm_log_1.csv"
    with open(bd_path, 'r') as file:
        bd_string = file.read()
    with open(clean_path, 'r') as file:
        clean_string = file.read()
    with open(dos_path, 'r') as file:
        dos_string = file.read()
    with open(gm_path, 'r') as file:
        gm_string = file.read()
    with open(mitm_path, 'r') as file:
        mitm_string = file.read()
    return bd_string, clean_string, dos_string, gm_string, mitm_string

def final_output(responses):
    prompt = "We have queried a model multiple times to detect cyber attacks in log data. Perform majority voting on the responses, and produce an output giving the classification and a description."
    for i, response in enumerate(responses):
        prompt += "Response "
        prompt += str(i)
        prompt += " "
        prompt += response
        prompt += "\n"
    prompt += "\n. This is all of the responses. OUTPUT FORMAT: Only respond with the classification and a brief description. DO NOT include any mention of majority voting, just the classification. EXAMPLE OUTPUT: This is a Man in the Middle Attack. There are many altered values in the log data that denote this.\n"
    prompt += "now perform majority voting and produce classification results.\n"
    final_response = query_ollama_llm(prompt)
    return final_response

def multi_query(prompt):
    """Query the Ollama model multiple times"""
    responses = []
    bd_string, clean_string, dos_string, gm_string, mitm_string = read_examples()
    in_context_prompt = "We are about to pass you log data from a DER system. We aim to determine in the system is under attack. Below are some examples of log data, both clean and under attack. Use the examples and example output to classify and describe the given log.\n"
    in_context_prompt += "Example of Battery Drain Attack File:\n"
    in_context_prompt += bd_string
    in_context_prompt += "\n. Example Output for Battery Drain: This is a battery drain attack, as denoted by the increase in Tesla Charger of Home Load Usage in the log data.\n"
    in_context_prompt += "Example of Denial of Service Attack File:\n"
    in_context_prompt += dos_string
    in_context_prompt += "\n. Example Output for DoS: This is a denial of service attack. There is missing data in the log file, indicating data has been lost due to denial of service.\n"
    in_context_prompt += "Example of Grid Manipulation Attack File:\n"
    in_context_prompt += gm_string
    in_context_prompt += "\n. Example Output for Grid Manipulation: This is a grid manipulation attack. The log data has inconsistent import and export values, demonstrating incorrect power readings.\n"
    in_context_prompt += "Example of Man in the Middle Attack File:\n"
    in_context_prompt += mitm_string
    in_context_prompt += "\n. Example Output for Man in the Middle: This is a man in the middle attack. The log data has many altered log values, like solar generation, battery charge levels, or grid import/export values.\n"
    in_context_prompt += "Example of Clean File with no attack:\n"
    in_context_prompt += clean_string
    in_context_prompt += "\n. Example Output for Clean: This is a clean log file that exhibits no attacks!\n"
    in_context_prompt += "OUTPUT FORMAT: Only respond with whether or not the file shows some type of attack, and a brief description of the type and reasoning.\n"
    in_context_prompt += "Classify this file:\n"
    in_context_prompt += prompt
    for i in range(5):
        responses.append(query_ollama_llm(in_context_prompt))
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
    print(f"🔹 Using model: gemma:2b-instruct-q2_K")
    
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
        response = final_output(responses)
        return jsonify({"query": user_query, "response": response})
    except Exception as e:
        return jsonify({"error": f"⚠️ Internal server error: {str(e)}"}), 500
    
if __name__ == '__main__':
    app.run(debug=True, port=8000)
