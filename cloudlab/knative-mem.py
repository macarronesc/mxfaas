import subprocess
import numpy as np
import threading
import requests
from statistics import mean, median,variance,stdev
import re
import time
from multiprocessing.pool import ThreadPool
import boto3
from botocore import UNSIGNED
from botocore.config import Config

## Parallel download
# Function that download 1 file
def download_url(filename, s3):
    try:
        bucket_name = "gnomad-public-us-east-1"
        bucket_dir = "truth-sets/hail-0.2/1000G.GRCh38.genotypes.20170504.mt/rows/rows/parts/"

        s3.download_file(Filename='/tmp/' + filename, Bucket=bucket_name, Key=bucket_dir + filename)

    except Exception as e:
        print('Exception in download_file():', e)

## MXFaaS
# get the url of a function
def getUrlByFuncName(funcName):
    try:
        output = subprocess.check_output("kn service describe " + funcName + " -vvv", shell=True).decode("utf-8")
    except Exception as e:
        print("Error in kn service describe == " + str(e))
        return None
    lines = output.splitlines()
    for line in lines:
        if "URL:"  in line:
            url = line.split()[1]
            return url

def lambda_func(service):
    global times
    t1 = time.time()
    r = requests.post(service, json={"name": "test"})
    t2 = time.time()

    # Convert bytes literal to string
    result_str = r.content.decode("utf-8")

    # Use regular expression to extract the number
    result_match = re.search(r'"result = ": ([0-9.e+-]+)', result_str)

    if result_match:
        result = float(result_match.group(1))
        times.append(t2-t1 - result)
        print(t2-t1 - result)
    else:
        times.append(t2-t1)

def print_output(times, experiment, load):
    global output_file, serviceName
    print("THREADS: " + str(load), file=output_file, flush=True)
    print(experiment, file=output_file, flush=True)
    print("=====================" + serviceName + "=====================", file=output_file, flush=True)
    print(mean(times), file=output_file, flush=True)
    print(median(times), file=output_file, flush=True)
    print(np.percentile(times, 90), file=output_file, flush=True)
    print(np.percentile(times, 95), file=output_file, flush=True)
    print(np.percentile(times, 99), file=output_file, flush=True)

serviceName = "mem-bandwidth"
service = getUrlByFuncName(serviceName)
loads = [5]
output_file = open("run-all-out.txt", "w")

print("Service: " + str(service))

for load in loads:
    print("LOAD: " + str(load))

    # MXFaaS
    print("MXFaaS")
    threads = []
    times = []

    for i in range(load, 0, -1):
        threadToAdd = threading.Thread(target=lambda_func, args=(service, ))
        threads.append(threadToAdd)
        threadToAdd.start()

    for thread in threads:
        thread.join()

    print_output(times, "MXFaaS", load)

    # Parallel
    print("Parallel")
    threads = []
    times = []

    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    filenames = ['part-17', 'part-18', 'part-19', 'part-20', 'part-21']

    for i in range(load, 0, -1):
        t1 = time.time()
        for filename in filenames:
            threadToAdd = threading.Thread(target=download_url, args=(filename, s3))
            threads.append(threadToAdd)
            threadToAdd.start()

        for thread in threads:
            thread.join()
        t2 = time.time()

        elapsed_time = t2 - t1
        times.append(elapsed_time)
        print(elapsed_time)

    print("", file=output_file, flush=True)
    print_output(times, "Parallel", load)