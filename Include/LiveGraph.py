from vispy import app
from vispy import gloo
import numpy as np
import math


class LiveGraph(object):
    def __init__(self, nrows=1, ncols=1, samples=1000, colours=None):
        self.no_rows = nrows
        self.no_cols = ncols
        self.m = nrows * ncols
        self.n = samples
        self.signals = None
        self.c = app.Canvas(keys='interactive')
        # Assign colours to each graph
        if not colours:
            self.colours = np.repeat(np.random.uniform(size=(self.m, 3), low=.5, high=.9),
                                     self.n, axis=0).astype(np.float32)
        else:
            self.colours = colours
        # Create index of graphs
        self.index = np.c_[np.repeat(np.repeat(np.arange(self.no_cols), self.no_rows), self.n),
                           np.repeat(np.tile(np.arange(self.no_rows), self.no_cols), self.n),
                           np.tile(np.arange(self.n), self.m)].astype(np.float32)


VERT_SHADER = """
#version 120
// y coordinate of the position.
attribute float a_position;
// row, col, and time index.
attribute vec3 a_index;
varying vec3 v_index;
// 2D scaling factor (zooming).
uniform vec2 u_scale;
// Size of the table.
uniform vec2 u_size;
// Number of samples per signal.
uniform float u_n;
// Color.
attribute vec3 a_color;
varying vec4 v_color;
// Varying variables used for clipping in the fragment shader.
varying vec2 v_position;
varying vec4 v_ab;
void main() {
    float nrows = u_size.x;
    float ncols = u_size.y;
    // Compute the x coordinate from the time index.
    float x = -1 + 2*a_index.z / (u_n-1);
    vec2 position = vec2(x - (1 - 1 / u_scale.x), a_position);
    // Find the affine transformation for the subplots.
    vec2 a = vec2(1./ncols, 1./nrows)*.9;
    vec2 b = vec2(-1 + 2*(a_index.x+.5) / ncols,
                  -1 + 2*(a_index.y+.5) / nrows);
    // Apply the static subplot transformation + scaling.
    gl_Position = vec4(a*u_scale*position+b, 0.0, 1.0);
    v_color = vec4(a_color, 1.);
    v_index = a_index;
    // For clipping test in the fragment shader.
    v_position = gl_Position.xy;
    v_ab = vec4(a, b);
}
"""

FRAG_SHADER = """
#version 120
varying vec4 v_color;
varying vec3 v_index;
varying vec2 v_position;
varying vec4 v_ab;
void main() {
    gl_FragColor = v_color;
    // Discard the fragments between the signals (emulate glMultiDrawArrays).
    if ((fract(v_index.x) > 0.) || (fract(v_index.y) > 0.))
        discard;
    // Clipping test.
    vec2 test = abs((v_position.xy-v_ab.zw)/v_ab.xy);
    if ((test.x > 1) || (test.y > 1))
        discard;
}
"""


class Canvas(app.Canvas):
    def __init__(self, graph, data, frequency):
        app.Canvas.__init__(self, title='Serial Data',
                            keys='interactive')
        self.program = gloo.Program(VERT_SHADER, FRAG_SHADER)
        self.program['a_position'] = data.y.reshape(-1, 1)
        self.program['a_color'] = graph.colours
        self.program['a_index'] = graph.index
        self.program['u_scale'] = (500., 500.)
        self.program['u_size'] = (graph.no_rows, graph.no_cols)
        self.program['u_n'] = graph.n
        self.n = graph.n
        self.m = graph.m
        self.data = data

        gloo.set_viewport(0, 0, *self.physical_size)

        # self._timer = app.Timer('auto', connect=self.on_timer, start=True)
        self._timer = app.Timer(1.0/frequency, connect=self.on_timer, start=True)

        gloo.set_state(clear_color='black', blend=True,
                       blend_func=('src_alpha', 'one_minus_src_alpha'))
        self.show()

    def on_resize(self, event):
        gloo.set_viewport(0, 0, *event.physical_size)

    def on_mouse_wheel(self, event):
        dx = np.sign(event.delta[1]) * .05
        scale_x, scale_y = self.program['u_scale']
        scale_x_new, scale_y_new = (scale_x * math.exp(2.5 * dx),
                                    scale_y * math.exp(2.5 * dx))
        self.program['u_scale'] = (max(1, scale_x_new), max(1, scale_y_new))
        self.update()

    def on_timer(self, event):
        """Add some data at the end of each signal (real-time signals)."""
        k = 1
        self.data.y[:, :-k] = self.data.y[:, k:]
        self.data.y[:, -k:] = self.data.get_data()

        self.program['a_position'].set_data(self.data.y.ravel().astype(np.float32))
        self.update()

    def on_draw(self, event):
        gloo.clear()
        self.program.draw('line_strip')
