from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from collections import Counter
import os
import concurrent.futures
import re
import csv
from io import StringIO
from io import TextIOWrapper
from datetime import datetime
from datetime import timedelta

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app)

# Attack signatures based on the simulation code
ATTACK_SIGNATURES = {
    "Battery Drain": {
        "key_indicators": [
            "Home_Load_kW consistently higher than baseline (>3.0kW)",
            "Tesla_Charger_kW active outside normal hours (normal: 11, 12, 13, 18, 19)",
            "Battery charge depleting more rapidly than normal"
        ],
        "detection_patterns": [
            "Higher than normal home load values",
            "Tesla charging outside of expected hours",
            "Reduced battery levels"
        ]
    },
    "Denial of Service": {
        "key_indicators": [
            "Missing data points (especially between 10-14h & 18-20h)",
            "Solar_Generation_kW and Battery_Charge_kWh abruptly set to 0.0",
            "Unexplained data outages during peak operation times"
        ],
        "detection_patterns": [
            "Zero values where non-zero values are expected",
            "Missing data points in specific time windows",
            "Sudden drops to zero in solar or battery readings"
        ]
    },
    "Grid Manipulation": {
        "key_indicators": [
            "Grid_Import_kW or Grid_Export_kW amplified by 1.8-3.0x normal values",
            "Negative Grid_Import_kW values (impossible in normal operation)",
            "Grid values inconsistent with load, generation, and battery activity"
        ],
        "detection_patterns": [
            "Negative grid import values",
            "Abnormally high grid values",
            "Grid values that don't match energy balance equations"
        ]
    },
    "Man-in-the-Middle": {
        "key_indicators": [
            "Solar_Generation_kW randomly altered by 50-150% of expected values",
            "Battery_Charge_kWh altered by 50-150% of expected values",
            "Random fluctuations not correlated with time of day"
        ],
        "detection_patterns": [
            "Solar values that don't follow expected solar curve",
            "Battery charge levels with unexpected fluctuations",
            "Energy values that technically fall within normal ranges but don't follow expected patterns"
        ]
    },
    "Clean": {
        "key_indicators": [
            "Solar generation follows expected sinusoidal curve based on time of day",
            "Tesla charging primarily during designated hours (11, 12, 13, 18, 19)",
            "Home load around baseline (1.5kW) with minor variations",
            "Energy balance equations are properly maintained"
        ],
        "detection_patterns": [
            "Normal solar curve pattern",
            "Expected Tesla charging patterns",
            "Consistent home load values",
            "Proper energy accounting across all columns"
        ]
    },
    "Unknown": {
        "key_indicators": [
            "Insufficient data to determine attack type",
            "Inconsistent or corrupted log data",
            "Patterns do not match known attack signatures"
        ],
        "detection_patterns": [
            "Incomplete or missing data",
            "Data inconsistencies",
            "Unrecognized patterns"
        ]
    }
}

def parse_csv_log(log_data):
    """Parse CSV log data into a structured format"""
    try:
        # If passed a file-like object, read and decode
        if hasattr(log_data, 'read'):
            log_data = log_data.read()
            if isinstance(log_data, bytes):  # Handle binary reads
                log_data = log_data.decode('utf-8')
        # Parse CSV
        reader = csv.reader(StringIO(log_data))
        headers = next(reader)
        rows = list(reader)
        # Convert to numerical values where appropriate
        parsed_data = []
        for row in rows:
            try:
                # Convert timestamp to datetime
                timestamp = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
                # Convert numerical values, treating empty values as 0.0
                numerical_values = [float(val) if val != '' else 0.0 for val in row[1:]]
                
                parsed_data.append({
                    'timestamp': timestamp,
                    'hour': timestamp.hour,
                    'solar_generation': numerical_values[0],
                    'home_load': numerical_values[1],
                    'tesla_charger': numerical_values[2],
                    'battery_charge': numerical_values[3],
                    'battery_discharge': numerical_values[4],
                    'grid_import': numerical_values[5],
                    'grid_export': numerical_values[6]
                })
            except (ValueError, IndexError) as e:
                print(f"Error parsing row: {e}")
                continue  # Skip rows with parsing errors
        
        return {
            'headers': headers,
            'rows': parsed_data,
            'row_count': len(parsed_data)
        }
    except Exception as e:
        print(f"Error parsing CSV: {e}")
        return None

