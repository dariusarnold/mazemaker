import numpy as np
from collections import namedtuple
import pprint
import matplotlib.pyplot as plt
from random import choice


class Stack:
    def __init__(self):
        self.l = []

    def push(self, value):
        self.l.append(value)

    def pop(self):
        return self.l.pop()

    def __len__(self):
        return len(self.l)


class Cell(namedtuple("Cell", ("x", "y"))):
    def __add__(self, other):
        return Cell(x=self.x + other[0], y=self.y + other[1])

    def __sub__(self, other):
        return self.x - other.x, self.y - other.y


class Maze():
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.maze = np.full((height+2, width+2), False)

    def get_neighbour_cells(self, cell):
        stencil = ((0, 2), (0, -2), (2, 0), (-2, 0))
        neighbour_cells = [cell + diff for diff in stencil]
        neighbour_cells = [cell for cell in neighbour_cells if 0 < cell.y <= self.width and 0 < cell.x <= self.height]
        neighbour_cells_state = [self.maze[cell] for cell in neighbour_cells]
        return neighbour_cells, neighbour_cells_state

    def get_unvisited_neighbours(self, cell):
        neighbour_cells, neighbour_cells_state = self.get_neighbour_cells(cell)
        unvisited_cells = [cell for cell, state in zip(neighbour_cells, neighbour_cells_state) if state == False]
        return unvisited_cells

    def set_visited(self, cell):
        self.maze[cell] = True

    def remove_wall(self, cell, diff):
        self.maze[cell+diff] = True

    def move(self, start_cell, end_cell):
        self.set_visited(end_cell)
        self.remove_wall(start_cell, [d//2 for d in end_cell-start_cell])


def has_unvisited_neighbours(maze, cell):
    neighbour_cells = maze.get_neighbour_cells(cell)
    neighbour_cells = [maze.maze[cell] for cell in neighbour_cells]
    return neighbour_cells



def generate_maze(width, height):
    maze = Maze(width, height)
    stack = Stack()
    current_cell = Cell(1, 1)
    maze.set_visited(current_cell)
    while not np.all(maze.maze):
        unvisited_cells = maze.get_unvisited_neighbours(current_cell)
        # if the current cell has any neighbours which have not been visited
        if len(unvisited_cells) > 0:
            # choose one random unvisited neighbour and travel there
            chosen_cell = choice(unvisited_cells)
            stack.push(current_cell)
            maze.move(current_cell, chosen_cell)
            current_cell = chosen_cell
        elif len(stack) > 0:
            # if all neighbours have been visited backtrack to the previous cell
            current_cell = stack.pop()
        else:
            # done, add entry and exit of maze
            maze.maze[0, 1] = True
            maze.maze[height, width+1] = True
            break
    plt.imshow(maze.maze, interpolation="None", cmap="gray")
    ax = plt.gca()
    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)
    plt.savefig("maze.png")


if __name__ == '__main__':
    generate_maze(55, 31)