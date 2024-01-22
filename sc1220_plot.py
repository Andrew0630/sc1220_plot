# tool: plot radar IQ output using SocioNext 60GHz radar
# date: Jan 12, 2024
# coder: YT

import sys
import matplotlib.pyplot as plt
import numpy as np
import sc1220at2 as sc1220
import threading
import queue

# 計算每個 fft peak 的距離


def calculate_range(freq_peak, TC, BW):  # fs_iq Mhz
    # ((c*TC)/(2*BW)) * fb
    dis_str = ""
    range_t = (C_speed*TC/1000000)/(2*BW*1000)
    for i in range(len(freq_peak)):
        if (freq_peak[i] > 0):
            distance = range_t * freq_peak[i]
            distance -= 0.023
            peak_str = 'peak ' + \
                str(i+1)+' distance: '+str(round(distance, 4)) + \
                ' m '+str(round(distance*100, 2))+' cm'
            print('-----', peak_str)
            if (len(dis_str)):
                dis_str += '\n'+peak_str
            else:
                dis_str += peak_str

    return dis_str

# 找出 fft 中的 peak 頻率


def find_fft_peak(r_fft, freq):
    freq_peak = []
    for i in range(1, len(r_fft)-1):
        amp_last = (r_fft.real[i-1] ** 2 + r_fft.imag[i-1] ** 2)**0.5
        amp = (r_fft.real[i] ** 2 + r_fft.imag[i] ** 2)**0.5
        amp_next = (r_fft.real[i+1] ** 2 + r_fft.imag[i+1] ** 2)**0.5
        if (amp_last <= amp):
            if ((amp >= amp_next) & (amp >= 10000)):
                print("-----peak at ", i, " value =", amp,
                      r_fft[i], " freq.=", freq[i], " KHz")
                freq_peak.append(freq[i])

    return freq_peak

# 劃出頻譜圖


def polt_fft_(ch, data_I, data_Q):
    print('==========RX '+str(ch)+'==========')

    font = {'family': 'serif',
            'color':  'white',
            'weight': 'normal',
            'size': 10,
            }
    r_fft = np.fft.fft(data_I, 128*4)
    freq = np.fft.fftfreq(np.size(data_I)*4, fs_time)
    plot_xlabel = 'Freq. (KHz) ----- fs_IQ:'+str(fs_IQ)+'KHz,number:'+str(NFFT)
    fft_peak = find_fft_peak(r_fft, freq)
    distance = calculate_range(fft_peak, TC, BW)

    ax[ch-1, 1].plot(np.abs(r_fft))
    ax[ch-1, 1].text(len(r_fft)/2, 10000, distance, fontdict=font,
                     horizontalalignment='center', bbox={'facecolor': 'red', 'alpha': 0.2, 'pad': 10})
    # ax[ch-1, 1].stem(np.abs(r_fft), 'b', markerfmt=" ", basefmt="-b")
    if (ch == 1):
        ax[ch-1, 1].set_title('bandwidth:'+str(BW)+'MHz, chrip time:' +
                              str(TC)+'us', size='large')
    ax[ch-1, 1].set_xlabel(plot_xlabel)


# speed of light unit: m/s
C_speed = 299792458
# chrip time unit: us
TC = 55
# bandwidth unit: MHz
BW = 6800
# fs unit: KHz
fs_IQ = 0


sc1220obj = sc1220.SC1220_object()

# 建立佇列
my_queue = queue.Queue()
# -- Get input com port from command line input,
if (len(sys.argv) < 2):
    if not sc1220obj.start("", my_queue):
        sys.exit(0)
else:
    sc1220obj.start(sys.argv[1], my_queue)
"""
sc1220_thread = threading.Thread(
    target=sc1220_get_data_thread, args=(sc1220obj, my_queue))  # 建立新的執行緒
sc1220_thread.daemon = True
sc1220_thread.start()
"""

while (True):
    try:
        msg = my_queue.get(True, 20)
        print('get message from sc1220 thread '+str(msg))
        if (msg == 1):
            break
        elif (msg > 10000):
            break
    except:
        msg = -1
        break

