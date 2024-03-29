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
            if ((amp >= amp_next) & (amp >= 5000)):
                print("-----peak at ", i, " value =", amp,
                      r_fft[i], " freq.=", freq[i], " KHz")
                freq_peak.append(freq[i])

    return freq_peak

# 劃出頻譜圖


def polt_fft_(ch, data_I, data_Q, bm, init):
    print('==========RX '+str(ch)+'==========')

    font = {'family': 'serif',
            'color':  'white',
            'weight': 'normal',
            'size': 10,
            }
    r_fft = np.fft.fft(data_I)
    freq = np.fft.fftfreq(np.size(data_I), fs_time)
    plot_xlabel = 'Freq. (KHz) ----- fs_IQ:'+str(fs_IQ)+'KHz,number:'+str(NFFT)
    fft_peak = find_fft_peak(r_fft, freq)
    distance = calculate_range(fft_peak, TC, BW)

    if init == 0:
        # ax[ch-1, 1].plot(np.abs(r_fft))
        # for text in ax[ch-1, 1].texts:
        # text.remove()
        text = ax[ch-1, 1].text(len(r_fft)/2, 5000, distance, fontdict=font, animated=True,
                                horizontalalignment='center', bbox={'facecolor': 'red', 'alpha': 0.2, 'pad': 10})
        bm.add_artist(text)
    else:
        for text in ax[ch-1, 1].texts:
            text.set_text(distance)

    if (ch == 1):
        ax[ch-1, 1].set_title('bandwidth:'+str(BW)+'MHz, Chirp time:' +
                              str(TC)+'us', size='large')
    ax[ch-1, 1].set_xlabel(plot_xlabel)
    return r_fft


# speed of light unit: m/s
C_speed = 299792458
# Chirp time unit: us
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

plt.style.use(['dark_background'])
fig, ax = plt.subplots(4, 2, constrained_layout=True, animated=True)
plt.suptitle(t='60GHz radar plot', size='xx-large', c='b')
plt.gcf().set_size_inches(14, 8)

# ax[0, 0].set_title('Number of Chirps:' + str(noc), size='large')
ax[0, 0].set_xlabel('NFFT Point-RX1')
ax[0, 0].set_ylabel('I and Q reading')
ax[0, 1].set_ylim([0, 20000])
ax[1, 0].set_xlabel('NFFT Point-RX2')
ax[1, 0].set_ylabel('I and Q reading')
ax[1, 1].set_ylim([0, 20000])
ax[2, 0].set_xlabel('NFFT Point-RX3')
ax[2, 0].set_ylabel('I and Q reading')
ax[2, 1].set_ylim([0, 20000])
ax[3, 0].set_xlabel('NFFT Point-RX4')
ax[3, 0].set_ylabel('I and Q reading')
ax[3, 1].set_ylim([0, 20000])

bm = BlitManager(fig.canvas)
# make sure our window is on the screen and drawn

plt.show(block=False)
plt.pause(1)

