# tool: plot radar IQ output using SocioNext 60GHz radar
# date: Jan 12, 2024
# coder: YT

import sys
import matplotlib.pyplot as plt
import numpy as np
import sc1220at2 as sc1220
import queue
import time


class BlitManager:
    def __init__(self, canvas, animated_artists=()):
        """
        Parameters
        ----------
        canvas : FigureCanvasAgg
            The canvas to work with, this only works for subclasses of the Agg
            canvas which have the `~FigureCanvasAgg.copy_from_bbox` and
            `~FigureCanvasAgg.restore_region` methods.

        animated_artists : Iterable[Artist]
            List of the artists to manage
        """
        self.canvas = canvas
        self._bg = None
        self._artists = []

        for a in animated_artists:
            self.add_artist(a)
        # grab the background on every draw
        self.cid = canvas.mpl_connect("draw_event", self.on_draw)

    def on_draw(self, event):
        """Callback to register with 'draw_event'."""
        print('Callback to register', event)
        cv = self.canvas
        if event is not None:
            if event.canvas != cv:
                raise RuntimeError
        # if self._bg is None:
            self._bg = cv.copy_from_bbox(cv.figure.bbox)
            print('Callback to register', self._bg)
        self._draw_animated()

    def add_artist(self, art):
        """
        Add an artist to be managed.

        Parameters
        ----------
        art : Artist

            The artist to be added.  Will be set to 'animated' (just
            to be safe).  *art* must be in the figure associated with
            the canvas this class is managing.

        """
        if art.figure != self.canvas.figure:
            raise RuntimeError
        art.set_animated(True)
        self._artists.append(art)

    def _draw_animated(self):
        """Draw all of the animated artists."""
        fig = self.canvas.figure
        for a in self._artists:
            fig.draw_artist(a)

    def update(self):
        """Update the screen with animated artists."""
        cv = self.canvas
        fig = cv.figure
        # paranoia in case we missed the draw event,
        if self._bg is None:
            self.on_draw(None)
        else:
            # restore the background
            cv.restore_region(self._bg)
            # draw all of the animated artists
            self._draw_animated()
            # update the GUI state
            cv.blit(fig.bbox)
        # let the GUI event loop process anything it has to do
        cv.flush_events()

# 計算每個 fft peak 的距離


def calculate_range_str(freq_peak):  # fs_iq Mhz
    # ((c*TC)/(2*BW)) * fb
    dis_str = ""

    for i in range(len(freq_peak)):
        if (freq_peak[i][0] > 0):   # a peak
            distance = freq_peak[i][1]
            peak_str = 'peak ' + \
                str(i+1)+' distance: '+str(round(distance, 4)) + \
                ' m '+str(round(distance*100, 2))+' cm'
            # print('-----', peak_str)
            if (len(dis_str)):
                dis_str += '\n'+peak_str
            else:
                dis_str += peak_str

    return dis_str

# 找出 fft 中的 peak 頻率


def find_fft_peak_and_calculate_range(r_fft, freq, TC, BW):
    range_peak = []
    range_t = (C_speed*TC/1000000)/(2*BW*1000)
    range_peak.append((0, 0, freq[0], r_fft[0]))
    for i in range(1, int(len(r_fft)/2)):
        amp_last = (r_fft[i-1].real ** 2 + r_fft[i-1].imag ** 2)**0.5
        amp = (r_fft[i].real ** 2 + r_fft[i].imag ** 2)**0.5
        amp_next = (r_fft[i+1].real ** 2 + r_fft[i+1].imag ** 2)**0.5
        peak = 0
        distance = 0
        if (amp_last <= amp):
            if ((amp >= amp_next) & (amp >= 5000)):
                peak = 1
                distance = range_t * freq[i]
                distance -= 0.023
                print("-----peak at ", i, "distance:", round(distance, 4), "m", " value =", amp,
                      r_fft[i], " freq.=", freq[i], " KHz")

        # 0:peak flag, 1:distance, 2:freq., 3:range-fft
        range_peak.append((peak, distance, freq[i], r_fft[i]))
    return range_peak


# 劃出頻譜圖


