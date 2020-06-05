from preprocess import preprocess
from evaluate import evaluate
import sys

if __name__ == '__main__':
    input_path = sys.argv[1]
    preprocessed = preprocess(input_path)
    out = evaluate(preprocessed)
    print(out)