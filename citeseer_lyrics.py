import mme
import tensorflow as tf
import datasets
import numpy as np
import os
from itertools import product
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

tf.get_logger().setLevel('ERROR')

base_savings = os.path.join("savings", "citeseer")
pretrain_path = os.path.join(base_savings,"pretrain")
posttrain_path = os.path.join(base_savings,"posttrain")

def main(lr,seed,perc_soft=0,l2w=0.1, w_rule=0.0001, test_size=0.5):



    (x_train, hb_train), (x_test, hb_test) = datasets.citeseer(test_size)
    num_examples = len(x_train)
    num_examples_test = len(x_test)
    num_classes = 6

    indices = np.reshape(np.arange(num_classes * num_examples),
                         [num_classes, num_examples]).T  # T because we made classes as unary potentials

    indices_test = np.reshape(np.arange(num_classes * num_examples_test),
                         [num_classes, num_examples_test]).T  # T because we made classes as unary potentials

    #I set the seed after since i want the dataset to be always the same
    np.random.seed(seed)
    tf.random.set_seed(seed)

    m_e = np.zeros_like(hb_train)
    m_e[:, num_examples*num_classes:] = 1


    nn = tf.keras.Sequential()
    nn.add(tf.keras.layers.Input(shape=(x_train.shape[1],)))
    nn.add(tf.keras.layers.Dense(50, activation=tf.nn.sigmoid, kernel_regularizer=tf.keras.regularizers.l2(l2w)))  # up to the last hidden layer
    nn.add(tf.keras.layers.Dense(num_classes, use_bias=False))

    adam = tf.keras.optimizers.Adam(lr=0.001)



    def training_step():
        with tf.GradientTape() as tape:
            neural_logits = nn(x_train)
            total_loss = tf.reduce_mean(
                tf.nn.softmax_cross_entropy_with_logits(labels=tf.gather(hb_train[0], indices),
                                                        logits=neural_logits))+ tf.reduce_sum(nn.losses)


        grads = tape.gradient(target=total_loss, sources=nn.variables)
        grad_vars = zip(grads, nn.variables)
        adam.apply_gradients(grad_vars)



    epochs = 300
    y_test = tf.gather(hb_test[0], indices_test)
    for e in range(epochs):
        training_step()
        y_nn = nn(x_test)
        acc_nn = tf.reduce_mean(tf.cast(tf.equal(tf.argmax(y_test, axis=1), tf.argmax(y_nn, axis=1)), tf.float32))
        print(acc_nn)



    """Inference"""

    m_e = np.zeros_like(hb_test)
    m_e[:, num_examples_test*num_classes:] = 1

    """Logic Program Definition"""
    o = mme.Ontology()

    # Domains
    docs = mme.Domain("Documents", data=x_train)
    o.add_domain([docs])

    # Predicates

    preds = ["ag", "ai", "db", "ir", "ml", "hci"]
    for name in preds:
        p = mme.Predicate(name, domains=[docs])
        o.add_predicate(p)

    cite = mme.Predicate("cite", domains=[docs, docs], given=True)
    o.add_predicate(cite)

    # Logical
    constraints = []
    for name in preds:
        c = mme.Formula(definition="%s(x) and cite(x,y) -> %s(y)" % (name, name), ontology=o)
        constraints.append(c)


    adam2 = tf.keras.optimizers.Adam(lr=lr)

    steps_map = 100

    # Recreating an mme scenario
    mutual = mme.potentials.MutualExclusivityPotential(indices)

    prior = tf.nn.softmax(nn(x_test))
    y_bb = tf.Variable(initial_value=0.5 * tf.ones_like(prior))
    max_beta_me = 2

    lambda_0 = 100

    def make_hb_with_model(neural_softmax, hb_all):
        new_hb = tf.concat(
            (tf.reshape(tf.transpose(neural_softmax, [1, 0]), [1, -1]), hb_all[:, num_examples_test * num_classes:]), axis=1)
        return new_hb


    def map_inference_step(i):

        with tf.GradientTape() as tape:
            y_map = tf.sigmoid(10 * (y_bb - 0.5))
            hb_model_test = make_hb_with_model(y_map, hb_test)
            groundings = c.ground(herbrand_interpretation=hb_model_test)
            inference_loss = w_rule * tf.reduce_mean(- c.compile(groundings, mme.logic.LukasiewiczLogic)) \
                             + lambda_0 * tf.reduce_mean(tf.square(prior - y_bb)) \
                             +(max_beta_me - max_beta_me*(steps_map - i)*steps_map)* tf.reduce_sum(- mutual.call_on_groundings(y_map))

        grads = tape.gradient(target=inference_loss, sources=y_bb)
        grad_vars = [(grads, y_bb)]
        adam2.apply_gradients(grad_vars)

    for e in range(steps_map):
        map_inference_step(e)
        acc_map = tf.reduce_mean(tf.cast(tf.equal(tf.argmax(y_test, axis=1), tf.argmax(y_bb, axis=1)), tf.float32))
        print(acc_map)
        if mme.utils.heardEnter(): break
    acc_map = tf.reduce_mean(tf.cast(tf.equal(tf.argmax(y_test, axis=1), tf.argmax(y_bb, axis=1)), tf.float32))

    return acc_nn, acc_map


if __name__ == "__main__":
    seed = 0

    res = []
    for a  in product([10,100], [0.01], [0.9, 0.75, 0.5, 0.25, 0.1]):
        w_rule, lr, test_size = a
        acc_map, acc_nn = main(lr=lr, seed=seed, w_rule=w_rule, l2w=0.001, test_size=test_size)
        acc_map, acc_nn = acc_map.numpy(), acc_nn.numpy()
        res.append("\t".join([str(a) for a in [w_rule, lr, acc_map, str(acc_nn)+"\n"]]))
        for i in res:
            print(i)

    with open("res_citeseer_lyrics_%d"%seed, "w") as file:
        file.write("perc, lr, acc_map, acc_nn\n")
        file.writelines(res)




