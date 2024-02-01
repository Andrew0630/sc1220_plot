import tkinter as tk
from tkinter import filedialog
import queue
import threading
import time
import serial


def test(n):
    a, b = 0, 1
    while a < n:
        print(a, end=' ')
        a, b = b, a+b
    print()


class ReadLine:
    def __init__(self, s):
        self.buf = bytearray()
        self.s = s

    def readline(self):
        i = self.buf.find(b"\n")
        if i >= 0:
            r = self.buf[:i+1]
            self.buf = self.buf[i+1:]
            return r
        while True:
            i = max(1, min(2048, self.s.in_waiting))
            data = self.s.read(i)
            i = data.find(b"\n")
            if i >= 0:
                r = self.buf + data[:i+1]
                self.buf[0:] = data[i+1:]
                return r
            else:
                self.buf.extend(data)


class SC1220_object(object):
    # 建構式
    # number of Chirp
    noc = 0
    # 取樣點
    NFFT = 0
    # Chirp time unit: us
    TC = 55
    # bandwidth unit: MHz
    BW = 6800
    # fs unit: KHz
    fs_IQ = 0
    # chirp rate
    fram_cc_rate = 0
    # arrange data
    # in the structure of [([],[]),([],[]), .. ([],[])]
    # It is a list of tuples.  There are noc tuples.  In each tuple, there are one list of I, and one list of Q.
    data_R1 = []
    data_R2 = []
    data_R3 = []
    data_R4 = []
    tempI = []
    tempQ = []
    get_rx1 = 0
    get_rx2 = 0
    get_rx3 = 0
    get_rx4 = 0
    t_run = False
    start_get_data = 0
    drawn_done = 0

    def __init__(self):
        self.drawn_done = 1
        pass

    def start(self, *arg):
        com_port = arg[0]
        m_queue = arg[1]
        if (not len(com_port)):
            # use file dialog to get filename
            root = tk.Tk()
            root.withdraw()
            input_file = filedialog.askopenfilename(filetypes=(
                ("text files", "*.txt"), ("all files", "*.*")))
            if (not input_file):
                print('file path is empty')
                m_queue.put(0)
                return 0
            else:
                _get_data_from_file(input_file, self)
                print(self.data_R1[0]
                      [0][0], self.data_R1[0][1][0])
                m_queue.put(100)
                return 1
        else:
            self.sc1220_thread = threading.Thread(
                # 建立新的執行緒
                target=_get_data_from_uart, args=(com_port, m_queue, self))
            self.sc1220_thread.daemon = True
            self.sc1220_thread.start()
            return 1

    def stop(self, m_queue):
        if not self.t_run:
            m_queue.put(0)
        self.t_run = False


