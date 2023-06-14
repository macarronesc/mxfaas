import subprocess
import time
import numpy as np
import threading
import requests
from statistics import mean, median,variance,stdev
import json

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

output = subprocess.check_output("kn service list", shell=True).decode("utf-8")
lines = output.splitlines()
lines = lines[1:] # delete the first line

services = []
serviceNames = []

for line in lines:
    serviceName = line.split()[0] 
    if serviceName not in serviceNames:
        serviceNames.append(serviceName)
        print("ServiceName: " + serviceName)

for serviceName in serviceNames:
    services.append(getUrlByFuncName(serviceName))

def extract_times(data):
    global times
    for item in data:
        time_text = item["time"]
        times.append(float(time_text))

def lambda_func(service, numFunctions):
    # r = requests.post(service, json={"numCores": 20, "affinity_mask": list(range(20)), "printInfo": " "})
    r = requests.post(service, json={"name": "test", "numFunctions": numFunctions})
    print(r.text)
    extract_times(json.loads(r.text))

loads = [1, 5, 10]

output_file = open("run-all-out.txt", "w")

for load in loads:
    print("LOAD: " + str(load))

    for service in services:
        print("Service: " + service)
        threads = []
        times = []

        lambda_func(service, load)

        print("=====================" + serviceNames[services.index(service)] + "=====================", file=output_file, flush=True)
        print(mean(times), file=output_file, flush=True)
        print(median(times), file=output_file, flush=True)
        print(np.percentile(times, 90), file=output_file, flush=True)
        print(np.percentile(times, 95), file=output_file, flush=True)
        print(np.percentile(times, 99), file=output_file, flush=True)
