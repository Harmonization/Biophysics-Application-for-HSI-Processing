from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Iterator

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseEvent
from matplotlib.image import AxesImage
from matplotlib.lines import Line2D
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox
from matplotlib.patches import Rectangle

class Creator(ABC):

    @abstractmethod
    def __init__(self, ax_in: plt.Axes):
        self.ax_in = ax_in # Ось привязки событий
        self.connects = 'on' # Подключение событий мыши

    def connect(self, event: str, function: Callable[[MouseEvent], None]):
        # Привязать вызов функции к событию мыши
        return self.ax_in.figure.canvas.mpl_connect(event, function)     

    def draw_in(self):
        self.ax_in.figure.canvas.draw()

    @abstractmethod
    def create_actors(self):
        # Создание анимированных элементов
        pass

    ########################################

    @abstractmethod
    def left_click(self, event: MouseEvent):
        pass

    @abstractmethod
    def right_click(self, event: MouseEvent):
        pass

    def exit_condition(self) -> bool:
        return False

    def after_click(self, event: MouseEvent):
        pass
    
    def click(self, event: MouseEvent):
        if event.inaxes != self.ax_in: return
        match event.button:
            case 1:
                self.left_click(event)
            case 3:
                self.right_click(event)
                if self.exit_condition(): return
            case _:
                return
        
        self.after_click(event)
        self.animated = 'start'

    def left_move(self, event: MouseEvent):
        pass

    def right_move(self, event: MouseEvent):
        pass

    def after_move(self, event: MouseEvent):
        pass

    def move(self, event: MouseEvent):
        if event.inaxes != self.ax_in: return
        match event.button:
            case 1:
                self.left_move(event)
            case 3:
                if self.exit_condition(): return
                self.right_move(event)
            case _:
                return
            
        self.after_move(event)
        self.animated = 'step'

    def body_release(self, event: MouseEvent):
        pass

    def after_release(self, event: MouseEvent):
        pass

    def release(self, event: MouseEvent):
        if event.inaxes != self.ax_in \
            or event.button not in (1, 3) \
                or self.exit_condition(): return
        self.body_release(event)
        self.animated = 'stop'
        self.after_release(event)
    
    @property
    def connects(self) -> list[int]:
        return self._connects
    
    @connects.setter
    def connects(self, mode: str):
        match mode:
            case 'on':
                self._connects = [self.connect('button_press_event', self.click), # Нажатие лкм/пкм
                                  self.connect('motion_notify_event', self.move), # Движение мыши
                                  self.connect('button_release_event', self.release)] # Отжатие лкм/пкм
            case 'off':
                for cid in self.connects:
                    self.ax_in.figure.canvas.mpl_disconnect(cid)

    ########################################

    @staticmethod
    def color_iter() -> Iterator[str]:
        colors = ['#FF47CA', '#FF033E', '#7FFFD4', '#A8E4A0', '#990066',
                  '#FAE7B5', '#77DDE7', '#98FB98', '#34C924', '#F64A46',
                  '#FF1493', '#00BFFF', '#FD7C6E', '#C7D0CC', '#EDFF21',
                  '#ED760E', '#FFFF00', '#BFFF00', '#3BB08F', '#FF4D00']
        i = 0
        while(True):
            yield colors[i % len(colors)]
            i += 1

    @property
    def color(self) -> str:
        return self._colors[-1]
    
    @property
    def colors(self):
        return self._colors
    
    @colors.setter
    def colors(self, colors: list[str]):
        self._colors += colors
    
    @colors.deleter
    def colors(self):
        self._colors.clear()

    def new_color_iter(self):
        self._colors_iter = Creator.color_iter()
    
    def new_color(self):
        if not hasattr(self, 'colors'): 
            self.new_color_iter()
            self._colors = []
        self.colors = [next(self._colors_iter)]

    ########################################

    @property
    def data(self) -> np.ndarray[float]:
        # Получить массив изображения под осями
        img: AxesImage = self.ax_in.images[0]
        return img.get_array()
    
    @property
    def height(self) -> int:
        # Высота данных в пикселях
        return self.data.shape[0]
    
    @property
    def width(self) -> int:
        # Ширина данных в пикселях
        return self.data.shape[1]
    
    ########################################
    @abstractmethod
    def create_actors(self):
        # Создание элементов при клике
        pass

    @property
    @abstractmethod
    def actors(self) -> list[Rectangle | AxesImage | Line2D]:
        # Анимированные элементы
        pass

    @property
    def animated(self) -> bool:
        for actor in self.actors:
            return actor.get_animated()
        return False

    @animated.setter
    def animated(self, mode: str):
        match mode:
            case 'start':
                self.figures: dict[Figure, Bbox] = {}
                
                for actor in self.actors:
                    actor.set_animated(True)
                    fig = actor.axes.figure
                    self.figures[fig] = None

                for fig in self.figures:
                    fig.canvas.draw()
                    self.figures[fig] = fig.canvas.copy_from_bbox(fig.bbox)

            case 'step':
                for fig, bg in self.figures.items():
                    fig.canvas.restore_region(bg)

                for actor in self.actors:
                    actor.axes.draw_artist(actor)

                for fig in self.figures:
                    fig.canvas.blit(fig.bbox)
                    # fig.canvas.flush_events()

            case 'stop':
                for actor in self.actors:
                    actor.set_animated(False)

                for fig in self.figures:
                    fig.canvas.draw()
                
                self.figures.clear()
            case _:
                return
