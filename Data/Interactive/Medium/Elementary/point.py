import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseEvent
from matplotlib.lines import Line2D
# from mpl_interactions import zoom_factory

from .creator import Creator

class RunningPoint(Creator):

    def __init__(self, ax_in: plt.Axes):
        super().__init__(ax_in)
        # zoom_factory(self.ax_in)

    ########################################

    def left_click(self, event: MouseEvent):
        self.create_actors()

    def right_click(self, event: MouseEvent):
        self.create_actors()
    
    def after_move(self, event: MouseEvent):
        self.actors = (event.xdata, event.ydata)

    def body_release(self, event: MouseEvent):
        self.actors = (event.xdata, event.ydata)

    def after_release(self, event: MouseEvent):
        del self.actors

    ########################################

    def create_point(self):
        self.point = self.ax_in.plot([0], [0], color=self.color, marker='p')[0]

    def create_actors(self):
        self.new_color()
        self.create_point()

    @property
    def actors(self):
        return [self.point] if hasattr(self, 'point') else []
    
    @actors.setter
    def actors(self, xy: tuple[float, float]):
        x, y = np.around(xy)
        self.point.set_xdata([x])
        self.point.set_ydata([y])

    @actors.deleter
    def actors(self):
        self.actors.clear()
        if hasattr(self, 'point'):
            del self.point

    @property
    def points(self) -> list[Line2D]:
        points: list[Line2D] = self.ax_in.lines
        return [point for point in points if point not in self.actors]
    
    @points.setter
    def points(self, points_int: list[tuple[int, int]]):
        del self.actors
        del self.points
        for xy in points_int:
            self.create_actors()
            self.actors = (xy[0], xy[1])
            del self.actors

    @points.deleter
    def points(self):
        for point in self.points:
            point.remove()

    @staticmethod
    def get_xy(point: Line2D):
        x = round(point.get_xdata()[0])
        y = round(point.get_ydata()[0])
        return x, y

    
def main():
    data = np.random.random((50, 50))

    fig, ax = plt.subplots()
    ax.imshow(data)
    ax.axis('off')
    point = RunningPoint(ax)
    plt.show()

if __name__ == '__main__':
    main()