def polt_fft_(ch, data_I, data_Q, bm, init, r_fft):
    print('==========RX '+str(ch)+'==========')

    font = {'family': 'serif',
            'color':  'white',
            'weight': 'normal',
            'size': 10,
            }
    i_q_raw = []
    for i in range(len(data_I)):
        i_q_raw.append(complex(data_I[i], data_Q[i]))

    freq = np.fft.fftfreq(np.size(data_I), fs_time)
    plot_xlabel = 'Freq. (KHz) ----- fs_IQ:'+str(fs_IQ)+'KHz,number:'+str(NFFT)
    range_peak = find_fft_peak_and_calculate_range(r_fft, freq, TC, BW)

    # return distance str for text
    distance = calculate_range_str(range_peak)

    # ax[ch-1, 1].plot(np.abs(r_fft))
    if init == 0:
        text = ax[ch-1, 1].text(len(r_fft)/2, 5000, distance, fontdict=font,
                                horizontalalignment='center', bbox={'facecolor': 'red', 'alpha': 0.2, 'pad': 10})
        bm.add_artist(text)
    else:
        for text in ax[ch-1, 1].texts:
            text.set_text(distance)

    # ax[ch-1, 1].stem(np.abs(r_fft), 'b', markerfmt=" ", basefmt="-b")
    if (ch == 1):
        ax[ch-1, 1].set_title('bandwidth:'+str(BW)+'MHz, Chirp time:' +
                              str(TC)+'us', size='large')
    ax[ch-1, 1].set_xlabel(plot_xlabel)
    return range_peak


def find_doppler_fft(frame):
    doppler_fft = []
    for p in range(len(frame[0])):

        all_chirp = 1
        for c in range(len(frame)):  # 檢查每個 chirp 是不是有相同的 peak
            if not frame[c][p][0]:
                all_chirp = 0
                break
        if all_chirp:
            chirp_peaks = []
            for c in range(len(frame)):  # 取出每個 chirp 的資料 做 fft
                chirp_peaks.append(frame[c][p][3].imag)
            # print(p, chirp_peaks)
            speed_fft = np.fft.fft(chirp_peaks, len(chirp_peaks))
            print(len(chirp_peaks), len(speed_fft))
            doppler_fft.append((p, speed_fft))  # 0:peak_index, 1:doppler_fft

    return doppler_fft


# speed of light unit: m/s
C_speed = 299792458
# Chirp time unit: us
TC = 55
# bandwidth unit: MHz
BW = 6800
# fs unit: KHz
fs_IQ = 0
cc = 0

sc1220obj = sc1220.SC1220_object()

# 建立佇列
my_queue = queue.Queue()
# -- Get input com port from command line input,
if (len(sys.argv) < 2):
    if not sc1220obj.start("", my_queue):
        sys.exit(0)
else:
    sc1220obj.start(sys.argv[1], my_queue)

plt.style.use('dark_background')
fig, ax = plt.subplots(4, 2, constrained_layout=True, animated=True)
plt.suptitle(t='60GHz radar plot', size='xx-large', c='b')
plt.gcf().set_size_inches(14, 8)

# ax[0, 0].set_title('Number of Chirps:' + str(noc), size='large')
ax[0, 0].set_xlabel('NFFT Point-Chirp 1')
ax[0, 0].set_ylabel('I and Q reading')
ax[0, 1].set_ylim([0, 20000])
ax[1, 0].set_xlabel('NFFT Point-Chirp 2')
ax[1, 0].set_ylabel('I and Q reading')
ax[1, 1].set_ylim([0, 5000])
ax[2, 0].set_xlabel('NFFT Point-Chirp 3')
ax[2, 0].set_ylabel('I and Q reading')
ax[2, 1].set_ylim([0, 5000])
ax[3, 0].set_xlabel('NFFT Point-Chirp 4')
ax[3, 0].set_ylabel('I and Q reading')
ax[3, 1].set_ylim([0, 5000])

bm = BlitManager(fig.canvas)
# make sure our window is on the screen and drawn

