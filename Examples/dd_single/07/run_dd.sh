#!/bin/bash
# this example uses two strategies to determine the starting model:

test -d results && rm -r results
DD_STARTING_MODEL=1 dd_single.py -f frequencies.dat -d data.dat -n 20 -o results --tausel data_ext\
    --nr_cores=1\
    --tausel data_ext\
    --lambda 1.0\
    --plot -c 1 --max_it 20 --plot_its

test -d results3 && rm -r results3
DD_STARTING_MODEL=3 dd_single.py -f frequencies.dat -d data.dat -n 20 -o results3 --tausel data_ext\
    --nr_cores=1\
    --tausel data_ext\
    --lambda 1.0\
    --plot -c 1 --max_it 20 --plot_its
