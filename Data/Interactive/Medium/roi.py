import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.backend_bases import MouseEvent
from matplotlib.image import AxesImage

from .Elementary.window import RunningWindow
from .Elementary.style import CMAP

class ROI(RunningWindow):

    def __init__(self, ax_in: plt.Axes, ax_out: plt.Axes | None = None):
        super().__init__(ax_in)
        self.fig_out, self.ax_out = (ax_out.figure, ax_out) if ax_out else plt.subplots()

    ########################################

    def after_click(self, event: MouseEvent):
        self.image_roi = self.roi

    def after_move(self, event: MouseEvent):
        self.image_roi = self.roi

    ########################################

    def get_roi(self, x0: int, y0: int, x1: int, y1: int) -> np.ndarray[float]:
        return self.data[y0:y1, x0:x1]

    @property
    def roi(self) -> np.ndarray[float]:
        # Получить данные изображения под прямоугольником
        x0, y0, x1, y1 = self.points
        return self.data[y0:y1, x0:x1]
    
    @property
    def image_roi(self) -> AxesImage:
        if not len(self.ax_out.images): self.ax_out.imshow(self.data, cmap=CMAP)
        return self.ax_out.images[-1]
    
    @image_roi.setter
    def image_roi(self, data: np.ndarray[float]):
        self.image_roi.set_data(data)

        new_extent = list(AxesImage(self.ax_out, data=data).get_extent())
        extent = self.image_roi.get_extent()
        if new_extent == (-.5,)*4 or new_extent == extent: return
        self.image_roi.set_extent(new_extent)
        # self.ax_out.figure.canvas.draw()

    ########################################

    @RunningWindow.actors.getter
    def actors(self) -> list[Rectangle | AxesImage]:
        return [self.rectangle, self.image_roi]

def main():
    data = np.random.random((50, 50))

    fig, ax = plt.subplots(1, 2)
    ax[0].imshow(data)
    ax[0].axis('off')
    roi = ROI(ax[0], ax[1])
    plt.show()

if __name__ == '__main__':
    main()