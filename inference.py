import tensorflow as tf
import abc
import utils




class Inference():

    def __init__(self, global_potential, parameters=None):
        self.global_potential = global_potential
        self.parameters = parameters

    @abc.abstractmethod
    def infer(self, x=None):
        pass



class Sampler(object):

    @tf.function
    def sample(self, conditional_data=None, num_samples=None, minibatch = None):
        pass

# class SamplerAggregation(Sampler):
#
#
#     def __init__(self, samplers):
#
#         self.samplers = []
#         for s in samplers:
#             if isinstance(s, Sampler):
#                 self.samplers.append(s)
#
#     @tf.function
#     def sample(self, conditional_data=None, num_samples=None, minibatch = None):
#
#         S = []
#         for s in self.samplers:
#             S.append(s.sample(conditional_data, num_samples, minibatch))
#
#         return tf.stack(S, axis=0)
#
# class VariationalMAPSamplerTF1(Sampler):
#
#     def __init__(self, name, global_potential, var_shape, convergence_threshold = 0.00001, max_num_iter = 1000, learning_rate = 0.1):
#         self.global_potential = global_potential
#         self.var_shape = var_shape
#         self.var_ = tf.get_variable("MAP_state_{}".format(name), initializer=tf.random_normal(shape=var_shape, mean=0.0, stddev=0.1))
#         # self.var_ = tf.get_variable("MAP_state_{}".format(name), initializer=0.5 * tf.ones(shape=var_shape))
#         self.convergence_threshold = convergence_threshold
#         self.max_num_iter = max_num_iter
#
#         self.optimizer = tf.train.AdamOptimizer(learning_rate)
#         # self.optimizer = tf.train.GradientDescentOptimizer(learning_rate)
#
#     def _internal_state(self):
#         return tf.sigmoid(self.var_)
#
#     def sample(self, conditional_data=None, num_samples=None, minibatch = None):
#
#         not_converged = lambda i:  tf.less(i, self.max_num_iter)
#         def body(i):
#             current_state = self._internal_state()
#             if minibatch is not None:
#                 current_state = tf.gather(current_state, minibatch)
#             update_map = self.optimizer.minimize(- self.global_potential(current_state, conditional_data), var_list=[self.var_])
#             with tf.control_dependencies([update_map]):
#                 i = tf.add(i, 1)
#                 return i
#
#         with tf.control_dependencies([tf.variables_initializer([self.var_])]):
#             loop = tf.while_loop(not_converged, body, [tf.constant(0.)])
#             with tf.control_dependencies([loop]):
#                 map = self.current_state = tf.stop_gradient(self._internal_state())
#         if minibatch is not None:
#             map = tf.gather(map, minibatch)
#         return map
#
# class VariationalMAPSamplerSigmoidTF1(Sampler):
#
#     def __init__(self, name, global_potential, var_shape, convergence_threshold = 0.00001, max_num_iter = 1000, learning_rate = 0.1):
#         self.global_potential = global_potential
#         self.var_shape = var_shape
#         # self.var_ = tf.get_variable("MAP_state_{}".format(name), initializer=tf.random_normal(shape=var_shape, mean=0.0, stddev=0.1))
#         self.var_ = tf.get_variable("MAP_state_{}".format(name), initializer=0.5 * tf.ones(shape=var_shape))
#         self.convergence_threshold = convergence_threshold
#         self.max_num_iter = max_num_iter
#
#         self.optimizer = tf.train.AdamOptimizer(learning_rate)
#         # self.optimizer = tf.train.GradientDescentOptimizer(learning_rate)
#
#     def _internal_state(self):
#         # return tf.sigmoid(self.var_)
#         return tf.identity(self.var_)
#
#     def sample(self, conditional_data=None, num_samples=None, minibatch = None):
#
#         not_converged = lambda i:  tf.less(i, self.max_num_iter)
#         def body(i):
#             current_state = self._internal_state()
#             if minibatch is not None:
#                 current_state = tf.gather(current_state, minibatch)
#             update_map = self.optimizer.minimize(- self.global_potential(current_state, conditional_data), var_list=[self.var_])
#             with tf.control_dependencies([update_map]):
#                 with tf.control_dependencies([tf.assign(self.var_, tf.clip_by_value(self.var_, clip_value_min=0, clip_value_max=1))]):
#                     i = tf.add(i, 1)
#                     return i
#
#
#
#         # with tf.control_dependencies([tf.variables_initializer([self.var_])]):
#         loop = tf.while_loop(not_converged, body, [tf.constant(0.)])
#         with tf.control_dependencies([loop]):
#             map = self.current_state = tf.stop_gradient(self._internal_state())
#         if minibatch is not None:
#             map = tf.gather(map, minibatch)
#         return map
#
# class VariationalBernoulliTF1(Sampler):
#
#     def __init__(self, name, global_potential, var_shape, convergence_threshold = 0.00001, max_num_iter = 1000, learning_rate = 0.1):
#         self.global_potential = global_potential
#         self.var_shape = var_shape
#         self.var_ = tf.get_variable("state_{}".format(name), initializer=tf.random_normal(shape=var_shape, mean=0.0, stddev=0.1))
#         self.convergence_threshold = convergence_threshold
#         self.max_num_iter = max_num_iter
#
#         self.optimizer = tf.train.AdamOptimizer(learning_rate)
#
#     def _internal_state(self):
#         #reparametrization trick
#         eps = tf.random_uniform(shape=self.var_shape, minval=0, maxval=1, dtype=tf.float32)
#         return eps * self.var_ / (eps * self.var_ + (1 - eps)*(1- self.var_))
#
#     def sample(self, conditional_data=None, num_samples=None, minibatch = None):
#
#         i = tf.constant(0)
#
#         converged = lambda i:  i < self.max_num_iter
#
#         def body(i):
#
#             current_state = self._internal_state()
#             if minibatch is not None:
#                 current_state = tf.gather(current_state, minibatch)
#             update = self.optimizer.minimize(- self.global_potential(current_state, conditional_data), var_list=[self.var_])
#             with tf.control_dependencies([update]):
#                 i = i + 1
#             return i
#
#         loop = tf.while_loop(converged, body, (i))
#         with tf.control_dependencies(loop):
#             eps = tf.random_uniform(shape=self.var_shape, minval=0, maxval=1, dtype=tf.float32)
#             sample = eps < tf.sigmoid(self.var_)
#         if minibatch is not None:
#             sample = tf.gather(sample, minibatch)
#         return sample
#
# class GenerativeNetworkSamplerTF1(Sampler):
#
#
#     def __init__(self, name, global_potential, num_samples, num_variables, generative_model, learning_rate = 0.001, noise_dimensions = 10, is_test = False):
#         self.global_potential = global_potential
#         self.num_samples = num_samples
#         self.model = generative_model
#         self.optimizer = tf.train.AdamOptimizer(learning_rate)
#         self.name = name
#         self.noise_dimensions = noise_dimensions
#         self.is_test = is_test
#
#         self.num_chains = num_samples
#         self.num_variables = num_variables
#
#         self.current_state = tf.get_variable(name,
#                                              initializer=tf.where(
#                                                  tf.random_uniform(shape=[self.num_chains, num_variables], minval=0,
#                                                                    maxval=1) > 0.5,
#                                                  tf.ones([self.num_chains, num_variables]),
#                                                  tf.zeros([self.num_chains, num_variables])),
#                                              trainable=False
#                                              )
#
#     def sample(self, conditional_data=None, num_samples=None, minibatch = None):
#
#         rand = tf.random_uniform(shape=[self.num_samples])
#         on_state = self.model(self.current_state)
#         off_state = self.current_state
#
#         potential_on = self.global_potential(on_state)
#         potential_off = self.global_potential(self.current_state)
#         p = tf.sigmoid(potential_on - potential_off)
#
#         cond = rand < p
#         new_state = tf.where(cond, on_state, off_state)
#
#
#         ass = tf.assign(self.current_state, new_state)
#         if not self.is_test:
#             update_map = self.optimizer.minimize(- self.global_potential(new_state, conditional_data), var_list=self.model.variables)
#             with tf.control_dependencies([ass, update_map]):
#                 new_state  = tf.stop_gradient(new_state)
#         return new_state
#
# class GPUGibbsSamplerTF1(Sampler):
#
#
#     def __init__(self, potential, num_variables, inter_sample_burn=0, num_chains = 10, initial_state=None, evidence = None, flips=None):
#
#         self.potential = potential
#         self.num_chains = num_chains
#         self.inter_sample_burn = inter_sample_burn
#         self.num_variables = num_variables
#         if initial_state is None:
#             self.current_state = tf.cast(tf.random.uniform(shape=[self.num_chains, num_variables], minval=0,
#                                                                            maxval=2, dtype=tf.int32), tf.float32)
#         else:
#             self.current_state = initial_state
#         self.evidence = evidence
#         self.flips = flips
#
#     @tf.function
#     def one_step(self, current_state, conditional_data):
#
#         num_examples = current_state.get_shape()[0]
#         num_variables = current_state.get_shape()[1]
#
#         K = tf.random.shuffle(tf.range(num_variables, dtype=tf.int32))
#         i = [tf.constant(0, dtype=tf.int32), current_state]
#         c = lambda i, s: i < num_variables
#
#         def body(i,s):
#             k = K[i]
#             mask = tf.one_hot(k, depth=num_variables)
#             off_state = s * (1 - mask)
#             on_state = off_state + mask
#             rand = tf.random.uniform(shape=[num_examples])
#
#             potential_on = self.potential(on_state, conditional_data)
#             potential_off = self.potential(off_state, conditional_data)
#             p = tf.sigmoid(potential_on - potential_off)
#             # p = tf.Print(p, [p, rand])
#
#             cond = tf.reshape(rand < p, shape=[-1, 1])
#             current_state = tf.where(cond, on_state, off_state)
#             if self.evidence is not None:
#                 current_state = tf.cond(tf.equal(self.evidence[0, k], 1), lambda: s, lambda: current_state)
#             i = i + 1
#             return i, current_state
#
#         i, r= tf.while_loop(c, body, i)
#         return r
#
#     @tf.function
#     def sample(self, conditional_data=None, num_samples=None, minibatch = None):
#
#         if num_samples is not None:
#             num_chain_temp = ((num_samples-1) // self.num_chains) + 1
#         else:
#             num_chain_temp = self.num_chains
#
#         current_state = self.current_state if minibatch is None else tf.gather(self.current_state, minibatch)
#
#         samples = []
#         for i in range(num_chain_temp):
#
#             current = samples[-1] if len(samples)>0 else current_state
#             samples.append(self.one_step(current_state=current, conditional_data=conditional_data))
#
#         if minibatch is None:
#             self.current_state = samples[-1]
#         else:
#             #todo minibatches not handled in v2
#             ass = tf.scatter_update(self.current_state, minibatch, samples[-1])
#         samples = tf.reshape(samples,[-1, self.num_variables])
#         # return samples
#         return tf.concat(samples,axis=0)[:num_samples]
#
class GPUGibbsSampler(Sampler):


    def __init__(self, potential, num_variables, inter_sample_burn=1, num_chains = 10, initial_state=None, evidence = None, evidence_mask = None, flips=None, num_examples=1):

        self.potential = potential
        self.inter_sample_burn = inter_sample_burn
        self.num_variables = num_variables
        self.num_examples = num_examples
        self.num_chains = num_chains

        if initial_state is None:
            self.current_state = tf.cast(tf.random.uniform(shape=[self.num_examples, self.num_chains, num_variables], minval=0,
                                                                           maxval=2, dtype=tf.int32), tf.float32)
        else:
            self.current_state = tf.cast(initial_state, tf.float32)
        self.evidence = evidence
        if evidence is not None:
            self.evidence = tf.tile(tf.expand_dims(evidence, axis=1), [1, num_chains, 1])
            self.evidence_mask =  tf.tile(tf.expand_dims(evidence_mask, axis=1), [1, num_chains, 1])
        self.flips = flips if flips is not None and flips > 0 else num_variables

    @tf.function
    def __sample(self, current_state, conditional_data=None, num_samples=None, minibatch = None):


        # Gibbs sampling in random scan mode
        # todo(giuseppe) allow ordered scan or other euristics from outside

        n_ex = self.num_examples if minibatch is None else len(minibatch)

        #todo(giuseppe) improve the speed of this shuffling and of the third dimension. It has slowed too much.
        scan = tf.reshape(tf.range(self.num_variables, dtype=tf.int32), [-1, 1, 1])
        scan = tf.tile(scan, [1, n_ex, self.num_chains]) #num_variables, num_examples, num_chains (needed for shuffling along the axis=0
        K = tf.random.shuffle(scan)[:self.flips,:,:]
        K = tf.transpose(K, [1, 2, 0])
        for i in range(self.flips):
            k = K[:,:,i]

            mask = tf.one_hot(k, depth=self.num_variables)
            off_state = current_state * (1 - mask)
            on_state = off_state + mask
            rand = tf.random.uniform(shape=[n_ex, self.num_chains])

            potential_on = self.potential(on_state, conditional_data)
            potential_off = self.potential(off_state, conditional_data)


            p = tf.sigmoid(potential_on - potential_off)
            cond = tf.reshape(rand < p, shape=[n_ex, self.num_chains, 1])
            current_state = tf.where(cond, on_state, off_state)
            if self.evidence is not None:
                current_state = tf.where(self.evidence_mask, self.evidence, current_state)



        return current_state



    def sample(self, conditional_data=None, num_samples=None, minibatch=None):

        current_state = self.current_state if minibatch is None else tf.gather(self.current_state, minibatch)

        for _ in range(self.inter_sample_burn):

            sample = self.__sample(current_state,conditional_data, num_samples, minibatch)
            if minibatch is None:
                self.current_state = sample
            else:
                self.current_state = tf.tensor_scatter_nd_update(self.current_state, tf.reshape(minibatch,[-1,1]), sample)

        return sample



