#/bin/bash

# Install the AWS Nitro Enclaves CLI
sudo amazon-linux-extras install aws-nitro-enclaves-cli -y
sudo yum install aws-nitro-enclaves-cli-devel -y

# Add your user to the ne user group
sudo usermod -aG ne ec2-user

# Add your user to the docker user group
sudo usermod -aG docker ec2-user

# Check the installation
nitro-cli --version