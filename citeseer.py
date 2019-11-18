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

def main(lr,seed,lambda_0,l2w, test_size):



    (x_train, hb_train), (x_test, hb_test) = datasets.citeseer(test_size)
    num_examples = len(x_train)
    num_examples_test = len(x_test)
    num_classes = 6


    #I set the seed after since i want the dataset to be always the same
    np.random.seed(seed)
    tf.random.set_seed(seed)

    m_e = np.zeros_like(hb_train)
    m_e[:, num_examples*num_classes:] = 1

    y_e_train = hb_train * m_e



    """Logic Program Definition"""
    o = mme.Ontology()

    #Domains
    docs = mme.Domain("Documents", data=x_train)
    o.add_domain([docs])

    # Predicates

    preds = ["ag","ai", "db","ir","ml","hci"]
    for name in preds:
        p = mme.Predicate(name, domains=[docs])
        o.add_predicate(p)

    cite = mme.Predicate("cite", domains=[docs,docs], given=True)
    o.add_predicate(cite)

    """MME definition"""
    potentials = []
    #Supervision
    indices = np.reshape(np.arange(num_classes * docs.num_constants),
                         [num_classes, docs.num_constants]).T # T because we made classes as unary potentials

    indices_test = np.reshape(np.arange(num_classes * num_examples_test),
                         [num_classes, num_examples_test]).T  # T because we made classes as unary potentials

    nn = tf.keras.Sequential()
    nn.add(tf.keras.layers.Input(shape=(x_train.shape[1],)))
    nn.add(tf.keras.layers.Dense(50, activation=tf.nn.sigmoid, kernel_regularizer=tf.keras.regularizers.l2(l2w)))  # up to the last hidden layer
    nn.add(tf.keras.layers.Dense(num_classes,use_bias=False))
    p1 = mme.potentials.SupervisionLogicalPotential(nn, indices)
    potentials.append(p1)

    #Mutual Exclusivity (needed for inference , since SupervisionLogicalPotential already subsumes it during training)
    p2 = mme.potentials.MutualExclusivityPotential(indices=indices)
    potentials.append(p2)

    #Logical
    logical_preds = []
    for name in preds:
        c = mme.Formula(definition="%s(x) and cite(x,y) -> %s(y)" % (name,name), ontology=o)
        p3 = mme.potentials.EvidenceLogicPotential(formula=c,logic=mme.logic.BooleanLogic, evidence=y_e_train, evidence_mask=m_e)
        potentials.append(p3)


    P = mme.potentials.GlobalPotential(potentials)
    pwt = mme.PieceWiseTraining(global_potential=P, y=hb_train)

    y_test = tf.gather(hb_test[0], indices_test)

    # tf.saved_model.save(P, os.path.join("savings","citeseer_pretrain"))
    # P = tf.saved_model.load(os.path.join("savings","citeseer_pretrain"))

    """BETA TRAINING"""
    pwt.compute_beta_logical_potentials()
    for p in potentials:
        print(p, p.beta)



    """NN TRAINING"""
    epochs = 300
    for _ in range(epochs):
        pwt.maximize_likelihood_step(hb_train, x=x_train)
        y_nn = nn(x_test)
        acc_nn = tf.reduce_mean(tf.cast(tf.equal(tf.argmax(y_test, axis=1), tf.argmax(y_nn, axis=1)), tf.float32))
        print(acc_nn)



    """Inference: Since the test size is different, we need to define a new program"""
    steps_map = 100
    hb = hb_test
    x = x_test
    num_examples = len(x_test)
    m_e = np.zeros_like(hb_test)
    m_e[:, num_examples_test*num_classes:] = 1
    y_e_test = hb_test * m_e

    num_classes = 6


    evidence = y_e_test
    evidence_mask = m_e > 0

    # Domains
    o = mme.Ontology()
    docs = mme.Domain("Documents", data=x_test)
    o.add_domain([docs])

    # Predicates

    preds = ["ag", "ai", "db", "ir", "ml", "hci"]
    for name in preds:
        p = mme.Predicate(name, domains=[docs])
        o.add_predicate(p)

    cite = mme.Predicate("cite", domains=[docs, docs], given=True)
    o.add_predicate(cite)

    """MME definition"""
    potentials = []
    # Supervision
    indices = np.reshape(np.arange(num_classes * docs.num_constants),
                         [num_classes, docs.num_constants]).T
    p1 = mme.potentials.SupervisionLogicalPotential(nn, indices)
    potentials.append(p1)

    # Mutual Exclusivity (needed for inference , since SupervisionLogicalPotential already subsumes it during training)
    p2 = mme.potentials.MutualExclusivityPotential(indices=indices)
    potentials.append(p2)

    # Logical
    logical_preds = []
    for name in preds:
        c = mme.Formula(definition="%s(x) and cite(x,y) -> %s(y)" % (name, name), ontology=o)
        p3 = mme.potentials.LogicPotential(formula=c, logic=mme.logic.BooleanLogic)
        potentials.append(p3)



    # We use the trained weights
    P_test = mme.potentials.GlobalPotential(potentials)
    for i,p in enumerate(P.potentials):
        P_test.potentials[i].beta = p.beta




    map_inference = mme.inference.FuzzyMAPInference(y_shape=hb.shape,
                                                    potential=P_test,
                                                    logic=mme.logic.LukasiewiczLogic,
                                                    evidence=evidence,
                                                    evidence_mask=evidence_mask,
                                                    learning_rate= lr)
                                                    # initial_value=initial_nn) #tf.keras.optimizers.schedules.ExponentialDecay(lr, decay_steps=steps_map, decay_rate=0.96, staircase=True))

    y_test = tf.gather(hb[0], indices)
    max_beta = 2
    P_test.potentials[0].beta = lambda_0
    for i in range(steps_map):
        P_test.potentials[1].beta = max_beta - max_beta * (steps_map - i) / steps_map
        map_inference.infer_step(x)
        y_map = tf.gather(map_inference.map()[0], indices)
        acc_map = tf.reduce_mean(tf.cast(tf.equal(tf.argmax(y_test, axis=1), tf.argmax(y_map, axis=1)), tf.float32))
        print("Accuracy MAP", acc_map.numpy())
        if mme.utils.heardEnter():
            break

    y_nn = p1.model(x)
    acc_nn = tf.reduce_mean(tf.cast(tf.equal(tf.argmax(y_test, axis=1), tf.argmax(y_nn, axis=1)), tf.float32))

    return [acc_map, acc_nn]



if __name__ == "__main__":
    seed = 0

    res = []
    for a  in product([0.1, 0.08, 0.05, 0.01], [0.01], [ 0.9, 0.75, 0.5, 0.25, 0.1]):
        lambda_0, lr, test_size = a
        acc_map, acc_nn = main(lr=lr, seed=seed, lambda_0 =lambda_0, l2w=0.001, test_size=test_size)
        acc_map, acc_nn = acc_map.numpy(), acc_nn.numpy()
        res.append("\t".join([str(a) for a in [lambda_0, lr, test_size, str(acc_nn), acc_map+"\n"]]))
        for i in res:
            print(i)

    with open("res_dlm_lambda_0_%d"%seed, "w") as file:
        file.write("perc, lr, acc_map, acc_nn\n")
        file.writelines(res)





