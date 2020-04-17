import os
import subprocess
import sys


def showImage(img_path):
    """显示图片"""
    try:
        if sys.platform.find('darwin') >= 0:
            subprocess.call(['open', img_path])
        elif sys.platform.find('linux') >= 0:
            subprocess.call(['xdg-open', img_path])
        else:
            os.startfile(img_path)  # pylint: disable=no-member
    except Exception:
        from PIL import Image  # pylint: disable=import-outside-toplevel
        img = Image.open(img_path)
        img.show()
        img.close()
    return img_path


def removeImage(img_path):
    """删除图片"""
    if sys.platform.find('darwin') >= 0:
        os.system("osascript -e 'quit app \"Preview\"'")
    os.remove(img_path)


def saveImage(img_bytes, img_path):
    """保存图片"""
    if os.path.isfile(img_path):
        os.remove(img_path)
    fp = open(img_path, 'wb')
    fp.write(img_bytes)
    fp.close()