def analyze_log_data(parsed_log):
    """Performs rule-based analysis on the parsed log data"""
    if not parsed_log or parsed_log['row_count'] == 0:
        return {
            'analysis': "Unable to analyze: Invalid or empty log data",
            'indicators': {},
            'likely_attack': "Unknown",
            'attack_likelihood': {
                "Battery Drain": 0,
                "Denial of Service": 0,
                "Grid Manipulation": 0,
                "Man-in-the-Middle": 0,
                "Clean": 0
            }
        }

    rows = parsed_log['rows']
    indicators = {}
    
    print(f"Analyzing {len(rows)} rows of log data")
    
    # Complete data check
    total_expected_hours = 24
    indicators['complete_data'] = len(rows) >= total_expected_hours * 0.9  # Allow 10% missing
    
    # ----- BATTERY DRAIN INDICATORS -----
    # Calculate high home load percentage
    high_home_load_count = sum(1 for row in rows if row['home_load'] > 3.0)
    indicators['high_home_load_pct'] = high_home_load_count / len(rows) if rows else 0
    
    # Calculate Tesla charging outside normal hours
    expected_charging_hours = [11, 12, 13, 18, 19]
    charging_in_expected = 0
    charging_in_unexpected = 0
    
    for row in rows:
        if row['tesla_charger'] > 5.0:  # Significant Tesla charging
            if row['hour'] in expected_charging_hours:
                charging_in_expected += 1
            else:
                charging_in_unexpected += 1
    
    indicators['tesla_charging_outside_normal'] = charging_in_unexpected > charging_in_expected
    
    # ----- DOS INDICATORS -----
    # Check for missing data in critical periods
    if len(rows) >= 2:
        start_time = rows[0]['timestamp']
        end_time = rows[-1]['timestamp']
        expected_timestamps = set()
        current_time = start_time
        while current_time <= end_time:
            expected_timestamps.add(current_time)
            current_time += timedelta(hours=1)
        
        actual_timestamps = set(row['timestamp'] for row in rows)
        missing_timestamps = expected_timestamps - actual_timestamps
        indicators['missing_data_count'] = len(missing_timestamps)
        
        # Check specifically for peak hour missing data (10-14h & 18-20h)
        peak_hours = [10, 11, 12, 13, 14, 18, 19, 20]
        peak_hour_missing = sum(1 for ts in missing_timestamps if ts.hour in peak_hours)
        indicators['peak_hour_missing_data'] = peak_hour_missing > len(peak_hours) * 0.3
    else:
        indicators['missing_data_count'] = 0
        indicators['peak_hour_missing_data'] = False
    
    # Check for zeroed critical values
    zeroed_entries = [row for row in rows if (row['solar_generation'] == 0 and 
                                             row['battery_charge'] == 0)]
    indicators['multiple_zeroed_values'] = len(zeroed_entries) > 3
    
    # ----- GRID MANIPULATION INDICATORS -----
    # Check for impossible negative grid import values
    negative_grid = [row for row in rows if row['grid_import'] < -0.1]  # Allow small measurement errors
    indicators['negative_grid_values_count'] = len(negative_grid)
    
    # Check for abnormally high grid values
    high_grid_values = [row for row in rows if row['grid_import'] > 12.0 or row['grid_export'] > 12.0]
    indicators['high_grid_values_count'] = len(high_grid_values)
    
    # ----- MAN-IN-THE-MIDDLE INDICATORS -----
    # Check for impossible solar generation at night
    night_hours = [0, 1, 2, 3, 4, 5, 20, 21, 22, 23]
    night_solar = [row for row in rows if row['hour'] in night_hours and row['solar_generation'] > 1.0]
    indicators['night_solar_count'] = len(night_solar)
    
    # Check for erratic battery behavior
    battery_values = [row['battery_charge'] for row in rows]
    if len(battery_values) >= 3:
        battery_diffs = [abs(battery_values[i] - battery_values[i-1]) for i in range(1, len(battery_values))]
        indicators['erratic_battery'] = any(diff > 2.0 for diff in battery_diffs)
    else:
        indicators['erratic_battery'] = False
    
    # ----- Calculate attack scores -----
    attack_likelihood = {
        "Battery Drain": 0,
        "Denial of Service": 0,
        "Grid Manipulation": 0,
        "Man-in-the-Middle": 0,
        "Clean": 0
    }
    
    # BATTERY DRAIN CRITERIA
    # Must have both high home load and Tesla charging issues
    if indicators['high_home_load_pct'] > 0.5:  # More than half of readings show high load
        attack_likelihood["Battery Drain"] += 5
    if indicators['tesla_charging_outside_normal']:
        attack_likelihood["Battery Drain"] += 5
    
    # DOS CRITERIA
    # Either significant missing data or zeroed values
    if indicators['missing_data_count'] > 5:
        attack_likelihood["Denial of Service"] += 3
    if indicators['peak_hour_missing_data']:
        attack_likelihood["Denial of Service"] += 3
    if indicators['multiple_zeroed_values']:
        attack_likelihood["Denial of Service"] += 4
    
    # GRID MANIPULATION CRITERIA
    # Either negative grid values or very high grid values
    if indicators['negative_grid_values_count'] > 0:
        attack_likelihood["Grid Manipulation"] += 8  # Strong indicator
    if indicators['high_grid_values_count'] > 2:
        attack_likelihood["Grid Manipulation"] += 5
    
    # MAN-IN-THE-MIDDLE CRITERIA
    # Must have impossible night solar AND erratic battery behavior
    if indicators['night_solar_count'] > 0 and indicators['erratic_battery']:
        attack_likelihood["Man-in-the-Middle"] += 5
    
    # CLEAN CRITERIA
    clean_score = 0
    if indicators['complete_data']:
        clean_score += 2
    if indicators['high_home_load_pct'] < 0.1:
        clean_score += 2
    if not indicators['tesla_charging_outside_normal']:
        clean_score += 2
    if indicators['negative_grid_values_count'] == 0:
        clean_score += 2
    if indicators['night_solar_count'] == 0:
        clean_score += 2
    if not indicators['erratic_battery']:
        clean_score += 2
    if indicators['missing_data_count'] < 3:
        clean_score += 2
    if not indicators['multiple_zeroed_values']:
        clean_score += 2
    
    # Only set Clean score if no other attack has significant likelihood
    max_attack_score = max(
        attack_likelihood["Battery Drain"],
        attack_likelihood["Denial of Service"],
        attack_likelihood["Grid Manipulation"],
        attack_likelihood["Man-in-the-Middle"]
    )
    
    if max_attack_score < 5 and clean_score >= 10:
        attack_likelihood["Clean"] = clean_score
    
    # Select most likely attack
    likely_attack = max(attack_likelihood, key=attack_likelihood.get)
    if attack_likelihood[likely_attack] < 5:
        likely_attack = "Unknown"
    
    print(f"Attack scores: {attack_likelihood}")
    print(f"Most likely attack: {likely_attack}")
    print(f"indicators: {indicators}")
    
    return {
        'analysis': f"Most likely classification: {likely_attack}",
        'indicators': indicators,
        'attack_likelihood': attack_likelihood,
        'likely_attack': likely_attack
    }

