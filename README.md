# med_ai_runner
A framework for running your deep learning models in practice

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
