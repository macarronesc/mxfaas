import subprocess
import time
import numpy as np
import threading
import requests
from statistics import mean, median,variance,stdev
import json
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import random

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

def plot_results(data, dst, service):
    x = []
    y = []
    colors = []

    for i, d in enumerate(data):
        x.extend([d['host_submit'], d['call_start'], d['call_done'], d['status_fetched']])
        y.extend([i + 1] * 4)
        colors.extend(['#E63946', '#00FF00AA', '#0077B6', '#FF9F1C'])  # Custom color palette

    x = [i - min(x) for i in x]

    plt.figure(figsize=(10, 6))  # Adjust the figure size as needed

    plt.scatter(x, y, c=colors, edgecolors='none', s=80, alpha=0.8)  # Remove marker borders

    # Create custom labels and colored rectangles for the legend
    legend_labels = ['Host Submit', 'Call Start', 'Call Done', 'Status Fetched']
    legend_colors = ['#E63946', '#00FF00AA', '#0077B6', '#FF9F1C']
    scatter_handles = []
    for color, label in zip(legend_colors, legend_labels):
        patch = mpatches.Patch(color=color, label=label)
        scatter_handles.append(patch)

    plt.xlabel('Execution time (sec)')
    plt.ylabel('Function calls')
    plt.title('Function Call Timeline (' + service + ")")  # Add a title
    plt.grid(True, zorder=1)

    # Add legend
    plt.legend(handles=scatter_handles, loc='upper right')

    if dst is None:
        os.makedirs('plots', exist_ok=True)
        dst = os.path.join(os.getcwd(), 'plots', '{}_{}'.format(int(time.time()), service + '_timeline.png'))
    else:
        os.makedirs('plots', exist_ok=True)
        dst = os.path.expanduser(dst) if '~' in dst else dst
        dst = '{}_{}'.format(os.path.realpath(dst), service + '_timeline.png')

    plt.tight_layout()  # Improve spacing and layout
    plt.savefig(dst, dpi=300)
    plt.close('all')

def extract_times(data, times_plot_aux):
    global times
    global times_plots

    for item in data:
        times_plot = {}
        times_plot["host_submit"] = times_plot_aux["host_submit"] 
        times_plot["call_start"] = item['times_plot']['call_start']
        times_plot["call_done"] = item['times_plot']['call_done']
        times_plot["status_fetched"] = times_plot_aux["status_fetched"] 
        times_plots.append(times_plot)

        time_text = item["time"]
        times.append(float(time_text))

def lambda_func(service, numFunctions):
    # Plot
    times_plot = {}
    times_plot["host_submit"] = time.time()

    # r = requests.post(service, json={"numCores": 5, "affinity_mask": list(range(5)), "printInfo": " "})
    r = requests.post(service, json={"name": "test", "numFunctions": numFunctions})

    # Plot
    times_plot["status_fetched"] = time.time()

    print(r.text)

    try:
        extract_times(json.loads(r.text), times_plot)
    except:
        print("ERROR")
        pass

loads = [1, 5, 10, 15]

output_file = open("run-all-out.txt", "w")

for load in loads:
    print("LOAD: " + str(load))

    for service in services:
        print("Service: " + service)
        threads = []
        times = []
        times_plots = []

        lambda_func(service, load)

        print("=====================" + serviceNames[services.index(service)] + "=====================", file=output_file, flush=True)
        print(mean(times), file=output_file, flush=True)
        print(median(times), file=output_file, flush=True)
        print(np.percentile(times, 90), file=output_file, flush=True)
        print(np.percentile(times, 95), file=output_file, flush=True)
        print(np.percentile(times, 99), file=output_file, flush=True)

        plot_results(times_plots, "./plots/" + str(load) + "_functions", serviceNames[services.index(service)])
