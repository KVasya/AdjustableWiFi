from MessageEcho import MessageEcho
from ParamDispatcher import MultipleParamDispatcher
#from skopt import gp_minimize
from collections import OrderedDict
import numpy as np
from gpflow_wrapper import GPMaximizer
import logging
import time
import pickle


# KEY PARAMS
N_msgs = 10000  # quantity of messages send per each channel rate testing
N_init_points = 5  # quantity of initial points required to build a model
# TODO: criterion to choose N_init_points (perhaps, we better need to reach some model quality)
# TODO: add early detection of zero-rate points, less than N_msgs should be spent on them

N_sequential = 20  # quantity of sequential search trials
N_search = 10000  # quantity of search points per trial (quantity of (mean, var) estimates)
gauss_thr = 2  # controls filtering of channel_rates close to zero
kappa = -1  # determines how new points are chosen -- either mean or variance is preferred
            # point with largest (mean + kappa*var) is chosen

# LOGGING
verbose = False  # if messages from 'MessageEcho' and 'ParamDispatcher' should be printed
log_f_name = './logs/'+ str(int(time.time()))+ '.log'
logging.basicConfig(filename=log_f_name, level=logging.INFO)


# SOCKETS TO COMMUNICATE WITH GNU RADIO  ------------------------------------------------------------------------------

# zmq SUB sockets addresses responsible for parameter changes (GNU Radio project defined)
Param2AddrMap = dict({
                           'freq': "tcp://127.0.0.1:52010",
                     'rx_if_gain': "tcp://127.0.0.1:52011",
                      'samp_rate': "tcp://127.0.0.1:52012",
                    'rx_vga_gain': "tcp://127.0.0.1:52013",
                    'tx_vga_gain': "tcp://127.0.0.1:52014",
                    'sensitivity': "tcp://127.0.0.1:52015"
                    })

# zmq SUB sockets addresses to send (PUB) and receive (SUB) messages echoed (GNU Radio project defined)
PUB_addr = "tcp://127.0.0.1:52002"
SUB_addr = "tcp://127.0.0.1:52003"
# TODO: single host is used, only the port varies


# GNU RADIO PARAMS INTERFACE  -----------------------------------------------------------------------------------------
MPD = MultipleParamDispatcher(Param2AddrMap, verbose=verbose)
MPD.setParam('samp_rate', 20E06) # initial change of params required by GNU Radio project to operate
MPD.setParam('samp_rate', 5E06)


# MESSAGE COMMUNICATOR TO/FROM GNU RADIO  -----------------------------------------------------------------------------
MessageEcho_ = MessageEcho(    N_msgs = N_msgs,
                           send_delay = 0.01,
                           PUB_addr   = PUB_addr,
                           SUB_addr   = SUB_addr,
                           verbose= verbose
                          )


# GNU RADIO PARAMS OPTIMIZATION  --------------------------------------------------------------------------------------
param_bounds_dict = OrderedDict({
                                        'freq':  (2.457E09,), # frequency is fixed for smooth kernel to work #(2.4E09, 2.5E09),
                                  'rx_if_gain': (0, 40),
                                 'rx_vga_gain': (0, 62),
                                 'tx_vga_gain': (0, 47),
                                 'sensitivity': (0, 1)
                                })
param_bounds = list(param_bounds_dict.values())

def channelRate(p):
    """
    INPUTS:
    -- p: list of floats, params to be set in GNU Radio project
    returns:
        quanity of messages echoed
    """
    arg_names = list(param_bounds_dict.keys())
    assert(len(p) == len(arg_names))

    for j, name in enumerate(arg_names):
        MPD.setParam(name, p[j])

    N_echoed = MessageEcho_.evaluateChnl()
    return float(N_echoed)


def is_gaussian(N_msgs, N_responses, thr=2):
    """ Check of Bernoulli value gaussianity """

    p = N_responses / float(N_msgs)
    q = 1 - p
    if N_msgs * p / q >= thr:
        return True
    else:
        return False


GPMaximizer_ = GPMaximizer(param_bounds, N_init_points, N_search)

print('HARDWARE CHECK AT MUST-WORK PARAMS')
rate = channelRate([2.457E09, 30, 52, 37, .5])
print('\t At close-to-maximal amplifications the channel rate is: {}'.format(rate) )
if rate == 0:
    raise(BaseException('No messages echoed. Hardware malfunctioning?\n N_msgs is too little?\n Program stops.'))


# CHANNEL RATE MEASUREMENT AT INITIAL RANDOM POINTS
print('\nCHANNEL RATE MEASUREMENT AT INITIAL RANDOM POINTS')
print('\t{} init points to be acquired by random search\n'.format(N_init_points))
X, Y = [],[]
trial_cnt = 0
while len(X) < N_init_points:
    x = GPMaximizer_.generate_random_point()
    y = channelRate(x)
    if is_gaussian(N_msgs, y, gauss_thr):
        X.append(x)
        Y.append([y])
        print('\t {}. point {} with rate={} accepted'.format(trial_cnt,x,y))
    else:
        print('\t {}. point {} with rate={} was rejected as being too noisy'.format(trial_cnt,  x,y))
    trial_cnt+=1

logging.info('init:system_params: ' + str(X))
logging.info('init:channel_rates: ' + str(Y))
X = np.array(X)
Y = np.array(Y)

GPMaximizer_.init_scaler(X)
print('\t rates at accepted initial points: {}'.format(Y))

# GP MODEL LEARNING AT INITIAL POINTS
print('\nGP MODEL LEARNING AT INITIAL POINTS')
model_log_prob = GPMaximizer_.learn_gp_model(X, Y)
logging.info('init:model_params: ' + str(GPMaximizer_.model_params(format='dict')) )
print('\t current GP model log_prob: {}'.format(model_log_prob))

# TODO: if X is empty raise an Error

# SEQUENTIAL OPTIMIZATION
print('\nSEQUENTIAL OPTIMIZATION')
print('\t{} model predictions to be tried\n'.format(N_sequential))
Ys = []
Xs = []
model_qlts = []
model_params = []

for j in range(N_sequential):
    X_new = GPMaximizer_.find_next_point(kappa=kappa)
    Y_new = channelRate(X_new[0])
    if is_gaussian(N_msgs, Y_new, gauss_thr):

        X = np.vstack([X, X_new])
        Y = np.vstack([Y, [Y_new]])
        model_log_prob = GPMaximizer_.learn_gp_model(X, Y)
        model_param = str(GPMaximizer_.model_params(format='dict'))
        model_params.append(model_param)


        print('\t Point {} with rate={} accepted for model update. Current model log_prob={}'.format(X_new, Y_new,
                                                                                                   model_log_prob))
        Ys.append(Y_new)
        Xs.append(X_new)
        model_qlts.append(model_log_prob)


    else:
        print('\t Point {} with rate={} is rejected as being too noisy'.format(X_new, Y_new))



print('Sequence of channel rates: {}'.format(Ys))
print('Sequence of model qualities: {}'.format(model_qlts))
logging.info('sequential:channel_rates=' + str(Ys))
logging.info('sequential:system_params=' + str(Xs))
logging.info('sequential:model_qualities=' + str(model_qlts))
logging.info('sequential:model_params: ' + str(model_params ))

