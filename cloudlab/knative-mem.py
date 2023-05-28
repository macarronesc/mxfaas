import subprocess
import numpy as np
import threading
import requests
from statistics import mean, median,variance,stdev
import re
import time

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
        print(result)
        times.append(t2-t1 - result)
    else:
        times.append(t2-t1)


serviceName = "mem-bandwidth"
service = getUrlByFuncName(serviceName)
loads = [5]
output_file = open("run-all-out.txt", "w")

print("Service: " + str(service))

for load in loads:
    print("LOAD: " + str(load))

    # MXFaaS
    threads = []
    times = []

    for i in range(5, 0, -1):
        threadToAdd = threading.Thread(target=lambda_func, args=(service, ))
        threads.append(threadToAdd)
        threadToAdd.start()

    for thread in threads:
        thread.join()

    print("MXFaaS", file=output_file, flush=True)
    print("=====================" + serviceName + "=====================", file=output_file, flush=True)
    print(mean(times), file=output_file, flush=True)
    print(median(times), file=output_file, flush=True)
    print(np.percentile(times, 90), file=output_file, flush=True)
    print(np.percentile(times, 95), file=output_file, flush=True)
    print(np.percentile(times, 99), file=output_file, flush=True)



    # Parallel
    times = []





    print("", file=output_file, flush=True)
    print("Parallel download", file=output_file, flush=True)
    print("=====================" + serviceName + "=====================", file=output_file, flush=True)
