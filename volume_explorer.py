import numpy as np
import argparse
import matplotlib.pyplot as plt
from matplotlib import gridspec as gs
from matplotlib.widgets import Slider

from imutils import load_volume, img_as_uint8


def coronal(volume, index):
    '''
    Return a coronal slice of the given volume
    '''
    return np.fliplr(np.rot90(volume[index, ...], 3))


def sagittal(volume, index):
    '''
    Return a sagittal slice of the given volume
    '''
    return np.rot90(volume[:, index, ...], 3)


def transverse(volume, index):
    '''
    Return a transverse slice of the given volume
    '''
    return volume[:, :, index, ...]


class VolumeExplorer:
    def __init__(self, volume, cmap=None, clim=None):
        # Volume to render
        self._volume = img_as_uint8(volume)

        # Data axes
        grid = gs.GridSpec(nrows=2, ncols=3, height_ratios=[8, 1])
        self._fig = plt.figure()
        # self._fig.set_size_inches(11, 8.5)
        self._cor_ax = self._fig.add_subplot(grid[0, 0])
        self._cor_ax.set_title('Coronal')
        self._sag_ax = self._fig.add_subplot(grid[0, 1])
        self._sag_ax.set_title('Sagittal')
        self._trans_ax = self._fig.add_subplot(grid[0, 2])
        self._trans_ax.set_title('Transverse')
        for ax in (self._cor_ax, self._sag_ax, self._trans_ax):
            ax.axis('off')
        plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, wspace=0.3, hspace=0.1)

        # Depth sliders
        self._cor_slider = Slider(self._fig.add_subplot(grid[1, 0]), '', 1, volume.shape[0], valinit=1, valstep=1, valfmt='%d')
        self._cor_slider.on_changed(self._update_cor)
        self._sag_slider = Slider(self._fig.add_subplot(grid[1, 1]), '', 1, volume.shape[1], valinit=1, valstep=1, valfmt='%d')
        self._sag_slider.on_changed(self._update_sag)
        self._trans_slider = Slider(self._fig.add_subplot(grid[1, 2]), '', 1, volume.shape[2], valinit=1, valstep=1, valfmt='%d')
        self._trans_slider.on_changed(self._update_trans)

        # Initialize images
        self._cor_img = self._cor_ax.imshow(coronal(self._volume, 0), cmap=cmap, origin='lower')
        self._sag_img = self._sag_ax.imshow(sagittal(self._volume, 0), cmap=cmap, origin='lower')
        self._trans_img = self._trans_ax.imshow(transverse(self._volume, 0), cmap=cmap, origin='lower')
        self.set_clim(clim)

        # Initialize navigation crosshairs
        self._cor_vline = self._cor_ax.axvline(0, color='r')
        self._cor_hline = self._cor_ax.axhline(0, color='b')
        self._sag_vline = self._sag_ax.axvline(0, color='g')
        self._sag_hline = self._sag_ax.axhline(0, color='b')
        self._trans_vline = self._trans_ax.axvline(0, color='r')
        self._trans_hline = self._trans_ax.axhline(0, color='g')

    @staticmethod
    def from_directory(directory):
        return VolumeExplorer(load_volume(directory))

    def set_cmap(self, cmap):
        self._cor_img.set_cmap(cmap)
        self._sag_img.set_cmap(cmap)
        self._trans_img.set_cmap(cmap)
        self._draw()

    def set_clim(self, clim):
        clim = clim if clim else (np.min(self._volume), np.max(self._volume))
        self._cor_img.set_clim(clim[0], clim[1])
        self._sag_img.set_clim(clim[0], clim[1])
        self._trans_img.set_clim(clim[0], clim[1])

    def start(self):
        plt.show()

    def _update_cor(self, idx):
        idx -= 1
        self._cor_img.set_data(coronal(self._volume, int(idx)))
        self._sag_vline.set_xdata(idx)
        self._trans_hline.set_ydata(idx)
        self._draw()

    def _update_sag(self, idx):
        idx -= 1
        self._sag_img.set_data(sagittal(self._volume, int(idx)))
        self._cor_vline.set_xdata(idx)
        self._trans_vline.set_xdata(idx)
        self._draw()

    def _update_trans(self, idx):
        idx -= 1
        self._trans_img.set_data(transverse(self._volume, int(idx)))
        self._cor_hline.set_ydata(idx)
        self._sag_hline.set_ydata(idx)
        self._draw()

    def _draw(self):
        self._fig.canvas.draw()
        plt.pause(0.005)


if __name__ == '__main__':
    # Parse arguments
    PARSER = argparse.ArgumentParser(description='Volume Explorer')
    PARSER.add_argument('directory', help='Directory containing transverse slices of a volume')
    PARSER.add_argument('--cmap', default=None, help='Colour map')
    PARSER.add_argument('--clim', default=None, help='Colour limits')
    ARGS = PARSER.parse_args()

    # Start explorer
    EXPLORER = VolumeExplorer.from_directory(ARGS.directory)
    EXPLORER.set_cmap(ARGS.cmap)
    EXPLORER.set_clim(ARGS.clim)
    EXPLORER.start()
