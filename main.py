from MessageEcho import MessageEcho
from ParamDispatcher import MultipleParamDispatcher
from skopt import gp_minimize
from collections import OrderedDict


verbose= True # if event messages should be printed


#************************** Sockets to communicate with GNU RADIO  ****************************************************

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
##*********************************************************************************************************************

# GNU Radio params interface
MPD = MultipleParamDispatcher(Param2AddrMap)
MPD.setParam('samp_rate', 20E06) # initial change of params required by GNU Radio project to operate
MPD.setParam('samp_rate', 5E06)
# MPD.setParam('rx_if_gain', 30)
# MPD.setParam('rx_vga_gain', 15)


# Message communicator to/from GNU Radio
MessageEcho_ = MessageEcho(N_msgs     = 10,
                           send_delay = 0.01,
                           PUB_addr   = PUB_addr,
                           SUB_addr   = SUB_addr,
                           verbose= verbose)

# N_rcvd= MessageEcho_.evaluateChnl(N_sent)
#print('{} messages were received out of {} sent'.format(N_rcvd, N_sent))


#************************* GNU RADIO PARAMS OPTIMIZATION  *************************************************************
param_bounds_dict = OrderedDict({
                                        'freq': (2.4E09, 2.5E09),
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
    return(N_echoed)


param_bounds_list = list(param_bounds_dict.values())
res = gp_minimize(channelRate,                  # the function to minimize
                  param_bounds_list,      # the bounds on each dimension of x
                  acq_func="EI",      # the acquisition function
                  n_calls=15,         # the number of evaluations of f
                  n_random_starts=5,  # the number of random initialization points
                  noise=0.1**2,       # the noise level (optional)
                  random_state=1234)   # the random seed


print(res)
# N_rcvd= MessageEcho_.evaluateChnl(N_sent)
# print('{} messages were received out of {} sent'.format(N_rcvd, N_sent))