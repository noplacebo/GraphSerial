from Include.SerialData import SerialStream
from serial.tools.list_ports import comports
from Include.LiveGraph import LiveGraph, Canvas, app

port = 'COM7'
baud = 115200
data_points = 2
rows = 2
cols = 1
samples = 1000
frequency = 100


def GraphSerial():
    # print(AvailablePorts())
    graph = LiveGraph(rows, cols, samples)
    with SerialStream(port, baud, data_points, samples) as data:
        c = Canvas(graph, data, frequency)
        app.run()


def AvailablePorts():
    for port in comports():
        print(port)


GraphSerial()
