from MessageEcho import MessageEcho
from ParamDispatcher import MultipleParamDispatcher
#from skopt import gp_minimize
from collections import OrderedDict
import numpy as np
from gpflow_wrapper import GPMaximizer
import time
import pickle



verbose = True  # if event messages should be printed
N_msgs = 1000
# ************************** Sockets to communicate with GNU RADIO  ****************************************************

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
# *********************************************************************************************************************

# GNU Radio params interface
MPD = MultipleParamDispatcher(Param2AddrMap, verbose=verbose)
MPD.setParam('samp_rate', 20E06) # initial change of params required by GNU Radio project to operate
MPD.setParam('samp_rate', 5E06)



# Message communicator to/from GNU Radio
MessageEcho_ = MessageEcho(N_msgs     = N_msgs,
                           send_delay = 0.01,
                           PUB_addr   = PUB_addr,
                           SUB_addr   = SUB_addr,
                           verbose= verbose)

# N_rcvd= MessageEcho_.evaluateChnl(N_sent)
#print('{} messages were received out of {} sent'.format(N_rcvd, N_sent))


# ************************ GNU RADIO PARAMS OPTIMIZATION  *************************************************************
param_bounds_dict = OrderedDict({
                                        'freq':  (2.457E09,), # frequency is fixed for smooth kernel to work               #(2.4E09, 2.5E09),
                                  'rx_if_gain': (0, 40),
                                 'rx_vga_gain': (0, 62),
                                 'tx_vga_gain': (0, 47),
                                 'sensitivity': (0, 1)
                                })


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
    return  float(N_echoed)


def is_gaussian(N_msgs, N_responses, thr=2):
    """ Check of Bernoulli value gaussianity """

    p = N_responses / float(N_msgs)
    q = 1 - p
    if N_msgs * p / q > thr:
        return True
    else:
        return False




N_init_points = 40
N_sequential = 20
N_search = 10000

param_bounds = list(param_bounds_dict.values())
GPMaximizer_ = GPMaximizer(param_bounds, N_init_points, N_search)


print('At maximal amplifications the channel rate is: {}'.format(channelRate([2.457E09, 30, 52, 37, .5])) )


print(10*'*' + '     Channel rate is estimated at random points    ' + 10*'*')
X = GPMaximizer_.generate_init_points()
Y = np.array([[channelRate(p)] for p in X])
X = np.array([x for j,x in enumerate(X) if is_gaussian(N_msgs, Y[j][0]) ])
Y = np.array([y for j,y in enumerate(Y) if is_gaussian(N_msgs, Y[j][0]) ])




print(10*'*' + '      Model is fit to initial data       ' + 10*'*')
GPMaximizer_.learn_gp_model(X, Y)
# TODO: if X is empty raise an Error


print(10*'*' + '     Investigating promising points     ' + 10*'*')
Ys = []
model_qlts = []
for j in range(N_sequential):
    X_new = GPMaximizer_.find_next_point(1000)
    Y_new = channelRate(X_new[0])
    if is_gaussian(N_msgs, Y_new):
        X = np.vstack([X, X_new])
        Y = np.vstack([Y, [Y_new]])
        model_qlty = GPMaximizer_.learn_gp_model(X, Y)
        Ys.append(Y_new)
        model_qlts.append(model_qlty)
    else:
        print('Point {} with y={} is rejected as being too noisy'.format(j, Y_new))
    if j%10 == 0: print('point {} out of {} has been handled'.format(j+1, N_sequential))

print('Sequence of channel rates: {}'.format(Ys))
print('Sequence of model qualities: {}'.format(model_qlts))