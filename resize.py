import os
import glob
from PIL import Image, ImageOps, ImageEnhance

path = "Maix_Toolbox/images"
files = glob.glob(path + '*.jpg')
count = 1
print(files)

for f in files:
    img = Image.open(f)
    img_resize = img.resize((240, 240))
    img_resize.save(path + str(count) + ".jpg")

