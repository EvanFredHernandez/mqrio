"""Thin wrapper around TensorFlow logic."""
from learner.config import *
import learner.graph as graph
import tensorflow as tf


class QNet(object):
    """A deep network Q-approximator implemented with TensorFlow.

    The network is structure is fixed, aside from the output width, which depends
    on the number of actions necessary to play a given game.
    """

    def __init__(self, output_width):
        """Initializes the TensorFlow graph.

        Args:
            output_width: The number of output units.
        """
        self.graph_in, self.graph_out = graph.construct_graph(output_width)

        self.target_reward = tf.placeholder(tf.float32)
        self.action_idxs = tf.placeholder(tf.int32)
        actual_reward = tf.gather_nd(self.graph_out, self.action_idxs)
        self.loss = tf.reduce_mean(
            tf.square(self.target_reward - actual_reward))
        self.optimizer = tf.train.AdamOptimizer(LEARNING_RATE).minimize(self.loss)

        self.sess = tf.Session()
        self.sess.run(tf.global_variables_initializer())

        self.saver = tf.train.Saver()

    def __del__(self):
        """Closes the TensorFlow session, freeing resources."""
        self.sess.close()

    def compute_q(self, net_in):
        """Forward-propagates the given input and returns the array of outputs.

        Args:
            net_in: Image to forward-prop through the network. Must be 1x84x84x4.

        Returns:
            The array of network outputs.
        """
        return self.sess.run(self.graph_out, feed_dict={self.graph_in:[net_in]})[0]

    def update(self, batch_frames, batch_actions, batch_targets):
        """Updates the network with the given batch input/target values using RMSProp.

        Args:
            batch_frames: Set of Nx84x84x4 network inputs, where N is the batch size.
            batch_actions: Set of N action indices, representing action taken at each state.
            batch_target: Corresponding target Q values for each input.
        """
        # Note: Action indicies must actually be tuples since graph_out is a 2D tensor.
        # To prevent tight coupling, modify the batch_actions list here.
        return self.sess.run(
            [self.optimizer, self.loss],
            feed_dict={
                self.graph_in:batch_frames,
                self.action_idxs:[tup for tup in enumerate(batch_actions)],
                self.target_reward:batch_targets})[1]
