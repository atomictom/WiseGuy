# Neural Network
# -- nn.py
#
# @package NeuralNetwork

import random
import math
import threading
import operator

NUM_THREADS = 1
NUM_TESTS = 100
NUM_INPUTS = 50
NUM_HIDDEN = 30
NUM_OUTPUTS = 50
USE_BACKPROPAGATE = False

class Layer(object):

    def activate(self, inputs):
        return inputs

    @staticmethod
    def sigmoid(num):
        return math.tanh(num)

class OutputLayer(Layer):

    def activate(self, inputs):
        return [ int(round(value / 2 + .5)) for value in inputs ]

class InnerLayer(Layer):

    def __init__(self, num_nodes, num_edges):
        # A list of lists
        # The rows correspond to the number of edges per node (number of nodes
        # in the next layer).
        # The columns correspond to the number of nodes in the current layer
        self.weight_matrix = []

        # Initialize the weights for each node
        random.seed()
        for row in range(num_edges):
            self.weight_matrix.append([ random.uniform(-1.0, 1.0) for edge in range(num_nodes) ])

    # TODO Parallelize this!
    def activate(self, inputs):
        """ Activate each neuron in the layer one at a time """
        outputs = []
        for weights in self.weight_matrix:
            # This computes the dot product of two "vectors" (lists here)
            dot_product = sum(map(operator.mul, inputs, weights))
            output = self.sigmoid(dot_product)
            outputs.append(output)

        return outputs

class NeuralNetwork(object):

    def __init__(self, nodes_per_layer):
        self.layers = []
        for num_nodes, num_edges in nodes_per_layer[:-1], nodes_per_layer[1:]:
            layer = InnerLayer(num_nodes, num_edges)
            self.layers.append(layer)

        output_layer = OutputLayer()
        self.layers.append(output_layer)

    def feedForward(self, inputs):
        # Process the inputs layer by layer until we have the final output
        for layer in self.layers:
            outputs = layer.activate(inputs)
            # Inputs to the next layer are outputs from the previous one
            inputs = outputs

        # 'outputs' is the output from the last layer...which is the output layer
        return outputs

    def backPropagate(desired_outputs):
        pass

def main():
    # Test Data
    inputs = [ random.random() for i in range(NUM_INPUTS) ]
    desired_outputs = [ random.choice([0, 1]) for i in range(NUM_OUTPUTS) ]
    print inputs
    print desired_outputs

    # initialize the neural network
    nn = NeuralNetwork([NUM_INPUTS, NUM_HIDDEN, NUM_OUTPUTS])

    for i in range(NUM_TESTS):
        output = nn.feedForward(inputs)
        if USE_BACKPROPAGATE:
            error = nn.backPropagate(desired_outputs)

        print output

if __name__ == "__main__":
    main()

# def derivSig(num):
#     #TODO: Might need to be `1 - tanh(num) ** 2`
#     return 1 - num**2
#
# def backPropagate(targets, inputs, hidden):
#     out_deltas = []
#     for i in range(NUM_OUTPUTS):
#         error = targets[i] - OUTPUTS[i]
#         out_deltas.append(error * derivSig(OUTPUTS[i]))
#
#     for i in range(NUM_HIDDEN):
#         for j in range(NUM_OUTPUTS):
#             delta = out_deltas[j] * hidden[i].final
#             hidden[i].weights[j] += .5 * delta
#
#     hidden_deltas = []
#     for i in range(NUM_HIDDEN):
#         error = 0
#         for j in range(NUM_OUTPUTS):
#             error += out_deltas[j] * hidden[i].weights[j]
#         hidden_deltas.append(error * derivSig(hidden[i].final))
#
#     for i in range(NUM_INPUTS):
#         for j in range(NUM_HIDDEN):
#             delta = hidden_deltas[j] * hidden[j].last_input
#             inputs[i].weights[j] += .5 * delta
#
#     error = 0
#     for i in range(len(targets)):
#         error += .5 * (targets[i] - OUTPUTS[i])**2
#
#     return error

# vim:ts=4:sw=4:sta:et:
