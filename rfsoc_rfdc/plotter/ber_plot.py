import numpy as np
import matplotlib.pyplot as plt
from rfsoc_rfdc.plotter.plot_format import PlotFormat


class BerPlot:
    def __init__(self, modu_list, snr_mat, ber_mat, fmt):
        self.modu_list = modu_list
        self.snr_mat = snr_mat
        self.ber_mat = ber_mat
        self.format = fmt

    def plot(self, save_path_png='SNR_BER.png', save_path_pdf='SNR_BER.pdf'):
        fig, ax = plt.subplots(
            figsize=(self.format.figSizeX, self.format.figSizeY))
        ax.set_position((self.format.axPosX, self.format.axPosY,
                        self.format.axSizeX, self.format.axSizeY))

        for idx, modu in enumerate(self.modu_list):
            snr_list = self.snr_mat[idx]
            ber_list = [max(ber, 1e-6) for ber in self.ber_mat[idx]]
            assert len(snr_list) == len(ber_list)

            ax.plot(snr_list, ber_list,
                    color=self.format.colorList[idx],
                    linewidth=self.format.lineWidth, linestyle=self.format.lineStyleList[0],
                    marker=self.format.markerList[idx], markersize=self.format.markerSizeList[1]*0.8,
                    markerfacecolor='none', label=modu, zorder=3)
            ax.plot(snr_list, ber_list,
                    color=self.format.colorList[idx], alpha=0.5,
                    marker=self.format.markerList[idx], markersize=self.format.markerSizeList[1]*0.8,
                    markerfacecolor=self.format.colorList[idx], zorder=3)

        ax.grid(zorder=0)
        ax.set_xlabel('SNR (dB)', fontsize=self.format.fontLabel)
        ax.set_xticks([0, 10, 20, 30, 40])
        ax.set_xticklabels([0, 10, 20, 30, 40], fontsize=self.format.fontTick)
        ax.set_xlim(left=0, right=40)

        ax.set_yscale('log')
        ax.set_ylabel('BER', fontsize=self.format.fontLabel)
        ax.set_ylim(bottom=1e-5, top=0.5)
        ax.set_yticks([1e-5, 1e-4, 1e-3, 1e-2, 1e-1])
        ax.set_yticklabels(['$10^{-5}$', '$10^{-4}$', '$10^{-3}$', '$10^{-2}$', '$10^{-1}$'],
                           fontsize=self.format.fontTick - 5)

        for spine in ax.spines.values():
            spine.set_linewidth(self.format.lineWidth)

        fig.savefig(save_path_png, format='png', dpi=300)
        # fig.savefig(save_path_pdf, format='pdf')
        plt.close(fig)


if __name__ == "__main__":

    format = PlotFormat(scaleX=1, scaleY=1)

    moduList = ['QPSK', '64QAM', '256QAM', '16QAM', '1024QAM']
    snrMat = [
        [33.983, 33.809, 33.851, 33.905, 31.261, 28.174, 25.281,
            22.35, 19.036, 16.428, 13.406, 10.487, 7.707, 5.039],
        [33.39, 33.221, 33.277, 33.265, 31.278, 28.389, 25.337,
            22.383, 19.512, 16.564, 13.482, 10.661, 7.855, 5.067],
        [34.925, 34.814, 34.85, 34.081, 31.188, 28.184, 25.248,
            22.307, 19.454, 16.439, 13.479, 10.494, 7.678, 4.989],
        [34.06, 34.164, 34.253, 34.177, 31.285, 28.249, 25.33,
            22.42, 19.451, 16.413, 13.592, 10.617, 7.804, 5.147],
        [35.048, 34.898, 34.777, 34.12, 31.294, 28.285, 25.389, 22.389, 19.481, 16.399, 13.499, 10.632, 7.737, 5.05]]
    berMat = [
        [0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00,
            0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00, 2.08E-03, 1.92E-02, 6.26E-02],
        [0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00,
            0.00E+00, 2.60E-04, 4.74E-03, 2.41E-02, 5.94E-02, 1.28E-01, 1.96E-01],
        [0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00, 6.94E-05, 7.64E-04,
            5.90E-03, 2.13E-02, 5.18E-02, 1.06E-01, 1.60E-01, 2.33E-01, 2.87E-01],
        [7.81E-05, 5.21E-05, 2.60E-04, 2.86E-04, 2.45E-03, 9.69E-03, 2.60E-02,
            5.46E-02, 8.75E-02, 1.39E-01, 1.89E-01, 2.51E-01, 2.98E-01, 3.36E-01],
        [7.38E-03, 4.85E-03, 5.13E-03, 9.33E-03, 2.67E-02, 5.08E-02, 8.09E-02, 1.16E-01, 1.62E-01, 2.06E-01, 2.53E-01, 2.99E-01, 3.42E-01, 3.75E-01]]

    ber_plotter = BerPlot(moduList, snrMat, berMat, format)
    ber_plotter.plot()
