import re

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.backend_bases import MouseEvent
from matplotlib.image import AxesImage
from mpl_toolkits.axes_grid1 import make_axes_locatable
from PyQt6.QtWidgets import QLineEdit

from .Interactive.Medium.Elementary.window import RunningWindow
from .Interactive.Medium.Elementary.style import *
from .hsi import HSI

class MeanSign(RunningWindow):

    def __init__(self, hsi: HSI, ax_in: plt.Axes, ax_out: list[plt.Axes] | None = None):
        super().__init__(ax_in)
        self.create_subplots(ax_out)
        self.hsi = hsi
        self.create_mean_sign()
        self.create_mean_matrix()
        self.create_input()
        self.create_mx_ticks()

    def create_subplots(self, ax_out: list[plt.Axes]):
        # Подграфик
        if not (ax_out is None):
            self.fig_out, (self.ax_out, self.mx_out) = ax_out[0].figure, ax_out
        else:
            self.fig_out= plt.figure()
            self.ax_out = self.fig_out.add_axes([.15, .7, .7, .27])
            self.mx_out = self.fig_out.add_axes([.15, .05, .7, .6])

        # ColorBar
        divider = make_axes_locatable(self.mx_out)
        self.cax = divider.append_axes('right', size='5%', pad=.05)
    
    def create_mx_ticks(self):
        # matrix ticks
        ticks = np.linspace(0, 203, 6, dtype=int)
        labels = self.hsi.wavelengths[ticks]

        self.mx_out.set_xticks(ticks)
        self.mx_out.set_yticks(ticks)
        self.mx_out.set_xticklabels(labels)
        self.mx_out.set_yticklabels(labels)

    def create_input(self):
        # Создать текстовое поле с координатами
        self.input = QLineEdit('', styleSheet=INPUT_STYLE)
        self.input.returnPressed.connect(self.edit_input)

    def update_input(self):
        # Обновить текстовое поле (нужно при движении окна)
        x0, y0, x1, y1 = self.points
        self.input.setText(f'{x0=} {y0=} {x1=} {y1=}')

    def edit_input(self):
        # Зафиксировать изменения в текстовом поле

        if not self.input.text():
            self.remove() # Если поле пустое, удаляем текущее окно
            return
        
        x0, y0, x1, y1 = map(int, re.findall(r'\d+', self.input.text())[1::2])
        self.points = (x0, y0, x1, y1)
        self.update_actors()
        self.draw_all()

    def draw_out(self):
        self.ax_out.figure.canvas.draw()

    def draw_all(self):
        self.draw_in()
        self.draw_out()

    ########################################

    def create_mean_sign(self):
        wave = self.hsi.wavelengths
        self.spectre = self.hsi.mean_sign()
        self._ms = self.ax_out.plot(wave, self.spectre, linewidth=LINEWIDTH, color='lime')[0]

    def create_mean_matrix(self):
        self._mx = self.mx_out.imshow(self.matrix, cmap='nipy_spectral')
        self.cb = self.fig_out.colorbar(self._mx, cax=self.cax, orientation='vertical')


    def create_spectre(self):
        # Высислить средний спектр для текущего прямоугольника
        self.spectre = self.hsi.mean_sign(self.deep_roi)

    def get_spectre(self, deep_roi: np.ndarray[float]) -> np.ndarray[float]:
        # Вычислить средний спектр
        return self.hsi.mean_sign(deep_roi)
    
    def get_matrix(self, spectre: np.ndarray[float]) -> np.ndarray[float]:
        # Вычислить матрицу по среднему спектру
        return self.hsi.mean_matrix(spectre)

    ########################################

    def update_actors(self):
        self.create_spectre()
        self.ms = self.spectre
        self.mx = self.matrix
        
        # Меняем границы cmap и colorbar
        self._mx.set_clim([self.mx.get_array().min(), self.mx.get_array().max()])

    def after_click(self, event: MouseEvent):
        super().after_click(event)
        self.update_actors()
        self.update_input()

    def after_move(self, event: MouseEvent):
        super().after_move(event)
        self.update_actors()
        self.update_input()

    ########################################
    
    def get_deep_roi(self, rectangle: Rectangle) -> np.ndarray[float] | None:
        # Получить данные HSI под прямоугольником
        x0, y0, x1, y1 = MeanSign.get_points(rectangle)
        if x0 != x1 and y0 != y1:
            return self.hsi.deep_roi(x0, y0, x1, y1)
        else:
            return None

    @property
    def deep_roi(self) -> np.ndarray[float] | None:
        # Получить данные HSI под текущим прямоугольником
        x0, y0, x1, y1 = self.points
        if x0 != x1 and y0 != y1:
            return self.hsi.deep_roi(x0, y0, x1, y1)
        else:
            return None


    @property
    def matrix(self) -> np.ndarray[float]:
        if self.spectre is None: return
        return self.hsi.mean_matrix(self.spectre)
    
    @property
    def ms(self):
        return self._ms
    
    @ms.setter
    def ms(self, spectre: np.ndarray[float]):
        if spectre is None: return
        self.ms.set_ydata(spectre)
        self.ax_out.set_ylim([spectre.min(), spectre.max()])
    
    @property
    def mx(self) -> AxesImage:
        return self._mx
    
    @mx.setter
    def mx(self, matrix: np.ndarray[float]):
        self._mx.set_data(matrix)

    ########################################

    @RunningWindow.actors.getter
    def actors(self) -> list[Rectangle | AxesImage]:
        return [self.rectangle, self.ms, self.mx]

    def takedown(self):
        # Уничтожить (вызывается из внешнего класса)
        self.input.deleteLater()
        del self.rectangles
        self.draw_in()

    def remove(self):
        # Удалить текущий прямоугольник
        self.spectre = self.hsi.mean_sign()
        self.ms = self.spectre
        self.mx = self.matrix
        del self.rectangle
        self.draw_all()

def main():
    hsi = HSI()
    hsi.load()
    channel = hsi.calculate_channel('b70 + b60 / 3')

    fig, ax = plt.subplots(1, 3)
    ax[0].imshow(channel)
    ax[0].axis('off')
    mean_sign = MeanSign(hsi, ax[0], ax[1:])
    plt.show()

if __name__ == '__main__':
    main()