class GPUGibbsSamplerV2(Sampler):


    def __init__(self, potential, num_variables, inter_sample_burn=1, num_chains = 10, initial_state=None, evidence = None, evidence_mask = None, flips=None, num_examples=1):

        self.potential = potential
        self.inter_sample_burn = inter_sample_burn
        self.num_variables = num_variables
        self.num_examples = num_examples
        self.num_chains = num_chains

        if initial_state is None:
            self.current_state = tf.cast(tf.random.uniform(shape=[self.num_examples, self.num_chains, num_variables], minval=0,
                                                                           maxval=2, dtype=tf.int32), tf.float32)
        else:
            self.current_state = tf.tile(tf.expand_dims(tf.cast(initial_state, tf.float32), axis=1), [1, self.num_chains, 1])
        self.evidence = evidence
        if evidence is not None:
            self.evidence = evidence
            self.evidence_mask = tf.cast(evidence_mask, tf.int32)
        if flips is not None and flips > 0:
            self.flips = flips
        elif self.evidence is not None:
            self.flips = tf.reduce_max(tf.reduce_sum(1 - evidence_mask, axis=-1)) #check the maximum number of non-observed
        else:
            self.flips = num_variables

    @tf.function
    def __sample(self, current_state, conditional_data=None, num_samples=None, minibatch = None):


        # Gibbs sampling in random scan mode
        # todo(giuseppe) allow ordered scan or other euristics from outside

        n_ex = self.num_examples if minibatch is None else len(minibatch)

        logits = tf.math.log((1 - self.evidence_mask) / tf.reduce_sum(1 - self.evidence_mask, axis=-1, keepdims=True))
        samples = tf.random.categorical(logits=logits, num_samples=tf.cast(self.flips*self.num_chains, tf.int32), dtype=None, seed=None, name=None)
        samples = tf.reshape(samples, [-1, self.num_chains, self.flips])
        masks = tf.one_hot(samples, depth=self.num_variables)
        for i in range(self.flips):
            mask = masks[:,:,i,:]

            off_state = current_state * (1 - mask)
            on_state = off_state + mask
            rand = tf.random.uniform(shape=[n_ex, self.num_chains])

            potential_on = self.potential(on_state, conditional_data)
            potential_off = self.potential(off_state, conditional_data)


            p = tf.sigmoid(potential_on - potential_off)
            cond = tf.reshape(rand < p, shape=[n_ex, self.num_chains, 1])
            current_state = tf.where(cond, on_state, off_state)



        return current_state



    def sample(self, conditional_data=None, num_samples=None, minibatch=None):

        current_state = self.current_state if minibatch is None else tf.gather(self.current_state, minibatch)

        for _ in range(self.inter_sample_burn):

            sample = self.__sample(current_state,conditional_data, num_samples, minibatch)
            if minibatch is None:
                self.current_state = sample
            else:
                self.current_state = tf.tensor_scatter_nd_update(self.current_state, tf.reshape(minibatch,[-1,1]), sample)

        return sample



