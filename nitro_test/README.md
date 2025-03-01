# Measuring Overhead in TEE Environments via AWS Nitro Enclaves

This folder provides a Docker-based setup for measuring the performance overhead of executing workloads
in a Trusted Execution Environment (TEE) using AWS Nitro Enclaves.

## AWS nitro enclaves

It is recommended to first read [AWS Nitro Enclaves User Guide](https://docs.aws.amazon.com/enclaves/latest/user/nitro-enclave.html).  

### Setup an EC2 instance to support nitro enclave

1. Create an EC2 instance with Nitro Enclave enabled. An instance under Intel or AMD requires 4 vCPUs and 8GB of memory.
   Instance types such as m5.xlarge or m6i.xlarge should be sufficient. 
   The c6g.large AWS Graviton instance failed to work with Nitro Enclaves. The reason is currently unknown.

2. Start the EC2 instance.

3. Install the Nitro Enclaves CLI on Linux. Refer to [this guide](https://docs.aws.amazon.com/enclaves/latest/user/nitro-enclave-cli-install.html).

4. Edit `/etc/nitro_enclaves/allocator.yaml` to ensure the memory size is at least 8GB.

## Measurement Instructions
1. **Build docker images for a compute bound task and a IO bound task**
   ```sh
   docker build -t compute-task -f Dockerfile.com .
   docker build -t io-task -f Dockerfile.io .
   ```

2. **Generate the EIF Images**
   ```sh
   nitro-cli build-enclave --docker-uri compute-task --output-file compute.eif
   nitro-cli build-enclave --docker-uri io-task --output-file io.eif 
   ```

3. **Run the Enclave**
   ```sh
   nitro-cli run-enclave --eif-path compute.eif --cpu-count 2 --memory 8192 --debug-mode
   ```
   f successful, the command will output an enclave-id.

4. **Capture Enclave Output**
   
   Check the enclave's output to verify the execution time for kernel operations and Python commands.
   To allow time for attaching the console, the Python script includes 10 seconds sleep.
   Use the enclave-id returned from run-enclave.
   ```sh
   nitro-cli console --enclave-id i-0b6a5c268ef861605-enc1954c4dea4068f5
   ```
    


