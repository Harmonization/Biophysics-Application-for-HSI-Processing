import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseEvent
from matplotlib.image import AxesImage
from mpl_toolkits.mplot3d.art3d import Patch3DCollection

from Elementary.window import RunningWindow

class ROI3D(RunningWindow):

    def __init__(self, ax_in: plt.Axes, ax_out: plt.Axes | None = None):
        super().__init__(ax_in)
        self.create_subplots(ax_out)
        self.create_roi()

    def create_subplots(self, ax_out: plt.Axes):
        if ax_out:
            self.fig_out, self.ax_out = ax_out.figure, ax_out
        else:
            self.fig_out = plt.figure()
            self.ax_out = self.fig_out.add_subplot(projection='3d')
        
    def create_roi(self):
        x = range(50)
        x, y = np.meshgrid(x, x)
        z = self.data
        self._roi_3d = self.ax_out.scatter(x, y, z, cmap='plasma')

    ########################################

    def after_click(self, event: MouseEvent):
        self.image_roi = self.roi

    def after_move(self, event: MouseEvent):
        self.image_roi = self.roi

    ########################################

    @property
    def roi(self) -> np.ndarray[float]:
        # Получить данные изображения под прямоугольником
        x0, y0, x1, y1 = self.points
        return self.data[y0:y1, x0:x1]
    
    @property
    def image_roi(self) -> AxesImage:
        if not len(self.ax_out.images): self.ax_out.imshow(self.data)
        return self.ax_out.images[-1]
    
    @property
    def roi_3d(self) -> Patch3DCollection:
        return self._roi_3d
    
    @image_roi.setter
    def image_roi(self, data: np.ndarray[float]):
        # self.image_roi.set_data(data)
        # self.roi_3d.set_array(data)
        
        # self.roi_3d.set_3d_properties([1, 2, 3], 'x')
        # self.roi_3d.set_3d_properties([1, 2, 3], 'y')
        self.roi_3d.set_3d_properties(self.data, 'z')

        # new_extent = list(AxesImage(self.ax_out, data=data).get_extent())
        # extent = self.image_roi.get_extent()
        # if new_extent == (-.5,)*4 or new_extent == extent: return
        # self.image_roi.set_extent(new_extent)
        # self.ax_out.figure.canvas.draw()

    ########################################

    # @RunningWindow.actors.getter
    # def actors(self) -> list[Rectangle | AxesImage]:
    #     return [self.rectangle, self.roi_3d]

def main():
    data = np.random.random((50, 50))

    fig, ax = plt.subplots()
    # ax_3d = Axes3D(fig)
    ax.imshow(data)
    ax.axis('off')
    roi_3d = ROI3D(ax)
    plt.show()

if __name__ == '__main__':
    main()