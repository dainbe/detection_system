import audio
import gc
import image
import lcd
import sensor
import sys
import time
import uos
import KPU as kpu
from fpioa_manager import *
from machine import I2C
from Maix import I2S, GPIO

#
# initialize
#
lcd.init()
lcd.rotation(2)
i2c = I2C(I2C.I2C0, freq=400000, scl=28, sda=29)

def set_backlight(level):
    if level > 8:
        level = 8
    if level < 0:
        level = 0
    val = (level+7) << 4
    i2c.writeto_mem(0x34, 0x91, int(val))




def initialize_camera():
    err_counter = 0
    while 1:
        try:
            sensor.reset()  # Reset sensor may failed, let's try some times
            break
        except:
            err_counter = err_counter + 1
            if err_counter == 20:
                lcd.draw_string(lcd.width()//2-100, lcd.height()//2-4,
                                "Error: Sensor Init Failed", lcd.WHITE, lcd.RED)
            time.sleep(0.1)
            continue

    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)  # QVGA=320x240
    sensor.run(1)


#
# main
#
if but_a.value() == 0:  # If dont want to run the demo
    set_backlight(0)
    print('[info]: Exit by user operation')
    sys.exit()
initialize_camera()

classes = ['aeroplane', 'bicycle', 'bird', 'boat', 'bottle', 'bus', 'car', 'cat', 'chair', 'cow', 'diningtable', 'dog', 'horse', 'motorbike', 'person', 'pottedplant', 'sheep', 'sofa', 'train', 'tvmonitor']
detect_class = ['bicycle', 'bus', 'car', 'motorbike', 'person']
bias = [1.1,1.3,1.5,1.3,1]
task = kpu.load("/sd/model/20class.kmodel")

anchor = (1.889, 2.5245, 2.9465, 3.94056, 3.99987, 5.3658, 5.155437, 6.92275, 6.718375, 9.01025)
# Anchor data is for bbox, extracted from the training sets.
kpu.init_yolo2(task, 0.5, 0.3, 5, anchor)

print('[info]: Started.')
but_stu = 1

try:
    while(True):
        #gc.collect()
        img = sensor.snapshot()
        code_obj = kpu.run_yolo2(task, img)

        if code_obj:  # object detected
            target = code_obj[0]
            max_id = 255
            max_rect = 0
            for i in code_obj:
                img.draw_rectangle(i.rect())
                '''
                text = ' ' + classes[i.classid()] + ' (' + str(int(i.value()*100)) + '%) '
                for x in range(-1,2):
                    for y in range(-1,2):
                        img.draw_string(x+i.x(), y+i.y()+(i.h()>>1), text, color=(250,205,137), scale=2,mono_space=False)
                img.draw_string(i.x(), i.y()+(i.h()>>1), text, color=(119,48,48), scale=2,mono_space=False)
                '''
                id = i.classid()
                rect_size = int(i.w() * i.h())
                print(str(int(i.value()*100))+'%')
                if i.value() > 0.6:
                    if classes[id] in detect_class:  # 検知したいものの中にあったら
                        detect_id = detect_class.index(classes[id])
                        rect_size = rect_size * bias[detect_id]

                        if rect_size > max_rect:  # 最も領域が大きいもを優先的に
                            i = target
                            max_rect = rect_size
                            max_id = detect_id

            print(max_id)

        lcd.display(img)
except KeyboardInterrupt:
    kpu.deinit(task)
    sys.exit()
