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

## Setup Parent and Enclave
- Install the AWS CLI and configure it with your credentials
- Create a parent instance with the following command:
```bash
aws ec2 run-instances \
--image-id ami-01387af90a62e3c01 \
--count 1 \
--instance-type m5.xlarge \
--key-name your_key_name \
--security-groups your_security_group_name \
--enclave-options 'Enabled=true'
```
remember to replace the ```key-name``` and ```security-groups``` with your own values. The ```image-id``` in the example above is the Amazon Linux 2 AMI (HVM) - Kernel 5.10, SSD Volume Type: you can change it to another AMI if you want.

- Connect to the parent instance: ```ssh -i your_private_key.pem ec2-user@public-ip```. Replace ```your_private_key.pem``` and ```public-ip``` with your own. For more information on how to connect to an instance, see [Connecting to Your Linux Instance Using SSH](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/connect-linux-inst-ssh.html)

- Install the enclave software on the parent instance using the instructions in the [AWS Nitro Enclaves documentation](https://docs.aws.amazon.com/enclaves/latest/user/nitro-enclave-cli-install.html). Be sure to select the appropriate Amazon linux version corresponding to the parent instance. If you are using the Amazon Linux 2 AMI (HVM) - Kernel 5.10, SSD Volume Type, you can use the ```amazon-linux-2-install-nitro.sh``` script in the project root folder.

- Build the enclave image by running the ```build-and-run-enclave.sh``` script in the project root folder. This script will 
    - Build the enclave docker image 
    - Run ```nitro-cli``` to build the enclave ```.eif``` file and output enclave measurement information (PCR0, PCR1, and PCR2) to ```nitro-cli-build.log``` log file
    - Assigns 2 vCPUs and 4 GB of memory to the enclave and starts the enclave instance on CID 16. The EnclaveCID is like an IP address for the local socket (vsock) between the parent instance and the enclave. The enclave starts and listens on the vsock port 5005.

- Run the ```nitro-cli describe-enclaves``` command to verify the enclave is running. The output should look like this:
```json
{
    "EnclaveID": "i-05f6ed443aEXAMPLE-enc173dfe3eEXAMPLE",
    "ProcessID": 7077,
    "EnclaveCID": 16,
    "NumberOfCPUs": 2,
    "CPUIDs": [
        1,
        3
    ],
    "MemoryMiB": 512,
    "State": "RUNNING",
    "Flags": "DEBUG_MODE"
}
```

- You can also view the read-only console output of the enclave by running the ```nitro-cli console --enclave-id i-05f6ed443aEXAMPLE-enc173dfe3eEXAMPLE``` command. Replace the ```i-05f6ed443aEXAMPLE-enc173dfe3eEXAMPLE``` with your own enclave ID.

- No longer need the enclave? You can terminate it with the ```nitro-cli terminate-enclave --enclave-id i-05f6ed443aEXAMPLE-enc173dfe3eEXAMPLE``` command. Replace the ```i-05f6ed443aEXAMPLE-enc173dfe3eEXAMPLE``` with your own enclave ID.