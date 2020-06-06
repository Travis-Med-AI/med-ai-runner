import sys
import pydicom as dicom
import numpy as np
from torch import from_numpy, save, unsqueeze, double, tensor
import torch
from skimage.transform import resize
import os

def read_dicom (dicom_path):
    dicom_file = dicom.read_file(dicom_path)
    pixel_data = list()
    for record in dicom_file.DirectoryRecordSequence:
        if record.DirectoryRecordType == "IMAGE":
        # Extract the relative path to the DICOM file
            dir_path = os.path.dirname(dicom_path)
            path = f'{dir_path}/{os.path.join(*record.ReferencedFileID)}'
            dcm = dicom.read_file(path)

            # Now get your image data
            pixel_data.append(dcm.pixel_array)
    return np.array(pixel_data)


def preprocess(dicom_path: str):
    image_2d = read_dicom(f'{dicom_path}/DICOMDIR').astype(float)


    # Rescaling grey scale between 0-255
    image_2d_scaled = (np.maximum(image_2d,0) / image_2d.max()) * 255.0

    # Convert to uint
    image_2d_scaled = np.uint8(image_2d_scaled)

    image_2d_scaled = resize(image_2d_scaled, (1, 32, 32)).reshape(1, 1, 32, 32)

    scaled_tensor = tensor(image_2d_scaled, dtype=double)

    return scaled_tensor


if __name__ == "__main__":
    preprocess(sys.argv[1])
