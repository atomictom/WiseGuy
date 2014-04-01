# Neural Network
# -- nn.py
#
# @package NeuralNetwork
# @author Jeff Hubbard

import Queue
import random
import math
import pickle
import zmq
import time

NUM_INPUTS = 3
NUM_HIDDEN = 3
NUM_OUTPUTS = 3
OUTPUTS = []

test_input = [ .0, .3, .6, .2, .8 ]

class Node:

    def __init__(self):
        self.connected_edges = []

    def sigmoid(self, num):
        return math.tanh(num)

class InputNode(Node):

    def __init__(self):
        self.input = Queue.Queue()

class HiddenNode(Node):

    def __init__(self):
        self.values = []
        self.final = 0
        self.last_input = None

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

def derivSig(num):
    return 1 - num**2

def run(inputs, hidden, outputs):
    for input in inputs:
        val = input.input.get()
        
        for i in range(NUM_HIDDEN):
            hidden[i].values.append(input.connected_edges[i] * val)
            hidden[i].last_input = val

    for node in hidden:
        node.final = node.activate()
        
        for i in range(NUM_OUTPUTS):
            outputs[i].values.append(node.connected_edges[i] * node.final)

    for out in outputs:
        OUTPUTS.append(out.checkThreshold())
    
def backPropagate(targets, inputs, hidden):
    out_deltas = []
    for i in range(NUM_OUTPUTS):
        error = targets[i] - OUTPUTS[i]
        out_deltas.append(error * derivSig(OUTPUTS[i]))

    for i in range(NUM_HIDDEN):
        for j in range(NUM_OUTPUTS):
            delta = out_deltas[j] * hidden[i].final
            hidden[i].connected_edges[j] += .5 * delta

    hidden_deltas = []
    for i in range(NUM_HIDDEN):
        error = 0
        for j in range(NUM_OUTPUTS):
            error += out_deltas[j] * hidden[i].connected_edges[j]
        hidden_deltas.append(error * derivSig(hidden[i].final))

    for i in range(NUM_INPUTS):
        for j in range(NUM_HIDDEN):
            delta = hidden_deltas[j] * hidden[i].last_input
            inputs[i].connected_edges[j] += .5 * delta
            
    error = 0
    for i in range(len(targets)):
        error += .5 * (targets[i] - OUTPUTS[i])**2

    return error  

def main():
    # initialize all node objects
    input_nodes = [ InputNode() for x in range(NUM_INPUTS) ]
    hidden_nodes = [ HiddenNode() for x in range(NUM_HIDDEN) ]
    output_nodes = [ OutputNode() for x in range(NUM_OUTPUTS) ]

    # create the weights
    initEdgeWeights(input_nodes)
    initEdgeWeights(hidden_nodes)

    context = zmq.Context()
    socket = context.socket(zmq.PAIR)
    socket.bind("tcp://*:4520")

    while True:
        global OUTPUTS

        new_inputs = socket.recv()
        try:
            new_inputs = pickle.loads(new_inputs)
        except:
            socket.send("SENT BAD DATA")

        # initialize input nodes with newest data
        recvInputVector(new_inputs, input_nodes)
        run(input_nodes, hidden_nodes, output_nodes)
        backPropagate([1, 0, 1], input_nodes, hidden_nodes)
        #print OUTPUTS
        socket.send(pickle.dumps(OUTPUTS))
        OUTPUTS = []
        
if __name__ == "__main__":
    main()
