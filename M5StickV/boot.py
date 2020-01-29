import gc
import image
import lcd
import sensor
import sys
import time
import uos
import KPU as kpu
from fpioa_manager import *
from machine import UART
from Maix import I2S, GPIO

#
# initialize
#

fm.register(35, fm.fpioa.UART1_TX)
fm.register(34, fm.fpioa.UART1_RX)
uart_out = UART(UART.UART1, 115200,8,0,0, timeout=1000, read_buf_len= 4096)

def initialize_camera():
    err_counter = 0
    while 1:
        try:
            sensor.reset() #Reset sensor may failed, let's try some times
            break
        except:
            err_counter = err_counter + 1
            if err_counter == 20:
                lcd.draw_string(lcd.width()//2-100,lcd.height()//2-4, "Error: Sensor Init Failed", lcd.WHITE, lcd.RED)
            time.sleep(0.1)
            continue

    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA) #QVGA=320x240
    sensor.set_vflip(True)
    sensor.run(1)

#
# main
#

initialize_camera()

classes = ['aeroplane', 'bicycle', 'bird', 'boat', 'bottle', 'bus', 'car', 'cat', 'chair', 'cow', 'diningtable', 'dog', 'horse', 'motorbike', 'person', 'pottedplant', 'sheep', 'sofa', 'train', 'tvmonitor']
detect_class = ['bicycle', 'bus', 'car', 'motorbike', 'person']
old_counter = []
bias = [1.1,1.3,1.5,1.3,1]
task = kpu.load(0x200000)

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
        counter_class = [0,0,0,0,0]

        if code_obj: # object detected
            max_id = 255
            max_rect = 0
            for i in code_obj:
                img.draw_rectangle(i.rect())
                """
                text = ' ' + classes[i.classid()] + ' (' + str(int(i.value()*100)) + '%) '
                for x in range(-1,2):
                    for y in range(-1,2):
                        img.draw_string(x+i.x(), y+i.y()+(i.h()>>1), text, color=(250,205,137), scale=2,mono_space=False)
                img.draw_string(i.x(), i.y()+(i.h()>>1), text, color=(119,48,48), scale=2,mono_space=False)
                """
                id = i.classid()
                rect_size = int(i.w() * i.h())
                if i.value() > 0.6:
                    if classes[id] in detect_class:  # 検知したいものの中にあったら
                        detect_id = detect_class.index(classes[id])
                        rect_size = rect_size * bias[detect_id]
                        counter_class[detect_id] = counter_class[detect_id] + 1
                        print(classes[id],str(int(i.value() * 100)) + "%" ,rect_size, i.w(), i.h())

                        if rect_size > max_rect:  # 最も領域が大きいもを優先的に
                            max_rect = rect_size
                            max_id = detect_id


            result = list(filter(lambda x: x not in old_counter, counter_class))
            #print(old_counter, counter_class,result)

            #if uart_out.read(4096):  # StickCに送る処理
            if result :
                if max_id < 255:
                    send_list = bytearray([max_id])
                    #print(max_id)
                    uart_out.write(send_list)

        old_counter = counter_class

        lcd.display(img)
except KeyboardInterrupt:
    kpu.deinit(task)
    sys.exit()

uart_Port.deinit()
del uart_Port
