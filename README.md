# med_ai_runner
A framework for running your deep learning models in practice

## Device Setup
- Install docker from [here](https://docs.docker.com/engine/install/ubuntu/)
- Install nvidia drivers
- Install nvidia runtime (more info [here](https://github.com/NVIDIA/nvidia-docker#quickstart))
``` 
# Add the package repositories
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```
- Install nvidia-container-runtime
``` 
sudo apt install nvidia-container-runtime 
```
- Add the following file at ```/etc/docker/daemon.json```
```
{

    "runtimes": {
        "nvidia": {
            "path": "nvidia-container-runtime",
            "runtimeArgs": []
        }
    }
}
```
- Test that the setup is working with the following command
```
docker run --runtime=nvidia nvidia/cuda:10.0-base nvidia-smi
```

## Model Containers
- Build on top of docker

### Container Metadata
- Metadata about the input and output of a given model container
- Attributes - docker labels attached to the image
  - input: Type of expected input (dicom)
  - output: Shape of output (numpy)
  - name: Name of the model
  - description: Description of what the model does
  
### Container Format
- Required members (exist as python scripts)
  - main.py - accepts path to dcm
