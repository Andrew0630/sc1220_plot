import tkinter as tk
from tkinter import filedialog
import queue
import threading
import time


def test(n):
    a, b = 0, 1
    while a < n:
        print(a, end=' ')
        a, b = b, a+b
    print()


class SC1220_object(object):
    # 建構式
    # number of chrip
    noc = 0
    # 取樣點
    NFFT = 0
    # chrip time unit: us
    TC = 55
    # bandwidth unit: MHz
    BW = 6800
    # fs unit: KHz
    fs_IQ = 0
    # arrange data
    # in the structure of [([],[]),([],[]), .. ([],[])]
    # It is a list of tuples.  There are noc tuples.  In each tuple, there are one list of I, and one list of Q.
    data_R1 = []
    data_R2 = []
    data_R3 = []
    data_R4 = []

    def __init__(self):
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
                m_queue.put(0)
                return 1
        else:
            sc1220_thread = threading.Thread(
                # 建立新的執行緒
                target=_get_data_from_uart, args=(com_port, m_queue, self))
            sc1220_thread.daemon = True
            sc1220_thread.start()
            return 1


def _get_data_from_file(filename, sc1220_ob):
    with open(filename) as file_obj:
        line = file_obj.readline()

        # 每次讀取一行 判斷
        while (len(line)):
            print(line)
            if line[0:len("Chirp number:")] == "Chirp number:":
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
            elif line[0:len("Chrip_")] == "Chrip_":
                # Chrip 資料段開始, init 資料陣列
                sc1220_ob.data_R1.clear()
                sc1220_ob.data_R2.clear()
                sc1220_ob.data_R3.clear()
                sc1220_ob.data_R4.clear()
            elif line[0:len("RX1=====")] == "RX1=====":
                tempI = []
                tempQ = []
                for i in range(sc1220_ob.NFFT):
                    line = file_obj.readline()
                    dot = line[:-1].split(',')
                    tempI.append(int(dot[0]))
                    tempQ.append(int(dot[1]))
                sc1220_ob.data_R1.append((tempI, tempQ))
            elif line[0:len("RX2=====")] == "RX2=====":
                tempI = []
                tempQ = []
                for i in range(sc1220_ob.NFFT):
                    line = file_obj.readline()
                    dot = line[:-1].split(',')
                    tempI.append(int(dot[0]))
                    tempQ.append(int(dot[1]))
                sc1220_ob.data_R2.append((tempI, tempQ))
            elif line[0:len("RX3=====")] == "RX3=====":
                tempI = []
                tempQ = []
                for i in range(sc1220_ob.NFFT):
                    line = file_obj.readline()
                    dot = line[:-1].split(',')
                    tempI.append(int(dot[0]))
                    tempQ.append(int(dot[1]))
                sc1220_ob.data_R3.append((tempI, tempQ))
            elif line[0:len("RX4=====")] == "RX4=====":
                tempI = []
                tempQ = []
                for i in range(sc1220_ob.NFFT):
                    line = file_obj.readline()
                    dot = line[:-1].split(',')
                    tempI.append(int(dot[0]))
                    tempQ.append(int(dot[1]))
                sc1220_ob.data_R4.append((tempI, tempQ))
            line = file_obj.readline()

        file_obj.close()


def _get_data_from_uart(port, m_queue, sc1220_ob):
    counter = 1
    while (True):
        time.sleep(1)
        counter += 1
        m_queue.put(counter)


if __name__ == "__main__":
    import sys
    test(int(sys.argv[1]))
