import numpy as np
import cv2


def normalize(l, axis=-1):
    return np.array(l) / np.linalg.norm(l, axis=axis, keepdims=True)


def sample_bilinear(data, points):
    # Pad the input data with zeros
    data = np.lib.pad(
        data, ((1, 1), (1, 1), (0, 0)), "constant", constant_values=0)
    points = np.asarray(points) + 1

    x, y = points.T
    x0, y0 = points.T.astype(int)
    x1, y1 = x0 + 1, y0 + 1

    x0 = np.clip(x0, 0, data.shape[1]-1)
    x1 = np.clip(x1, 0, data.shape[1]-1)
    y0 = np.clip(y0, 0, data.shape[0]-1)
    y1 = np.clip(y1, 0, data.shape[0]-1)

    Ia = data[y0, x0]
    Ib = data[y1, x0]
    Ic = data[y0, x1]
    Id = data[y1, x1]

    wa = (x1-x) * (y1-y)
    wb = (x1-x) * (y-y0)
    wc = (x-x0) * (y1-y)
    wd = (x-x0) * (y-y0)
    return (Ia.T*wa).T + (Ib.T*wb).T + (Ic.T*wc).T + (Id.T*wd).T


def sample_descriptors(descriptor_map, keypoints, image_size):
    factor = np.array(descriptor_map.shape[:-1]) / np.array(image_size)
    desc = sample_bilinear(descriptor_map, keypoints*factor[::-1])
    desc = normalize(desc, axis=1)
    assert np.all(np.isfinite(desc))
    return desc


def matching(desc1, desc2, do_ratio_test=False, cross_check=True):
    if desc1.dtype == np.bool and desc2.dtype == np.bool:
        desc1, desc2 = np.packbits(desc1, axis=1), np.packbits(desc2, axis=1)
        norm = cv2.NORM_HAMMING
    else:
        desc1, desc2 = np.float32(desc1), np.float32(desc2)
        norm = cv2.NORM_L2

    if do_ratio_test:
        matches = []
        matcher = cv2.BFMatcher(norm)
        for m, n in matcher.knnMatch(desc1, desc2, k=2):
            m.distance = m.distance / n.distance
            matches.append(m)
    else:
        matcher = cv2.BFMatcher(norm, crossCheck=cross_check)
        matches = matcher.match(desc1, desc2)
    return matches_cv2np(matches)


def matches_cv2np(matches_cv):
    matches_np = np.int32([[m.queryIdx, m.trainIdx] for m in matches_cv])
    distances = np.float32([m.distance for m in matches_cv])
    return matches_np.reshape(-1, 2), distances