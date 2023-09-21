import matplotlib.pyplot as plt
import numpy as np

class DataSlice:

    def __init__(self, data, ax, img):
        self.data = data
        self.ax = ax
        self.fig = ax[0].figure
        self.img = img
        self.canvas = self.fig.canvas
        self.curves = []
        
        def get_color():
            colors = ['#FF47CA', '#FF033E', '#7FFFD4', '#A8E4A0', '#990066',
                  '#FAE7B5', '#77DDE7', '#98FB98', '#34C924', '#F64A46',
                  '#FF1493', '#00BFFF', '#FD7C6E', '#C7D0CC', '#EDFF21',
                  '#ED760E', '#FFFF00', '#BFFF00', '#3BB08F', '#FF4D00']
            i = 0
            while(True):
                yield colors[i % len(colors)]
                i += 1

        self.color_gen = get_color()

        self._start()
        self.ax[1].set_ylim([data.min(), data.max()])
        self.connect()

    def connect(self):
        self.canvas.mpl_connect("button_press_event", self.on_click)
        self.canvas.mpl_connect("motion_notify_event", self.on_move)

    def set_data(self, data):
        self.data = data
        self.img.set_data(data)
        self.ax[1].set_ylim([data.min(), data.max()])
        self.curve_v.set_xdata(range(self.data.shape[0]))
        # self.canvas.draw()

    def _start(self):
        color = next(self.color_gen)
        self.vline = self.ax[0].axvline(0, color=color, visible=False)
        a = range(self.data.shape[0])
        self.curve_v = self.ax[1].plot(a, a, color=color, visible=False)[0]
        self.text = self.ax[0].text(0, 10, len(self.curves) + 1, fontsize=15, color=color, visible=False)

    def on_click(self, event):
        if event.inaxes != self.ax[0]: return
        self.vline.set_xdata([event.xdata])
        self.curve_v.set_ydata(self.data[:, round(event.xdata)])
        self.text.set_x(event.xdata)

        for line in [self.vline, self.curve_v, self.text]:
            line.set_animated(False)
        self.backgrounds = None
        self.canvas.draw()

        self.curves.append({'vline': self.vline, 'curve_v': self.curve_v, 'text': self.text})
        self._start()

    def on_move(self, event):
        if event.inaxes != self.ax[0]:
            # За пределами осей скрываем линии
            for line in [self.vline, self.curve_v, self.text]:
                if line.get_visible(): line.set_visible(False)
                if line.get_animated(): line.set_animated(False)
            self.canvas.draw()
            return
        
        if not self.vline.get_visible():
            for line in [self.vline, self.curve_v, self.text]:
                line.set_visible(True)
                line.set_animated(True)
            # self.canvas.draw()
            self.backgrounds = [self.canvas.copy_from_bbox(axi.bbox) for axi in self.ax]

        self.vline.set_xdata([event.xdata])
        self.curve_v.set_ydata(self.data[:, round(event.xdata)])
        self.text.set_x(event.xdata)
        
        [self.canvas.restore_region(back) for back in self.backgrounds]
        self.ax[0].draw_artist(self.vline)
        self.ax[1].draw_artist(self.curve_v)
        self.ax[0].draw_artist(self.text)
        [self.canvas.blit(axi.bbox) for axi in self.ax]

    def disconnect(self):
        self.canvas.mpl_disconnect("button_press_event", self.on_click)
        self.canvas.mpl_disconnect("motion_notify_event", self.on_move)
    

if __name__ == "__main__":
    x = np.linspace(0, np.pi, 100)
    y = np.linspace(0, 10, 200)
    X, Y = np.meshgrid(x, y)
    data = np.sin(X) + np.exp(np.cos(Y))

    fig, ax = plt.subplots(1, 2)
    img = ax[0].imshow(data)
    ax[0].axis('off')
    ds = DataSlice(data=data, ax=ax, img=img)
    plt.show()
