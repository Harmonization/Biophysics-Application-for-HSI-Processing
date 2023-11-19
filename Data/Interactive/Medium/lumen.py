from functools import reduce
from matplotlib.backend_bases import MouseEvent

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from .Elementary.point import RunningPoint
from .Elementary.style import LINEWIDTH

class Lumen(RunningPoint):

    def __init__(self, ndata: np.ndarray[float], ax_in: plt.Axes, ax_out: plt.Axes | None = None):
        super().__init__(ax_in)
        self.fig_out, self.ax_out = (ax_out.figure, ax_out) if not (ax_out is None) else plt.subplots()
        self._ndata = ndata

    def fix_lim(self, eps: float = .05):

        def find_max(prev_max: float, spectre: Line2D):
            y_max = np.max(spectre.get_ydata())
            return max(y_max, prev_max)
        
        y_max = reduce(find_max, self.spectres + [self.spectre], 1 + eps)

        self.ax_out.set_ylim([-eps, y_max+eps])

    def draw_out(self):
        self.ax_out.figure.canvas.draw()

    def draw_all(self):
        self.draw_in()
        self.draw_out()

    ########################################

    def create_signature(self):
        x = range(self.depth)
        self.spectre = self.ax_out.plot(x, [0]+[1]*(len(x)-1), color=self.color, linewidth=LINEWIDTH)[0]

    def create_actors(self):
        super().create_actors()
        self.create_signature()
        # self.fix_lim()

    def body_release(self, event: MouseEvent):
        super().body_release(event)
        self.fix_lim()

    ########################################

    @property
    def ndata(self) -> np.ndarray[float]:
        return self._ndata
    
    @ndata.setter
    def ndata(self, ndata: np.ndarray[float]):
        if len(ndata.shape) != 3: return
        self._ndata = ndata

    @property
    def depth(self):
        return self.ndata.shape[-1]
    
    def get_lumen(self, x: float, y: float) -> np.ndarray[float]:
        return self.ndata[round(y), round(x), :]

    ########################################

    @RunningPoint.actors.getter
    def actors(self) -> list[Line2D]:
        return [self.point, self.spectre] if hasattr(self, 'point') else []
    
    @actors.setter
    def actors(self, xy: tuple[float, float]):
        super(Lumen, Lumen).actors.__set__(self, xy)
        x, y = xy
        lumen = self.get_lumen(x, y)
        self.spectre.set_ydata(lumen)

    @actors.deleter
    def actors(self):
        super(Lumen, Lumen).actors.__delete__(self)
        if hasattr(self, 'spectre'):
            del self.spectre

    @property
    def spectres(self):
        spectres: list[Line2D] = self.ax_out.lines
        return [spectre for spectre in spectres if spectre not in self.actors]
    
    @spectres.deleter
    def spectres(self):
        for spectre in self.spectres:
            spectre.remove()

def main():
    data = np.random.random((50, 50, 204))

    fig, ax = plt.subplots(1, 2)
    ax[0].imshow(data[:, :, 0])
    ax[0].axis('off')

    lumen = Lumen(data, ax[0], ax[1])
    plt.show()

if __name__ == '__main__':
    main()