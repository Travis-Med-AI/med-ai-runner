FROM pytorch/pytorch

# Add Metadata
LABEL input="dicom" 
LABEL output_type=""
LABEL output="[1,4]"
LABEL name="Example"
LABEL description="An example model"

# Install dependencies
RUN pip install pydicom scikit-image

# add current directory to container
ADD ./* /opt/
WORKDIR /opt

CMD python main.py /opt/${FILENAME}