#
#
# class PartialGPUGibbsKernelTF1(tfp.mcmc.TransitionKernel):
#
#     def __init__(self, potential, conditional_data, flips, evidence_mask=None):
#         super(PartialGPUGibbsKernel, self).__init__()
#         self.potential = potential
#         self.masks = []
#         self.evidence_mask = evidence_mask if evidence_mask is not None else None
#         self.flips = flips
#         self.conditional_data = conditional_data
#
#     @tf.function()
#     def one_step(self, current_state, previous_kernel_results):
#
#         num_examples = current_state.get_shape()[0].value
#         num_variables = current_state.get_shape()[1].value
#
#         P = tf.zeros([num_examples])
#         OFF = tf.constant(0.)
#         ON = tf.constant(0.)
#         DELTA = tf.constant(0.)
#         i = [tf.constant(0, dtype=tf.int32),current_state,P, OFF, ON, DELTA]
#         c = lambda i,s,p,off,on,delta: i < self.flips
#
#         def body(i,s,P,OFF, ON, DELTA):
#             if self.evidence_mask is not None:
#                 k = tf.squeeze(tf.multinomial(tf.log(1 - tf.cast(self.evidence_mask, tf.float32)), 1, output_dtype=tf.int32))
#             else:
#                 k = tf.random_uniform(minval=0,
#                                       maxval=num_variables,
#                                       dtype=tf.int32,
#                                       shape=())
#             mask = tf.one_hot(k, depth=num_variables)
#             off_state = s * (1 - mask)
#             on_state = off_state + mask
#             rand = tf.random_uniform(shape=[num_examples])
#
#             #Time efficient
#             potential_on = self.potential(on_state, x=self.conditional_data)
#             potential_off = self.potential(off_state, x=self.conditional_data)
#             delta_potential = tf.abs(potential_on - potential_off)
#             p = tf.reshape(tf.sigmoid(potential_on - potential_off), [-1])
#             #Memory Efficient
#             # energy_on = self.model.compute_energy(on_state)
#             # energy_off = self.model.compute_energy(off_state)
#             # p = tf.reshape(tf.sigmoid(- energy_on + energy_off), [-1])
#
#             cond = rand < p
#             current_state = tf.where(cond, on_state, off_state)
#             if self.evidence_mask is not None:
#                 current_state= tf.cond(tf.equal(self.evidence_mask[0, i],1), lambda: s, lambda: current_state)
#             i = i+1
#             OFF = OFF + tf.reduce_sum(potential_off)
#             ON = ON + tf.reduce_sum(potential_on)
#             DELTA = DELTA + tf.reduce_sum(delta_potential)
#             return i,current_state, p, OFF, ON, DELTA
#
#         i,r,p, OFF,ON, DELTA = tf.while_loop(c, body, i)
#         return r, [p, OFF/(num_examples*self.flips),ON/(num_examples*self.flips), DELTA/(num_examples*self.flips)]
#
#     @tf.function()
#     def is_calibrated(self):
#         return True
#
#     @tf.function()
#     def bootstrap_results(self, init_state):
#         num_examples = init_state.get_shape()[0]
#         return [tf.zeros([num_examples]), tf.constant(0.), tf.constant(0.), tf.constant(0.)]
#
#

