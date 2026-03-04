import numpy as np
import matplotlib.pyplot as plt
from rfsoc_rfdc.plotter.plot_format import PlotFormat


class EvmPlot:
    def __init__(self, modu_list, snr_mat, evm_mat, fmt, auto_thres=True, thres=0.0):
        self.modu_list = modu_list
        self.snr_mat = snr_mat
        self.evm_mat = evm_mat
        self.format = fmt
        # QPSK, 16QAM, 64QAM, 256QAM
        self.evm_thres = [0.175, 0.125, 0.08, 0.035]
        self.auto_thres = auto_thres
        self.thres = thres

    def plot(self, save_path_png='SNR_EVM.png', save_path_pdf='SNR_EVM.pdf'):
        fig, ax = plt.subplots(
            figsize=(self.format.figSizeX, self.format.figSizeY))
        ax.set_position((self.format.axPosX, self.format.axPosY,
                        self.format.axSizeX, self.format.axSizeY))

        for idx, modu in enumerate(self.modu_list):
            snr_list = self.snr_mat[idx]
            evm_list = self.evm_mat[idx]
            assert len(snr_list) == len(evm_list)

            ax.plot(snr_list, evm_list,
                    color=self.format.colorList[idx],
                    linewidth=self.format.lineWidth, linestyle=self.format.lineStyleList[0],
                    marker=self.format.markerList[idx], markersize=self.format.markerSizeList[1]*0.8,
                    markerfacecolor='none', label=modu, zorder=3)
            ax.plot(snr_list, evm_list,
                    color=self.format.colorList[idx], alpha=0.5,
                    marker=self.format.markerList[idx], markersize=self.format.markerSizeList[1]*0.8,
                    markerfacecolor=self.format.colorList[idx], zorder=3)

        ax.grid(zorder=0)
        ax.set_xlabel('SNR (dB)', fontsize=self.format.fontLabel)
        ax.set_xticks([0, 10, 20, 30, 40])
        ax.set_xticklabels([0, 10, 20, 30, 40], fontsize=self.format.fontTick)
        ax.set_xlim(left=0, right=40)

        ax.set_ylabel('EVM (%)', fontsize=self.format.fontLabel)
        ax.set_yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5])
        ax.set_yticklabels(['0', '10', '20', '30', '40', '50'],
                           fontsize=self.format.fontTick)
        ax.set_ylim(bottom=0, top=0.5)

        if self.auto_thres:
            for idx, thres in enumerate(self.evm_thres):
                ax.hlines(thres, xmin=-100, xmax=+100, linewidth=self.format.lineWidth,
                          linestyle='dashed', color=self.format.colorList[idx], zorder=3)
        else:
            ax.hlines(self.thres, xmin=-100, xmax=+100, linewidth=self.format.lineWidth,
                      linestyle='dashed', color='tab:gray', zorder=3)

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
    evmMat = [
        [0.024, 0.026, 0.026, 0.028, 0.036, 0.048, 0.066,
            0.09, 0.132, 0.177, 0.248, 0.347, 0.451, 0.636],
        [0.035, 0.032, 0.03, 0.03, 0.037, 0.05, 0.067,
            0.093, 0.126, 0.174, 0.22, 0.263, 0.442, 0.438],
        [0.024, 0.022, 0.023, 0.027, 0.037, 0.048, 0.067,
            0.09, 0.112, 0.13, 0.144, 0.18, 0.328, 0.349],
        [0.024, 0.026, 0.027, 0.028, 0.037, 0.047, 0.057,
            0.066, 0.069, 0.077, 0.09, 0.173, 0.274, 0.353],
        [0.023, 0.022, 0.022, 0.024, 0.029, 0.032, 0.034, 0.037, 0.042, 0.06, 0.088, 0.132, 0.2, 0.27]]

    evm_plotter = EvmPlot(moduList, snrMat, evmMat, format)
    evm_plotter.plot()
