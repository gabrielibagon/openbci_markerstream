import json
import sys
import numpy as np
import time
import zmq
from pylsl import StreamInfo, StreamOutlet

class Interface:
    def __init__(self, verbose=False):
        context = zmq.Context()
        self._socket = context.socket(zmq.PAIR)
        self._socket.connect("tcp://localhost:3004")

        self.verbose = verbose

        if self.verbose:
            print("Client Ready!")

        # Send a quick message to tell node process we are up and running
        self.send(json.dumps({
            'action': 'started',
            'command': 'status',
            'message': time.time()*1000.0
        }))

    def send(self, msg):
        """
        Sends a message to TCP server
        :param msg: str
            A string to send to node TCP server, could be a JSON dumps...
        :return: None
        """
        if self.verbose:
            print('<- out ' + msg)
        self._socket.send_string(msg)
        return

    def recv(self):
        """
        Checks the ZeroMQ for data
        :return: str
            String of data
        """
        return self._socket.recv()


def initializeOutlet(interface):
    """
    Initializes and returns an LSL outlet
    :param interface: Interface
        the Python interface to communicate with node
    :return: StreamOutlet
        returns a labstreaminglayer StreamOutlet
    """
    numChans = None
    while not numChans:
        msg = interface.recv()
        try:
            dicty = json.loads(msg)
            numChans = dicty.get('numChans')
            sampleRate = dicty.get('sampleRate')
        except ValueError as e:
            print(e)
    data_info = StreamInfo('OpenBCI_EEG', 'EEG', numChans, sampleRate, 'float32', 'myuid34234')
    marker_info = StreamInfo('MarkerStream', 'Markers',1,0,'string','markerstream12345')
    data_outlet = StreamOutlet(data_info)
    marker_outlet = StreamOutlet(marker_info)

    print('init')
    return data_outlet, marker_outlet

def main(argv):
    verbose = False
    # Create a new python interface.
    interface = Interface(verbose)
    # Create a new labstreaminglayer outlet
    data_outlet,marker_outlet = initializeOutlet(interface);

    import struct
    from collections import deque
    import numpy as np
    d = deque(maxlen=3)
    TRIGGER = False

    # Stream incoming data to LSL
    while True:
        msg = interface.recv()
        # try:
        dicty = json.loads(msg)
        message = dicty.get('message')
        sensor = str(message.get('auxData')['data'][0])
        # print(struct.unpack("h",sensor))
        # sensor = parseInt(sample.auxData.toString('hex'),16);

        data=message.get('channelData')
        timeStamp = message.get('timeStamp')
        data_outlet.push_sample(data,timeStamp)
        d.append(sensor)
        if not TRIGGER:
            if sensor == '3':
                marker_outlet.push_sample(str(sensor))
                TRIGGER = True
        else:
            if all(i=='0' for i in d):
                print(d)
                TRIGGER = False


        # except BaseException as e:
        #     print(e)


if __name__ == '__main__':
    main(sys.argv[1:])
