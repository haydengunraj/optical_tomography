import numpy as np
from pathlib import Path

from skimage.transform import iradon_sart

from imutils import load_images, crop_images, rescale_images, save_png


def sinograms(images):
    '''
    Convert intensity profiles to slice-wise sinograms
    '''
    r, c = images[0].shape[:2]
    dtype = images[0].dtype
    sinog = [np.zeros((c, len(images)), dtype=dtype) for _ in range(r)]
    for i, image in enumerate(images):
        for j in range(r):
            sinog[j][:, i] = image[r - j - 1, :]
    return sinog


def slice(sinogram, theta):
    '''
    Convert a sinogram to a slice
    '''
    return iradon_sart(sinogram, theta)


def slices(sinograms, theta):
    '''
    Convert a set of sinograms into their corresponding slices
    '''
    return[slice(sg, theta) for sg in sinograms]


def reconstruct(images, theta):
    '''
    Reconstruct a 3D volume from a set of 2D projections
    '''
    sinog = sinograms(images)
    slcs = slices(sinog, theta)
    return np.dstack(slcs)


class Reconstructor:
    def __init__(self, directory, angle_step, **kwargs):
        # Directory containing raw images
        self._directory = Path(directory)

        # Reconstruction parameters
        self._crop = False
        if kwargs.get('crop'):
            self._crop = True
            self._crop_params = (kwargs['crop']['top_left'], kwargs['crop']['width'], kwargs['crop']['height'])
        self._scale = kwargs.get('scale', 1)
        self._angle_step = angle_step

    def set_crop(self, top_left, width, height):
        '''
        Set cropping parameters
        '''
        self._top_left = top_left
        self._width = width
        self._height = height

    def set_scale(self, scale):
        '''
        Set scaling factor
        '''
        self._scale = scale

    def reconstruct(self, std_rng=1, channel_wise=True, save=True, verbose=False):
        '''
        Reconstruct the volume
        '''
        # Load images
        self._print(f'Loading images from {self._directory}...', verbose, end='')
        images = load_images(self._directory, gray=not channel_wise)
        self._print('done', verbose)

        # Crop images
        if self._crop:
            self._print('Cropping images...', verbose, end='')
            images = crop_images(images, self._crop_params[0], self._crop_params[1], self._crop_params[2])
            self._print('done', verbose)

        # Rescale images
        if self._scale != 1:
            self._print('Rescaling images...', verbose, end='')
            images = rescale_images(images, self._scale)
            self._print('done', verbose)

        # Resolve colour channels
        channels = 1
        if channel_wise and len(images[0].shape) == 3:
            channels = images[0].shape[2]
            recombined = np.stack([np.zeros((images[0].shape[1], images[0].shape[1], channels)) for _ in
                                   range(images[0].shape[0])], axis=2)

        # Parameters for saving
        if save:
            save_loc = self._directory.parent.joinpath('volumes')
            zpad = len(str(images[0].shape[0]))

        # Perform reconstructions
        volumes = []
        for ch in range(channels):
            self._print(f'Reconstructing channel {ch+1}/{channels}...', verbose, end='')
            # Create volume
            if channel_wise and channels > 1:
                images2d = [im[..., ch].squeeze() for im in images]
            else:
                images2d = images
            theta = np.arange(0, len(images2d)*self._angle_step, self._angle_step)
            volume = reconstruct(images2d, theta)
            std = np.std(volume)
            med = np.median(volume)
            volume = np.clip(volume, med - std_rng*std, med + std_rng*std)
            self._print('done', verbose)

            self._print(f'Saving channel {ch+1}/{channels}...', verbose=(verbose and save), end='')
            for i in range(volume.shape[2]):
                # Add channel data to recombined images
                if channel_wise:
                    recombined[:, :, i, ch] = volume[:, :, i]

                # Save volume
                if save:
                    folder = save_loc
                    if channel_wise:
                        folder = folder.joinpath(f'channel{str(ch).zfill(len(str(channels)))}')
                    else:
                        folder = folder.joinpath('intensity')
                    folder.mkdir(parents=True, exist_ok=True)
                    save_png(folder.joinpath(f'slice{str(i).zfill(zpad)}'), volume[..., i])
            self._print('done', verbose=(verbose and save))
        volumes.append(recombined)

        # Save recombined volume
        if channel_wise and save:
            self._print(f'Saving recombined volume...', verbose, end='')
            for i in range(recombined.shape[2]):
                folder = save_loc.joinpath('recombined')
                folder.mkdir(parents=True, exist_ok=True)
                save_png(folder.joinpath(f'slice{str(i).zfill(zpad)}'), recombined[:, :, i, :])
            self._print('done', verbose)

        return volumes

    @staticmethod
    def _print(msg, verbose, **kwargs):
        '''
        Helper for printing
        '''
        if verbose:
            print(msg, **kwargs)


if __name__ == '__main__':
    from examples.examples import EXAMPLE_DICT
    from volume_explorer import VolumeExplorer

    # Choose example
    keys = [k for k in EXAMPLE_DICT]
    for i, k in enumerate(keys):
        print(f'({i}) - {k}')
    v = input('Choose an example:\n')
    selection = keys[int(v)]
    print(f'Using example {selection}')

    # Get parameters
    obj = EXAMPLE_DICT[selection]
    channel_wise = obj.get('channel_wise', False)

    # Reconstruct
    recon = Reconstructor(**obj)
    volumes = recon.reconstruct(obj.get('std_range', 1), obj.get('channel_wise', False), save=True, verbose=True)

    # Open reconstruction
    explorer = VolumeExplorer(volumes[-1])
    explorer.start()
