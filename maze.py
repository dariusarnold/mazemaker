import argparse
import enum
import itertools
import sys
from collections import namedtuple
from random import choice, seed
from typing import List

import numpy as np
from PIL import Image, ImageDraw, ImageColor


class Stack:
    def __init__(self):
        self._list = []

    def push(self, value):
        self._list.append(value)

    def pop(self):
        return self._list.pop()

    def __len__(self):
        return len(self._list)


class Direction(enum.IntEnum):
    N = 0
    E = 1
    S = 2
    W = 3


class Mapping:
    direction_to_step = {Direction.N: (0, -1),
                         Direction.E: (1, 0),
                         Direction.S: (0, 1),
                         Direction.W: (-1, 0)}

    step_to_direction = {value: key for key, value in direction_to_step.items()}


class CellIndex(namedtuple("Cell", ("x", "y"))):
    def __add__(self, other):
        return CellIndex(x=self.x + other[0], y=self.y + other[1])

    def __sub__(self, other):
        return self.x - other.x, self.y - other.y


class Cell:
    def __init__(self):
        self.visited = False
        self.walls = [True] * 4

    def remove_wall(self, direction):
        self.walls[direction.value] = False

    def __repr__(self):
        return f"Cell({self.walls}, visited={self.visited})"


class Maze:
    def __init__(self, width: int, height: int, mask=None):
        """
        Initialize a Maze object with given dimensions and optional mask.
        Masks are used to exclude certain cells from the maze generation algorithm.

        :param width: Number of cells in horizontal direction
        :param height: Number of cells in vertical direction
        :param mask: Bool array where False marks cells that are not visited by the algorithm
        """
        self.width = int(width)
        self.height = int(height)
        self.cell_grid = np.array([Cell() for _ in range(height * width)]).reshape((height, width))
        self.mask = mask
        self.start_cell = None

    def get_neighbour_cell_indices(self, cell_index: CellIndex) -> List[CellIndex]:
        """
        Return the indices of all neighbour cells of cell_index that lie within the grid.

        :param cell_index: The index of the cell for which neighbours are to be found
        :return: A list of CellIndex objects representing the neighbour cells
        """
        stencil = ((0, 1), (0, -1), (1, 0), (-1, 0))
        neighbour_cell_indices = [cell_index + diff for diff in stencil]
        neighbour_cell_indices = [cell_index for cell_index in neighbour_cell_indices if self.index_in_grid(cell_index)]
        return neighbour_cell_indices

    def index_in_grid(self, cell_index: CellIndex) -> bool:
        """
        Check if the cell_index is within the grid.

        :param cell_index: The index of the cell to check
        :return: True if the cell_index is within the grid, otherwise False
        """
        return 0 <= cell_index.x < self.width and 0 <= cell_index.y < self.height

    def get_unvisited_neighbours(self, cell_index: CellIndex) -> List[CellIndex]:
        """
        Return the indices of unvisited neighbour cells of the given cell_index within the grid.

        :param cell_index: The index of the cell for which unvisited neighbours are to be found
        :return: A list of CellIndex objects representing the unvisited neighbour cells
        """
        neighbour_cell_indices = self.get_neighbour_cell_indices(cell_index)
        unvisited_cells = [index for index in neighbour_cell_indices if self.get_cell(index).visited is False]
        # TODO inherit from Maze to implement masked maze and override this function
        # Do not use 'is True' since the returned value is a numpy.bool_ or a Python bool
        unvisited_cells = [index for index in unvisited_cells if self.get_mask(index) == True]
        return unvisited_cells

    def set_visited(self, cell_index: CellIndex):
        """
        Set the visited attribute of the cell at cell_index to True.

        :param cell_index: The index of the cell to set as visited
        """
        self.get_cell(cell_index).visited = True

    def remove_walls(self, start_cell_index: CellIndex, end_cell_index: CellIndex):
        """
        Remove the walls between the start_cell_index and end_cell_index.
        start_cell_index and end_cell_index must be neighbours (not diagonal).

        :param start_cell_index: The index of the start cell
        :param end_cell_index: The index of the end cell
        """
        direction_to = Mapping.step_to_direction[end_cell_index - start_cell_index]
        direction_from = Mapping.step_to_direction[start_cell_index - end_cell_index]
        self.get_cell(start_cell_index).remove_wall(direction_to)
        self.get_cell(end_cell_index).remove_wall(direction_from)

    def move(self, start_cell_index: CellIndex, end_cell_index: CellIndex):
        """
        Move from the start_cell_index to the end_cell_index by setting the end_cell_index as visited
        and removing the walls between them.

        :param start_cell_index: The index of the start cell
        :param end_cell_index: The index of the end cell
        """
        self.set_visited(end_cell_index)
        self.remove_walls(start_cell_index, end_cell_index)

    def get_cell(self, cell_index: CellIndex) -> Cell:
        """
        Return the cell object at the given cell_index.

        :param cell_index: The index of the cell to get
        :return: The cell object at cell_index
        """
        return self.cell_grid[cell_index.y, cell_index.x]

    def get_mask(self, cell_index: CellIndex) -> bool:
        """
        Return the mask value at cell_index.

        :param cell_index: The index of the cell to get the mask value for
        :return: The mask value at cell_index (True if allowed, False if not allowed)
        """
        if self.mask is not None:
            return self.mask[cell_index.y, cell_index.x]
        # Return True (allowed cell) if no mask was set
        else:
            return True