def _proc_data(line, sc1220_ob):

    if line[0:len("IQ_DATA_START")] == "IQ_DATA_START":
        sc1220_ob.data_R1 = []
        sc1220_ob.data_R2 = []
        sc1220_ob.data_R3 = []
        sc1220_ob.data_R4 = []
        # sc1220_ob.start = 1
    elif line[0:len("Chirp number:")] == "Chirp number:":
        sc1220_ob.start_get_data = 1
        sc1220_ob.noc = int(line[len("Chirp number: "):-1])
        print('noc =', sc1220_ob.noc)
    elif line[0:len("Chirp points:")] == "Chirp points:":
        sc1220_ob.NFFT = int(line[len("Chirp points: "):-1])
        print('NFFT =', sc1220_ob.NFFT)
    elif line[0:len("Bandwidth_MHz:")] == "Bandwidth_MHz:":
        sc1220_ob.BW = int(line[len("Bandwidth_MHz: "):-1])
        print('bandwidth =', sc1220_ob.BW)
    elif line[0:len("Chirp time_us:")] == "Chirp time_us:":
        sc1220_ob.TC = int(line[len("Chirp time_us: "):-1])
        print('chirp time =', sc1220_ob.TC)
    elif line[0:len("Chirp rate:")] == "Chirp rate:":
        sc1220_ob.fram_cc_rate = int(line[len("Chirp rate: "):-1])
        print('chirp time =', sc1220_ob.TC)
    elif line[0:len("FS_IQ_KHz:")] == "FS_IQ_KHz:":
        sc1220_ob.fs_IQ = float(line[len("FS_IQ_KHz: "):-1])
        print('fs_IQ =', sc1220_ob.fs_IQ)
    elif line[0:len("IQ_DATA_END")] == "IQ_DATA_END":
        # 結束
        if (sc1220_ob.start_get_data):
            sc1220_ob.start_get_data = 0
            return 1
    elif line[0:len("Chirp_")] == "Chirp_":
        # Chirp 資料段開始, init 資料陣列
        sc1220_ob.get_rx1 = 0
        sc1220_ob.get_rx2 = 0
        sc1220_ob.get_rx3 = 0
        sc1220_ob.get_rx4 = 0
    elif line[0:len("RX1=====")] == "RX1=====":
        sc1220_ob.tempI = []
        sc1220_ob.tempQ = []
        sc1220_ob.get_rx1 = 1
        sc1220_ob.get_rx2 = 0
        sc1220_ob.get_rx3 = 0
        sc1220_ob.get_rx4 = 0
    elif line[0:len("RX2=====")] == "RX2=====":
        sc1220_ob.tempI = []
        sc1220_ob.tempQ = []
        sc1220_ob.get_rx1 = 0
        sc1220_ob.get_rx2 = 1
        sc1220_ob.get_rx3 = 0
        sc1220_ob.get_rx4 = 0
    elif line[0:len("RX3=====")] == "RX3=====":
        sc1220_ob.tempI = []
        sc1220_ob.tempQ = []
        sc1220_ob.get_rx1 = 0
        sc1220_ob.get_rx2 = 0
        sc1220_ob.get_rx3 = 1
        sc1220_ob.get_rx4 = 0
    elif line[0:len("RX4=====")] == "RX4=====":
        sc1220_ob.tempI = []
        sc1220_ob.tempQ = []
        sc1220_ob.get_rx1 = 0
        sc1220_ob.get_rx2 = 0
        sc1220_ob.get_rx3 = 0
        sc1220_ob.get_rx4 = 1
    elif line[0:len("RX_END=====")] == "RX_END=====":
        if (sc1220_ob.get_rx1 == 1):
            sc1220_ob.data_R1.append((sc1220_ob.tempI, sc1220_ob.tempQ))
        elif (sc1220_ob.get_rx2 == 1):
            sc1220_ob.data_R2.append((sc1220_ob.tempI, sc1220_ob.tempQ))
        elif (sc1220_ob.get_rx3 == 1):
            sc1220_ob.data_R3.append((sc1220_ob.tempI, sc1220_ob.tempQ))
        elif (sc1220_ob.get_rx4 == 1):
            sc1220_ob.data_R4.append((sc1220_ob.tempI, sc1220_ob.tempQ))
        sc1220_ob.get_rx1 = 0
        sc1220_ob.get_rx2 = 0
        sc1220_ob.get_rx3 = 0
        sc1220_ob.get_rx4 = 0
    elif ((sc1220_ob.get_rx1 == 1) | (sc1220_ob.get_rx2 == 1) | (sc1220_ob.get_rx3 == 1) | (sc1220_ob.get_rx4 == 1)):
        dot = line[:-1].split(',')
        sc1220_ob.tempI.append(int(dot[0]))
        sc1220_ob.tempQ.append(int(dot[1]))

    return 0


