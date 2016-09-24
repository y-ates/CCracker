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

from PIL import Image, ImageDraw, ImageFont
import os
import string
import random
import argparse
import textwrap

def gen(file_name, font_size=35):
    '''
    Generate captchas with random characters, random character colors and random
    obfuscation lines.
    '''
    # Keep font_size small so that it will fit in the captcha
    if font_size < 15 or font_size > 35:
        font_size = 35

    # Using fixed (DejaVuSerif) font for now.
    font = ImageFont.truetype("fonts/DejaVuSerif.ttf", int(font_size))
    captcha_width = 300
    captcha_height = 2*font_size
    # Create new image with fixed size.
    im = Image.new('RGBA', (captcha_width, captcha_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    '''
    Randomly choose two numbers between 1 and 10 which will specify the number
    of obfuscation lines. There will be obfuscation lines starting from the
    right and from the left.
    '''
    num_lines_left = random.randint(1, 10)
    num_lines_right = random.randint(1, 10)
    # Captchas will contain 8 characters every time
    num_chars = 8
    # char_pool contains [a-zA-Z0-9]
    char_pool = string.letters + string.digits
    
    for i in range(num_chars):
        # Characters are chosen randomly out of [a-zA-Z0-9]
        random_string = random.choice(char_pool)
        draw.text((10+(i*(font_size-1)), 10), random_string,
                  (random.randint(0, 255),
                   random.randint(100, 255),
                   random.randint(100, 255)),
                  font = font)

    # Randomly choose the starting coordiantes (x,y) of the obfuscation lines
    x = random.randint(1, captcha_height)
    y = random.randint(1, captcha_height)

    # Draw the lines starting left with random color
    for i in range(int(num_lines_left)):
        draw.line((captcha_width, 10*i, x*i, 20),
                  fill = (random.randint(100, 255),
                          random.randint(100, 255),
                          random.randint(100, 255)),
                  width = 1)

    # Draw the lines starting left with random color
    for i in range(int(num_lines_right)):
        draw.line((captcha_width, 10, y*i, 20*i),
                  fill = (random.randint(100, 255),
                          random.randint(100, 255),
                          random.randint(100, 255)),
                  width = 1)    

    ''''
    Captchas will be saved in the "captchas" directory as png files with the
    specified filename. Creating directory "captchas" if neccessary.
    '''
    img_dir_path = "captchas/"
    img_path = str(img_dir_path)+str(file_name)+".png"
    if os.path.isdir(img_dir_path):
        im.save(img_path)
    else:
        os.makedirs(img_dir_path)
        print "[#] NOTE"
        print "----------"
        print "[+] I created a directory named \"captchas\"." + \
            " The captchas are located within."
        im.save(img_path)


if __name__ == '__main__':
    '''
    Arguments will be parsed here. The user is allowed to specify the number of
    captchas that will be generated. The generating process is done with the
    gen() function.
    '''
    parser = argparse.ArgumentParser(description="Generate random captchas.",
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-n', '--number', type=int, dest="number", const=5, nargs="?",
                        help="Define number of captchas that will be generated."
                        + " If no value is given 5 captchas will be generated.")
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
    # It is not allowed to generate more than 1000 captchas in one run
    MAX_NUMBER = 1000
    count = args["number"]

    # No argument given, show help
    if count == None:
        print parser.parse_args(['-h'])

    # Generate captchas
    if count > 0 and count < MAX_NUMBER:
        for i in range(count):
            gen(i)
