import torch
import torch.nn as nn
import torch.nn.functional as F
from net import Net
import numpy as np
import sys


def evaluate(input: torch.tensor):
    net = Net()
    net.float()
    net.cuda()

    with torch.no_grad():
        out = net(input.float().cuda())
    
    return out

if __name__ == "__main__":
    print(evaluate(sys.argv[0]))