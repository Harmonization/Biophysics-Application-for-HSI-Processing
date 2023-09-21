from PyQt6 import QtWidgets as QW
from PyQt6.QtGui import QIcon, QAction
import sys, re

import numpy as np, pandas as pd
from pysptools.util import load_ENVI_file as load_hsi
import matplotlib.pyplot as plt
from matplotlib import rc
from matplotlib.image import AxesImage
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas, NavigationToolbar2QT as Toolbar
from mpl_toolkits.axes_grid1 import make_axes_locatable
import plotly.graph_objs as go

from sympy import lambdify, symbols
from sympy.parsing.sympy_parser import parse_expr
from sympy.printing.latex import LatexPrinter

from Components.rects_draw import RectanglesDraw
from Components.data_slice import DataSlice
wave = np.around(np.load('Components/wave.npy')).astype(int)
RGB_BANDS = (70, 53, 19)
rc('font', size=11)
BACK_COLOR = '#E0FFFF'


class AppWindow(QW.QMainWindow):
    latex_printer = LatexPrinter()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Индексы и каналы HSI")

        # Элементы графиков
        self.fig, self.ax = plt.subplots()
        self.fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        self.ax.axis('off')
        self.img = self.ax.imshow(np.full((512, 512), 0))

        # ColorBar
        divider = make_axes_locatable(self.ax)
        cax = divider.append_axes('bottom', size='5%', pad=.025)
        self.cb = self.fig.colorbar(self.img, cax=cax, orientation='horizontal')

        self.canvas = Canvas(self.fig)
        self.canvas.setFixedWidth(550)

        self.stack_plots = QW.QStackedWidget() # Страницы с графиками
        self.stack_plots.addWidget(QW.QLabel(''))
        # self.stack_plots.setFixedWidth(350) # for test

        # Элементы меню
        menu = self.menuBar()
        file = menu.addMenu('&Файл')
        edit = menu.addMenu('&Редактировать')
        tools = menu.addMenu('&Инструменты')
        
        # File
        open = QAction(QIcon('1.png'), '&Открыть', self)
        open.setStatusTip('Create a new document')
        open.triggered.connect(self.open_hsi)
        file.addAction(open)

        self.save = QAction(QIcon('1.png'), '&Сохранить', self, visible=False)
        self.save.triggered.connect(self.save_xlsx)
        file.addAction(self.save)

        # Edit
        self.surface = QAction(QIcon('1.png'), '&Отобразить в 3D', self, visible=False)
        self.surface.triggered.connect(self.surface_3d)
        edit.addAction(self.surface)

        rotate = QAction(QIcon('1.png'), '&Повернуть', self)
        rotate.triggered.connect(self.rotate)
        edit.addAction(rotate)

        # Tools
        self.check_rect = QAction(QIcon('1.png'), '&Прямоугольники', self, checkable=True, visible=False)
        self.check_rect.triggered.connect(lambda _: self.rd.connect() if self.check_rect.isChecked() else self.rd.disconnect())
        tools.addAction(self.check_rect)

        self.pages = QW.QMenu('&Страницы', self)
        tools.addMenu(self.pages)
        
        # Pages (into Tools)
        self.clear = QAction(QIcon('1.png'), '&Очистить', self, visible=False)
        self.clear.triggered.connect(self.clear_plots)
        # self.pages.addAction(self.clear)

        # Панель инструментов
        self.editToolBar = QW.QToolBar("Панель инструментов", self)
        self.addToolBar(self.editToolBar)
        
        self.input = QW.QLineEdit('', placeholderText='(b70 - b30) / (b70 + b30)', 
                                  styleSheet=f'background-color: {BACK_COLOR}; color: black;')
        
        toolbar = Toolbar(self.canvas, self)
        self.editToolBar.addWidget(toolbar)

        self.input.returnPressed.connect(self.parse_string) # self.input.setFocus()
        self.editToolBar.addWidget(self.input)

        self.rd = RectanglesDraw(self.ax)
        self.open_hsi()

        # Сборка интерфейса
        widget = QW.QWidget(styleSheet='background-color: white')
        hbox = QW.QHBoxLayout()
        hbox.addWidget(self.canvas)
        hbox.addWidget(self.stack_plots)

        widget.setLayout(hbox)

        self.setCentralWidget(widget)

        self.showMaximized()

    def parse_string(self):
        try:
            expr = parse_expr(string := self.input.text())
            lets = symbols(list(set(re.findall(r'[a-zA-Zа-яА-Я]+\d+', string))), integer=True, positive=True) # переменные

            def transform_string(string):
                el = string.group(0)
                return f"{re.search(r'[a-zA-Zа-яА-Я]+', el)[0]}{wave[int(re.search(r'[0-9]+', el)[0])]}"

            string_nm = re.sub(r'[a-zA-Zа-яА-Я]+\d+', transform_string, string)
            self.expr_nm = parse_expr(string_nm)
            f = lambdify(lets, expr)

            latex_expr = self.latex_printer.doprint(self.expr_nm) # Визуализация формулы
            self.ax.set_title(f'${latex_expr}$')

            if not self.cb.ax.get_visible():
                self.cb.ax.set_visible(True)
                
            if not self.save.isVisible():
                for el in [self.save, self.surface, self.check_rect, self.clear]:
                    el.setVisible(True)

            bands = [int(re.search(r'\d+', str(let))[0]) for let in lets] # номера каналов
            self.channel = f(*[self.hsi[:, :, b] for b in bands])
            self.img.set_data(self.channel)

            self.img.set_clim(*np.percentile(self.channel, (1, 99)))
            # img_r.set_clim(img.get_clim())
            self.canvas.draw()

        except Exception as ex:
            print(ex)
            QW.QMessageBox(windowTitle='Ошибка', text='Некорректное значение', icon=QW.QMessageBox.Icon.Warning).exec()

    def clear_plots(self):
        # Очистка QStackedWidget от графиков, QMenu от страниц и удаление прямоугольников
        for _ in range(self.stack_plots.count() - 1):
            self.stack_plots.removeWidget(self.stack_plots.widget(1))
            
        self.pages.clear()
        self.pages.addAction(self.clear)

        self.rectangles = []
        self.rd.clear()

    def surface_3d(self):
        fig_3d = go.Figure()
        fig_3d.add_trace(go.Surface(z=self.channel))
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

    def rotate(self):
        self.channel = np.rot90(self.channel)
        self.img.set_data(self.channel)
        self.hsi = np.rot90(self.hsi)
        self.canvas.draw()

    def save_xlsx(self):
        save_path = QW.QFileDialog.getSaveFileName(self, "Save File", f'({self.expr_nm})', '.xlsx')
        # if save_path[0]: 
        #     pd.DataFrame(self.channel).to_excel(''.join(save_path))
        if not save_path[0]: return
        with pd.ExcelWriter(''.join(save_path), engine='openpyxl') as writer:
            pd.DataFrame(self.channel).to_excel(writer, sheet_name=f'Индекс')

            for i, el in enumerate(self.rectangles):
                slice = el['slice']
                data = slice.data
                pd.DataFrame(data).to_excel(writer, sheet_name=f'Область {i+1}')
                
                curves_data = np.array([list(curve['curve_v'].get_ydata()) for curve in slice.curves]).T
                pd.DataFrame(curves_data, columns=[f'Кривая {j}' for j in range(1, len(slice.curves) + 1)]).to_excel(writer, 
                                                                                                                    sheet_name=f'Кривые {i+1}')

    def open_hsi(self):
        self.path, _ = QW.QFileDialog.getOpenFileName(self, "Open File", '', '*.hdr')
        # self.path = 'test_data/tobacco.hdr' # for test
        if self.path:
            self.hsi = np.rot90(load_hsi(self.path)[0], k = 3)
            self.channel = self.hsi[:, :, RGB_BANDS]
            self.img.set_data(self.channel)
            self.cb.ax.set_visible(False)
            self.clear_plots()

            def change_page():
                # При смене страницы в меню меняется страница с графиком
                self.rd.rect_indx = int(self.pages.sender().text()[1:]) # текущий нажатый номер страницы
                self.stack_plots.setCurrentIndex(self.rd.rect_indx)

            def create_plot():
                fig, ax = plt.subplots(2)
                fig.subplots_adjust(left=.1, right=.97, bottom=.05, top=.97)
                img = ax[0].imshow(self.channel)
                self.stack_plots.addWidget(canvas := Canvas(fig))

                self.stack_plots.setCurrentIndex(self.rd.rect_indx + 1)

                page = QAction(QIcon('1.png'), f'&{self.rd.rect_indx + 1}', self)
                page.triggered.connect(change_page)
                self.pages.addAction(page)

                self.rectangles.append({'figure': (ax, img, canvas)})
            
            def move_rect(event):
                if not self.check_rect.isChecked() or event.button not in (1, 3): return
                
                def set_data():
                    ax_r, img_r, canvas_r = self.rectangles[self.rd.rect_indx]['figure']
                    x, y, w, h = np.around([*self.rd.rect.xy, self.rd.rect.get_width(), self.rd.rect.get_height()]).astype(int)                            
                    h0, h1 = (y, y+h) if h > 0 else (y+h, y)
                    w0, w1 = (x, x+w) if w > 0 else (x+w, x)
                    self.data = self.channel[h0:h1, w0:w1]
                    img_r.set_data(self.data)
                    return ax_r, img_r, canvas_r

                match event.button:
                    case 1:
                        if self.rd.press_flag:
                            create_plot()

                        ax_r, img_r, canvas_r = set_data()

                        if (extent := AxesImage(ax_r[0], data=self.data).get_extent()) != (-.5,)*4: 
                            # Обход предупреждения возникающего при малых размерах выделяемого прямоугольника
                            img_r.set_extent(extent) # которое так или иначе возникает в начале выделения

                    case 3:
                        if not self.rd.rect: return
                        ax_r, img_r, canvas_r = set_data()
                        self.stack_plots.setCurrentIndex(self.rd.rect_indx + 1)

                canvas_r.draw()

            def release_rect(event):
                if not self.check_rect.isChecked() or event.button not in (1, 3): return
                ax_r, img_r, canvas_r = self.rectangles[self.rd.rect_indx]['figure']
                img_r.set_data(self.data)
                match event.button:
                    case 1:
                        img_r.set_extent(AxesImage(ax_r[0], data=self.data).get_extent())
                        self.rectangles[self.rd.rect_indx] |= {'rectangle': self.rd.rectangles[self.rd.rect_indx], 
                                                               'slice': DataSlice(self.data.copy(), ax=ax_r, img=img_r)}
                    case 3:
                        self.rectangles[self.rd.rect_indx]['slice'].set_data(self.data)
                canvas_r.draw()
                        
            self.canvas.mpl_connect('motion_notify_event', move_rect)
            self.canvas.mpl_connect('button_release_event', release_rect)

        elif self.centralWidget() is None:
            sys.exit() # Если окно приложения еще не открыто, то выходим


if __name__ == "__main__":
    app = QW.QApplication([])
    application = AppWindow()
    application.show()
 
    sys.exit(app.exec())