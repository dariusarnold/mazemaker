import argparse
import sys
import enum
import numpy as np
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont


class Color(enum.IntEnum):
    white = 255
    black = 0


def _create_fitting_image(text: str, font: ImageFont.ImageFont, bordersize: int, fill_color: Color = Color.white) -> Image.Image:
    """
    Create an image that fits the given text.
    :param text: Text to draw on image
    :param font: PIL.ImageFont instance
    :param bordersize: Size of the border around the text in pixels
    :param fill_color: Color of the image background
    :return: PIL.Image instance large enough to fit text on it with a distance border_size to the border of the image
    in every direction
    """
    img_size = (1, 1)
    img = Image.new("L", img_size, color=fill_color)
    draw = ImageDraw.Draw(img)
    left, top, right, bottom = draw.textbbox((0, 0), text, font)
    textwidth, textheight = right - left, bottom - top
    img_size = (textwidth + 2 * bordersize, textheight + 2 * bordersize)
    img = img.resize(img_size)
    return img


def _draw_text_outline(img: Image.Image, font: ImageFont.ImageFont, text: str, fill_color: Color, line_color: Color, origin: Tuple[int, int]) -> None:
    """
    Draw text on image with an outline around the text.
    :param img: PIL.Image instance on which to draw
    :param font: PIL.ImageFont to use for drawing the text
    :param text: String to draw on image
    :param fill_color: Color of the text
    :param line_color: Color of the outline
    :param origin: (xy) coordinate tuple where the top left point of the text bounding box should be placed
    """
    draw = ImageDraw.Draw(img)
    # set to render text unaliased (https://mail.python.org/pipermail/image-sig/2005-August/003497.html)
    draw.fontmode = "1"
    # correct for font offset
    x_offset, y_offset, _, _ = font.getbbox(text)
    # These values were tweaked by hand to get a better centered text
    x, y = (origin[0]-2*x_offset, origin[1]-y_offset//2)
    origin = (x, y)
    # draw border
    draw.text((x - 1, y), text, font=font, fill=line_color)
    draw.text((x + 1, y), text, font=font, fill=line_color)
    draw.text((x, y - 1), text, font=font, fill=line_color)
    draw.text((x, y + 1), text, font=font, fill=line_color)
    # draw text over it
    draw.text(origin, text, font=font, fill=fill_color)


def text_mask(text: str, fontsize: int, bordersize: int = 32, invert: bool = False) -> Image.Image:
    """
    Create mask image from text. A mask image is used during maze creation to mark areas where the algorithm
    won't go. Black pixels mark cells the algorithm won't move into, i.e. the represent walls.
    :param text: String to draw on image. Image will be created with the correct size to fit the text.
    :param fontsize: Font size to use for the text.
    :param bordersize: Thickness of space around the text bounding box to the image border in pixels.
    :param invert: If False (default), the letters will be white inside, with a black outline,
    so a maze can be generated inside them.
    If true, the letters will be full black and the maze can be generated around the text.
    :return: PIL.Image instance with the text drawn as specified.
    """
    text = text.lower()
    if invert:
        fill_color = Color.black
        line_color = Color.white
    else:
        fill_color = Color.white
        line_color = Color.black
    try:
        # TODO add option to load other font
        font = ImageFont.truetype("fonts/Unicorn.ttf", size=fontsize)
    except IOError:
        sys.exit("Please place Unicorn.ttf, containing the Unicorn font made by Nick Curtis in the fonts folder.")
    img = _create_fitting_image(text, font, bordersize)
    _draw_text_outline(img, font, text, fill_color, line_color, origin=(bordersize, bordersize))
    return img


def text_mask_to_boolarray(img: Image, invert: bool = False):
    arr = np.array(img)
    # Compare with threshold to get bool array
    bool_mask = arr >= 128
    return bool_mask


def find_start(img: Image):
    x, y = 0, int(img.height / 2)
    # Go right until the outline is hit
    while img.getpixel((x, y)) == Color.white:
        x += 1
    # Go over the outline into the text
    while img.getpixel((x, y)) == Color.black:
        x += 1
    return x, y


def save_image_to_disk(image: Image.Image, filename: str) -> None:
    """
    Save given image
    :param image: PIL.Image instance to save.
    :param filename: Filename under which to save the image.
    :return:
    """
    image.save(filename)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate a mask image to be used with the maze generator."
                                                 " This script creates a mask image from the text string."
                                                 "Areas in black will be treated as walls by the algorithm, acting as a"
                                                 "border of the maze generation.")
    parser.add_argument("text", type=str, help="Text to be used as mask. Will be converted to lower case")
    parser.add_argument("-f", "--filename", type=str, default="mask.png",
                        help="Filename under which the mask image will be saved. ")
    parser.add_argument("-s", "--fontsize", type=int, default=32,
                        help="Font size in points to use for text. A size <16 will be too small for letters to connect"
                             " with the default Unicorn font.")
    parser.add_argument("-b", "--bordersize", type=int, default=32,
                        help="Thickness of space around the text bounding box to the image border in pixels.")
    parser.add_argument("-i", "--invert", action="store_true",
                        help="Flag argument. If not specified (default) the letters will be white with a black border. "
                             "This means the maze can be generated within the letters. "
                             "Otherwise, if this option is specified, the letters will be the completely black and the "
                             "maze will be generated around them.")

    args = parser.parse_args()

    if not args.filename.endswith(".png"):
        args.filename = f"{args.filename}.png"

    img = text_mask(args.text, args.fontsize, args.bordersize, args.invert)
    save_image_to_disk(img, args.filename)

# TODO: add script that converts an image to the expected format: bw, 8bpp
