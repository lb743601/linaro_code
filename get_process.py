import time

import cv2
import numpy as np
from skimage import feature
import gxipy as gx
from PIL import Image
from time import sleep
from periphery import Serial
serial = Serial("/dev/ttyS0", 9600)

class camera:
    def __init__(self):
        self.device_manager = gx.DeviceManager()
        dev_num, dev_info_list = self.device_manager.update_device_list()
        if dev_num == 0:
            print("Number of enumerated devices is 0")
            return

    def open_camera(self):
        self.cam = self.device_manager.open_device_by_index(1)

        # exit when the camera is a mono camera
        if self.cam.PixelColorFilter.is_implemented() is False:
            print("This sample does not support mono camera.")
            self.cam.close_device()
            return
        # set continuous acquisition
        self.cam.TriggerMode.set(gx.GxSwitchEntry.OFF)

    def set_ex_gain(self, ex, gain):
        self.cam.ExposureTime.set(ex)

        # set gain
        self.cam.Gain.set(gain)

        # get param of improving image quality
        if self.cam.GammaParam.is_readable():
            gamma_value = self.cam.GammaParam.get()
            self.gamma_lut = gx.Utility.get_gamma_lut(gamma_value)
        else:
            self.gamma_lut = None
        if self.cam.ContrastParam.is_readable():
            contrast_value = self.cam.ContrastParam.get()
            self.contrast_lut = gx.Utility.get_contrast_lut(contrast_value)
        else:
            self.contrast_lut = None
        if self.cam.ColorCorrectionParam.is_readable():
            self.color_correction_param = self.cam.ColorCorrectionParam.get()
        else:
            self.color_correction_param = 0

    def stream_on(self):
        self.cam.stream_on()

    def stream_off(self):
        self.cam.stream_off()

    def close_crema(self):
        self.cam.close_device()


    def get_current_image(self):
        raw_image = self.cam.data_stream[0].get_image()
        if raw_image is None:
            return None
        rgb_image = raw_image.convert("RGB")
        #rgb_image.image_improvement(self.color_correction_param, self.contrast_lut, self.gamma_lut)
        numpy_image = rgb_image.get_numpy_array()
        return numpy_image

    def save_image(self):
        np_image = self.get_current_image()
        img = Image.fromarray(np_image, 'RGB')
        img.save("image22.jpg")


def closest_color(np_image):
    # 定义纯黄色和纯绿色
    yellow = np.array([0, 255, 255], dtype=np.uint8)
    green = np.array([0, 255, 0], dtype=np.uint8)

    # 计算每个像素到黄色和绿色的距离
    dist_to_yellow = np.linalg.norm(np_image - yellow, axis=-1)
    dist_to_green = np.linalg.norm(np_image - green, axis=-1)

    # 生成一个布尔掩码，用于选择黄色或绿色
    mask = dist_to_yellow < dist_to_green

    # 应用掩码
    np_image[mask] = yellow
    np_image[~mask] = green
    return np_image
def closest_color_hsv(np_image):
    # 转换到HSV空间
    hsv_image = cv2.cvtColor(np_image, cv2.COLOR_BGR2HSV)

    # 计算每个像素的色调、饱和度、明度
    hue, sat, val = cv2.split(hsv_image)

    # 定义黄色和绿色的色调范围（在OpenCV中）
    yellow_lower, yellow_upper = 15, 30
    green_lower, green_upper = 30, 80

    # 判断每个像素的颜色
    yellow_mask = np.logical_and(hue >= yellow_lower, hue <= yellow_upper)
    green_mask = np.logical_and(hue >= green_lower, hue <= green_upper)

    # 应用掩码
    np_image[yellow_mask] = [0, 255, 255]  # BGR for yellow
    np_image[green_mask] = [0, 255, 0]     # BGR for green

    return np_image


import cv2
import numpy as np


# ... [之前的camera类和closest_color_hsv函数代码] ...

