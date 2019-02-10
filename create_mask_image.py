import argparse
import sys
import enum

from PIL import Image, ImageDraw, ImageFont, ImageOps

class Color(enum.IntEnum):
    white = 255
    black = 0


def _create_fitting_image(text, font, border_size, fill_color=Color.white):
    """
    Create an image with the dimensions of the text and 32 pixels border around it. The whole image will be
    filled with fill colour.
    """
    img_size = (300, 200)
    img = Image.new("L", img_size, color=fill_color)
    draw = ImageDraw.Draw(img)
    width, height = draw.textsize(text, font)
    text_size = (width + 2*border_size, height + 2*border_size)
    img = img.resize(text_size)
    return img


def _draw_text_outline(img, font, text, fill_color, line_color):
    draw = ImageDraw.Draw(img)
    draw.fontmode = "1"
    x, y = 32, 32
    # draw border
    draw.text((x - 1, y), text, font=font, fill=line_color)
    draw.text((x + 1, y), text, font=font, fill=line_color)
    draw.text((x, y - 1), text, font=font, fill=line_color)
    draw.text((x, y + 1), text, font=font, fill=line_color)
    # draw text over it
    draw.text((x, y), text, font=font, fill=fill_color)


def text_mask(filename, text, fontsize, invert=False):
    text = text.lower()
    if invert:
        fill_color = Color.black
        line_color = Color.white
    else:
        fill_color = Color.white
        line_color = Color.black
    try:
        font = ImageFont.truetype("fonts/Unicorn.ttf", size=fontsize)
    except IOError:
        sys.exit("Please place Unicorn.ttf, containing the Unicorn font made by Nick Curtis. in the fonts folder.")
    img = _create_fitting_image(text, font, bordersize)
    _draw_text_outline(img, font, text, fill_color, line_color, origin=(bordersize, bordersize))
    img.save(filename)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate a mask image to be used with the maze generator. This script allows text to be used as a mask.")
    parser.add_argument("text", type=str, help="Text to be used as mask. Will be converted to lower case")
    parser.add_argument("filename", type=str, default="mask.png", help="Filename under which the mask image will be saved. ")
    parser.add_argument("-f", "--fontsize", type=int, default=32, help="Font size to use for text. A size < 16 will be too small for letters to connect.")
    parser.add_argument("-b", "--bordersize", type=int, default=32, help="Thickness of space around the text bounding box to the image border in pixels. ")
    parser.add_argument("-i", "--invert", action="store_true", help="By default the maze will be generated within the letters. If this is set to true, the letters will be the forbidden space and the maze will be generated around it.")

    args = parser.parse_args()

    if not args.filename.endswith(".png"):
        args.filename = f"{args.filename}.png"

    text_mask(args.filename, args.text, args.fontsize, args.bordersize, args.invert)

# TODO: add script that converts an image to the expected format: bw, 8bpp