import re
from matplotlib.backend_bases import MouseEvent

import numpy as np
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QLineEdit

from .Medium.lumen import Lumen
from .Medium.Elementary.style import *

class FlexLumen(Lumen):

    def __init__(self, ndata: np.ndarray[float], ax_in: plt.Axes, ax_out: plt.Axes | None = None):
        super().__init__(ndata, ax_in, ax_out)
        self.create_input()
    
    def create_input(self):
        self.input = QLineEdit('', styleSheet=INPUT_STYLE)
        self.input.returnPressed.connect(self.edit_input)

    def update_input(self):
        # Обновить текстовое поле (нужно при движении окна)
        res = ' '.join([str(self.get_xy(point)) for point in self.points + [self.point]])
        self.input.setText(res)
        self.fix_lim()

    def edit_input(self):
        # Зафиксировать изменения в текстовом поле
        points = re.findall(r'\(\d+, \d+\)', self.input.text())
        points_str = [re.findall(r'\d+', point) for point in points]
        points_int = list(map(lambda xy: (int(xy[0]), int(xy[1])), points_str))
        del self.spectres
        self.points = points_int
        self.draw_all()

    def after_click(self, event: MouseEvent):
        super().after_click(event)
        self.update_input()

    def after_move(self, event: MouseEvent):
        super().after_move(event)
        self.update_input()

    def takedown(self):
        self.input.deleteLater()
        del self.actors
        del self.points
        self.draw_in()

def main():
    data = np.random.random((50, 50, 204))

    fig, ax = plt.subplots(1, 2)
    ax[0].imshow(data[:, :, 0])
    ax[0].axis('off')

    flex_lumen = FlexLumen(data, ax[0], ax[1])
    plt.show()

if __name__ == '__main__':
    main()