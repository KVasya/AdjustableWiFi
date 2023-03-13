
from MessageEcho import MessageEcho
from ParamDispatcher import MultipleParamDispatcher



#**************************  GNU RADIO project params  **************************************#

# zmq SUB sockets addresses responsible for parameter changes
Param2AddrMap= dict({
                           'freq': "tcp://127.0.0.1:52010",
                     'rx_if_gain': "tcp://127.0.0.1:52011",
                    'samp_rate': "tcp://127.0.0.1:52012"
                    })

# zmq SUB sockets addresses to send (PUB) and receive (SUB) messages echoed
PUB_addr= "tcp://127.0.0.1:52002"
SUB_addr= "tcp://127.0.0.1:52003"
# TODO: single host is used, only the port varies
#*********************************************************************************************#


MPD = MultipleParamDispatcher(Param2AddrMap)
MPD.setParam('samp_rate', 20E06)
MPD.setParam('samp_rate', 5E06)
# MPD.setParam('rx_if_gain', 30)
# MPD.setParam('rx_vga_gain', 15)


N_sent= 10000
MessageEcho_ = MessageEcho(send_delay=0.01, PUB_addr= PUB_addr, SUB_addr= SUB_addr)
N_rcvd= MessageEcho_.evaluateChnl(N_sent)
print('{} messages were received out of {} sent'.format(N_rcvd, N_sent))



# N_rcvd= MessageEcho_.evaluateChnl(N_sent)
# print('{} messages were received out of {} sent'.format(N_rcvd, N_sent))