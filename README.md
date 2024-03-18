# how-to-recover-secret
Implementation for How to Recover a Cryptographic Secret From the Cloud Paper

## Setup
- Install Python 3.11 and python3.11-venv
- Create a virtual environment: `python3.11 -m venv .venv`
- Activate the virtual environment: `source .venv/bin/activate`
- Run ```pip install -r requirements.txt``` to install the required packages
- Run ```docker compose up -d``` to start the database(mongodb)

## Running the Ordering Service and Noise Simulation
- Run ```python -m fabric.ordering_service``` to start the ordering services
- Run ```python -m fabric.noise_simulation``` to run processes that simulate noise by create random transactions

## Running the Secret Recovery
The ```scripts``` folder contains the scripts to run the secret recovery. The scripts are: 
- ```store.py```: This script runs the secret recovery store algorithm
- ```retrieve.py```: This script runs the secret recovery retrieve algorithm
- ```remove.py```: This script runs the secret recovery remove algorithm
- ```recover.py```: This script runs the secret recovery recover algorithm

To run the scripts, you can use the following commands: ```python -m scripts.store```, ```python -m scripts.retrieve```, ```python -m scripts.remove```, and ```python -m scripts.recover```