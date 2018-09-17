import tensorflow as tf
import numpy as np
from tensorflow.core.protobuf import saver_pb2
import cnn_model
import data_handler

import os

class ModelTrainer:
    def __init__(self, epochs = 30, val_split=0.2, L2_norm_const = 0.001, batch_size=100, logs_path='./logs', model_save_path='./save', data_path='./data', data_desc_file='driving_log.csv', contains_full_path=False):
        self.epochs = epochs
        self.val_split = val_split
        self.L2_norm_const = L2_norm_const
        self.batch_size = batch_size

        self.logs_path = logs_path
        self.model_save_path = model_save_path

        # initialize saver
        self.saver = tf.train.Saver(write_version=saver_pb2.SaverDef.V1)

        # op to write logs to Tensorboard
        self.summary_writer = tf.summary.FileWriter(logs_path, graph=tf.get_default_graph())

        self.data_handler = data_handler.DataHandler(data_path, data_desc_file, contains_full_path)

        self.sess = tf.InteractiveSession()


    def train_model(self):

        train_vars = tf.trainable_variables()
        loss = tf.reduce_mean(tf.square(tf.subtract(cnn_model.y_in, cnn_model.y))) + tf.add_n(
            [tf.nn.l2_loss(v) for v in train_vars]) * self.L2_norm_const
        train_step = tf.train.AdamOptimizer(1e-4).minimize(loss)

        self.sess.run(tf.global_variables_initializer())

        tf.summary.scalar("loss", loss)
        merged_summary_op = tf.summary.merge_all()

        train_data, val_data = self.data_handler.generate_data_splits(self.val_split)

        iterations = []
        loss_values = []

        for epoch in range(self.epochs):
            print("Epoch " + str(epoch))

            for iteration in range(int(len(train_data) / self.batch_size)):

                train_data_batch_x, train_data_batch_y = self.data_handler.get_train_batch(self.batch_size)

                train_step.run(feed_dict={cnn_model.x: train_data_batch_x,
                                          cnn_model.y_in: np.expand_dims(train_data_batch_y, axis=1),
                                          cnn_model.keep_prob: 0.8})


                if iteration % 10 == 0:
                    val_batch_x, val_batch_y = self.data_handler.get_val_batch(self.batch_size)

                    loss_value = loss.eval(feed_dict={cnn_model.x: val_batch_x,
                                          cnn_model.y_in: np.expand_dims(val_batch_y, axis=1),
                                          cnn_model.keep_prob: 1.0})
                    print("Epoch: %d, Step: %d, Loss: %g" % (epoch, epoch * self.batch_size + iteration, loss_value))

                    loss_values.append(loss_value)
                    iterations.append(epoch * self.batch_size + iteration)


                # write logs at every iteration
                summary = merged_summary_op.eval(feed_dict={cnn_model.x: train_data_batch_x,
                                          cnn_model.y_in: np.expand_dims(train_data_batch_y, axis=1), cnn_model.keep_prob: 1.0})
                self.summary_writer.add_summary(summary, epoch * len(train_data) + iteration)


            self.save_model_iteration()


    def plot_loss_values(self,):

    def save_model_iteration(self):
        if not os.path.exists(self.model_save_path):
            os.makedirs(self.model_save_path)

        checkpoint_path = os.path.join(self.model_save_path, "model.ckpt")
        filename = self.saver.save(self.sess, checkpoint_path)
        print("Model saved in file: %s" % filename)


if __name__ == '__main__':
    model_trainer = ModelTrainer(epochs=30, data_path='./data/augmented_data', data_desc_file='augmented_log.csv', contains_full_path = True)
    model_trainer.train_model()

