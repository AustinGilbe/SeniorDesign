import random

# Sample examples to use as semantic priors
EXAMPLES = [
    {"input": "Unauthorized login attempt from 192.168.1.100", "output": "Threat: Possible Brute Force Attack"},
    {"input": "Multiple failed login attempts", "output": "Threat: Account Takeover Attempt"},
    {"input": "User logged in from a new location", "output": "No Threat"},
]

def format_prompt(log_data):
    """Creates a few-shot learning prompt for LLM."""
    prompt = "Analyze the following log entry for potential security threats:\n\n"
    
    # Select random examples to include in the prompt
    examples = random.sample(EXAMPLES, k=2)
    for ex in examples:
        prompt += f"Log: {ex['input']}\nClassification: {ex['output']}\n\n"
    
    # Add user input
    prompt += f"Log: {log_data}\nClassification:"
    return prompt
