# Neural Network
# -- nn.py
#
# @package NeuralNetwork

# ------------------------ ATTENTION, MORTALS: README ------------------------
# I will now describe how the code is organized so anyone interested in it can
# quickly get up to speed.
#
# Being a neural network, there needs to be some number of nodes and some number
# of edges. However, rather than using an explicit node class or explicit edges,
# I simplified it by just having a "Layer" class that represents all the nodes
# in a given layer (as in input, hidden, output) and all the edges leaving that
# layer. So: the layer class handles all nodes and edges in a layer and the
# "activation" of a layer activates all nodes inside it.
#
# Now, to be more orthogonal, I made it so that the activation essentially just
# takes the input (from the previous layer, or the nn input itself) and applies
# some process to it, resulting in an output list. In general, this means
# activating the "nodes" as one would expect. The exception to this is the
# OutputLayer class which just transforms it's input into either 0 or 1.
#
# The layers are organized by the NeuralNetwork class which creates "n" layers
# given a list of "n" integers where the integer value is the number of nodes in
# a given layer. So [3, 5, 2] makes 3 layers with the input of size 3, hidden
# of size 5, and output of size 2. It automatically makes the last layer the
# output layer and links them all up when the feedForward method is called
# (output of one is input to the next). The feedForward method returns the
# results of the last (output) layer.
#
# ------------------------ NOTES ON THE PARALLEL VERSION------------------------
#
# The parallel version uses java's concurrent classes. It makes a global
# threadpool to handle tasks. Currently the activation of a layer is done in
# parallel by making a new task for each "node" to be activated. Because all
# nodes in a layer must finish activating before moving on, it calls the .get()
# method on all the futures returned by the threadpool's .invokeAll() method.
# Because .get() on a Future is blocking until it has the value, this is like
# joining on a thread, but without causing the thread to die.
#
# At the end of the program, the threadpool has to be shutdown or else the
# program will not quit.

# ------------------------ NOTES TO DIEGO!!! ------------------------
# I've included running the profiler as an option. I recommend it since it
# will show the time taken to run various functions. In this file, one of
# the "__init__" will take a long time because it creates a lot of values
# with random which is slow. This should probably be disregarded. Essentially
# the only thing that matters is how long the various "activation" functions
# take.
#
# Feel free to play around with the various parameters for different test cases.
# For instance, when there aren't many nodes, the parallel version is REALLY slow
# compared to the sequential one, but as you start bumping up the number of nodes,
# the difference isn't as big. (So we can say it's not practical for small networks)
#
# Also, you can create more than just 3 layers. The "LAYERS" global variable is a
# list of the number of nodes in each layer. Just adding more numbers increases the
# number of layers automagically. So [5, 5, 5] makes a NN with 3 layers, but
# [5, 5, 4, 5] makes it with 4 layers! woot!
#
# Just be sure that the number of layers and the number of nodes in each layer
# is the same in both "sequential_nn.py" and "parallel_nn.py". Triple check.
# I've already made the mistake of them not being the same too many times...
#
# Last minute addition! I added "pipelining" as a parallelization technique. The idea
# is that in the general use case, the neural network is ONLY feedforward (as in, if
# it's not learning, it doesn't use backpropagation). That means that two executions
# of the network do not rely on each other. So, in theory, you can immediately start
# the next feedforward operation as soon as you receive the input (i.e. from the game)
# So you would have multiple feedforward operations happening at the same time! woo!
# I tested, and, oddly, it seems like pipelining it is slower...

import random
import math
import threading
import operator
import java.util.concurrent

# Try doing tests with 3000+ input/hidden nodes (but only like 5 tests)
# Also try doing it with less nodes but a lot more tests
# and remember to use the parallel "technique" toggles below

NUM_THREADS = 8
NUM_TESTS = 300
NUM_INPUTS = 1000
NUM_HIDDEN = 1200
NUM_OUTPUTS = 1
LAYERS = [NUM_INPUTS, NUM_HIDDEN, NUM_OUTPUTS]
USE_BACKPROPAGATE = False
USE_PROFILE = True

# These are the two "parallel" techniques
# Turning both off should give the same performance as sequential_nn.py
USE_PIPELINING = True
USE_LOW_LEVEL_TASKS = True

threadpool = java.util.concurrent.Executors.newFixedThreadPool(NUM_THREADS)

class Layer(object):

    def activate(self, inputs):
        return inputs

    @staticmethod
    def sigmoid(num):
        return math.tanh(num)

    @staticmethod
    def derivSig(num):
        return 1 - math.tanh(num) ** 2

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

        if USE_LOW_LEVEL_TASKS:
            outputs = [ None ] * len(self.weight_matrix)
            def activate_one_node(index, weights):
                # This computes the dot product of two "vectors" (lists here)
                dot_product = sum(map(operator.mul, inputs, weights))
                output = self.sigmoid(dot_product)
                outputs[index] = output

            callables = []
            for index, weights in enumerate(self.weight_matrix):
                callables.append(MakeCallable(activate_one_node, index, weights))

            futures = threadpool.invokeAll(callables)
            # It's like "join"ing
            for future in futures:
                future.get()
        else:
            outputs = []
            for weights in self.weight_matrix:
                # This computes the dot product of two "vectors" (lists here)
                dot_product = sum(map(operator.mul, inputs, weights))
                output = self.sigmoid(dot_product)
                outputs.append(output)

        return outputs

class MakeCallable(java.util.concurrent.Callable):

    def __init__(self, fn, *args):
        self.fn = fn
        self.args = args

    def call(self):
        return self.fn(*self.args)

class NeuralNetwork(object):

    def __init__(self, nodes_per_layer):
        self.layers = []
        for num_nodes, num_edges in zip(nodes_per_layer[:-1], nodes_per_layer[1:]):
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
    # print inputs
    # print desired_outputs

    # initialize the neural network
    nn = NeuralNetwork(LAYERS)

    if USE_PIPELINING:
        # The idea is that we can start processing the next set of
        # inputs from the game even before the old ones are finished.
        # So it's like a processor pipeline.
        class NN_Runner(java.util.concurrent.Callable):
            def __init__(self, i):
                self.i = i
            def call(self):
                return (self.i, nn.feedForward(inputs))

        output_futures = threadpool.invokeAll([ NN_Runner(i) for i in range(NUM_TESTS) ])
        for i, future in enumerate(output_futures):
            print "Test number {} -> ".format(i), future.get()
    else:
        for i in range(NUM_TESTS):
            output = nn.feedForward(inputs)
            if USE_BACKPROPAGATE:
                error = nn.backPropagate(desired_outputs)

            print "Test number {} -> ".format(i), output

    threadpool.shutdown()

if __name__ == "__main__":
    if USE_PROFILE:
        import profile
        profile.run('main()')
    else:
        main()

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
