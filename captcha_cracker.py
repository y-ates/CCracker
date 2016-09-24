#!/usr/bin/env python

################################################################################
# Copyright (C) 2016 Yakup Ates <Yakup.Ates@rub.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import matplotlib.pyplot as plt
import string
import numpy as np
import scipy
from scipy import signal, ndimage
import cv2
import pylab
import captcha_generator
import argparse
import textwrap
import os, sys
import operator

import imagehash
import random

def crop(img):
    '''
    This function is designed to crop single characters from captchas generated
    by captcha_generator. Thus it won't work with captchas of other sizes as the
    boxes are specifically for that font and size.
    '''

    img = Image.open(img)
    img = img.convert("RGB")
    # Get width (w) and height (h) of the image
    w, h = img.size

    # Every cropped character will be added to img_chars. We will loop through
    # this one later on to crack every character one by one.
    img_chars = list()
    for i in range(num_chars):
        # We work with tmp images as we want to crop from the
        # original everytime and don't want to edit the original one
        tmp_img = img
        '''
        TODO:
        Calculate the crop boxes dynamically and more precisely such that only
        the characters are returned. More dynamically means that the image size
        character font and font size do not matter at all.
        '''
        # Defining the box or frame which will be cropped
        box = ((35*i), 10, (35*(i+1)), 45)
        a = np.asarray(img)
        b = a[0:100, 0:100]
        tmp_img = img.crop(box)
        
        img_chars.append(tmp_img)

    return img_chars

                
def color_to_black_white(img):
    '''
    Converts and returns the given image into a black and white image.
    '''
    img = img.convert('1')
    #img = Image.fromarray(img)
    return img


def deobfuscate(img):
    '''
    Applies a median filter to delete obfuscation lines and dots. Furthermore it
    will enhance the contrast of the image and converts the image into a black
    and white image.
    '''
    img = img.filter(ImageFilter.MedianFilter())
    img = ImageEnhance.Contrast(img).enhance(1)
    img = color_to_black_white(img)
    
    return img


def gen_char_image(char, font_size=35):
    '''
    Generates single character images which will be compared with the cropped
    characters of the captcha.
    '''
    font = ImageFont.truetype("fonts/DejaVuSerif.ttf", int(font_size))
    
    if font_size < 0 or font_size > 100:
        font_size = 35

    # Captcha does only contain [a-zA-Z0-9]
    if char not in char_pool:
        return "[-] Error: Requested char is not in character pool."
    else:
        # Generates images of the same size (like the cropped image)
        im = Image.new('RGBA', (35, 35), (0, 0, 0, 0))
        draw = ImageDraw.Draw(im, mode="RGBA")

        # Character is white as the cropped character will result in white after
        # convertions too
        draw.text((0, 0), char, (255, 255, 255),
                  font=font)
        return im


def cross_correlate(img_1, img_2):
    '''
    Calculates the cross-correlation of img_1 and img_2
    '''
    # Casting the ndarray of img_1 and img_2 to a float array
    img_1_tmp = img_1.astype('float')
    img_2_tmp = img_2.astype('float')

    #img_1_tmp -= np.mean(img_1_tmp)
    #img_2_tmp -= np.mean(img_2_tmp)

    # We need to work with absolute numbers. The convolve2d function will result
    # in a weird behavior else.
    #img_1_tmp = np.absolute(img_1_tmp)
    #img_2_tmp = np.absolute(img_2_tmp)

    return scipy.signal.correlate2d(img_1_tmp, img_2_tmp, mode="same")
    #return scipy.signal.convolve2d(img_1_tmp, img_2_tmp[::-1, ::-1], mode='same')


def shift_img_2d(img, x, y):
    '''
    Shift the given image with an affine transformation by x and y
    '''
    M = np.float32([[1, 0, int(x)],[0, 1, int(y)]])
    cols, rows = img.shape
    res_img = cv2.warpAffine(img, M, (cols, rows))

    return res_img


def get_best_shift(img_1, img_2):
    '''
    Calculate cross-correlation of the two given images and extract the argmax
    value such that we know at which point these two images are most
    similar. This position in which these images are most similar is the
    position where we want to shift generated character image to.
    '''
    img_1_arr, img_2_arr = get_img_array(img_1, img_2)
    #np.random.seed(42)
    #print np.sum(np.abs(img_1_arr))
    #print imagehash.hash(img_1_arr)
    corr = cross_correlate(img_1_arr, img_2_arr)
    #print np.sum(np.abs(img_2_arr))
    #print np.sum(corr/35)
    #print np.sort(corr.reshape(35*35))[::-1][1:10]
    #print corr[1:10]
    '''
    TODO:
    Somehow the argmax value and np.sum of the generated image is changing and
    thus leads to wrong shifts so that we are correlating totally wrong images.
    '''
    argmax = np.argmax(corr)
    best_w = argmax % corr.shape[0]
    best_h = argmax / corr.shape[0]


    #print "argmax: " + str(np.argmax(corr)/35) + " shape: " + str(corr.shape)
    #print corr[np.argmax(corr)%corr.shape[0]]
    #print "best_w: " + str(best_w) + " best_h: " + str(best_h)

    return (best_w, best_h)


def get_img_array(img_1, img_2):
    '''
    Converts given images into numpy arrays.
    '''
    return (np.asarray(img_1), np.asarray(img_2))


def get_char_pool():
    '''
    The generated captchas can only contain [a-zA-Z0-9].
    '''
    return string.letters + string.digits