class MazeVisualizerPIL:
    def __init__(self, maze, cell_size_pixels, line_width_pixels):
        """
        Initialize a MazeVisualizerPIL instance.

        :param maze: The Maze instance to be visualized
        :param cell_size_pixels: The size of each cell in pixels for the visualized maze
        :param line_width_pixels: The width of the walls in pixels for the visualized maze
        """
        self.maze = maze
        self.cell_size_pixels = cell_size_pixels
        self.bg_color = ImageColor.getrgb("white")
        self.fill_color = ImageColor.getrgb("black")
        self.start_color = ImageColor.getrgb("green")
        self.line_width = line_width_pixels
        self._init_plot()

    def _init_plot(self):
        """
        Initialize the plot with the given dimensions and color.
        """
        width = self.maze.width * self.cell_size_pixels + 1
        height = self.maze.height * self.cell_size_pixels + 1
        self.img = Image.new(mode="RGB", size=(width, height), color=self.bg_color)
        self.draw = ImageDraw.Draw(self.img)

    def plot_walls(self, color_start_cell=True):
        """
        Plot the walls of the maze cells on the initialized plot.
        """
        # Color start cell
        if color_start_cell:
            x, y = self.maze.start_cell
            top_left_pixel, _, _, bottom_right_pixel = self._calc_cell_bbox(x, y)
            self.draw.rectangle((top_left_pixel, bottom_right_pixel), fill=self.start_color, outline=self.bg_color)

        for hor_index, ver_index in itertools.product(range(self.maze.width), range(self.maze.height)):
            top_left_pixel, top_right_pixel, bottom_left_pixel, bottom_right_pixel = self._calc_cell_bbox(hor_index,
                                                                                                          ver_index)
            if not self.maze.get_mask(CellIndex(x=hor_index, y=ver_index)):
                self.draw.rectangle((top_left_pixel, bottom_right_pixel), outline=self.fill_color, fill=self.fill_color)
            cell = self.maze.get_cell(CellIndex(x=hor_index, y=ver_index))
            if cell.visited is True:
                if cell.walls[Direction.N]:
                    self.draw.line((top_left_pixel, top_right_pixel), self.fill_color, self.line_width)
                if cell.walls[Direction.E]:
                    self.draw.line((top_right_pixel, bottom_right_pixel), self.fill_color, self.line_width)
                if cell.walls[Direction.S]:
                    self.draw.line((bottom_right_pixel, bottom_left_pixel), self.fill_color, self.line_width)
                if cell.walls[Direction.W]:
                    self.draw.line((top_left_pixel, bottom_left_pixel), self.fill_color, self.line_width)

    def _calc_cell_bbox(self, hor_index: int, ver_index: int):
        top_left_pixel = (hor_index * self.cell_size_pixels, ver_index * self.cell_size_pixels)
        top_right_pixel = ((hor_index + 1) * self.cell_size_pixels, ver_index * self.cell_size_pixels)
        bottom_left_pixel = (hor_index * self.cell_size_pixels, (ver_index + 1) * self.cell_size_pixels)
        bottom_right_pixel = ((hor_index + 1) * self.cell_size_pixels, (ver_index + 1) * self.cell_size_pixels)
        return top_left_pixel, top_right_pixel, bottom_left_pixel, bottom_right_pixel

    def save_plot(self, filename: str):
        """
        Save the plot to a file with the given filename.

        :param filename: The name of the file to save the plot
        """
        self.img.save(filename)


