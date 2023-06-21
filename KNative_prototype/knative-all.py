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

for serviceName in serviceNames:
    services.append(getUrlByFuncName(serviceName))

def plot_results(data, dst, service):
    x = []
    y = []
    colors = []

    for i, d in enumerate(data):
        x.extend([d['host_submit'], d['call_start'], d['call_done'], d['status_fetched']])
        y.extend([i + 1] * 4)
        colors.extend(['#E63946', '#FFC300', '#0077B6', '#FF9F1C'])  # Custom color palette

    x = [i - min(x) for i in x]

    plt.figure(figsize=(10, 6))  # Adjust the figure size as needed

    plt.scatter(x, y, c=colors, edgecolors='none', s=80, alpha=0.8)  # Remove marker borders

    # Create custom labels and colored rectangles for the legend
    legend_labels = ['Host Submit', 'Call Start', 'Call Done', 'Status Fetched']
    legend_colors = ['#E63946', '#FFC300', '#0077B6', '#FF9F1C']
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
        dst = os.path.expanduser(dst) if '~' in dst else dst
        dst = '{}_{}'.format(os.path.realpath(dst), service + '_timeline.png')

    plt.tight_layout()  # Improve spacing and layout
    plt.savefig(dst, dpi=300)
    plt.close('all')


def extract_times(data, times_plot):
    global times_plots

    times_plot["call_start"] = data['times_plot']['call_start']
    times_plot["call_done"] = data['times_plot']['call_done']

    times_plots.append(times_plot)


def lambda_func(service, host_submit):
    global times
    times_plot = {}

    t1 = time.time()

    # Plot
    times_plot["host_submit"] = host_submit

    r = requests.post(service, json={"name": "test"})

    # Plot
    times_plot["status_fetched"] = time.time()

    print(r.text)
    t2 = time.time()
    times.append(t2-t1)

    # Plot
    try:
        extract_times(json.loads(r.text), times_plot)
    except:
        pass

def EnforceActivityWindow(start_time, end_time, instance_events):
    events_iit = []
    events_abs = [0] + instance_events
    event_times = [sum(events_abs[:i]) for i in range(1, len(events_abs) + 1)]
    event_times = [e for e in event_times if (e > start_time)and(e < end_time)]
    try:
        events_iit = [event_times[0]] + [event_times[i]-event_times[i-1]
                                         for i in range(1, len(event_times))]
    except:
        pass
    return events_iit

loads = [1, 5, 10, 15]

output_file = open("run-all-out.txt", "w")

indR = 0
for load in loads:
    duration = 1
    seed = 100
    rate = load
    # generate Poisson's distribution of events 
    inter_arrivals = []
    np.random.seed(seed)
    beta = 1.0/rate
    oversampling_factor = 2
    inter_arrivals = list(np.random.exponential(scale=beta, size=int(oversampling_factor*duration*rate)))
    instance_events = EnforceActivityWindow(0,duration,inter_arrivals)
        
    for service in services:
        
        threads = []
        times = []
        after_time, before_time = 0, 0
        times_plots = []

        st = 0
        for t in instance_events:
            st = st + t - (after_time - before_time)
            before_time = time.time()
            if st > 0:
                time.sleep(st)

            threadToAdd = threading.Thread(target=lambda_func, args=(service, time.time()))
            threads.append(threadToAdd)
            threadToAdd.start()
            after_time = time.time()

        for thread in threads:
            thread.join()

        print("=====================" + serviceNames[services.index(service)] + "=====================", file=output_file, flush=True)
        print(mean(times), file=output_file, flush=True)
        print(median(times), file=output_file, flush=True)
        print(np.percentile(times, 90), file=output_file, flush=True)
        print(np.percentile(times, 95), file=output_file, flush=True)
        print(np.percentile(times, 99), file=output_file, flush=True)

        plot_results(times_plots, "./plots/" + str(load) + "_functions", serviceNames[services.index(service)])