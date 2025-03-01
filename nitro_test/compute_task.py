import numpy as np
import time
import hashlib

def matrix_multiplication():
    size = 10000
    A = np.random.rand(size, size)
    B = np.random.rand(size, size)
    return np.dot(A, B)

def hash_computation():
    data = b"AWS Nitro Enclave Performance Test" * 1000000
    return hashlib.sha256(data).hexdigest()

print(f"wait 10secs..")
time.sleep(10)

print(f"start")

start = time.time()
matrix_multiplication()
hash_computation()
end = time.time()

print(f"Compute-Intensive Task Completed in {end - start:.2f} seconds")