# def detect_and_draw_vertical_line(np_image):
#     # 边缘检测
#     edges = cv2.Canny(np_image, 50, 150)
#
#     # 使用霍夫变换检测直线
#     lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)
#
#     # 找到最佳垂直线
#     if lines is not None:
#         best_line = None
#         max_len = 0
#         for line in lines:
#             for rho, theta in line:
#                 a = np.cos(theta)
#                 b = np.sin(theta)
#                 if b != 0 and abs(a / b) < 1:  # 过滤非垂直线
#                     continue
#                 x0 = a * rho
#                 y0 = b * rho
#                 x1 = int(x0 + 1000 * (-b))
#                 y1 = int(y0 + 1000 * (a))
#                 x2 = int(x0 - 1000 * (-b))
#                 y2 = int(y0 - 1000 * (a))
#                 line_len = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
#                 if line_len > max_len:
#                     max_len = line_len
#                     best_line = (x1, y1, x2, y2)
#
#         # 在原图上绘制最佳垂直线
#         if best_line is not None:
#             cv2.line(np_image, (best_line[0], best_line[1]), (best_line[2], best_line[3]), (0, 0, 255), 2)
#
#     return np_image

def detect_and_draw_vertical_line(np_image):
    # 边缘检测
    edges = cv2.Canny(np_image, 50, 150)

    # 使用霍夫变换检测直线
    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)

    # 初始化返回值
    status = -1  # 分割线状态
    mid_x = -1   # 分割线中点横坐标
    side = -1    # 分割线左侧区域颜色

    # 找到最佳垂直线
    if lines is not None:
        best_line = None
        max_len = 0
        for line in lines:
            for rho, theta in line:
                a = np.cos(theta)
                b = np.sin(theta)
                if b != 0 and abs(a / b) < 1:  # 过滤非垂直线
                    continue
                x0 = a * rho
                y0 = b * rho
                x1 = int(x0 + 1000 * (-b))
                y1 = int(y0 + 1000 * (a))
                x2 = int(x0 - 1000 * (-b))
                y2 = int(y0 - 1000 * (a))
                line_len = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                if line_len > max_len:
                    max_len = line_len
                    best_line = (x1, y1, x2, y2)

        # 在原图上绘制最佳垂直线
        if best_line is not None:
            print(best_line[0],best_line[1],best_line[2],best_line[3])
            mid_x = (best_line[0] + best_line[2]) // 2
            cv2.line(np_image, (best_line[0], best_line[1]), (best_line[2], best_line[3]), (0, 0, 255), 2)
            status = 3
            # 检查左侧区域颜色
            if np_image[:, 0:mid_x].mean() > np_image[:, mid_x:].mean():
                side = 1  # 左侧黄色
            else:
                side = 2  # 左侧绿色

    # 如果没有找到分割线，判断整个画面的颜色
    if status == -1:
        if np_image.mean() > 128:  # 阈值128用于判断颜色主导
            status = 1  # 主要为黄色
        else:
            status = 0  # 主要为绿色

    return status, mid_x, side, np_image

if __name__ == "__main__":
    c = camera()
    c.open_camera()
    c.stream_on()
    c.set_ex_gain(40000, 10)

    while True:
        np_image = c.get_current_image()
        #time.sleep(0.5)
        if np_image is not None:
            np_image = cv2.resize(np_image, (400, 300))
            np_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2BGR)

            # #cv2.imshow("Ori Image", np_image)
            #
            # processed_image = closest_color_hsv(np_image)
            # processed_image = cv2.GaussianBlur(processed_image, (9, 9), 0)
            # x= detect_and_draw_vertical_line(processed_image)
            # #x[0]为0代表全绿，x[0]为1代表全黄，x[0]为3代表黄绿，x[1]为分割线中点横坐标，x[2]为1则代表左黄右绿，为2代表左绿右黄
            # if(x[0]==0):
            #     number=255
            # if(x[0]==1):
            #     number=0
            # if(x[0]==3):
            #     if(x[2]==1):
            #         number=128+int(100*x[1]/612)
            #     else:
            #         number=int(100*x[1]/612)
            # #11111111为全绿，00000000为全黄，否则1开头为左黄右绿，0开头左绿右黄
            # print(number,x[0],x[1],x[2])
            # data = number.to_bytes(1, 'big')
            # serial.write(data)
            # time.sleep(1)
            cv2.imshow("Camera Image", np_image)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    c.stream_off()
    c.close_crema()
    cv2.destroyAllWindows()

