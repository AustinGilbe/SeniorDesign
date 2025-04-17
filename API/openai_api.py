from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

# Initialize Flask app and CORS
app = Flask(__name__)
CORS(app)

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")  # You should set your OpenAI API key in environment variables

def read_examples():
    """Read example log data for various attack types."""
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
    """Combine model responses and perform majority voting."""
    prompt = "We have queried a model multiple times to detect cyber attacks in log data. Perform majority voting on the responses, and produce an output giving the classification and a description.\n"
    
    for i, response in enumerate(responses):
        prompt += f"Response {i+1}: {response}\n"
    
    prompt += (
        "\nThis is all of the responses.\n"
        "OUTPUT FORMAT: Only respond with the classification and a brief description. "
        "DO NOT include any mention of majority voting, just the classification.\n"
        "EXAMPLE OUTPUT: This is a Man in the Middle Attack. There are many altered values in the log data that denote this.\n"
        "Now perform majority voting and produce classification results.\n"
    )
    # Call OpenAI API for the final result based on majority voting
    final_response = query_openai(prompt)
    return final_response

def multi_query(prompt):
    """Query OpenAI model multiple times with the log data."""
    responses = []
    bd_string, clean_string, dos_string, gm_string, mitm_string = read_examples()
    
    # Build the in-context prompt (with examples)
    in_context_prompt = (
        "We are about to pass you log data from a DER system. We aim to determine if the system is under attack. "
        "Below are some examples of log data, both clean and under attack. Use the examples and example output to classify "
        "and describe the given log.\n"
    )
    
    in_context_prompt += f"Example of Battery Drain Attack File:\n{bd_string}\nExample Output: This is a battery drain attack... \n\n"
    in_context_prompt += f"Example of Denial of Service Attack File:\n{dos_string}\nExample Output: This is a denial of service attack... \n\n"
    in_context_prompt += f"Example of Grid Manipulation Attack File:\n{gm_string}\nExample Output: This is a grid manipulation attack... \n\n"
    in_context_prompt += f"Example of Man in the Middle Attack File:\n{mitm_string}\nExample Output: This is a man in the middle attack... \n\n"
    in_context_prompt += f"Example of Clean File with no attack:\n{clean_string}\nExample Output: This is a clean log file... \n\n"
    
    in_context_prompt += "OUTPUT FORMAT: Only respond with whether or not the file shows some type of attack, "
    in_context_prompt += "and a brief description of the type and reasoning.\n"
    in_context_prompt += f"Classify this file:\n{prompt}\n"
    
    # Run the query 5 times for multiple responses
    for i in range(5):
        responses.append(query_openai(in_context_prompt))
    return responses

def query_openai(prompt):
    """Query OpenAI's GPT-4 API for text generation."""
    try:
        response = openai.Completion.create(
            model="gpt-4",
            prompt=prompt,
            max_tokens=300,
            temperature=0.7,
            n=1,
            stop=None
        )
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return f"⚠️ Error: {str(e)}"

@app.route('/ask_llm', methods=['POST'])
def ask_llm():
    """API endpoint to handle incoming queries."""
    data = request.json
    user_query = data.get("query", "")
    
    if not user_query:
        return jsonify({"error": "⚠️ Query is required."}), 400
    
    print(f"Received prompt: {user_query}")
    try:
        # Query the model 5 times with different responses
        responses = multi_query(user_query)
        response = final_output(responses)
        return jsonify({"query": user_query, "response": response})
    except Exception as e:
        return jsonify({"error": f"⚠️ Internal server error: {str(e)}"}), 500
    
if __name__ == '__main__':
    app.run(debug=True, port=8000)

