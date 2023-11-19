import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseEvent
from matplotlib.lines import Line2D

from .creator import Creator
from .style import LINEWIDTH

class RunningLine(Creator):

    def __init__(self, ax_in: plt.Axes):
        super().__init__(ax_in)

    def create_line(self):
        self.line = self.ax_in.axvline(0, color=self.color, linewidth=LINEWIDTH)

    def create_actors(self):
        self.new_color()
        self.create_line()

    ########################################

    def left_click(self, event: MouseEvent):
        self.create_actors()

    def right_click(self, event: MouseEvent):
        self.create_actors()

    def after_move(self, event: MouseEvent):
        self.actors = event.xdata

    def body_release(self, event: MouseEvent):
        self.actors = event.xdata

    def after_release(self, event: MouseEvent):
        del self.actors

    ########################################

    @property
    def actors(self) -> list[Line2D]:
        return [self.line] if hasattr(self, 'line') else []
    
    @actors.setter
    def actors(self, xdata: float):
        self.line.set_xdata([round(xdata)])

    @actors.deleter
    def actors(self):
        self.actors.clear()
        if hasattr(self, 'line'):
            del self.line

    @property
    def lines(self) -> list[Line2D]:
        lines: list[Line2D] = self.ax_in.lines
        return [line for line in lines if line not in self.actors]

    @lines.setter
    def lines(self, lines: list[Line2D]):
        del self.lines
        for line in lines:
            self.ax_in.add_artist(line)

    @lines.deleter
    def lines(self):
        for line in self.lines:
            line.remove()

    ########################################

    @staticmethod
    def get_x(line: Line2D) -> int:
        return round(line.get_xdata()[0])
    
    @staticmethod
    def xdata2text(lines: list[Line2D]) -> str:
        line_xdata = map(RunningLine.get_x, lines)
        line_str_xdata = map(str, line_xdata)
        return ' '.join(line_str_xdata)

def main():
    data = np.random.random((50, 50))

    fig, ax = plt.subplots()
    ax.imshow(data)
    ax.axis('off')
    vline = RunningLine(ax)
    plt.show()

if __name__ == '__main__':
    main()