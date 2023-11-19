import re

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseEvent
from PyQt6.QtWidgets import QLineEdit

from .Medium.roi import ROI
from .storage_slice import StorageSlice
from .Medium.Elementary.style import *

class LimSlice(ROI):

    def __init__(self, ax_in: plt.Axes, ax_out: list[plt.Axes] | None = None):
        self.create_subplots(ax_out)
        super().__init__(ax_in, self.ax_out)
        self.create_input()
        self.slice = StorageSlice(self.ax_out, self.slice_out)

    def create_input(self):
        self.input = QLineEdit('', styleSheet=INPUT_STYLE)
        self.input.returnPressed.connect(self.edit_input)

    def update_input(self):
        x0, y0, x1, y1 = self.points
        self.input.setText(f'{x0=} {y0=} {x1=} {y1=}')
        self.slice.input.setText(' '.join([str(StorageSlice.get_x(line)) for line in self.slice.lines]))

    def edit_input(self):
        if not self.input.text():
            self.remove() # Если поле пустое, удаляем текущее окно
            return
            
        x0, y0, x1, y1 = map(int, re.findall(r'\d+', self.input.text())[1::2])
        self.points = (x0, y0, x1, y1)

        self.image_roi = self.roi

        self.slice.redraw()
        self.draw_all()

    def create_subplots(self, ax_out: list[plt.Axes]):
        # Подграфик
        if not (ax_out is None):
            self.fig_out, (self.ax_out, self.slice_out) = ax_out[0].figure, ax_out
        else:
            self.fig_out, (self.ax_out, self.slice_out) = plt.subplots(2)

    def draw_all(self):
        self.draw_in()
        self.slice.draw_all()

    ########################################

    def after_click(self, event: MouseEvent):
        super().after_click(event)
        self.slice.key = self._rectangle
        self.update_input()

    def right_move(self, event: MouseEvent):
        super().right_move(event)
        self.slice.redraw()

    def after_move(self, event: MouseEvent):
        super().after_move(event)
        self.update_input()
        self.slice.redraw()

    def body_release(self, event: MouseEvent):
        super().body_release(event)
        self.slice.redraw()

    ########################################
    
    @ROI.actors.getter
    def actors(self):
        return [self.rectangle, self.image_roi] + \
            self.slice.lines + self.slice.curves
    
    def takedown(self):
        # Уничтожить (вызывается из внешнего класса)
        self.slice.takedown()
        self.input.deleteLater()
        del self.rectangles
        self.draw_in()

    def remove(self):
        # Удалить текущий прямоугольник
        self.slice.clear_canvas()
        del self.rectangle
        self.draw_all()

    

def main():
    data = np.random.random((50, 50))

    fig, ax = plt.subplots(1, 3)
    ax[0].imshow(data)
    ax[0].axis('off')
    lim_slice = LimSlice(ax[0], ax[1:])
    plt.show()

if __name__ == '__main__':
    main()