class FuzzyMAPInference(Inference):

    def __init__(self,  global_potential, preferences):

        super(FuzzyMAPInference, self).__init__(global_potential, preferences)
        self.potential = global_potential
        self.var_map = self.parameters["var"]
        self.opt = self.parameters["opt_var_map"]
        self.evidence = self.parameters["evidence"]
        self.evidence_mask = self.parameters["evidence_mask"]



    def infer_step(self, x=None):

        with tf.GradientTape() as tape:
            y = self.map()
            p_m = - self.potential(y, x=x)
        grad = tape.gradient(p_m, self.var_map)
        grad_vars = [(grad, self.var_map)]
        self.opt.apply_gradients(grad_vars)

    def map(self):
        y_map = tf.where(self.evidence_mask, self.evidence, tf.sigmoid(self.var_map))
        return y_map


    def infer(self, x=None):
        steps_map = 10
        for i in range(steps_map):
            self.infer_step(x)
            if "evaluate" in self.parameters and i % 2 == 0:
                y_map = tf.gather(self.map()[0], self.parameters["indices_to_test"])
                y_test = tf.gather(tf.cast(self.evidence[0], dtype=tf.int32), self.parameters["indices_to_test"])
                acc_map = tf.reduce_mean(
                    tf.cast(tf.equal(tf.argmax(y_test, axis=1), tf.argmax(y_map, axis=1)), tf.float32))
                print("Accuracy MAP Fuzzy at %d" % i, acc_map.numpy())
        return self.map() > 0.5


