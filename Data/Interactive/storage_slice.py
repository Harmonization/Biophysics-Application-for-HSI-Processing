import re

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseEvent
from PyQt6.QtWidgets import QLineEdit

from .Medium.slice import Slice
from .Medium.Elementary.style import *

class StorageSlice(Slice):

    def __init__(self, ax_in: plt.Axes, ax_out: plt.Axes | None = None):
        super().__init__(ax_in, ax_out)
        self.create_input()
        self._container: dict[int, list[int]] = {} # Контейнер хранит координаты линий для разных ключей
        self._key = -1 # Ключ отвечает за текущий элемент контейнера и меняется только извне

    def create_input(self):
        # Создание текстовой области для записи координат линий
        self.input = QLineEdit('', styleSheet=INPUT_STYLE)
        self.input.returnPressed.connect(self.draw_input)

    def update_input(self):
        text = ' '.join(map(str, self.xlines + [Slice.get_x(self.line)]))
        self.input.setText(text)

    def after_move(self, event: MouseEvent):
        super().after_move(event)
        self.update_input()

    def body_release(self, event: MouseEvent):
        super().body_release(event)
        self.xlines = Slice.get_x(self.line)

    ########################################

    @property
    def container(self):
        return self._container
    


    def draw_container(self):
        # Рисование кривых их контейнера по текущему ключу
        self.clear_canvas()
        self.new_color_iter()

        if self.key not in self._container:
            self._container[self.key] = []
        else:
            for x in self.xlines:
                self.create_actors()
                self.actors = x
                del self.actors

    @property
    def key(self) -> int:
        # Текущий ключ
        return self._key
    
    @key.setter
    def key(self, key: int):
        # Изменить текущее состояние {ключ: координаты}
        if self._key == key: return
        self._key = key
        self.draw_container()

    @key.deleter
    def key(self):
        # Срабатывает когда удаляется прямоугольник
        del self._container[self.key]
        self._key = -1

    @property
    def xlines(self) -> list[int]:
        # Текущие координаты линий
        if self.key == -1: return []
        return self._container[self.key]
    
    @xlines.setter
    def xlines(self, x: int):
        self._container[self.key].append(x)

    @xlines.deleter
    def xlines(self):
        # Очистка текущего прямоугольника
        self._container[self.key].clear()
    
    def get_xlines(self, key: int) -> list[int]:
        # Получить координаты по ключу
        if key not in self._container: return []
        return self._container[key]

    ########################################

    def clear_canvas(self):
        del self.actors
        del self.lines
        del self.curves

    def redraw(self):
        # Обновить данные под кривыми (в случае изменения данных изображения)
        for (xdata, line, curve) in zip(self.xlines, self.lines, self.curves):
            # xdata = Slice.get_x(line) # если мы хотим двигать x при изменении размера
            x = min(xdata, self.width-1) # В случае изменения размера изображения
            line.set_xdata([x])
            curve.set_xdata(range(self.height))
            curve.set_ydata(self.data[:, x])

        self.fix_lim()

    def draw_input(self):
        # Пересоздание кривых по позициям из input
        positions = list(map(int, re.findall(r'\d+', self.input.text())))
        if positions == list(self.xlines): return
        try:
            self.clear_canvas()
            for x in positions:
                self.create_actors()
                self.actors = x
                del self.actors
                self.xlines = x
                
        except:
            self.draw_container()
            print('Некорректное значение')
        else:
            del self.xlines
            for x in positions:
                self.xlines = x
            self.draw_all()

    def takedown(self):
        # Уничтожить (вызывается из внешнего класса)
        # del self.key
        # self._container = {}
        self.input.deleteLater()

def main():
    data = np.random.random((50, 50))

    fig, ax = plt.subplots(1, 2)
    ax[0].imshow(data)
    ax[0].axis('off')
    containerized_slice = StorageSlice(ax[0], ax[1])
    containerized_slice.key = 0
    plt.show()

if __name__ == '__main__':
    main()