line_rx1_init = 0
line_rx2_init = 0
line_rx3_init = 0
line_rx4_init = 0

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
        break
    if (msg == 100):

        data_R1 = sc1220obj.data_R1
        data_R2 = sc1220obj.data_R2
        data_R3 = sc1220obj.data_R3
        data_R4 = sc1220obj.data_R4
        print("***get data R1 " + str(len(data_R1)) + " R2 " + str(len(data_R2)) + " R3 "
              + str(len(data_R3)) + " R4 " + str(len(data_R4)))
        if ((len(data_R1) == 1) & (len(data_R2) == 1) & (len(data_R3) == 1) & (len(data_R4) == 1)):
            TC = sc1220obj.TC
            BW = sc1220obj.BW
            fs_IQ = sc1220obj.fs_IQ
            NFFT = sc1220obj.NFFT
            noc = sc1220obj.noc
            fs_time = 1/fs_IQ

            # Joint the data and plotting.
            print("fs_IQ/points =", fs_IQ/NFFT, "KHz")
            ax[0, 0].set_title('Number of Chirps:' + str(noc), size='large')
        else:
            msg = -1
            sc1220obj.drawn_done = 1

    if (msg == 100):
        # plotting Rx1
        if (len(data_R1)):
            data_I = []
            data_Q = []

            for i in range(len(data_R1)):
                data_I += data_R1[i][0]
                data_Q += data_R1[i][1]

            r_fft = polt_fft_(1, data_I, data_Q, bm, line_rx1_init)

            # plotting
            if not line_rx1_init:
                (lineRx1_I,) = ax[0, 0].plot(data_I, 'b', label='I')
                (lineRx1_Q,) = ax[0, 0].plot(data_Q, 'r', label='Q')
                (lineRx1_fft,) = ax[0, 1].plot(np.abs(r_fft))
                legend = ax[0, 0].legend(
                    loc='upper right', shadow=False, fontsize='x-small', framealpha=0.2)
                # Put a nicer background color on the legend.
                legend.get_frame().set_facecolor('C0')
                bm.add_artist(lineRx1_I)
                bm.add_artist(lineRx1_Q)
                bm.add_artist(lineRx1_fft)
                plt.draw()
                line_rx1_init = 1
            else:
                lineRx1_I.set_ydata(data_I)
                lineRx1_Q.set_ydata(data_Q)
                lineRx1_fft.set_ydata(np.abs(r_fft))

        else:
            if not line_rx1_init:
                ax[0, 0].set_title('Number of Chirps:' +
                                   str(noc), size='large')
                ax[0, 1].set_title('bandwidth:'+str(BW)+'MHz, Chirp time:' +
                                   str(TC)+'us', size='large')
                line_rx1_init = 1

        # plotting Rx2
        if (len(data_R2)):
            data_I = []
            data_Q = []

            for i in range(len(data_R2)):
                data_I += data_R2[i][0]
                data_Q += data_R2[i][1]

            r_fft = polt_fft_(2, data_I, data_Q, bm, line_rx2_init)

            # plotting
            if not line_rx2_init:
                (lineRx2_I,) = ax[1, 0].plot(data_I, 'b', label='I')
                (lineRx2_Q,) = ax[1, 0].plot(data_Q, 'r', label='Q')
                (lineRx2_fft,) = ax[1, 1].plot(np.abs(r_fft))
                legend = ax[1, 0].legend(
                    loc='upper right', shadow=False, fontsize='x-small', framealpha=0.2)
                # Put a nicer background color on the legend.
                legend.get_frame().set_facecolor('C0')
                bm.add_artist(lineRx2_I)
                bm.add_artist(lineRx2_Q)
                bm.add_artist(lineRx2_fft)
                plt.draw()
                line_rx2_init = 1
            else:
                lineRx2_I.set_ydata(data_I)
                lineRx2_Q.set_ydata(data_Q)
                lineRx2_fft.set_ydata(np.abs(r_fft))

        # plotting Rx3
        if (len(data_R3)):
            data_I = []
            data_Q = []

            for i in range(len(data_R3)):
                data_I += data_R3[i][0]
                data_Q += data_R3[i][1]

            r_fft = polt_fft_(3, data_I, data_Q, bm, line_rx3_init)

            # plotting
            if not line_rx3_init:
                (lineRx3_I,) = ax[2, 0].plot(data_I, 'b', label='I')
                (lineRx3_Q,) = ax[2, 0].plot(data_Q, 'r', label='Q')
                (lineRx3_fft,) = ax[2, 1].plot(np.abs(r_fft))
                legend = ax[2, 0].legend(
                    loc='upper right', shadow=False, fontsize='x-small', framealpha=0.2)
                # Put a nicer background color on the legend.
                legend.get_frame().set_facecolor('C0')
                bm.add_artist(lineRx3_I)
                bm.add_artist(lineRx3_Q)
                bm.add_artist(lineRx3_fft)
                plt.draw()
                line_rx3_init = 1
            else:
                lineRx3_I.set_ydata(data_I)
                lineRx3_Q.set_ydata(data_Q)
                lineRx3_fft.set_ydata(np.abs(r_fft))
        # plotting Rx4
        if (len(data_R4)):
            data_I = []
            data_Q = []

            for i in range(len(data_R4)):
                data_I += data_R4[i][0]
                data_Q += data_R4[i][1]

            r_fft = polt_fft_(4, data_I, data_Q, bm, line_rx4_init)

            # plotting
            if not line_rx4_init:
                (lineRx4_I,) = ax[3, 0].plot(data_I, 'b', label='I')
                (lineRx4_Q,) = ax[3, 0].plot(data_Q, 'r', label='Q')
                (lineRx4_fft,) = ax[3, 1].plot(np.abs(r_fft))
                legend = ax[3, 0].legend(
                    loc='upper right', shadow=False, fontsize='x-small', framealpha=0.2)
                # Put a nicer background color on the legend.
                legend.get_frame().set_facecolor('C0')
                bm.add_artist(lineRx4_I)
                bm.add_artist(lineRx4_Q)
                bm.add_artist(lineRx4_fft)
                plt.draw()
                line_rx4_init = 1
            else:
                lineRx4_I.set_ydata(data_I)
                lineRx4_Q.set_ydata(data_Q)
                lineRx4_fft.set_ydata(np.abs(r_fft))
        data_redraw = 1

    bm.update()
    if data_redraw:
        sc1220obj.drawn_done = 1
        print('redraw done ', (time.time() - start_time), 's')

    # time.sleep(0.1)

sc1220obj.stop(my_queue)
try:
    msg = my_queue.get(True, 3)
    print('get message from sc1220 thread '+str(msg))
except:
    msg = -1  # time out
# plt.show()
plt.savefig('sc1220_plot' + '.png')