def extract_classification(response):
    """Extract classification from a response string"""
    match = re.search(r"CLASSIFICATION:\s*(.*?)(?:\n|$)", response, re.IGNORECASE)
    if match:
        # Normalize classification names by looking for key terms
        classification = match.group(1).strip().lower()
        
        if "battery" in classification and "drain" in classification:
            return "Battery Drain"
        elif ("denial" in classification and "service" in classification) or "dos" in classification:
            return "Denial of Service"
        elif "grid" in classification and "manipulation" in classification:
            return "Grid Manipulation"
        elif ("man" in classification and "middle" in classification) or "mitm" in classification:
            return "Man-in-the-Middle"
        elif "clean" in classification:
            return "Clean"
        else:
            return "Unknown"
    return "Unknown"

def extract_description(response):
    """Extract description from a response string"""
    match = re.search(r"DESCRIPTION:\s*(.*?)(?:\n|CONFIDENCE:|$)", response, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""

def extract_confidence(response):
    """Extract confidence from a response string"""
    match = re.search(r"CONFIDENCE:\s*(\d+)%", response, re.IGNORECASE)
    return int(match.group(1)) if match else 0

def query_openai(prompt, max_tokens=200, temperature=0.1):
    """Query OpenAI API with error handling"""
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API Error: {str(e)}")
        return f"⚠️ Error: {str(e)}"

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

def create_smart_prompt(log_data, analysis_results):
    """Create a smart prompt with log data, analysis results, and examples"""
    indicators = analysis_results['indicators']
    log_sample = "\n".join(log_data.split("\n")[:15])
    
    likely_attack = analysis_results['likely_attack']
    
    # Get attack signatures for the likely attack
    # attack_signatures = ATTACK_SIGNATURES.get(likely_attack, {}).get('key_indicators', [])
    # signature_text = "\n".join([f"- {sig}" for sig in attack_signatures])
    bd_sig = ATTACK_SIGNATURES.get("Battery Drain", {}).get('key_indicators', [])
    bd_signature_text = "\n".join([f"- {sig}" for sig in bd_sig])
    clean_sig = ATTACK_SIGNATURES.get("Clean", {}).get('key_indicators', [])
    clean_signature_text = "\n".join([f"- {sig}" for sig in clean_sig])
    mitm_sig = ATTACK_SIGNATURES.get("Man-in-the-Middle", {}).get('key_indicators', [])
    mitm_signature_text = "\n".join([f"- {sig}" for sig in mitm_sig])
    dos_sig = ATTACK_SIGNATURES.get("Denial of Service", {}).get('key_indicators', [])
    dos_signature_text = "\n".join([f"- {sig}" for sig in dos_sig])
    gm_sig = ATTACK_SIGNATURES.get("Grid Manipulation", {}).get('key_indicators', [])
    gm_signature_text = "\n".join([f"- {sig}" for sig in gm_sig])

    
    # Get example logs
    example_logs = read_examples()
    
    # Initialize example variables with safe defaults
    battery_drain_example = "Example not available"
    grid_manipulation_example = "Example not available"
    clean_example = "Example not available"
    dos_example = "Example not available"
    mitm_example = "Example not available"
    
    # Safely extract examples if they exist
    if "Battery Drain" in example_logs and example_logs["Battery Drain"]:
        battery_drain_example = example_logs["Battery Drain"][0]
    if "Grid Manipulation" in example_logs and example_logs["Grid Manipulation"]:
        grid_manipulation_example = example_logs["Grid Manipulation"][0]
    if "Clean" in example_logs and example_logs["Clean"]:
        clean_example = example_logs["Clean"][0]
    if "Denial of Service" in example_logs and example_logs["Denial of Service"]:
        dos_example = example_logs["Denial of Service"][0]
    if "Man-in-the-Middle" in example_logs and example_logs["Man-in-the-Middle"]:
        mitm_example = example_logs["Man-in-the-Middle"][0]
    
    # Format examples with explanations
    examples_format = f"""
EXAMPLE LOGS:

BATTERY DRAIN EXAMPLE:
{battery_drain_example}
Key indicators: Home load consistently >3.5kW, Tesla charging outside normal hours, rapid battery depletion

GRID MANIPULATION EXAMPLE:
{grid_manipulation_example}
Key indicators: Negative grid import values (physically impossible), abnormally high grid values

CLEAN EXAMPLE:
{clean_example}
Key indicators: Normal solar generation curve, appropriate Tesla charging hours, balanced energy equations

DENIAL OF SERVICE EXAMPLE:
{dos_example}
Key indicators: Multiple zero values during peak hours, missing data in sequential time periods

MAN-IN-THE-MIDDLE EXAMPLE:
{mitm_example}
Key indicators: Solar generation at night (impossible), random battery fluctuations, unnatural energy patterns
"""
    
    # Create a detailed prompt with analysis context and examples
    prompt = f"""
As a cybersecurity expert specializing in Distributed Energy Resource (DER) systems, analyze this log data to identify any security threats.

DER security threats include:
1. Battery Drain: Characterized by Home load >3kW AND Tesla charging outside hours [11,12,13,18,19]. Normal grid values.
2. Denial of Service: Characterized by Data outages 10-14h & 18-20h OR zeroed values. Missing sequential data points.
3. Grid Manipulation: Characterized by Import/export amplified 1.8-3x OR negative grid values (physically impossible).
4. Man-in-the-Middle: Characterized by Solar/battery altered by 50-150% AND random fluctuations throughout day.
5. Clean: Normal operation with no security threats - solar generation follows expected curve, normal grid values.

Look carefully at each metric and time pattern. ONLY select the classification that BEST matches the primary attack signature.

{examples_format}

Initial analysis indicates these observations:
- Complete data coverage: {indicators.get('complete_data', 'Unknown')}
- Tesla charging outside normal hours: {indicators.get('tesla_charging_outside_normal', 'Unknown')}
- High home load percentage: {indicators.get('high_home_load_pct', 'Unknown')}
- Missing data count: {indicators.get('missing_data_count', 'Unknown')}
- Peak hour missing data: {indicators.get('peak_hour_missing_data', 'Unknown')}
- Multiple zeroed critical values: {indicators.get('multiple_zeroed_values', 'Unknown')}
- Negative grid values count: {indicators.get('negative_grid_values_count', 'Unknown')}
- High grid values count: {indicators.get('high_grid_values_count', 'Unknown')}
- Nighttime solar generation count: {indicators.get('night_solar_count', 'Unknown')}
- Erratic battery behavior: {indicators.get('erratic_battery', 'Unknown')}

Key indicators for Battery Drain:
{bd_signature_text}

Key indicators for Denial of Service:
{dos_signature_text}

Key indicators for Grid Manipulation:
{gm_signature_text}

Key indicators for Man-in-the-Middle:
{mitm_signature_text}

Key indicators for Clean Files (no attack):
{clean_signature_text}

Based on your expertise and the example logs provided, analyze this log sample:
{log_sample}

Respond with ONLY the following format:
CLASSIFICATION: [select ONE from: "Battery Drain", "Denial of Service", "Grid Manipulation", "Man-in-the-Middle", "Clean"]
DESCRIPTION: [key indicators observed in the log data]
CONFIDENCE: [percentage]%
"""
    return prompt

def multi_query(log):
    """Perform multiple queries with different prompts and approaches"""
    # First, parse and analyze the log data
    parsed_log = parse_csv_log(log)
    analysis_results = analyze_log_data(parsed_log)
    
    print(f"Initial analysis indicates: {analysis_results['likely_attack']}")
    print(f"Attack likelihood scores: {analysis_results['attack_likelihood']}")
    
    responses = []
    
    # Create a smart prompt using the analysis results
    smart_prompt = create_smart_prompt(log, analysis_results)
    print(smart_prompt)
    
    # Run multiple queries with the smart prompt
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(lambda: query_openai(smart_prompt, max_tokens=250)) for _ in range(3)]
        for future in concurrent.futures.as_completed(futures):
            try:
                responses.append(future.result())
            except Exception as e:
                print(f"Thread error: {e}")
                responses.append(f"⚠️ Error in thread: {str(e)}")
    for i, response in enumerate(responses):
        print(f"Response {i+1}:")
        print(response)
        print(f"Extracted classification: {extract_classification(response)}")
        print(f"Extracted confidence: {extract_confidence(response)}")
        print("---")
    return responses, analysis_results

