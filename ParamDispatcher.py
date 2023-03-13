from time import sleep
import zmq
import pmt


class SingleParamDispatcher():
    '''
    Proxy to control parameter values of GNU Radio script.
    '''

    #TODO: response from GNU script on actual variable change

    def __init__(self, PUB_addr="tcp://192.168.0.84:52010",
                 init_delay= 1):
        '''
        INPUTS:
        -- PUB_addr: address to send (variable, value) message to (new value of a variable to set)
        '''
        self.PUB_addr= PUB_addr

        context = zmq.Context()
        self.socket_PUB = context.socket(zmq.PUB)
        bind_result = self.socket_PUB.bind(PUB_addr)
        sleep(init_delay)

    def setVariable(self, Variable, Value):
        '''
        -- Variable: str, name of variable to set
        -- Value: float, numerical value
        '''

        Variable_pmt= pmt.to_pmt(Variable)
        Value_pmt= pmt.from_float(Value)
        tuple_pmt= pmt.cons(Variable_pmt, Value_pmt)
        serlzd_tuple_pmt= pmt.serialize_str(tuple_pmt)
        self.socket_PUB.send(serlzd_tuple_pmt)

class MultipleParamDispatcher():
    '''
    Single interface to control many params in GNUradio project.
    Distributes the task of setting a parameter to specific SingleParamDispatcher, responsible for the param.
    On the GNUradio project side there must be a socket accepting the message for the parameter.
    '''
    def __init__(self, Param2AddrMap):
        '''
        INPUTS:
        -- Param2AddrMap: dict, pairs of ( str param_name, str address )
        '''

        self.Param2DispatcherMap = dict({}) #dict setting a dispatcher for each parameter
        for param, addr in Param2AddrMap.items():
            self.Param2DispatcherMap[param]= SingleParamDispatcher(PUB_addr= addr)

    def setParam(self, Param, Value):
        dispatcher= self.Param2DispatcherMap[Param]
        dispatcher.setVariable(Param, Value)




if __name__ == '__main__':

    Param2AddrMap= dict({'variable_1': "tcp://192.168.0.84:52010",
                         'variable_0': "tcp://192.168.0.84:52011"
                         })

    ParamDispatcher_ = MultipleParamDispatcher(Param2AddrMap)
    ParamDispatcher_.setParam('variable_0', 1000E06)
