#!/usr/bin/env python3

"""

"""

import sys
import re

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

## create regex for getting data
DATA_REGEX = re.compile(r"""(\d+)\s*([\d\.]+) ns\/op$""")

## N_VALUE_REGEX is used to get the value of N, etc.
N_VALUE_REGEX = re.compile(r"""^BenchmarkIPSizes\/[\w_]+,n=(\d+)\/""")

## LABEL_REGEX is used to get the label for the line
LABEL_REGEX = re.compile(r"""^BenchmarkIPSizes\/([\w_]+),n=\d+\/""")

## GRAPH_REGEX is used to differentiate between different graphs
## set to None if you only have one graph
GRAPH_REGEX = re.compile(r"""^BenchmarkIPSizes\/[\w_]+,n=\d+\/([\w_]+)""")

if __name__ == "__main__":

    ## data["graph"]["label"] = np.array
    data = {}

    ## read data from stdin (so tests can be piped in)
    for line in sys.stdin:
        ## identify the data
        match = DATA_REGEX.search(line)
        if match is None:
            print("Ignoring non-matching line:", line)
            continue
        groups = match.groups()
        
        to_add = [float(d) for d in list(groups)]

        ## identify the N value
        match = N_VALUE_REGEX.search(line)
        if match is None:
            print("Ignoring non-matching line:", line)
            continue
        groups = match.groups()

        N = float(groups[0])
        to_add = [N]+to_add

        ## identify the label
        match = LABEL_REGEX.search(line)
        if match is None:
            print("Ignoring non-matching line:", line)
            continue
        groups = match.groups()

        label = groups[0].replace("_", " ")

        ## identify the graph name
        if GRAPH_REGEX is not None:
            match = GRAPH_REGEX.search(line)
            if match is None:
                print("Ignoring non-matching line:", line)
                continue
            groups = match.groups()

            graph = groups[0].replace("_", " ")
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
    fig = plt.figure(figsize=(12 * len(data), 12))

    ## construct a gridspec for this data
    gs = gridspec.GridSpec(1, len(data))

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
