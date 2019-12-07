import numpy as np
from PIL import Image

def read_rle_bytes(bytes_):

    pixels = []
    line_builder = []

    i = 0
    while i < len(bytes_):
        if bytes_[i]:
            incr = 1
            color = bytes_[i]
            length = 1
        else:
            check = bytes_[i+1]
            if check == 0:
                incr = 2
                color = 0
                length = 0
                pixels.append(line_builder)
                line_builder = []
            elif check < int('01000000', 2):
                incr = 2
                color = 0
                length = check
            elif check < int('10000000', 2):
                incr = 3
                color = 0
                length = int(bin(check)[-6:] + bin(bytes_[i+2])[2:], 2)
            elif check < int('11000000', 2):
                incr = 3
                color = bytes_[i+2]
                length = check - int('10000000', 2)
            else:
                incr = 4
                color = bytes_[i+3]
                length = int(bin(check)[-6:] + bin(bytes_[i+2])[2:], 2)
        line_builder.extend([color]*length)
        i += incr

    if line_builder:
        print(f'Probably an error; hanging pixels: {line_builder}')

    return pixels
                        
def ycbcr2rgb(ar):
    xform = np.array([[1, 0, 1.402], [1, -0.34414, -.71414], [1, 1.772, 0]])
    rgb = ar.astype(np.float)
    # Subtracting by 128 the R and G channels
    rgb[:,[1,2]] -= 128
    #.dot is multiplication of the matrices and xform.T is a transpose of the array axes
    rgb = rgb.dot(xform.T)
    # Makes any pixel value greater than 255 just be 255 (Max for RGB colorspace)
    np.putmask(rgb, rgb > 255, 255)
    # Sets any pixel value less than 0 to 0 (Min for RGB colorspace)
    np.putmask(rgb, rgb < 0, 0)
    return np.uint8(rgb)

def px_rgb_a(ods, pds):
    px = read_rle_bytes(ods.img_data)
    px = np.array([[255]*(ods.width - len(l)) + l for l in px], dtype=np.uint8)
    
    ycbcr = np.array([c[:-1] for c in pds.palette])
    rgb = ycbcr2rgb(ycbcr)
    
    a = [c[-1] for c in pds.palette]
    a = np.array([[a[x] for x in l] for l in px], dtype=np.uint8)

    return px, rgb, a

def make_image(ods, pds):
    px, rgb, a = px_rgb_a(ods, pds)
    alpha = Image.fromarray(a, mode='L')
    img = Image.fromarray(px, mode='P')
    img.putpalette(rgb)
    img.putalpha(alpha)
    return img
