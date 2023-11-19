import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from .Elementary.vline import RunningLine
from .Elementary.style import LINEWIDTH

class Slice(RunningLine):

    def __init__(self, ax_in: plt.Axes, ax_out: plt.Axes | None = None):
        super().__init__(ax_in)
        _, self.ax_out = (ax_out.figure, ax_out) if ax_out else plt.subplots() # Оси для вывода кривых

    def fix_lim(self):
        self.ax_out.set_xlim([0, self.height])
        self.ax_out.set_ylim([self.data.min(), self.data.max()])

    def draw_out(self):
        self.ax_out.figure.canvas.draw()

    def draw_all(self):
        self.draw_in()
        self.draw_out()

    ########################################

    def create_curve(self):
        x = range(self.height)
        self.curve = self.ax_out.plot(x, x, color=self.color, linewidth=LINEWIDTH)[0]

    def create_actors(self):
        super().create_actors()
        self.create_curve()
        self.fix_lim()

    ########################################

    @RunningLine.actors.getter
    def actors(self) -> list[Line2D]:
        return [self.line, self.curve] if hasattr(self, 'line') else []
    
    @actors.setter
    def actors(self, xdata: float):
        super(Slice, Slice).actors.__set__(self, xdata)
        self.curve.set_ydata(self.data[:, round(xdata)])

    @actors.deleter
    def actors(self):
        super(Slice, Slice).actors.__delete__(self)
        if hasattr(self, 'curve'):
            del self.curve

    @property
    def curves(self) -> list[Line2D]:
        curves: list[Line2D] = self.ax_out.lines
        return [curve for curve in curves if curve not in self.actors]
    
    @curves.setter
    def curves(self, curves: list[Line2D]):
        del self.curves
        for curve in curves:
            self.ax_out.add_artist(curve)
    
    @curves.deleter
    def curves(self):
        for curve in self.curves:
            curve.remove()

def main():
    data = np.random.random((50, 50))

    fig, ax = plt.subplots(1, 2)
    ax[0].imshow(data)
    ax[0].axis('off')
    slice = Slice(ax[0], ax[1])
    plt.show()

if __name__ == '__main__':
    main()