# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


from time import sleep
import zmq
import pmt
from multiprocessing import Process, Queue

class MessageEcho():
    # TODO: if exactly 0 messages received error should be raised
    # TODO: check if the received messages coincide with the messages sent
    # TODO: add handling the busy socket address error
    # TODO: various verbosity levels, status messages


    """
    This object  sends and receives back messages from SDR
    through ZeroMQ PUB/SUB sockets.
    """

    def __init__(self, SUB_addr= "tcp://*:52004",
                       PUB_addr= "tcp://192.168.0.84:52001",
                       send_delay= .1,
                       init_delay= 1

                 ):
        '''
        ARGUMENTS:
            SUB_addr -- ZMQ socket address from which to receive messages
            PUB_addr -- ZMQ socket address  to send messages to
            delay -- pause between messages sent
            init_delay -- pause for SUB socket to initialize before sending
        '''

        self.SUB_addr= SUB_addr
        self.PUB_addr= PUB_addr
        self.send_delay= send_delay
        self.init_delay= init_delay



    def sendMsgs(self, N_messages):

        context = zmq.Context()
        socket_PUB = context.socket(zmq.PUB)
        bind_result = socket_PUB.bind(self.PUB_addr)
        sleep(self.init_delay)


        test_msg= 'TEST'
        for i in range(N_messages):
            i += 1
            sleep(self.send_delay)
            pmt_msg = pmt.to_pmt(test_msg + str(i))
            socket_PUB.send(pmt.serialize_str(pmt_msg))




    def recvMsgs(self, queue):

        context = zmq.Context()
        socket_SUB = context.socket(zmq.SUB)
        connect_result = socket_SUB.connect(self.SUB_addr)
        socket_SUB.setsockopt(zmq.SUBSCRIBE, b'')

        while True:

            msg_echoed = socket_SUB.recv()
            msg_echoed = pmt.to_python(pmt.deserialize_str(msg_echoed))

            print('Received message:{}'.format(msg_echoed))
            queue.put(msg_echoed)


    def evaluateChnl(self, N_msgs):
        '''
        sends N_msgs over the channel
        returns quantity of messages received
        '''

        Q_recv= Queue()
        sendProcess= Process(target= self.sendMsgs, args= (N_msgs,))
        recvProcess= Process(target= self.recvMsgs, args=(Q_recv,) )

        sendProcess.start()
        recvProcess.start()
        sendProcess.join()
        sendProcess.terminate()
        recvProcess.terminate()


        return(Q_recv.qsize())



if __name__ == '__main__':


    N_sent= 10
    MessageEcho_ = MessageEcho()
    N_rcvd= MessageEcho_.evaluateChnl(N_sent)
    print('{} messages were received out of {} sent'.format(N_rcvd, N_sent))