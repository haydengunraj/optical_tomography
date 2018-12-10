import numpy as np
from pathlib import Path

from skimage.io import imread, imsave
from skimage.transform import rescale, warp, ProjectiveTransform

EXTENSIONS = ('png', 'jpg')


def crop(image, top_left, width, height):
    '''
    Crop an image
    '''
    return image[top_left[1]:top_left[1] + height, top_left[0]:top_left[0] + width]


def crop_images(images, top_left, width, height):
    '''
    Crop a set of images to the same region
    '''
    return [crop(image, top_left, width, height) for image in images]


def rescale_images(images, scale, order=1):
    '''
    Rescale a set of images
    '''
    multi = False
    if len(images[0].shape) == 3:
        multi = True
    return [rescale(image, scale, order, preserve_range=True, multichannel=multi, mode='reflect', anti_aliasing=True)
            for image in images]


def projective_transform(image, original_corners, final_corners):
    '''
    Correct perspective warping
    '''
    original_corners = np.array(original_corners)
    final_corners = np.array(final_corners)

    w = np.max(final_corners[:, 0])
    h = np.max(final_corners[:, 1])

    tform = ProjectiveTransform()
    tform.estimate(final_corners, original_corners)
    warped = warp(image, tform, output_shape=(h, w))
    return warped


def projective_transform_images(images, original_corners, final_corners):
    '''
    Correct perspective warping in a set of images
    '''
    return [projective_transform(image, original_corners, final_corners) for image in images]


def load_images(path, gray=False):
    '''
    Load a list of images
    '''
    image_files = []
    path = Path(path)
    for ext in EXTENSIONS:
        image_files.extend(list(path.glob(f'*{ext}')))
    if gray:
        return [imread(str(im), as_gray=True) for im in sorted(image_files)]
    else:
        return [imread(str(im)) for im in sorted(image_files)]


def load_volume(path):
    '''
    Load a 3D volume
    '''
    return np.stack(load_images(path), axis=2)


def img_as_uint8(image):
    '''
    Convert an image to uint8
    '''
    return np.uint8((image - np.min(image))/np.ptp(image)*255)


def save_png(fname, image):
    '''
    Save the given image as fname.png
    '''
    imsave(str(fname) + '.png', img_as_uint8(image))
