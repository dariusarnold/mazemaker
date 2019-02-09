import argparse
from collections import namedtuple
from random import choice, seed
import enum

import numpy as np
from PIL import Image, ImageDraw


class Stack:
    def __init__(self):
        self.l = []

    def push(self, value):
        self.l.append(value)

    def pop(self):
        return self.l.pop()

    def __len__(self):
        return len(self.l)


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
        self.walls = [True]*4

    def remove_wall(self, direction):
        self.walls[direction.value] = False

    def __repr__(self):
        return f"Cell({self.walls}, visited={self.visited})"

class Maze:
    def __init__(self, width, height):
        self.width = int(width)
        self.height = int(height)
        self.cell_grid = np.array([Cell() for _ in range(height * width)]).reshape((height, width))

    def get_neighbour_cell_indices(self, cell_index):
        stencil = ((0, 1), (0, -1), (1, 0), (-1, 0))
        neighbour_cell_indices = [cell_index + diff for diff in stencil]
        neighbour_cell_indices = [cell_index for cell_index in neighbour_cell_indices if self.index_in_grid(cell_index)]
        return neighbour_cell_indices

    def index_in_grid(self, cell_index):
        return 0 <= cell_index.y < self.width and 0 <= cell_index.x < self.height

    def get_unvisited_neighbours(self, cell_index):
        neighbour_cell_indices = self.get_neighbour_cell_indices(cell_index)
        unvisited_cells = [index for index in neighbour_cell_indices if self.get_cell(index).visited == False]
        return unvisited_cells

    def set_visited(self, cell_index):
        self.get_cell(cell_index).visited = True

    def remove_walls(self, start_cell_index, end_cell_index):
        direction_to = Mapping.step_to_direction[end_cell_index - start_cell_index]
        direction_from = Mapping.step_to_direction[start_cell_index - end_cell_index]
        self.get_cell(start_cell_index).remove_wall(direction_to)
        self.get_cell(end_cell_index).remove_wall(direction_from)

    def move(self, start_cell_index, end_cell_index):
        self.set_visited(end_cell_index)
        self.remove_walls(start_cell_index, end_cell_index)

    def get_cell(self, cell_index):
        return self.cell_grid[cell_index.y, cell_index.x]


class MazeVisualizerPIL:
    def __init__(self, maze, cell_size_pixels):
        self.maze = maze
        self.cell_size_pixels = cell_size_pixels
        self._init_plot()

    def _init_plot(self):
        width = self.maze.width*self.cell_size_pixels+1
        height = self.maze.height*self.cell_size_pixels+1
        self.img = Image.new(mode="L", size=(width, height), color=255)
        self.draw = ImageDraw.Draw(self.img)

    def plot_walls(self):
        for hor_index in range(self.maze.width):
            for ver_index in range(self.maze.height):
                cell = self.maze.get_cell(CellIndex(x=hor_index, y=ver_index))
                top_left_pixel = (hor_index*self.cell_size_pixels, ver_index*self.cell_size_pixels)
                top_right_pixel = ((hor_index+1)*self.cell_size_pixels, ver_index*self.cell_size_pixels)
                bottom_left_pixel = (hor_index*self.cell_size_pixels, (ver_index+1)*self.cell_size_pixels)
                bottom_right_pixel = ((hor_index+1)*self.cell_size_pixels, (ver_index+1)*self.cell_size_pixels)
                fill = 0
                width = 1
                if cell.walls[Direction.N]:
                    self.draw.line((top_left_pixel, top_right_pixel), fill, width)
                if cell.walls[Direction.E]:
                    self.draw.line((top_right_pixel, bottom_right_pixel), fill, width)
                if cell.walls[Direction.S]:
                    self.draw.line((bottom_right_pixel, bottom_left_pixel), fill, width)
                if cell.walls[Direction.W]:
                    self.draw.line((top_left_pixel, bottom_left_pixel), fill, width)

    def save_plot(self):
        self.img.save("test.png")


def generate_maze(width, height):
    maze = Maze(width, height)
    stack = Stack()
    current_cell_index = CellIndex(0, 0)
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
    plotter = MazeVisualizerPIL(maze, 5)
    plotter.plot_walls()
    plotter.save_plot()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate mazes.")
    parser.add_argument("width", type=int, help="Width of the maze in cells")
    parser.add_argument("height", type=int, help="Height of the maze in cells")
    parser.add_argument("-s", "--seed", help="Seed for random generator")
    args = parser.parse_args()

    seed(args.seed)

    generate_maze(args.width, args.height)
