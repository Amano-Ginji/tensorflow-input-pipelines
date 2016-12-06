##############################################################################
# Author:       Imanol Schlag (more info on ischlag.github.io)
# Description:  TensorFlow building blocks for models.
# Date:         11.2016
#
#

import tensorflow as tf
import numpy as np

def dense(data, 
          n_units,
          phase_train,
          activation,
          scope,
          initializer,
          dropout=True):
  """ Fully-connected network layer."""
  shape = data.get_shape().as_list()
  print("DENSE IN: ",  data)
  with tf.variable_scope(scope):
    #w = tf.get_variable('dense-weights',
    #                    [shape[1], n_units],
    #                    initializer=initializer)
    w = tf.Variable(tf.random_normal([shape[1], n_units], stddev=0.01),
                    name='dense-weights')
    b = tf.get_variable('dense-bias',
                        [n_units],
                        initializer=tf.zeros_initializer)
    dense = activation(tf.matmul(data, w) + b)
    if dropout:
      dense = tf.cond(phase_train, lambda: tf.nn.dropout(dense, 0.5), lambda: dense)

    print("DENSE OUT:", dense)
    return dense

def flatten(pre):
  """ Flattens the 2d kernel images into a single vector. Ignore the batch dimensionality."""
  pre_shape = pre.get_shape().as_list()
  print("FLAT IN:  ", pre)
  flat = tf.reshape(pre, [pre_shape[0], pre_shape[1] * pre_shape[2] * pre_shape[3]])
  print("FLAT OUT: ", flat)
  return flat

def conv2d(data, 
           n_filters,
           scope,
           initializer,
           k_h=3, k_w=3,
           stride_h=1, stride_w=1,
           bias=True,
           padding='SAME'):
  """ Convolutional layer implementation without an activation function"""
  with tf.variable_scope(scope):
    print("CONV IN:  ", data)
    #w = tf.get_variable('conv-weights',
    #                    [k_h, k_w, data.get_shape()[-1], n_filters],
    #                    initializer=initializer)
    w = tf.Variable(tf.random_normal([int(k_h), int(k_w), int(data.get_shape()[-1]), int(n_filters)], stddev=0.01),
                    name='conv-weights')
    conv = tf.nn.conv2d(data, w,
                        strides=[1, stride_h, stride_w, 1],
                        padding=padding)
    b = tf.get_variable('conv-bias',
                        [n_filters],
                        initializer=tf.zeros_initializer)
    conv = tf.nn.bias_add(conv, b)
    print("CONV OUT: ", conv)
    return conv


def batch_norm(x, n_out, phase_train, scope='bn'):
  """
  Batch normalization on convolutional maps.
  Args:
      x:           Tensor, 4D BHWD input maps
      n_out:       integer, depth of input maps
      phase_train: boolean tf.Varialbe, true indicates training phase
      scope:       string, variable scope
  Return:
      normed:      batch-normalized maps

  Note:
    Source is http://stackoverflow.com/questions/33949786/how-could-i-use-batch-normalization-in-tensorflow
  """
  #print("BNORM IN: ", x)
  with tf.variable_scope(scope):
    beta = tf.Variable(tf.constant(0.0, shape=[n_out]),
                        name='beta', trainable=True)
    gamma = tf.Variable(tf.constant(1.0, shape=[n_out]),
                        name='gamma', trainable=True)
    batch_mean, batch_var = tf.nn.moments(x, [0,1,2], name='moments')
    ema = tf.train.ExponentialMovingAverage(decay=0.5)

    def mean_var_with_update():
      ema_apply_op = ema.apply([batch_mean, batch_var])
      with tf.control_dependencies([ema_apply_op]):
        return tf.identity(batch_mean), tf.identity(batch_var)

    mean, var = tf.cond(phase_train,
                        mean_var_with_update,
                        lambda: (ema.average(batch_mean), ema.average(batch_var)))
    normed = tf.nn.batch_normalization(x, mean, var, beta, gamma, 1e-3)

  #print("BNORM OUT:", normed)
  return normed

def push_into_queue(value, queue, tag, step, writer):
  """Pushes new values into a queue of fixed length and writes the average of that queue into a summary operation."""
  queue.pop()
  queue.appendleft(value)
  avg = np.mean(queue).item()
  avg_summary = tf.Summary(value=[tf.Summary.Value(tag=tag, simple_value=avg)])
  writer.add_summary(avg_summary, global_step=step)
  return avg