class GibbsSamplingInference(Inference):

    def __init__(self,  global_potential, preferences):

        super(GibbsSamplingInference, self).__init__(global_potential, preferences)
        self.potential = global_potential

        self.sampler = GPUGibbsSamplerV2(potential=self.potential,
                                         num_variables = self.parameters["num_variables"],
                                         inter_sample_burn=1,
                                         num_chains = self.parameters["num_chains"],
                                         initial_state=self.parameters["initial_state"],
                                         evidence = self.parameters["evidence"],
                                         evidence_mask = self.parameters["evidence_mask"],
                                         flips=None,
                                         num_examples=1)

        self.num_samples = self.parameters["num_samples"]


    def infer(self, x=None):

        res = []
        for _ in range(self.num_samples // self.sampler.num_chains + 1):
            res.append(self.sampler.sample(conditional_data=x))

        res = tf.concat(res, axis=1)
        return tf.reduce_mean(res, axis=1) > 0.5



class FuzzyMAPGibbsSamplingInference(Inference):


    def __init__(self,global_potential,preferences):
        super(FuzzyMAPGibbsSamplingInference, self).__init__(global_potential, preferences)
        self.potential = global_potential
        self.var_map = self.parameters["var"]
        self.opt = self.parameters["opt_var_map"]
        self.evidence = self.parameters["evidence"]
        self.evidence_mask = self.parameters["evidence_mask"]



    def _create_sampler(self):
        self.sampler = GPUGibbsSamplerV2(potential=self.potential,
                                         num_variables=self.parameters["num_variables"],
                                         inter_sample_burn=1,
                                         num_chains=self.parameters["num_chains"],
                                         initial_state=self.map_state,
                                         evidence=self.parameters["evidence"],
                                         evidence_mask=self.parameters["evidence_mask"],
                                         flips= self.parameters["flips"] if "flips" in self.parameters else None,
                                         num_examples=1)

        self.num_samples = self.parameters["num_samples"]


    def infer_gs(self, x=None):
        res = []
        for _ in range(self.num_samples // self.sampler.num_chains + 1):
            res.append(self.sampler.sample(conditional_data=x))

        res = tf.concat(res, axis=1)
        return tf.reduce_mean(res, axis=1) > 0.5



    def infer_step(self, x=None):

        with tf.GradientTape() as tape:
            y = self.map()
            p_m = - self.potential(y, x=x)
        grad = tape.gradient(p_m, self.var_map)
        grad_vars = [(grad, self.var_map)]
        self.opt.apply_gradients(grad_vars)

    def map(self):
        y_map = tf.where(self.evidence_mask, self.evidence, tf.sigmoid(self.var_map))
        return y_map


    def infer_fuzzy(self, x=None):
        steps_map = 2
        for i in range(steps_map):
            self.infer_step(x)
            if "evaluate" in self.parameters and i % 2 == 0:
                y_map = tf.gather(self.map()[0], self.parameters["indices_to_test"])
                y_test = tf.gather(tf.cast(self.evidence[0], dtype=tf.int32), self.parameters["indices_to_test"])
                acc_map = tf.reduce_mean(
                    tf.cast(tf.equal(tf.argmax(y_test, axis=1), tf.argmax(y_map, axis=1)), tf.float32))
                print("Accuracy MAP Fuzzy at %d" % i, acc_map.numpy())
        return self.map() > 0.5

    def infer(self,x=None):

        print("Fuzzy MAP inference")
        self.map_state = self.infer_fuzzy(x)

        print("Gibbs sampling inference")
        self._create_sampler()
        return self.infer_gs(x)


FUZZY = "f0221"
GIBBS_SAMPLING = "gi88s 54mp1in6"
FUZZYGS = FUZZY + GIBBS_SAMPLING

def create_inference(id, P, parameters):
    if id == FUZZY:
        return FuzzyMAPInference(P, parameters)
    elif id == GIBBS_SAMPLING:
        return GibbsSamplingInference(P, parameters)
    elif id == FUZZYGS:
        return FuzzyMAPGibbsSamplingInference(P, parameters)

    else:
        raise Exception("Training algorithm %s is not known." % str(id))