# arrange data
# in the structure of [([],[]),([],[]), .. ([],[])]
# It is a list of tuples.  There are noc tuples.  In each tuple, there are one list of I, and one list of Q.
data_R1 = sc1220obj.data_R1
data_R2 = sc1220obj.data_R2
data_R3 = sc1220obj.data_R3
data_R4 = sc1220obj.data_R4
print("***get data R1 " + str(len(data_R1)) + " R2 " + str(len(data_R2)) + " R3 "
      + str(len(data_R3)) + " R4 " + str(len(data_R4)))
TC = sc1220obj.TC
BW = sc1220obj.BW
fs_IQ = sc1220obj.fs_IQ
NFFT = sc1220obj.NFFT
noc = sc1220obj.noc
fs_time = 1/fs_IQ

# Joint the data and plotting.
print("fs_IQ/points =", fs_IQ/NFFT, "KHz")

plt.style.use('dark_background')
fig, ax = plt.subplots(4, 2, constrained_layout=True)
plt.suptitle(t='60GHz radar plot', size='xx-large', c='b')
plt.gcf().set_size_inches(14, 8)

# plotting Rx1
if (len(data_R1)):
    data_I = []
    data_Q = []

    for i in range(len(data_R1)):
        data_I += data_R1[i][0]
        data_Q += data_R1[i][1]

    # plotting
    ax[0, 0].plot(data_I, 'b', label='I')
    ax[0, 0].plot(data_Q, 'r', label='Q')
    ax[0, 0].set_xlabel('NFFT Point-RX1')
    ax[0, 0].set_ylabel('I and Q reading')
    ax[0, 0].set_title('Number of Chirps:' + str(noc), size='large')
    legend = ax[0, 0].legend(
        loc='upper right', shadow=False, fontsize='x-small', framealpha=0.2)
    # Put a nicer background color on the legend.
    legend.get_frame().set_facecolor('C0')

    polt_fft_(1, data_I, data_Q)
else:
    ax[0, 0].set_title('Number of Chirps:' + str(noc), size='large')
    ax[0, 1].set_title('bandwidth:'+str(BW)+'MHz, chrip time:' +
                       str(TC)+'us', size='large')
# plotting Rx2
if (len(data_R2)):
    data_I = []
    data_Q = []

    for i in range(len(data_R2)):
        data_I += data_R2[i][0]
        data_Q += data_R2[i][1]
    # plotting
    ax[1, 0].plot(data_I, 'b', label='I')
    ax[1, 0].plot(data_Q, 'r', label='Q')
    ax[1, 0].set_xlabel('NFFT Point-RX2')
    ax[1, 0].set_ylabel('I and Q reading')
    legend = ax[1, 0].legend(
        loc='upper right', shadow=False, fontsize='x-small', framealpha=0.2)
    # Put a nicer background color on the legend.
    legend.get_frame().set_facecolor('C0')

    polt_fft_(2, data_I, data_Q)
# plotting Rx3
if (len(data_R3)):
    data_I = []
    data_Q = []

    for i in range(len(data_R3)):
        data_I += data_R3[i][0]
        data_Q += data_R3[i][1]
    # plotting
    ax[2, 0].plot(data_I, 'b', label='I')
    ax[2, 0].plot(data_Q, 'r', label='Q')
    ax[2, 0].set_xlabel('NFFT Point-RX3')
    ax[2, 0].set_ylabel('I and Q reading')
    legend = ax[2, 0].legend(
        loc='upper right', shadow=False, fontsize='x-small', framealpha=0.2)
    # Put a nicer background color on the legend.
    legend.get_frame().set_facecolor('C0')

    polt_fft_(3, data_I, data_Q)
# plotting Rx4
if (len(data_R4)):
    data_I = []
    data_Q = []

    for i in range(len(data_R4)):
        data_I += data_R4[i][0]
        data_Q += data_R4[i][1]
    # plotting
    ax[3, 0].plot(data_I, 'b', label='I')
    ax[3, 0].plot(data_Q, 'r', label='Q')
    ax[3, 0].set_xlabel('NFFT Point-RX4')
    ax[3, 0].set_ylabel('I and Q reading')
    legend = ax[3, 0].legend(
        loc='upper right', shadow=False, fontsize='x-small', framealpha=0.2)
    # Put a nicer background color on the legend.
    legend.get_frame().set_facecolor('C0')

    polt_fft_(4, data_I, data_Q)

plt.savefig('sc1220_plot' + '.png')

plt.show()
