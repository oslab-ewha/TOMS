import os
import time
import requests
import pandas as pd

def file_io_test():
    filename = "/tmp/test_large_file.csv"
    data = "A,B,C,D\n" + "\n".join(["1,2,3,4"] * 20000000)
    with open(filename, "w") as f:
        f.write(data)
    
    df = pd.read_csv(filename)
    os.remove(filename)

print(f"wait 10secs..")
time.sleep(10)

print(f"start")

start = time.time()
file_io_test()
end = time.time()

print(f"File I/O Time: {end - start:.2f} sec")
