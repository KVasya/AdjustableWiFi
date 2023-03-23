from MessageEcho import MessageEcho
from ParamDispatcher import MultipleParamDispatcher
from skopt import gp_minimize
from collections import OrderedDict
import pickle

verbose = True  # if event messages should be printed

# ************************* Sockets to communicate with GNU RADIO  ****************************************************

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

# ********************** GP OPTIMIZATION HYPERPARAMS *******************************************************************
# Quantity of messages sent to GNU Radio to test channel rate
N_msgs = 10000

isGauss_thr = git0  # this value determines the threshold for quantity of messages received ( Bernoulli distributed )
# to be in Gauss limit
# **********************************************************************************************************************




# GNU Radio params interface
MPD = MultipleParamDispatcher(Param2AddrMap)
MPD.setParam('samp_rate', 20E06)  # initial change of params required by GNU Radio project to operate
MPD.setParam('samp_rate', 5E06)
# MPD.setParam('rx_if_gain', 30)
# MPD.setParam('rx_vga_gain', 15)




MessageEcho_ = MessageEcho(N_msgs=N_msgs,
                           send_delay=0.01,
                           PUB_addr=PUB_addr,
                           SUB_addr=SUB_addr,
                           verbose=verbose)

# ************************* GNU RADIO PARAMS OPTIMIZATION  *************************************************************
param_bounds_dict = OrderedDict({
    'freq': (2.4E09, 2.5E09),
    # [2412000000.0, 2417000000.0, 2422000000.0, 2427000000.0, 2432000000.0, 2437000000.0, 2442000000.0, 2447000000.0, 2452000000.0, 2457000000.0, 2462000000.0, 2467000000.0, 2472000000.0, 2484000000.0],
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
        -(quanity of messages echoed)
    """
    arg_names = list(param_bounds_dict.keys())
    assert (len(p) == len(arg_names))

    for j, name in enumerate(arg_names):
        MPD.setParam(name, p[j])

    N_echoed = MessageEcho_.evaluateChnl()
    return (-N_echoed)


param_bounds_list = list(param_bounds_dict.values())

# res = gp_minimize(channelRate,                  # the function to minimize
#                   param_bounds_list,      # the bounds on each dimension of x
#                   acq_func="EI",      # the acquisition function
#                   n_calls=15,         # the number of evaluations of f
#                   n_random_starts=5,  # the number of random initialization points
#                   noise=0.1**2,       # the noise level (optional)
#                   random_state=1234)   # the random seed


# print(res)

from skopt_wrapper import gp_minimize_modified

res = gp_minimize_modified(
    isGauss_thr,
    N_msgs,
    channelRate,  # the function to minimize
    param_bounds_list,  # the bounds on each dimension of x
    n_points=10,
    n_initial_points=10

)
print('Sequential optimization results are as follows:{}'.format(res))
print('The sequence of channel rates is:{}'.format([ abs(r[1]) for r in res ]) )


f_name = 'res_' + 'N_msgs=' + str(N_msgs) + '.p'
with open(f_name, 'wb') as f:
    pickle.dump(res,f)


