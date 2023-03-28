import pickle
from collections import OrderedDict
import gpflow
from sklearn import preprocessing
import numpy as np
import logging

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

#TODO: put this class into 'utilities' module

class BoundsScaler():
    """ Scaler based on strict bounds for variables, it scales each bound to [-1,1]
    If variable is single-valued it's scaled to 0."""
    def __init__(self, param_bounds):
        self.param_bounds = param_bounds

    def fit(self, X):  # just for compatibility with 'sklearn.preprocessing.StandardScaler'
        pass

    def transform(self, X):

        X = X.copy()
        for j, bnds in enumerate(self.param_bounds):

            if len(bnds) == 1:
                X[:, j] = 0

            if len(bnds) == 2:
                L_bnds = bnds[1] - bnds[0]
                X[:, j] = 2 * (X[:, j] - bnds[0]) / L_bnds - 1

        return X

    def inverse_transform(self, X):
        X = X.copy()
        for j, bnds in enumerate(self.param_bounds):

            if len(bnds) == 1:
                X[:, j] = bnds[0]

            if len(bnds) == 2:
                L_bnds = bnds[1] - bnds[0]
                X[:, j] = bnds[0] + L_bnds * (1 + X[:, j]) / 2

        return X


class GPMaximizer():
    """
        Object for sequential optimization.
        It holds GP model, updates it, generates new points.
    """
    def __init__(self, param_bounds, N_init_points, N_search, scaler_type='bounds', y_normalize=True):
        """ inputs:
                --scaler_type, str: 'bounds', 'sklearn'
        """
        self.param_bounds = param_bounds
        self.N_init_points = N_init_points
        if scaler_type=='bounds':
            self.scaler = BoundsScaler(param_bounds)
        if scaler_type=='sklearn':
            self.scaler = preprocessing.StandardScaler()
        self.model = None
        self.N_search = N_search
        self.scaler_type = scaler_type
        self.y_normalize = y_normalize

    def generate_random_point(self):
        """ generate random points within param bounds
         """
        N_points = 1
        random_point = generate_random_points(N_points, self.param_bounds)[0]

        return random_point


    def init_scaler(self, X):
        self.scaler.fit(X)

    def model_params(self, format= 'dict'):
        """ Returns dict with model params
            Inputs:
                -- format: 'dict': dict, 'array': np.array
        """

        names = ['kernel.length', 'kernel.variance', 'noise.variance']
        params = [p.numpy() for p in self.model.parameters]
        if format == 'dict':
            return dict(zip(names,params))
        if format == 'array':
            return np.vstack(params)



    def learn_gp_model(self, X, Y, N_restarts=100, verbose=True):
        """ Several model examples are learned, the best one is taken"""

        X__ = self.scaler.transform(X)
        if self.y_normalize:
            Y__ = Y - np.mean(Y, axis=0)

        models = []
        opt = gpflow.optimizers.Scipy()

        for j in range(N_restarts):
            model = gpflow.models.GPR((X__, Y__),
                                      kernel=gpflow.kernels.SquaredExponential()
                                      )

            opt.minimize(model.training_loss, model.trainable_variables)
            log_probs = model.predict_log_density((X__, Y__))
            mean_log_prob = np.mean(log_probs)
            models += [(model, mean_log_prob)]

        models = sorted(models, key=lambda x: x[1])

        model_qlty = models[-1][1]


        # best model chosen
        self.model = models[-1][0]

        return model_qlty

    def find_next_point(self, kappa=1):
        """ generates 'N_search' new points and finds the most promising one """
        X_candidate = generate_random_points(self.N_search, self.param_bounds)
        X_candidate = self.scaler.transform(X_candidate)
        mean, var = self.model.predict_f(X_candidate)
        X_new = np.array([X_candidate[np.argmax((mean + kappa * var))]])
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
