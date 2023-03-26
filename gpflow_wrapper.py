import pickle
from collections import OrderedDict
import gpflow
from sklearn import preprocessing
import numpy as np

""" 
This wrapper of gpflow defines a class to fit experimental
data from echoed messages.     
"""


def generate_random_points(N_points, param_bounds):
    """ generates 'N_points' random points within bounds set by param_bounds
        if param_bounds is a number, the values is fixed by this number
    """
    points = []

    for j in range(N_points):
        point= []
        for bounds in param_bounds:
            if len(bounds)==2:
                value = bounds[0] + (bounds[1] - bounds[0])*np.random.random()
            else:
                value = bounds[0]
            point.append(value)

        points.append(point)

    return np.array(points)
# TODO: put this function into utilities



class GPMaximizer():
    """
        Object for sequential optimization.
        It holds GP model, updates it, generates new points.
    """
    def __init__(self, param_bounds, N_init_points, N_search):
        self.param_bounds = param_bounds
        self.N_init_points = N_init_points
        self.scaler = preprocessing.StandardScaler()
        self.model = None
        self.N_search = N_search

    def generate_init_points(self):
        """ generate initial points to evaluate optimized function at
            fits scaler to initial points
         """
        init_points = generate_random_points(self.N_init_points, self.param_bounds)
        self.scaler.fit(init_points)
        self.init_points = self.scaler.transform(init_points)

        return init_points

    def learn_gp_model(self, X, Y, N_restarts=100, verbose=True):
        """ Several model examples are learned, the best one is taken"""

        X__ = self.scaler.transform(X)

        models = []
        opt = gpflow.optimizers.Scipy()

        for j in range(N_restarts):
            model = gpflow.models.GPR((X__, Y),
                                      kernel=gpflow.kernels.SquaredExponential()
                                      )

            opt.minimize(model.training_loss, model.trainable_variables)
            log_probs = model.predict_log_density((X__, Y))
            mean_log_prob = np.mean(log_probs)
            models += [(model, mean_log_prob)]

        models = sorted(models, key=lambda x: x[1])

        model_qlty = models[-1][1]
        if verbose:
            print('The best model quality: {}'.format(model_qlty))

        # best model chosen
        self.model = models[-1][0]

        return model_qlty

    def find_next_point(self, kappa=1):
        """ generates 'N_search' new points and finds the most promising one """
        X_candidate = generate_random_points(self.N_search, self.param_bounds)
        X_candidate = self.scaler.transform(X_candidate)
        mean, var = self.model.predict_f(X_candidate)
        X_new = np.array([X_candidate[np.argmax((mean - kappa * var))]])
        __X_new = self.scaler.inverse_transform(X_new)  # X_new transformed to original space to put into function

        return __X_new



if __name__ == '__main__':
    param_bounds_dict = OrderedDict({
        'freq': (2.457E09,),  # frequency is fixed for smooth kernel to work               #(2.4E09, 2.5E09),
        'rx_if_gain': (0, 40),
        'rx_vga_gain': (0, 62),
        'tx_vga_gain': (0, 47),
        'sensitivity': (0, 1)
    })
    param_bounds = list(param_bounds_dict.values())

    N_init_points= 10
    GPMaximizer_ = GPMaximizer(param_bounds, N_init_points)
    init_points = GPMaximizer_.generate_init_points()
    with open('res.p', 'rb') as f:
        res = pickle.load(f)

    X = np.vstack([t[1] for t in res])
    Y = np.array([[t[0]] for t in res], dtype=np.float64)

    GPMaximizer_.learn_gp_model(X, Y)

    print(init_points)
    print(GPMaximizer_.find_next_point(1000))
