#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from simanneal import Annealer
import math
import random

from junction_simulator import TrafficSimulator


class TrafficAnnealer(Annealer):
    """Optimize the traffic light simulation for the minimal waiting time sum.

    """

    def __init__(self, state, args):
        self.args = args
        super().__init__(state)

    def move(self):
        parameter = random.randint(0, len(self.state)-1)
        change = random.choice([-0.1, 0.1])
        self.state[parameter] += change

    def energy(self):
        try:
            ts = TrafficSimulator(*(self.args + [self.state]))
            return ts.calculateSumWaitTime()
        except KeyboardInterrupt as e:
            raise e
        except:
            return float("inf")

def run_test(matrix):
    import pprint
    pp = pprint.PrettyPrinter()
    pp.pprint(matrix)
    traffic_annealer = TrafficAnnealer(
        [0.2, 0.2, 0.2, 0.2],
        args=[
            matrix,
            60 * 4,
            3,
            60,
        ],
    )
    x, y = traffic_annealer.anneal()
    print(x, y)

def main(argv=None):
    max_traffic = 1440
    traffic_matrix = [
        [
	        [0, 0.75 * max_traffic, 1.00 * max_traffic, 0.50 * max_traffic],
	        [0.75 * max_traffic, 0, 1.00 * max_traffic, 0.50 * max_traffic],
	        [0.25 * max_traffic, 0.25 * max_traffic, 0, 0.25 * max_traffic],
	        [0.25 * max_traffic, 0.25 * max_traffic, 0.50 * max_traffic, 0],
        ],
        [
	        [0, 0.50 * max_traffic, 0.25 * max_traffic, 0.25 * max_traffic],
	        [0.50 * max_traffic, 0, 0.50 * max_traffic, 0.25 * max_traffic],
	        [0.25 * max_traffic, 0.50 * max_traffic, 0, 0.25 * max_traffic],
	        [0.25 * max_traffic, 0.25 * max_traffic, 0.25 * max_traffic, 0],
        ],
        [
	        [0, 0.75 * max_traffic, 0.25 * max_traffic, 0.25 * max_traffic],
	        [0.75 * max_traffic, 0, 0.25 * max_traffic, 0.25 * max_traffic],
	        [1.00 * max_traffic, 1.00 * max_traffic, 0, 0.50 * max_traffic],
	        [0.50 * max_traffic, 0.50 * max_traffic, 0.25 * max_traffic, 0],
        ],
        [
	        [0, 0.25 * max_traffic, 0.05 * max_traffic, 0.05 * max_traffic],
	        [0.25 * max_traffic, 0, 0.05 * max_traffic, 0.05 * max_traffic],
	        [0.05 * max_traffic, 0.05 * max_traffic, 0, 0.05 * max_traffic],
	        [0.05 * max_traffic, 0.05 * max_traffic, 0.05 * max_traffic, 0],
        ],
    ]
    for m in traffic_matrix:
        run_test(m)

if __name__ == '__main__':
    from sys import argv
    main(argv)
