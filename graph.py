#!/usr/bin/env python3

import sys
import re

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FormatStrFormatter

## create regex for getting data
data_regex = re.compile(r"""(\d+)\s*([\d\.]+) ns\/op$""")

## specific_regex is used to get information specific to this test, e.g. the series label, the value of N, etc.
specific_regex = re.compile(r"""^BenchmarkIPSizes\/([\w_]+),n=(\d+)\/""")
label_index = 0
n_index = not label_index ## if label_index is 1, n_index is automatically 0

## graph_regex is used to differentiate between different graphs
## set to None if you only have one graph
graph_regex = re.compile(r"""^BenchmarkIPSizes\/[\w_]+,n=\d+\/([\w_]+)""")
graph_index = 0

if __name__ == "__main__":

    ## data["graph"]["label"] = np.array
    data = {}

    ## read data from stdin (so tests can be piped in)
    for line in sys.stdin:
        ## identify the data
        match = data_regex.search(line)
        if match is None:
            print("Ignoring non-matching line:", line)
            continue
        groups = match.groups()
        
        to_add = [float(d) for d in list(groups)]

        ## identify the label and N value
        match = specific_regex.search(line)
        if match is None:
            print("Ignoring non-matching line:", line)
            continue
        groups = match.groups()

        label = groups[label_index].replace("_", " ")
        N = float(groups[n_index])
        to_add = [N]+to_add

        ## identify the graph name
        if graph_regex is not None:
            match = graph_regex.search(line)
            if match is None:
                print("Ignoring non-matching line:", line)
                continue
            groups = match.groups()

            graph = groups[graph_index].replace("_", " ")
        else:
            graph = ""
            
        ## add to the data set
        if graph not in data:
            data[graph] = {}
        if label not in data[graph]:
            data[graph][label] = []
        data[graph][label].append(to_add)

    ## make into numpy arrays
    for key in data.keys():
        for k, val in data[key].items():
            data[key][k] = np.array(val)
    ## data has structure [n, iterations, time (ns)]

    ###################
    # generate a plot #
    ###################
    fig = plt.figure(figsize=(12*len(data), 12))

    ## construct a gridspec for this data
    gs = gridspec.GridSpec(1,len(data))

    ## do the graphs in graph name order
    graph_names = sorted([k for k in data.keys()], key=lambda x:x.lower())

    for g in range(len(data)):
        ## Add next plot
        ax = fig.add_subplot(gs[g])

        graph_name = graph_names[g]

        ## Iterate through all the data for this graph
        for key in data[graph_name].keys():
            ax.plot(data[graph_name][key][:,0], data[graph_name][key][:,2], "o-", label=key)
            
            ax.legend()
            ax.set_title(graph_name)
            ax.set_xlabel("N")
            ax.set_ylabel("Time Taken, $ns$")
            ax.set_xscale("log")
            
    plt.savefig("graph.png")
    # plt.show()
