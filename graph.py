#!/usr/bin/env python3

# pylint: disable=invalid-name

"""\
Golang Benchmark Grapher

This program parses the output of go test and uses matplotlib to
create useful graphs to compare benchmarks. It allows for mutliple
graphs to be produced in the same figure if multiple benchmarks are
being performed, and can parse line labels from the tests to
differentiate between different methods on the same graph. These are
all configured through regex + formatting strings.

Your regex should match the test names you wish to graph. The times
will be automatically extracted, but other data must be configured:

    * Put {N} in your regex to indicate where the value of N can be
      found.
    * Put {label} in your regex to indicate where the line labels can
      be found.
    * Put {graph} in your regex to indicate where the graph titles can
      be found.

{graph} is optional -- if it is not included, a default graph name
will be used.

Example: If your tests were named like this:
    TestGraph/TestLabel,N=N

    The regex you should supply is "Test{graph}\/Test{label},N={N}",
    and these fields should be successfully detected.

    Note the backslash preceeding the forward slash (/). This is
    necessary as the forward slash represents the pattern delimeter.


Pipe the output of "go test -bench" into this command, e.g.:
    go test -bench ./... | graph.py <regex>

Usage:
    graph.py <regex>

"""

import sys
import re

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

## create regex for getting data
data_regex = re.compile(r"""(\d+)\s*([\d\.]+) ns\/op$""")

ALLOWED_NAME_CHARS = "\w\d_"
ALLOWED_DIGIT_CHARS = "\d"

def format_regex(general_regex):
    """Takes a general regular expression and formats it into the three
required expressions. These are returned in the order: specific_regex,
label_regex, graph_regex

arg general_regex should contain three format tags: 

    {N} : This should be placed where the value of N can be found

    {label} : This should be placed where the line label can be found

    {graph} : (optional) This should be placed where the graph name
    can be found. If ommitted, the name "default" will be used.

    """
    disable_graph = False
    if "{graph}" not in general_regex:
        disable_graph = True
        general_regex += "{graph}"

    specific_regex = re.compile(general_regex.format(N="(["+ALLOWED_DIGIT_CHARS+"]+)",
                                                     label="["+ALLOWED_NAME_CHARS+"]+",
                                                     graph=("["+ALLOWED_NAME_CHARS+"]+") if not disable_graph else ""))
    label_regex = re.compile(general_regex.format(N="["+ALLOWED_DIGIT_CHARS+"]+",
                                                  label="(["+ALLOWED_NAME_CHARS+"]+)",
                                                  graph=("["+ALLOWED_NAME_CHARS+"]+") if not disable_graph else ""))
    graph_regex = re.compile(general_regex.format(N="["+ALLOWED_DIGIT_CHARS+"]+",
                                                  label="["+ALLOWED_NAME_CHARS+"]+",
                                                  graph=("(["+ALLOWED_NAME_CHARS+"]+)"))) if not disable_graph else None

    return specific_regex, label_regex, graph_regex

if __name__ == "__main__":
    from docopt import docopt

    args = docopt(__doc__)
    # print(args)

    regex = args["<regex>"]
    specific_regex, label_regex, graph_regex = format_regex(regex)

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

        ## identify the N value
        match = specific_regex.search(line)
        if match is None:
            print("Ignoring non-matching line:", line)
            continue
        groups = match.groups()

        N = float(groups[0])
        to_add = [N]+to_add

        ## identify the label
        match = label_regex.search(line)
        if match is None:
            print("Ignoring non-matching line:", line)
            continue
        groups = match.groups()

        label = groups[0].replace("_", " ")

        ## identify the graph name
        if graph_regex is not None:
            match = graph_regex.search(line)
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
