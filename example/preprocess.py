import sys
import pydicom
import numpy as np
from torch import from_numpy, save, unsqueeze, double, tensor
import torch
from skimage.transform import resize

def preprocess(dicom_path: str):
    ds = pydicom.dcmread(dicom_path, force=True)

    # Convert to float to avoid overflow or underflow losses.
    image_2d = ds.pixel_array.astype(float)

    # Rescaling grey scale between 0-255
    image_2d_scaled = (np.maximum(image_2d,0) / image_2d.max()) * 255.0

    # Convert to uint
    image_2d_scaled = np.uint8(image_2d_scaled)

    image_2d_scaled = resize(image_2d_scaled, (32, 32)).reshape(1,1,32,32)

    scaled_tensor = tensor(image_2d_scaled, dtype=double)

    return scaled_tensor


if __name__ == "__main__":
    preprocess(sys.argv[1])
