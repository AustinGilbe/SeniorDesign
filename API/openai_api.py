from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

import os
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize OpenAI with your API key

# Initialize Flask app and CORS
app = Flask(__name__)
CORS(app)

# Function to read example log data
def read_examples():
    """Read example log data for various attack types."""
    bd_path = "../DER Data/Logs/BD/bd_log_1.csv"
    clean_path = "../DER Data/Logs/CLEAN/clean_log_1.csv"
    dos_path = "../DER Data/Logs/DOS/dos_log_1.csv"
    gm_path = "../DER Data/Logs/GM/gm_log_1.csv"
    mitm_path = "../DER Data/Logs/MITM/mitm_log_1.csv"
    
    def read_first_lines(file_path, num_lines=5):
        with open(file_path, 'r') as file:
            return '\n'.join([file.readline().strip() for _ in range(num_lines)])

    bd_string = read_first_lines(bd_path)
    clean_string = read_first_lines(clean_path)
    dos_string = read_first_lines(dos_path)
    gm_string = read_first_lines(gm_path)
    mitm_string = read_first_lines(mitm_path)
    
    return bd_string, clean_string, dos_string, gm_string, mitm_string

# Function to combine model responses and perform majority voting
# Function to combine model responses and perform majority voting
def final_output(responses):
    """Combine model responses and perform majority voting."""
    prompt = (
        "We have queried a model multiple times to detect cyber attacks in log data. "
        "Perform majority voting on the responses, and produce a classification result.\n\n"
        "Instructions: Only provide the classification and a brief description of the attack, if any. "
        "Do NOT mention majority voting in your response.\n\n"
    )

    for i, response in enumerate(responses):
        prompt += f"Response {i+1}: {response}\n"

    prompt += (
        "\nExpected Output: "
        "Provide a concise classification and description. "
        "For example: 'This is a Denial of Service attack. The log shows multiple failed requests and timeout errors.'\n"
        "Now, process the responses and generate the final classification.\n"
    )
    # Call OpenAI API for the final result based on majority voting
    final_response = query_openai(prompt)
    return final_response

# Function to query OpenAI multiple times
def multi_query(prompt):
    """Query OpenAI model multiple times with the log data."""
    responses = []
    bd_string, clean_string, dos_string, gm_string, mitm_string = read_examples()

    # Build the in-context prompt (with examples)
    in_context_prompt = (
        "We are analyzing log data from a DER system to detect potential cyber attacks. "
        "The goal is to classify whether the system is under attack and, if so, identify the type of attack.\n"
        "Below are some example logs, both clean and under attack, along with their classifications.\n\n"
    )

    in_context_prompt += f"Example of Battery Drain Attack:\n{bd_string}\nClassification: Battery Drain Attack. The log shows abnormal battery usage.\n\n"
    in_context_prompt += f"Example of Denial of Service Attack:\n{dos_string}\nClassification: Denial of Service Attack. Multiple failed requests detected.\n\n"
    in_context_prompt += f"Example of Grid Manipulation Attack:\n{gm_string}\nClassification: Grid Manipulation Attack. Irregular grid parameters observed.\n\n"
    in_context_prompt += f"Example of Man-in-the-Middle Attack:\n{mitm_string}\nClassification: Man-in-the-Middle Attack. Intercepted and altered communication logs.\n\n"
    in_context_prompt += f"Example of Clean Log (no attack):\n{clean_string}\nClassification: Clean log. No signs of attacks detected.\n\n"

    in_context_prompt += "OUTPUT FORMAT: Respond with the classification and a brief description of the attack if detected, "
    in_context_prompt += "or state that the log is clean with no attack. The description should include specific reasoning.\n"
    in_context_prompt += f"Classify the following log data:\n{prompt}\n"

    # Run the query 5 times for multiple responses
    for i in range(5):
        responses.append(query_openai(in_context_prompt))
    return responses

# Function to query OpenAI's GPT-4 API for text generation
def query_openai(prompt):
    """Query OpenAI's GPT-4 API for text generation."""
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()  # Access the correct field in the response
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return f"⚠️ Error: {str(e)}"

# Flask route to handle incoming queries
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

