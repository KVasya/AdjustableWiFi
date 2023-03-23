from skopt import Optimizer
from collections import OrderedDict
from skopt.utils import cook_initial_point_generator

""" 
This wrapper of scikit-optimize is written to change its  default behaviour.
It filters zero or too little values of function observed which are Bernoulli-distributed 
instead being Gaussian as implied by scikit-optimize.  

'gp_minimize_modified' takes  -(quantity of messages received) as the function to optimize 
"""


def is_gaussian(N_msgs, N_responses, thr=10):
    """ Check of Bernoulli value gaussianity """


    p = N_responses / float(N_msgs)
    q = 1 - p
    if N_msgs * p / q > thr:
        return True
    else:
        return False


def gp_minimize_modified(isGauss_thr,
                         N_msgs,
                         func,
                         dimensions,
                         # base_estimator=None,
                         n_calls=100,  # n_random_starts=None,
                         n_initial_points=10,
                         # initial_point_generator="random",
                         # acq_func="gp_hedge", acq_optimizer="auto", x0=None, y0=None,
                         # random_state=None, verbose=False, callback=None,
                         n_points=10000,
                         # n_restarts_optimizer=5, xi=0.01, kappa=1.96,
                         # noise="gaussian", n_jobs=1, model_queue_size=None
                         ):
    # initial points
    initial_point_generator = cook_initial_point_generator('lhs')  # init points for GP model initialization
    X = initial_point_generator.generate(dimensions, n_initial_points)
    Y = [func(x) for x in X]
    print('Function values at initial points: {}'.format(Y))

    # filtering initial points
    Y_filtered = [y for y in Y if is_gaussian(N_msgs, abs(y), isGauss_thr)]
    X_filtered = [X[j] for j, x in enumerate(X) if is_gaussian(N_msgs, abs(Y[j]), isGauss_thr)]

    if len(X_filtered) == 0:
        raise (BaseException('The function at initial points is too noisy for GP, you need to increase N_messages'))


    Optimizer_ = Optimizer(dimensions)
    Optimizer_.tell(X_filtered, Y_filtered)

    results = []
    for j in range(n_points):
        x_new = Optimizer_.ask()
        print('New point: {}'.format(x_new))
        y_new = func(x_new)
        if is_gaussian(N_msgs, abs(y_new), isGauss_thr):
            Optimizer_.tell(x_new, y_new)
            results += [(x_new, y_new)]

    # TODO: ?!?!?!?!?! Is Optimizer_.ask() random, otherwise algo stucks. If yes, what controls randomization?

    # initial random samples are added to the results
    results += [(x, Y_filtered[j]) for j, x in enumerate(X_filtered)]


    return results


if __name__ == '__main__':
    def func(x):
        return 990


    param_bounds_dict = OrderedDict({
        'freq': (2.4E09, 2.5E09),
        # [2412000000.0, 2417000000.0, 2422000000.0, 2427000000.0, 2432000000.0, 2437000000.0, 2442000000.0, 2447000000.0, 2452000000.0, 2457000000.0, 2462000000.0, 2467000000.0, 2472000000.0, 2484000000.0],
        'rx_if_gain': (0, 40),
        'rx_vga_gain': (0, 62),
        'tx_vga_gain': (0, 47),
        'sensitivity': (0, 1)
    })

    param_bounds_list = list(param_bounds_dict.values())

    gp_minimize_modified(1000, func, param_bounds_list, n_points=100)
    # initial_point_generator = cook_initial_point_generator('lhs') # init points for GP model initialization
    # initial_points = initial_point_generator.generate(param_bounds_list, 2, 12)
    # func_vals = [func(x) for x in initial_points]
    #
    #
    #
    #
    # Optimizer_ = Optimizer(param_bounds_list)
    #
    # #print(Optimizer_.tell(initial_points, func_vals))
    # print(Optimizer_.ask())
