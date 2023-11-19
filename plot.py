import numpy as np, matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from matplotlib.image import AxesImage
import plotly.graph_objs as go

from Data.hsi import HSI
from Data.mean_sign import MeanSign

from Data.Interactive.lim_slice import LimSlice
from Data.Interactive.flex_lumen import FlexLumen

from Data.Interactive.Medium.Elementary.style import CMAP

class Plot:
    # Графики matplotlib

    def __init__(self):
        self.create_axes()
        self._mode = 0
        self.hsi = HSI()

    def create_axes(self):
        self.fig, self.ax_in = plt.subplots()
        self.fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        self.axes_in.axis('off')

        # Canvas
        self._canvas = Canvas(self.fig)
        self._canvas.setFixedWidth(550)

    @property
    def axes_in(self) -> plt.Axes:
        return self.ax_in

    ########################################

    @property
    def channel(self) -> AxesImage:
        return self._channel
    
    @channel.setter
    def channel(self, img: np.ndarray[float]):
        if not hasattr(self, '_channel'):
            self._channel = self.axes_in.imshow(img, cmap=CMAP)

            # ColorBar
            divider = make_axes_locatable(self.ax_in)
            cax = divider.append_axes('bottom', size='5%', pad=.025)
            self.cb = self.fig.colorbar(self.channel, cax=cax, orientation='horizontal')
        else:
            self.channel.set_data(img)
        
        self.channel.set_clim(*np.percentile(img, (1, 99)))
        self.axes_in.set_title(f'${self.hsi.parser.latex_nm}$')

    def draw(self, img: np.ndarray | None = None):
        self.channel = self.hsi.mask_channel if img is None else img
        self.draw_in()

    def draw_in(self):
        self.canvas.draw()

    def load_hsi(self, path: str = None):
        if path is None: self.hsi.load()
        else: self.hsi.load(path)        

    def redraw(self, expression: str | None = None):
        self.hsi.calculate_channel(expression)
        self.draw()

    ########################################

    def rotate(self):
        self.hsi.rot()
        self.redraw()

    def filter(self):
        self.hsi.savgol()
        self.redraw()

    def rgb(self):
        Plot.imshow(self.hsi.rgb)
    
    def surface(self, img: np.ndarray | None = None):
        if not img: img = self.hsi.channel
        fig_3d = go.Figure()
        fig_3d.add_trace(go.Surface(z=img))
        fig_3d.update_layout(
            width=700, height=600, autosize=False, 
            margin=dict(t=0, b=0, l=0, r=0), 
            template="plotly_white",
            updatemenus=[
                dict(
                    type = "buttons",
                    direction = "left",
                    buttons=list([
                        dict(
                            args=["type", "surface"],
                            label="3D Surface",
                            method="restyle"
                        ),
                        dict(
                            args=["type", "heatmap"],
                            label="Heatmap",
                            method="restyle"
                        )
                    ]),
                    pad={"r": 10, "t": 10, 'l': 10},
                    showactive=True,
                    x=0.11,
                    xanchor="left",
                    y=1.1,
                    yanchor="top"
                ),
            ],
            # annotations=[
            #     dict(text="Trace type:", showarrow=False,
            #                         x=0, y=1.08, yref="paper", align="left")
            # ]
        )

        fig_3d.show()

    ########################################

    @property
    def mode(self):
        return self._mode
    
    @mode.setter
    def mode(self, mode: int):
        match mode:
            case 1:
                # rectangles and slices
                self.mode_object = LimSlice(self.ax_in)

            case 2:
                # lumen
                self.mode_object = FlexLumen(self.hsi.hsi, self.ax_in)

            case 3:
                # mean_sign
                self.mode_object = MeanSign(self.hsi, self.ax_in)

            case _:
                return
        
        self.mode_object.fig_out.subplots_adjust(left=.1, right=.97, bottom=.05, top=.97)
        self.canvas_out = Canvas(self.mode_object.fig_out)
        self._mode = mode
            
    @mode.deleter
    def mode(self):
        if not self.mode: return
        self.mode_object.takedown()
        self.mode_object = None
        self.canvas_out.deleteLater()
        self._mode = 0
    
    ########################################

    @staticmethod
    def imshow(img: np.ndarray):
        fig, ax = plt.subplots()
        ax.imshow(img)
        ax.axis('off')
        fig.show()
    
    @staticmethod
    def lineplot(x: np.ndarray, y: np.ndarray, label: str):
        fig, ax = plt.subplots()
        ax.plot(x, y, label=label, c='b')
        fig.show()

    @property
    def canvas(self):
        return self._canvas
    
    @property
    def sub_canvas(self):
        return self.canvas_out

    # def recreate(self):
    #     del self.mode


def main():
    hsi = HSI()
    hsi.load()
    channel = hsi.calculate_channel('b70 + b60 / 3')
    
    plot = Plot()
    plot.imshow(channel)
    plt.show()

if __name__ == '__main__':
    main()