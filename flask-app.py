from flask import Flask, send_file, request, render_template
import io
from maze import generate_maze, MazeVisualizerPIL, CellIndex, masked_maze
from create_mask_image import text_mask
from PIL import Image, ImageColor

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/maze')
def maze():
    width = int(request.args.get('width', 10))
    height = int(request.args.get('height', 10))
    maze = generate_maze(width, height)
    vis = MazeVisualizerPIL(maze, 5, 1)
    vis.plot_walls()
    img = vis.img
    img = img.resize((4 * img.size[0], 4 * img.size[1]), Image.Resampling.NEAREST)
    img_io = io.BytesIO()
    img.save(img_io, 'PNG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


@app.route('/mask')
def mask():
    text = request.args.get('text', 'example')
    fontsize = int(request.args.get('fontsize', 32))
    bordersize = int(request.args.get('bordersize', 32))

    img = text_mask(text, fontsize, bordersize)
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


@app.route('/masked_maze')
def masked_maze_route():
    text = request.args.get('text', 'example')
    fontsize = int(request.args.get('fontsize', 32))
    bordersize = int(request.args.get('bordersize', 32))
    cell_size = int(request.args.get('cell_size', 5))
    wall_width = int(request.args.get('wall_width', 1))

    maze = masked_maze(text, fontsize, bordersize)
    vis = MazeVisualizerPIL(maze, cell_size, wall_width)
    vis.plot_walls()
    img = vis.img
    img_io = io.BytesIO()
    img.save(img_io, 'PNG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


if __name__ == '__main__':
    app.run(debug=True)