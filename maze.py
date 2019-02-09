import argparse
from collections import namedtuple
from random import choice, seed
import enum

import matplotlib.pyplot as plt
import numpy as np


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


def has_unvisited_neighbours(maze, cell):
    neighbour_cells = maze.get_neighbour_cell_indices(cell)
    neighbour_cells = [maze.maze[cell] for cell in neighbour_cells]
    return neighbour_cells


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
    plt.imshow(maze.maze, interpolation="None", cmap="gray")
    ax = plt.gca()
    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)
    plt.savefig("maze.pdf", dpi=666)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate mazes.")
    parser.add_argument("width", type=int, help="Width of the maze in cells")
    parser.add_argument("height", type=int, help="Height of the maze in cells")
    parser.add_argument("-s", "--seed", help="Seed for random generator")
    args = parser.parse_args()

    seed(args.seed)

    generate_maze(args.width, args.height)
