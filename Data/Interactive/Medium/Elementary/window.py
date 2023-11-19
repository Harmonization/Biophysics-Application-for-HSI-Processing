from functools import reduce
from collections.abc import Sequence

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.backend_bases import MouseEvent
from matplotlib.image import AxesImage

from .creator import Creator
from .style import RECT_COLOR, RECT_COLOR_CHANGE, LINEWIDTH

class RunningWindow(Creator):

    def __init__(self, ax_in: plt.Axes):
        super().__init__(ax_in)
        self._rectangle: int = None

    def draw_in(self):
        self.ax_in.figure.canvas.draw()

    def clear(self):
        self.rectangle = None
        for patch in self.rectangles:
            patch.remove()
        self.draw_in()

    ########################################

    def create_actors(self, x0: float, y0: float):
        rectangle = Rectangle((x0, y0), 0, 0, 
                                fill=False, color=RECT_COLOR_CHANGE, 
                                linewidth=LINEWIDTH, linestyle='--')
        self.ax_in.add_patch(rectangle)

        self.change_color(RECT_COLOR)
        self.rectangle = len(self) - 1

    def change_color(self, color: str):
        if not (self.rectangle is None):
            self.rectangle.set_color(color)
    
    def change_rectangle(self, event: MouseEvent):
        self.change_color(RECT_COLOR)
        def func(prev: tuple[int, float], indx: int) -> tuple[int, float]:
            cur = self[indx]
            area = RunningWindow.area(cur)
            condition = cur.contains(event)[0] and area < prev[-1]
            return (indx, area) if condition else prev
            
        self.rectangle = reduce(func, range(len(self)), (None, float('inf')))[0]
        self.change_color(RECT_COLOR_CHANGE)


    def shift_rectangle(self, event: MouseEvent):
        # Вычисление сдвига по координатам
        x0, y0 = self.start_rect_xy
        press_x0, press_y0 = self.start_press_xy
        x, y = event.xdata, event.ydata
        dx, dy = (x - press_x0, y - press_y0)

        self.xy = (x0+dx, y0+dy)

    @staticmethod
    def area(rectangle: Rectangle) -> float:
        return abs(rectangle.get_width() * rectangle.get_height())
    
    ########################################

    def left_click(self, event: MouseEvent):
        self.create_actors(event.xdata, event.ydata)

    def right_click(self, event: MouseEvent):
        self.change_rectangle(event)
        if self._rectangle is None: return
        
        # Стартовая координата прямоугольника в момент нажатия
        self.start_rect_xy = self.rectangle.xy 
        
        # Стартовая координата мыши в момент нажатия
        self.start_press_xy = event.xdata, event.ydata

    def exit_condition(self) -> bool:
        return self._rectangle is None

    def left_move(self, event: MouseEvent):
        # Меняем размер прямоугольника
        x0, y0 = self.rectangle.xy
        self.size = (event.xdata - x0, event.ydata - y0)

    def right_move(self, event: MouseEvent):
        # Вычисление сдвига по координатам
        self.shift_rectangle(event)

    ########################################

    @property
    def actors(self) -> list[Rectangle | AxesImage]:
        return [self.rectangle]

    @property
    def rectangles(self) -> Sequence[Rectangle]:
        return self.ax_in.patches

    @rectangles.deleter
    def rectangles(self):
        for rectangle in self.rectangles:
            rectangle.remove()

    @property
    def rectangle(self) -> Rectangle | None:
        # Получить текущий прямоугольник
        if self._rectangle is None: return None
        return self[self._rectangle]
    
    @rectangle.setter
    def rectangle(self, indx: int | None):
        if indx is None or 0 <= indx < len(self):
            self._rectangle = indx

    @rectangle.deleter
    def rectangle(self):
        self.rectangle.remove()
        self._rectangle = None
        
    ########################################
    
    @staticmethod
    def get_size(rectangle: Rectangle) -> np.ndarray[int]:
        return np.around([rectangle.get_width(), rectangle.get_height()]).astype(int)

    @property
    def size(self) -> np.ndarray[int]:
        # Получить размер текущего прямоугольника
        return np.around([self.rectangle.get_width(), self.rectangle.get_height()]).astype(int)
    
    @size.setter
    def size(self, new_size: tuple[float, float]):
        # Поменять размер текущего прямоугольника
        self.rectangle.set_width(new_size[0])
        self.rectangle.set_height(new_size[1])

    @staticmethod
    def get_xy(rectangle: Rectangle) -> np.ndarray[int]:
        return np.around(rectangle.xy).astype(int)

    @property
    def xy(self) -> np.ndarray[int]:
        return np.around(self.rectangle.xy).astype(int)
    
    @xy.setter
    def xy(self, x_y: tuple[float, float]):
        self.rectangle.set_x(x_y[0])
        self.rectangle.set_y(x_y[1])

    @staticmethod
    def get_points(rectangle: Rectangle):
        image: AxesImage = rectangle.axes.images[0]
        data: np.ndarray[float] = image.get_array()
        
        x, y = RunningWindow.get_xy(rectangle)
        w, h = RunningWindow.get_size(rectangle)

        x0, x1 = (x, x+w) if w > 0 else (x+w, x)
        y0, y1 = (y, y+h) if h > 0 else (y+h, y)
        
        x0 = max(x0, 0)
        y0 = max(y0, 0)
        x1 = min(x1, data.shape[1])
        y1 = min(y1, data.shape[0])
        return x0, y0, x1, y1

    @property
    def points(self):
        # Получение левой верхней и правой нижней точек прямоугольника
        x, y = self.xy
        w, h = self.size
        x0, x1 = (x, x+w) if w > 0 else (x+w, x)
        y0, y1 = (y, y+h) if h > 0 else (y+h, y)
        
        x0 = max(x0, 0)
        y0 = max(y0, 0)
        x1 = min(x1, self.data.shape[1])
        y1 = min(y1, self.data.shape[0])
        return x0, y0, x1, y1
    
    @points.setter
    def points(self, points: tuple[float, float, float, float]):
        x0, y0, x1, y1 = points
        self.xy = (x0, y0)
        w, h = x1 - x0, y1 - y0
        self.size = (w, h)

    ########################################

    def __len__(self):
        return len(self.rectangles)

    def __getitem__(self, indx: int) -> Rectangle:
        if type(indx) != int: raise TypeError('Неправильный тип индекса')
        if indx >= len(self): raise IndexError('Слишком большой индекс')
        return self.rectangles[indx]
    
def main():
    data = np.random.random((50, 50))

    fig, ax = plt.subplots()
    ax.imshow(data)
    ax.axis('off')
    window = RunningWindow(ax)
    plt.show()

if __name__ == '__main__':
    main()