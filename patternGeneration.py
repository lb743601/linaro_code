import cv2
import numpy as np
def pG(image):
    sigma = 10  # sigma = a * complex_index + b
    blurred_image = cv2.GaussianBlur(image, (5, 5), sigma)
    pixels = image.reshape((-1, 3))
    pixels = np.float32(pixels)
    classNum = 2
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 1000, 0.2)
    _, labels, centers = cv2.kmeans(pixels, classNum, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    centers = np.uint8(centers)
    control_matrix = labels.flatten()
    control_matrix = control_matrix.reshape(image.shape[0], image.shape[1])
    control_matrix = np.float32(control_matrix)
    # control_matrix_temp = cv2.normalize(control_matrix, None, 0, 255, cv2.NORM_MINMAX)
    # control_matrix_uint8 = control_matrix_temp.astype(np.uint8)
    control_matrix = cv2.resize(control_matrix, (8, 8), interpolation=cv2.INTER_NEAREST)
    control_matrix = control_matrix == 1.0
    return control_matrix,centers
if __name__ == '__main__':
    # read color image
    image = cv2.imread('./data/grass.png', cv2.IMREAD_COLOR)
    control_matrix,centers=pG(image)