def generate_maze(width: int, height: int, start_cell_index: CellIndex = None, mask: np.ndarray = None) -> Maze:
    """
    Generate a maze with the given width, height, start_cell_index, and mask.
    :param width: The width of the maze in cells
    :param height: The height of the maze in cells
    :param start_cell_index: The index of the start cell (default is (0, 0))
    :param mask: An optional mask to apply to the maze
    :return: The generated maze
    """
    maze = Maze(width, height, mask)
    stack = Stack()
    if start_cell_index is None:
        start_cell_index = CellIndex(x=0, y=0)
    maze.start_cell = start_cell_index
    current_cell_index = start_cell_index
    maze.set_visited(current_cell_index)
    while True:
        unvisited_cells = maze.get_unvisited_neighbours(current_cell_index)
        # if the current cell has any neighbours which have not been visited
        if len(unvisited_cells) > 0:
            # choose one random unvisited neighbour and travel there
            chosen_cell_index = choice(unvisited_cells)
            stack.push(current_cell_index)
            maze.move(current_cell_index, chosen_cell_index)
            current_cell_index = chosen_cell_index
        elif len(stack) > 0:
            # if all neighbours have been visited backtrack to the previous cell
            current_cell_index = stack.pop()
        else:
            break
    return maze


def plot_maze(maze: Maze, output_filename: str, cell_size_pixels: int = 5, line_width_pixels: int = 1):
    """
    Plot the maze and save the plot to a file.
    :param maze: The maze to plot
    :param output_filename: The name of the file to save the plot
    :param cell_size_pixels: The size of each cell in pixels for plotting (default is 5)
    :param line_width_pixels: The width of the cell walls in pixels for plotting (default is 1)
    """
    visualizer = MazeVisualizerPIL(maze, cell_size_pixels, line_width_pixels)
    visualizer.plot_walls()
    visualizer.save_plot(output_filename)


if __name__ == '__main__':
    # top level parser
    parser = argparse.ArgumentParser(description="Generate mazes.")
    parser.add_argument("-f", "--filename", help="Filename that is used to save the maze.", default="maze.png")
    parser.add_argument("-s", "--seed", default=None, help="Seed for random generator.")
    parser.add_argument("-o", "--origin", nargs=2, type=int, default=[0, 0], help="x y coordinate of the start cell in the maze")
    parser.add_argument("-c", "--cellsize", type=int, default=5, help="Cell size in pixels for plotting.")
    parser.add_argument("-l", "--linewidth", type=int, default=1, help="Line width of cell walls for plotting in pixels.")
    # sub parsers
    subparsers = parser.add_subparsers(dest="command", help="Select between just maze generation with width/height or generating a maze with a mask.")

    parser_generate = subparsers.add_parser("generate", help="Generate a maze within a rectangle.")
    parser_generate.add_argument("width", type=int, help="Width of the maze in cells.")
    parser_generate.add_argument("height", type=int, help="Height of the maze in cells.")

    parser_mask = subparsers.add_parser("mask", help="Apply mask to limit maze.")
    parser_mask.add_argument("-m", "--maskimg", default=None, help="Image to use as mask, where only white pixels can be visited by the algorithm, while black pixels are forbidden. If this is specified, the maze will be of the same dimensions as the mask image.")
    args = parser.parse_args()

    if seed is not None:
        seed(args.seed)

    if args.command is None:
        parser.print_help()
        sys.exit()

    # extract mask maze options
    mask = None
    if args.command.lower() == "mask":
        if args.maskimg is not None:
            try:
                img = Image.open(args.maskimg)
            except IOError:
                sys.exit(f"Can't open maskimage {args.maskimg}.")
            mask = np.asarray(img, dtype=bool)
            args.width = img.size[0]
            args.height = img.size[1]
        else:
            sys.exit("No mask image specified.")

    maze = generate_maze(args.width, args.height, CellIndex(x=args.origin[0], y=args.origin[1]), mask)
    plot_maze(maze, args.filename, cell_size_pixels=args.cellsize, line_width_pixels=args.linewidth)
