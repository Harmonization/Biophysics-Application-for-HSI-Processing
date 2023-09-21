import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from mpl_interactions import zoom_factory
from functools import reduce

class RectanglesDraw:
    def __init__(self, ax=None):
        if ax is None:
            self.fig, self.ax = plt.subplots()
        else: 
            self.ax = ax
            self.fig = ax.figure
        self.canvas = self.fig.canvas
        self.rectangles = []
        self.text = []
        self.rect = None
        self.rect_indx = 0
        self.press_flag = False # произошло ли нажатие
        zoom_factory(self.ax)

    def connect(self):
        self.connects = [self.canvas.mpl_connect('button_press_event', self.on_press),
                        self.canvas.mpl_connect('motion_notify_event', self.on_move),
                        self.canvas.mpl_connect('button_release_event', self.on_release)]
        
    def get_xywh(self):
        # Получить начальную точку, ширину и высоту (могут быть отрицательными)
        return np.around([*self.rect.xy, self.rect.get_width(), self.rect.get_height()]).astype(int)
    
    def txt_move(self):
        # Двигать текст оставляя его внутри прямоугольника
        x, y, w, h = self.get_xywh()
        self.txt.set_x((x+x+w)//2)
        self.txt.set_y((y+y+h)//2)
        
    def clear(self):
        # Очистить данные от фигур
        for (rect, txt) in zip(self.rectangles, self.text):
            rect.remove()
            txt.remove()
        self.rectangles = []
        self.text = []
        self.rect_indx = 0
        if hasattr(self, 'rect'):
            del self.rect
        self.canvas.draw()

    def start_animation(self, ax, *elements):
        for el in elements:
            el.set_animated(True)
            el.figure.canvas.draw()
        background = self.canvas.copy_from_bbox(ax.bbox)
        for el in elements:
            ax.draw_artist(el)
            el.figure.canvas.blit(ax.bbox)
        return background
    
    def animation(self, *elements):
        self.canvas.restore_region(self.background)
        for el in elements:
            self.ax.draw_artist(el)
        self.canvas.blit(self.ax.bbox)
    
    def end_animation(self, *elements):
        for el in elements:
            el.set_animated(False)
        self.background = None
        self.canvas.draw()

    def on_press(self, event):
        if event.inaxes != self.ax or event.button not in (1, 3): return
        self.press_flag = True
        match event.button:
            case 1:
                self.rectangles.append(self.ax.add_patch(
                    Rectangle((event.xdata, event.ydata), 0, 0, fill=False, color='#FF4D00', linewidth=2, linestyle='--')
                    ))
                
                self.rect = self.rectangles[-1]
                self.rect_indx = len(self.rectangles) - 1
                self.text.append(self.ax.text(0, 0, self.rect_indx+1, fontsize=15, color='#FF47CA'))
            
            case 3:
                self.rect_indx, self.rect, _ = reduce(lambda prev, cur: (*cur, area) if cur[1].contains(event)[0] and 
                                (area := abs(cur[1].get_width() * cur[1].get_height())) < prev[-1] else prev, 
                                enumerate(self.rectangles), 
                                first_element := (rect_indx := 0, rect := None, area := float('inf')))

                if not self.rect: return

                self.press = self.rect.xy, (event.xdata, event.ydata)

            case _:
                return
        
        self.txt = self.text[self.rect_indx]
        self.background = self.start_animation(self.ax, self.rect, self.txt)

    def on_move(self, event):
        if event.inaxes != self.ax or event.button not in (1, 3) or not self.rect: return
        self.press_flag = False
        match event.button:
            case 1:
                try:
                    x0, y0 = self.rect.xy
                    self.rect.set_width(event.xdata - x0)
                    self.rect.set_height(event.ydata - y0)
                except:
                    pass

            case 3:
                if not self.rect or event.inaxes != self.ax: return
                
                (x0, y0), (xpress, ypress) = self.press
                x, y = event.xdata, event.ydata
                dx = x - xpress
                dy = y - ypress
                self.rect.set_x(x0+dx)
                self.rect.set_y(y0+dy)
                
            case _:
                return
            
        self.txt_move()
        self.animation(self.rect, self.txt)

    def on_release(self, event):
        if event.button not in (1, 3) or not self.rect: return
        
        self.end_animation(self.rect, self.txt)
        self.rect = self.txt = None

    def disconnect(self):
        for connect in self.connects:
            self.canvas.mpl_disconnect(connect)

if __name__ == "__main__":

    def get_test_data():
        x = np.linspace(0, np.pi, 100)
        y = np.linspace(0, 10, 200)
        X, Y = np.meshgrid(x, y)
        return np.sin(X) + np.exp(np.cos(Y))

    fig, ax = plt.subplots()
    ax.imshow(get_test_data())
    a = RectanglesDraw(ax)
    a.connect()
    plt.show()