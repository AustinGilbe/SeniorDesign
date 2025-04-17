This directory contains code for the LLM API. The API runs with a model from OLLAMA.  

## Setup  
To start the API, first create a virtual environment. Mine is called '.venv'.  
1. You can create a virtual environment with the command `python3 -m venv .venv`.  
2. Activate the virtual environment with: `source .venv/bin/activate`  
2. Then, download the necesary packages with pip. I've included a requirements.txt file to make this easy. Use this: `pip install -r requirements.txt`  

## Running the API
To run the api, we need to serve OLLAMA. OLLAMA exposes a port on localhost, and we can interact with it through http requests. By default it is on port 11434.  
1. Serve ollama in the background by typing `ollama serve &`  
2. Now, to start the LLM api, type `python oll_api.py`  

## Overview
Basically, to interact with the model, we use http requests. Ollama opens a local port, and the api queries it through this port. The api itself is what is connected to the web-app. Including the API separately allows us to construct the prompts we want. We can change which model to interact with by downloading the appropriate model with ollama in the root directory and then updating the api code.