def parse_arguments():
    '''
    Arguments will be parsed here. The user is allowed to specify a captcha. If
    none is given it will generate and crack some.
    '''
    parser = argparse.ArgumentParser(description="Crack some captchas.",
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-if', '--input-file', dest="img", nargs="?",
                        help="Select captcha to crack.")
    parser.add_argument('-v', '--version', action="version",
                        version=textwrap.dedent('''
                        --------------------------------------------------------
                        \tProject  : %(prog)s 1.0
                        \tCopyright: (C) 2016 Yakup Ates
                        \tE-Mail   : <Yakup.Ates@rub.de>
                        \tLicense  : GPLv3 (http://www.gnu.org/licenses/)
                        --------------------------------------------------------
                        '''),
                        help="Program version and license.")

    # Parse arguments
    args = vars(parser.parse_args())
    img_path = args['img']
    gen_img_path = "captchas/1.png"

    if img_path != None:
        # An image path is given
        if os.path.exists(img_path):
            # The given image path exists, crack the captcha
            # TODO: Check if it is a valid captcha
            crack(img_path)
        else:
            # The given image path does not exist.
            print "[#] NOTE"
            print "----------"
            print "[-] Could not find given file."

            answer = raw_input("[?] Do you want me to generate a captcha? [Y/n]: ")
            if answer == 'n' or answer == 'N':
                # Exit, user does not want to continue
                return "[+] Alright. Have a nice day.\r\n"
            else:
                # Generate captcha and crack it.
                print "[+] I will generate and crack one.\r\n"
                cap = captcha_generator.gen(1)
                crack(gen_img_path)
    else:
        # No path given. Generate captcha and crack it.
        print "[#] NOTE"
        print "----------"
        print "[-] No captcha given. I will generate and crack one of my own.\r\n"
        cap = captcha_generator.gen(1)
        crack(gen_img_path)


def plot_comparison(gen_img, cap_img, corr_img):
    '''
    Create 1 row with 3 different plots. The first one is the generated
    character image, the second the cropped image and the third the actual
    result of the cross-correlation.
    '''
    clock = np.arange(64, len(corr_img), 128)
    '''
    TODO:
    It would be cool if the user could watch the cracking process by observing
    the actual comparison and the resulting correlation while cracking. 
    '''
    pylab.figure("Captcha character comparison")
    pylab.subplot(131)
    pylab.title('Generated image')
    pylab.imshow(gen_img, interpolation='nearest', cmap=pylab.gray())
    pylab.subplot(132)
    pylab.title('Cropped image')
    pylab.imshow(cap_img, interpolation='nearest', cmap=pylab.gray())
    pylab.subplot(133)
    pylab.title('Correlation')
    pylab.plot(corr_img/35)
    pylab.plot(clock, corr_img[clock], 'ro')
    pylab.axhline(0.5, ls=':')
    pylab.tight_layout()
    pylab.show()
    
    
def crack(cap_img):
    '''
    Compares a cropped character image with a generated one by
    cross-correlating. Every possible character will be generated and shifted
    such that both are most similar and cross-correlated afterwards. The
    generated image which results with the highest cross-correlation is the most
    probable character in the cropped image.
    '''
    
    print '%-12s%-12s%-24s%-12s' % ("#Character", "Index", "Correlation", "Character")
    for i in range(num_chars):
        best_corr = [[], []]
        tmp_file = "tmp.png"
        tmp_file_crop = "crop.png"
        crop_img = crop(cap_img)[i]
        crop_img = deobfuscate(crop_img)
        crop_img.save(tmp_file_crop)
        #print "### Cracking crop #", i

        for j in char_pool:
            #print "### Trying char:", j
            #gen_char_img = gen_char_image(j)
            gen_img = Image.open("chars/"+j+".png", mode="r")
            gen_img = deobfuscate(gen_img)
            #gen_img = np.asarray(gen_img)
            #print "gen_char_img npsum:", np.sum(gen_char_img)
            #print np.sum(np.abs(gen_img))
            gen_img.save(tmp_file)
            #print "hash: ", imagehash.average_hash(Image.open(tmp_file))
            
            gen_img_array, crop_img_array = get_img_array(gen_img, crop_img)
            best_w, best_h = get_best_shift(gen_img, crop_img)
            #print best_w, best_h

            # pylab.figure()
            # pylab.imshow(gen_img)
            # pylab.figure()
            # pylab.imshow(crop_img)
            # pylab.show()
            #print np.sum(np.abs(gen_img))
            #print np.sum(np.abs(crop_img))
            img = cv2.imread(tmp_file, 0)
            shifted_img = shift_img_2d(img, (best_h-float(35/2)),
                                       (best_w-float(35/2)))
            #shifted_img = shift_img_2d(img, 10, 0)
            cv2.imwrite(tmp_file, shifted_img)
            gen_img = Image.open(tmp_file)
            gen_img_array = np.asarray(gen_img)
            corr = cross_correlate(gen_img_array, crop_img_array)
            #print "Korellation: ", np.amax(corr)/35

            best_corr[0].append(np.amax(corr)/gen_img.size[0])
            best_corr[1].append(j)

            gen_img = Image.open(tmp_file)
            #plot_comparison(gen_img, crop_img, corr)

        # Print results
        index, value = max(enumerate(best_corr[0]), key=operator.itemgetter(1))
        print '%-12i%-12i%-24f%-12c' % (i, index, value, best_corr[1][index])
        
    # Clear tmp files
    os.remove(tmp_file)
    os.remove(tmp_file_crop)
    

if __name__ == "__main__":
    global num_chars, char_pool
    char_pool = get_char_pool()
    num_chars = 8
    random.seed(42)
    np.random.seed(42)

    parse_arguments()