plt.show(block=False)
plt.pause(1)
drawcount = 0
line_rx1_init = 0
line_rx2_init = 0
line_rx3_init = 0
line_rx4_init = 0
artists = []
artists_speed = []
while (True):
    data_redraw = 0

    try:
        msg = my_queue.get(True, 0.5)
        print('get message from sc1220 thread '+str(msg))
        if (msg == 100):  # get data
            pass
        elif (msg == 0):
            pass
    except:
        msg = -1  # time out

    start_time = time.time()
    if not plt.fignum_exists(1):
        print("exit")
        break
    if (msg == 100):

        data_R1 = sc1220obj.data_R1
        data_R2 = sc1220obj.data_R2
        data_R3 = sc1220obj.data_R3
        data_R4 = sc1220obj.data_R4
        print("***get data R1 " + str(len(data_R1)) + " R2 " + str(len(data_R2)) + " R3 "
              + str(len(data_R3)) + " R4 " + str(len(data_R4)))
        if ((len(data_R1) == sc1220obj.noc) & (len(data_R2) == 0) & (len(data_R3) == 0) & (len(data_R4) == 0)):
            TC = sc1220obj.TC
            BW = sc1220obj.BW
            fs_IQ = sc1220obj.fs_IQ
            NFFT = sc1220obj.NFFT
            noc = sc1220obj.noc
            fram_cc_rate = sc1220obj.fram_cc_rate
            fs_time = 1/fs_IQ

            # Joint the data and plotting.
            print("fs_IQ/points =", fs_IQ/NFFT, "KHz")
            ax[0, 0].set_title('Number of Chirps:' + str(noc), size='large')
        else:
            msg = -1
            sc1220obj.drawn_done = 1

    if (msg == 100):
        # plotting Rx1
        data_I = []
        data_Q = []
        c_count = 0
        frame_chirps_peaks = []
        for c in range(len(data_R1)):
            data_I = data_R1[c][0]
            data_Q = data_R1[c][1]

            print("I Q", c, data_I[0], data_Q[0], len(data_I), len(data_Q))
            if ((len(data_I) == NFFT) & (len(data_Q) == NFFT)):
                c_count += 1
                r_fft = np.fft.fft(data_I, NFFT)
                range_peak_per_chirp = polt_fft_(
                    1, data_I, data_Q, bm, line_rx1_init, r_fft)
                frame_chirps_peaks.append(range_peak_per_chirp)
                # plotting
                if not line_rx1_init:
                    if not c:
                        (lineRx1_I,) = ax[0, 0].plot(data_I, 'b', label='I')
                        (lineRx1_Q,) = ax[0, 0].plot(data_Q, 'r', label='Q')
                        ax[0, 1].set_ylim([0, 20000])
                        legend = ax[0, 0].legend(
                            loc='upper right', shadow=False, fontsize='x-small', framealpha=0.2)
                        # Put a nicer background color on the legend.
                        legend.get_frame().set_facecolor('C0')
                    else:
                        (lineRx1_I,) = ax[0, 0].plot(data_I, 'b')
                        (lineRx1_Q,) = ax[0, 0].plot(data_Q, 'r')
                    (lineRx1_fft,) = ax[0, 1].plot(np.abs(r_fft))

                    bm.add_artist(lineRx1_I)
                    bm.add_artist(lineRx1_Q)
                    bm.add_artist(lineRx1_fft)
                    artists.append(lineRx1_I)
                    artists.append(lineRx1_Q)
                    artists.append(lineRx1_fft)
                    plt.draw()

                else:
                    artists[c*3].set_ydata(data_I)
                    artists[c*3+1].set_ydata(data_Q)
                    artists[c*3+2].set_ydata(np.abs(r_fft))
        if (c_count == len(data_R1)):
            print('get frame', len(frame_chirps_peaks))
            doppler_fft = find_doppler_fft(frame_chirps_peaks)
            for i in range(len(doppler_fft)):

                value_buff = []
                for j in range(len(doppler_fft[i][1])):
                    value = (doppler_fft[i][1][j].real ** 2 +
                             doppler_fft[i][1][j].imag ** 2) ** 0.5
                    value_buff.append(round(value, 3))
                print('peak', doppler_fft[i][0], value_buff)
                if value_buff[0] > 10000:
                    value_buff[0] = value_buff[1] + 100
                if not line_rx1_init:
                    if (i < 3):
                        # print(doppler_fft[i][1])
                        (line_speed_fft,) = ax[i+1,
                                               1].plot(np.abs(value_buff))
                        bm.add_artist(line_speed_fft)
                        artists_speed.append(line_speed_fft)
                        plt.draw()
                else:
                    for a in range(len(artists_speed)):
                        artists_speed[a].set_ydata(np.abs(value_buff))

            line_rx1_init = 1
        data_redraw = 1

    bm.update()
    if data_redraw:
        sc1220obj.drawn_done = 1
        drawcount += 1
        print('redraw done ', (time.time() - start_time), 's')
    if (drawcount == 10):
        plt.draw()
    # time.sleep(0.1)

sc1220obj.stop(my_queue)
try:
    msg = my_queue.get(True, 3)
    print('get message from sc1220 thread '+str(msg))
except:
    msg = -1  # time out
# plt.show()
plt.savefig('sc1220_plot' + '.png')
