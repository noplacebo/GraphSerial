import time
import numpy as np
import serial


class SerialStream(object):
    def __init__(self, port, baud, datapoints, samples, delim=" ", max=1500, stripped=" \n\r", progress_cbf=print):
        self.port = port
        self.baud = baud
        self.delim = delim
        self.stripped = stripped
        self.points = datapoints
        self.max = max
        self.progress_cbf = progress_cbf
        self.y = np.zeros((datapoints, samples), dtype=np.float32)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __del__(self):
        pass

    def connect(self):
        self.ser = serial.Serial(self.port, self.baud, timeout=10)
        self.progress_cbf(self.ser.isOpen())
        time.sleep(1)
        self.ser.readline()
        # self.ser.reset_output_buffer()
        self.ser.reset_input_buffer()

    def disconnect(self):
        pass

    def get_string(self):

        data = self.ser.readline()
        # self.progress_cbf(data)
        # self.progress_cbf(self.ser.inWaiting())
        self.ser.read_all()
        # self.ser.reset_output_buffer()
        # self.progress_cbf(data)
        string = data.decode('ascii')
        # self.progress_cbf(string)
        return string

    def parse_data(self, int_string):
        # Remove chars off ends
        int_string = int_string.strip(self.stripped)
        # Split data points
        int_split = int_string.split(self.delim)
        # Remove blank data points
        try:
            while True:
                int_split.remove('')
        except ValueError:
            pass
        # self.progress_cbf(int_split)
        yn = np.zeros((len(int_split), 1), dtype=np.float32)
        for n in range(len(int_split)):
            yn[n:] = int(int_split[n]) / self.max
        return yn

    def get_data(self):
        string = self.get_string()
        data_array = self.parse_data(string)
        # self.progress_cbf(data_array)
        return data_array[:self.points]
        # .astype(np.float32)


