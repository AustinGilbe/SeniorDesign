from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from collections import Counter
import os
import concurrent.futures
import random

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app)

def read_examples():
    paths = {
        "Battery Drain": ["../Data2/Logs/bd/bd_simulation_log_1.csv"],
        "Denial of Service": ["../Data2/Logs/dos/dos_simulation_log_1.csv"],
        "Grid Manipulation": ["../Data2/Logs/gm/gm_simulation_log_1.csv"],
        "Man-in-the-Middle": ["../Data2/Logs/mitm/mitm_simulation_log_1.csv"],
        "Clean": ["../Data2/Logs/clean/clean_simulation_log_1.csv"],
        "Clean1": ["../Data2/Logs/clean/clean_simulation_log_2.csv"]
    }

    examples = {}
    def read_first_lines(file_path, num_lines=5):
        with open(file_path, 'r') as f:
            return '\n'.join([f.readline().strip() for _ in range(num_lines)])

    for label, file_list in paths.items():
        examples[label] = [read_first_lines(fp) for fp in file_list]
    return examples

def final_output(responses):
    final_output_prompt = "We have performed multi-querying to analyze log data and determine whether or not there is a security threat.\n"
    final_output_prompt += "You will perform majority voting based on the following responses and correctly classify the instance based on the CLASSIFICATION, DESCRIPTION, and CONFIDENCE from the responses.\n"
    final_output_prompt += "DO NOT mention that we are performing majority voting. Simply respond with the final classification, description, and confidence based on the responses provided.\n"
    final_output_prompt += "OUTPUT INSTRUCTIONS: Respond with the classification, description, and confidence score formatted like this:\n"
    final_output_prompt += "CLASSIFICATION:\nDESCRIPTION:\nCONFIDENCE:\n"
    final_output_prompt += "Now, classify the following file based on the responses below:\n"
    for i, response in enumerate(responses):
        final_output_prompt += "Response {i}:\n"
        final_output_prompt += response
        final_output_prompt += "\n\n"
    return query_openai(final_output_prompt)
        

def query_openai(prompt, max_tokens=100, temperature=0.2):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

def multi_query(prompt):
    responses = []
    examples = read_examples()

    # Prepare all example snippets
    example_snippets = [
        f"Example 1:\n{examples['Battery Drain'][0]}\nOUTPUT: CLASSIFICATION: Battery Drain Attack. DESCRIPTION: Increased home load and constant Tesla charging.\nCONFIDENCE: 85%.\n",
        f"Example 2:\n{examples['Denial of Service'][0]}\nOUTPUT: CLASSIFICATION: Denial of Service Attack. DESCRIPTION: Multiple outages and sometimes sets solar generation and battery charge to 0.0.\nCONFIDENCE: 90%.\n",
        f"Example 3:\n{examples['Grid Manipulation'][0]}\nOUTPUT: CLASSIFICATION: Grid Manipulation Attack. DESCRIPTION: Distorted grid import/export values with impossible negative values.\nCONFIDENCE: 95%.\n",
        f"Example 4:\n{examples['Man-in-the-Middle'][0]}\nOUTPUT: CLASSIFICATION: Man-in-the-Middle Attack. DESCRIPTION: Randomly alters solar generation and battery charge by up to 50-150%.\nCONFIDENCE: 97%.\n",
        f"Example 5:\n{examples['Clean'][0]}\nOUTPUT: CLASSIFICATION: Clean log file. DESCRIPTION: The file exhibits no unordinary behavior.\nCONFIDENCE: 87%.\n",
        f"Example 6:\n{examples['Clean1'][0]}\nOUTPUT: CLASSIFICATION: Clean log file. DESCRIPTION: The file exhibits no unordinary behavior.\nCONFIDENCE: 91%.\n"
    ]

    def single_query():
        # Randomize example order to prevent bias
        random.shuffle(example_snippets)
        in_context_prompt = (
            "You are a DER cybersecurity expert that analyzes DER grids and identifies attacks in them.\n"
            "The system is vulnerable to 4 kinds of attacks:\n"
            "   - DOS: causes data outages between 10–14h & 18–20h, sets values to 0.0\n"
            "   - MITM: alters solar & battery by 50–150%\n"
            "   - Battery Drain: high home load, constant Tesla charging\n"
            "   - Grid Manipulation: distorts grid import/export up to 3x or goes negative\n"
            "Respond in the format:\n"
            "CLASSIFICATION:\nDESCRIPTION:\nCONFIDENCE:\n\n"
            + ''.join(example_snippets) +
            "\nNow, classify this log:\n" + prompt
        )
        return query_openai(in_context_prompt)

    # Run 5 threaded queries
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(single_query) for _ in range(5)]
        for future in concurrent.futures.as_completed(futures):
            try:
                responses.append(future.result())
            except Exception as e:
                responses.append(f"⚠️ Error in thread: {str(e)}")

    return responses


@app.route('/ask_llm', methods=['POST'])
def ask_llm():
    data = request.json
    log = data.get("query")

    if not log or not isinstance(log, str):
        return jsonify({"error": "⚠️ 'query' must be a single log string."}), 400
    else:
        print("Received Request: {log}\n")

    # Step 1: Run multi-query on the log data
    responses = multi_query(log)

    # Step 2: Use final_output to process the responses and format them for the user
    final_result = final_output(responses)

    return jsonify(final_result)

if __name__ == '__main__':
    app.run(debug=True, port=8000)