def final_output(responses, analysis_results):
    """Generate final classification output"""
    # Extract classifications and count occurrences
    classifications = [extract_classification(r) for r in responses]
    classification_counter = Counter(classifications)
    
    # Filter out "Unknown" classifications if we have other valid classifications
    valid_classifications = {k: v for k, v in classification_counter.items() if k != "Unknown"}
    
    if valid_classifications:
        # Convert back to Counter object - this fixes the bug
        classification_counter = Counter(valid_classifications)
    
    # Handle empty counter after filtering
    if not classification_counter:
        return {
            "classification": "Unknown",
            "description": "Unable to determine a clear classification from the responses.",
            "confidence": 50
        }
    
    # Get majority classification
    majority_classification = classification_counter.most_common(1)[0][0]
    
    # Consider rule-based analysis in the final decision
    rule_based_classification = analysis_results['likely_attack']
    
    # If rule-based analysis strongly differs from LLM majority, use a weighted approach
    final_classification = majority_classification
    if rule_based_classification != majority_classification and rule_based_classification != "Unknown":
        # Check the confidence levels
        llm_count = classification_counter[majority_classification]
        rule_score = analysis_results['attack_likelihood'].get(rule_based_classification, 0)
        
        # If rule-based score is significantly higher, override
        if rule_score > 3 and llm_count < 3:
            final_classification = rule_based_classification
            print(f"Rule-based classification ({rule_based_classification}, score {rule_score}) overrode LLM classification ({majority_classification}, count {llm_count})")
    
    # Calculate confidence - with better error handling
    agreement_ratio = classification_counter[final_classification] / len(classifications) if final_classification in classification_counter else 0
    confidence_values = [extract_confidence(r) for r in responses if extract_classification(r) == final_classification]
    
    # Avoid division by zero
    if confidence_values:
        avg_confidence = sum(confidence_values) / len(confidence_values)
    else:
        avg_confidence = 0
    
    # Weighted confidence (agreement + original confidence + rule-based strength)
    rule_confidence_bonus = min(10, analysis_results['attack_likelihood'].get(final_classification, 0) * 2)
    final_confidence = int((agreement_ratio * 100 * 0.6) + (avg_confidence * 0.3) + rule_confidence_bonus)
    
    # Cap confidence at 98%
    final_confidence = min(98, final_confidence)
    
    # Get relevant descriptions
    descriptions = [extract_description(r) for r in responses if extract_classification(r) == final_classification]
    
    # If no relevant descriptions, get any description
    if not descriptions:
        descriptions = [extract_description(r) for r in responses if extract_description(r)]
    
    # Use longest description (likely most detailed)
    final_description = max(descriptions, key=len) if descriptions else ""
    
    # If still no good description, generate one based on attack signatures
    if len(final_description) < 20:
        signatures = ATTACK_SIGNATURES.get(final_classification, {}).get('key_indicators', [])
        final_description = f"{'; '.join(signatures)}"
    
    return {
        "classification": final_classification,
        "description": final_description,
        "confidence": final_confidence
    }

@app.route('/ask_llm', methods=['POST'])
@app.route('/ask_llm', methods=['POST'])
def ask_llm():
    """Handle API request with CSV file upload"""
    if 'file' not in request.files:
        return jsonify({"error": "⚠️ No file uploaded."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "⚠️ No selected file."}), 400

    try:
        # Read the uploaded file
        decoded_file = StringIO(file.read().decode('utf-8'))
        parsed = parse_csv_log(decoded_file)

        if parsed["row_count"] == 0:
            return jsonify({"error": "⚠️ CSV log appears empty or invalid."}), 400

        print(f"Received file with {parsed['row_count']} rows")

        # Step 1: Run multi-query with analysis
        responses, analysis_results = multi_query(decoded_file.getvalue())

        # Step 2: Use final_output to process the responses
        result_dict = final_output(responses, analysis_results)

        final_result = f"CLASSIFICATION: {result_dict['classification']}\nDESCRIPTION: {result_dict['description']}\nCONFIDENCE: {result_dict['confidence']}%"
        print(f"Final classification: {final_result}")

        print(f"Sending response: {final_result}")
        return jsonify({"response": final_result})
    
    except Exception as e:
        return jsonify({"error": f"❌ Exception occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)
