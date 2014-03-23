#!/usr/bin/python

# Neural Network
# -- nn.py
#
# @package NeuralNetwork
# @author Jeff Hubbard

import Queue
import random
import math

NUM_INPUTS = 5
NUM_HIDDEN = 5
NUM_OUTPUTS = 5

test_input = [ .0, .3, .6, .2, .8 ]

class Node:

    def __init__(self):
        self.connected_edges = []

    def sigmoid(self, num):
        return 1/(1+(math.e**-num))

class InputNode(Node):

    def __init__(self):
        self.input = Queue.Queue()

class HiddenNode(Node):

    def __init__(self):
        self.values = []
        self.final = 0

    def activate(self):
        sum = 0

        for value in self.values:
            sum += value

        return self.sigmoid(sum)

class OutputNode(Node):

    def __init__(self):
        self.values = []

    def checkThreshold(self):
        sum = 0

        for value in self.values:
            sum += value

        fin = self.sigmoid(sum)
        if fin < 0.5:
            return 0
        else:
            return 1

def initEdgeWeights(nodes):
    random.seed()

    for node in nodes:
        node.connected_edges = [ random.uniform(-1.0, 1.0) for x in range(NUM_INPUTS) ]

def recvInputVector(input, input_nodes):
    for i in range(NUM_INPUTS):
        input_nodes[i].input.put(input[i])

def start(inputs, hidden, outputs):
    for input in inputs:
        val = input.input.get()

        for i in range(5):
            hidden[i].values.append(input.connected_edges[i] * val)

    for node in hidden:
        node.final = node.activate()

        for i in range(5):
            outputs[i].values.append(node.connected_edges[i] * node.final)

    for out in outputs:
        print out.checkThreshold()

def main():
    # initialize all node objects
    input_nodes = [ InputNode() for x in range(NUM_INPUTS) ]
    hidden_nodes = [ HiddenNode() for x in range(NUM_HIDDEN) ]
    output_nodes = [ OutputNode() for x in range(NUM_OUTPUTS) ]

    # create the weights
    initEdgeWeights(input_nodes)
    initEdgeWeights(hidden_nodes)

    # initialize input nodes with test data
    recvInputVector(test_input, input_nodes)

    # and begin (sequentially for now)
    start(input_nodes, hidden_nodes, output_nodes)

if __name__ == "__main__":
    main()