def _get_data_from_file(filename, sc1220_ob):
    with open(filename) as file_obj:
        line = file_obj.readline()

        # 每次讀取一行 判斷
        while (len(line)):
            print(line)
            if line[0:len("IQ_DATA_START")] == "IQ_DATA_START":
                sc1220_ob.data_R1 = []
                sc1220_ob.data_R2 = []
                sc1220_ob.data_R3 = []
                sc1220_ob.data_R4 = []
            elif line[0:len("Chirp number:")] == "Chirp number:":
                sc1220_ob.noc = int(line[len("Chirp number: "):-1])
                print('noc =', sc1220_ob.noc)
            elif line[0:len("Chirp points:")] == "Chirp points:":
                sc1220_ob.NFFT = int(line[len("Chirp points: "):-1])
                print('NFFT =', sc1220_ob.NFFT)
            elif line[0:len("Bandwidth_MHz:")] == "Bandwidth_MHz:":
                sc1220_ob.BW = int(line[len("Bandwidth_MHz: "):-1])
                print('bandwidth =', sc1220_ob.BW)
            elif line[0:len("Chirp time_us:")] == "Chirp time_us:":
                sc1220_ob.TC = int(line[len("Chirp time_us: "):-1])
                print('chirp time =', sc1220_ob.TC)
            elif line[0:len("FS_IQ_KHz:")] == "FS_IQ_KHz:":
                sc1220_ob.fs_IQ = float(line[len("FS_IQ_KHz: "):-1])
                print('fs_IQ =', sc1220_ob.fs_IQ)
            elif line[0:len("IQ_DATA_END")] == "IQ_DATA_END":
                # 結束
                break
            elif line[0:len("Chirp_")] == "Chirp_":
                # Chirp 資料段開始, init 資料陣列
                pass
            elif line[0:len("RX1=====")] == "RX1=====":
                sc1220_ob.tempI = []
                sc1220_ob.tempQ = []
                for i in range(sc1220_ob.NFFT):
                    line = file_obj.readline()
                    dot = line[:-1].split(',')
                    sc1220_ob.tempI.append(int(dot[0]))
                    sc1220_ob.tempQ.append(int(dot[1]))
                # print("I-", tempI)
                # print("Q-", tempQ)
                # print("--", sc1220_ob.data_R1)
                sc1220_ob.data_R1.append((sc1220_ob.tempI, sc1220_ob.tempQ))
                # print("----", sc1220_ob.data_R1)

                for num in range(len(sc1220_ob.data_R1)):
                    print(num, sc1220_ob.data_R1[num]
                          [0][0], sc1220_ob.data_R1[num][1][0])
            elif line[0:len("RX2=====")] == "RX2=====":
                sc1220_ob.tempI = []
                sc1220_ob.tempQ = []
                for i in range(sc1220_ob.NFFT):
                    line = file_obj.readline()
                    dot = line[:-1].split(',')
                    sc1220_ob.tempI.append(int(dot[0]))
                    sc1220_ob.tempQ.append(int(dot[1]))
                sc1220_ob.data_R2.append((sc1220_ob.tempI, sc1220_ob.tempQ))
            elif line[0:len("RX3=====")] == "RX3=====":
                sc1220_ob.tempI.clear()
                sc1220_ob.tempQ.clear()
                for i in range(sc1220_ob.NFFT):
                    line = file_obj.readline()
                    dot = line[:-1].split(',')
                    sc1220_ob.tempI.append(int(dot[0]))
                    sc1220_ob.tempQ.append(int(dot[1]))
                sc1220_ob.data_R3.append((sc1220_ob.tempI, sc1220_ob.tempQ))
            elif line[0:len("RX4=====")] == "RX4=====":
                sc1220_ob.tempI = []
                sc1220_ob.tempQ = []
                for i in range(sc1220_ob.NFFT):
                    line = file_obj.readline()
                    dot = line[:-1].split(',')
                    sc1220_ob.tempI.append(int(dot[0]))
                    sc1220_ob.tempQ.append(int(dot[1]))
                sc1220_ob.data_R4.append((sc1220_ob.tempI, sc1220_ob.tempQ))
            line = file_obj.readline()

        file_obj.close()


def _get_data_from_uart(port, m_queue, sc1220_ob):
    print('open com port ' + port)
    ser = serial.Serial(port, 921600)
    try:
        if ser.isopen():
            ser.close()
            ser.open()
        else:
            ser.open()
    except:
        ser.close()
        ser.open()
    counter = 1
    sc1220_ob.t_run = True
    rl = ReadLine(ser)
    while (sc1220_ob.t_run):
        try:
            line = rl.readline()
            line_str = line.decode("utf-8")

            if (sc1220_ob.drawn_done):
                if (_proc_data(line_str, sc1220_ob) == 1):
                    print("get data R1 " + str(len(sc1220_ob.data_R1)) + " R2 " + str(len(sc1220_ob.data_R2)) + " R3 "
                          + str(len(sc1220_ob.data_R3)) + " R4 " + str(len(sc1220_ob.data_R4)))
                    # if ((len(sc1220_ob.data_R1) == 1) & (len(sc1220_ob.data_R2) == 1) & (len(sc1220_ob.data_R3) == 1) & (len(sc1220_ob.data_R4) == 1)):
                    sc1220_ob.drawn_done = 0
                    m_queue.put(100)
        except Exception as e:
            print(e)

    ser.close()
    m_queue.put(0)  # exit


if __name__ == "__main__":
    import sys
    test(int(sys.argv[1]))
