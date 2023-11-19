import sys
from functools import partial
from collections.abc import Callable

import pandas as pd
from PyQt6 import QtWidgets as QW
from PyQt6.QtGui import QIcon, QAction
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as Toolbar
from mpl_interactions import zoom_factory

from plot import Plot
from Data.Interactive.Medium.Elementary.style import *

class Interface(QW.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HSI Editor")
        self.plot = Plot()
        self.open()

        zoom_factory(self.plot.ax_in)
        self.check_mode(2)

        self.showMaximized()

    def _create_elements(self):
        # Панель инструментов
        self._create_toolbar()

        # Элементы меню
        menu = self.menuBar()
        self._create_menu_file(menu)
        self._create_menu_edit(menu)
        self._create_menu_tools(menu)

        # Сборка интерфейса
        self._build()

    def _create_toolbar(self):
        # Панель инструментов
        self.editToolBar = QW.QToolBar("Панель инструментов", self)
        self.addToolBar(self.editToolBar)

        # Toolbar
        self.toolbar = Toolbar(self.plot.canvas, self)
        self.editToolBar.addWidget(self.toolbar)

        # Input
        self.input = QW.QLineEdit('b170', 
                                  placeholderText='(b70 - b30) / (b70 + b30)', 
                                  styleSheet=INPUT_STYLE)
        
        self.input.returnPressed.connect(self.parse) # self.input.setFocus()
        self.editToolBar.addWidget(self.input)
    
    def _add_menu_item(self, menu: QW.QMenu, title: str, function: Callable[[], None]):
        item = QAction(QIcon('1.png'), f'&{title}', self)
        item.triggered.connect(function)
        menu.addAction(item)

    def _add_menu(self, parent_menu: QW.QMenu, title: str) -> QW.QMenu:
        menu = QW.QMenu(f'&{title}', self)
        parent_menu.addMenu(menu)
        return menu

    def _create_menu_file(self, menu: QW.QMenuBar):
        # File
        file = menu.addMenu('&Файл')
        add_menu_file = partial(self._add_menu_item, menu=file)

        add_menu_file(title='Открыть', function=self.open)
        add_menu_file(title='Сохранить индекс', function=self.save_index)
        add_menu_file(title='Сохранить результаты', function=self.save)

    def _create_menu_edit(self, menu: QW.QMenuBar):
        # Edit
        edit = menu.addMenu('&Редактировать')
        add_edit_item = partial(self._add_menu_item, menu=edit)
        
        add_edit_item(title='RGB', function=self.plot.rgb)
        add_edit_item(title='Повернуть', function=self.plot.rotate)
        add_edit_item(title='Отобразить в 3D', function=self.plot.surface)
        add_edit_item(title='Фильтр Савицкого-Голея', function=self.plot.filter)

    def _create_menu_tools(self, menu: QW.QMenuBar):
        # Tools
        tools = menu.addMenu('&Режимы')
        add_menu_tools = partial(self._add_menu_item, menu=tools)

        def create_hbox():
            hbox = QW.QHBoxLayout()
            hbox.addWidget(self.plot.mode_object.input)
            hbox.addWidget(self.plot.mode_object.slice.input)
            return hbox

        # Modes
        add_menu_tools(title='Спектральный просвет', function=lambda : self.check_mode(2))
        add_menu_tools(title='Средний спектр', function=lambda : self.check_mode(3))
        add_menu_tools(title='Срез данных', function=lambda : self.check_mode(1, create_hbox))

    def check_mode(self, num: int, create_hbox: Callable[[], QW.QHBoxLayout] | None = None):
        # Функция выбора режима под номером num
        # В функции create_hbox создается контейнер с доп элементами
        if self.plot.mode != num:

            if hasattr(self, 'vbox'): # очистка предыдущего режима
                del self.plot.mode
                self.hbox.removeItem(self.vbox)

            if create_hbox is None: # Функция создания контейнера по умолчанию
                def create_hbox():
                    hbox = QW.QHBoxLayout()
                    hbox.addWidget(self.plot.mode_object.input)
                    return hbox

            self.plot.mode = num
            self.vbox = QW.QVBoxLayout()
            hbox = create_hbox()
            self.vbox.addLayout(hbox)
            self.vbox.addWidget(self.plot.sub_canvas)

            self.hbox.addLayout(self.vbox)
        
    def _build(self):
        # Сборка главного виджета
        widget = QW.QWidget(styleSheet='background-color: white')
        hbox = QW.QHBoxLayout()

        hbox.addWidget(self.plot.canvas)

        widget.setLayout(hbox)
        self.setCentralWidget(widget)

        self.hbox = hbox

    def open(self):
        self.path = QW.QFileDialog.getOpenFileName(self, "Open File", '', '*.hdr')[0]

        # Если окно приложения еще не открыто, то выходим
        if not self.path and self.centralWidget() is None: sys.exit()
        if not self.path: return

        self.plot.load_hsi(self.path)
        # self.plot.load_hsi()
        if self.centralWidget() is None:
            self._create_elements()
        self.parse()

    def save_index(self):
        save_path = QW.QFileDialog.getSaveFileName(self, "Save File", f'{self.input.text()}_index', '.xlsx')
        if not save_path[0]: return
        with pd.ExcelWriter(''.join(save_path), engine='openpyxl') as writer:
            pd.DataFrame(self.plot.hsi.channel).to_excel(writer, sheet_name=f'Индекс')

    def save_mode_1(self):
        save_path = QW.QFileDialog.getSaveFileName(self, "Save File", f'{self.input.text()}_mode_1', '.xlsx')
        if not save_path[0]: return
        with pd.ExcelWriter(''.join(save_path), engine='openpyxl') as writer:
            height = self.plot.mode_object.height
            data_roi = {'roi_id': [], 'x0': [], 'y0': [], 'x1': [], 'y1': [], 'area, pix': []}
            data_lines = {'roi_id': [], 'x_abs': [], 'x': []} | {i: [] for i in range(height)}

            rectangles = self.plot.mode_object
            container = rectangles.slice.container
            for i in container:
                rectangle = rectangles[i]

                area = round(rectangles.area(rectangle))
                x0, y0, x1, y1 = rectangles.get_points(rectangle)
                
                data_roi['roi_id'].append(i)
                data_roi['area, pix'].append(area)
                data_roi['x0'].append(x0)
                data_roi['y0'].append(y0)
                data_roi['x1'].append(x1)
                data_roi['y1'].append(y1)

                xlines = rectangles.slice.get_xlines(i) # Координаты линий
                roi = rectangles.get_roi(x0, y0, x1, y1) # Данные под прямоугольником
                
                for x in xlines:
                    data_lines['roi_id'].append(i)
                    data_lines['x'].append(x)
                    data_lines['x_abs'].append(x0 + x)

                    roi_slice = roi[:, x]
                    for k in range(height):
                        data_lines[k].append(roi_slice[k] if k < len(roi_slice) else None)


            pd.DataFrame(data_roi).to_excel(writer, sheet_name='roi')
            pd.DataFrame(data_lines).to_excel(writer, sheet_name='slice')

    def save_mode_3(self):
        save_path = QW.QFileDialog.getSaveFileName(self, "Save File", f'{self.input.text()}_mode_3', '.xlsx')
        if not save_path[0]: return
        with pd.ExcelWriter(''.join(save_path), engine='openpyxl') as writer:
            id = 'roi_id'
            data_roi = {id: [], 'x0': [], 'y0': [], 'x1': [], 'y1': [], 'area, pix': []}
            data_ms = {id: []} | {nm_i: [] for nm_i in self.plot.hsi.wavelengths}

            mean_sign = self.plot.mode_object
            rectangles = mean_sign.rectangles
            for i, rectangle in enumerate(rectangles):
                area = round(mean_sign.area(rectangle))
                x0, y0, x1, y1 = mean_sign.get_points(rectangle)
                
                data_roi[id].append(i)
                data_roi['area, pix'].append(area)
                data_roi['x0'].append(x0)
                data_roi['y0'].append(y0)
                data_roi['x1'].append(x1)
                data_roi['y1'].append(y1)
                
                deep_roi = mean_sign.get_deep_roi(rectangle)
                spectre = mean_sign.get_spectre(deep_roi)
                matrix = mean_sign.get_matrix(spectre)

                data_ms[id].append(i)
                for j, value in enumerate(spectre):
                    data_ms[self.plot.hsi.wavelengths[j]].append(value)
                
                pd.DataFrame(matrix).to_excel(writer, sheet_name=f'matrix_{i}')
                

            pd.DataFrame(data_roi).to_excel(writer, sheet_name='roi')
            pd.DataFrame(data_ms).to_excel(writer, sheet_name='mean_spectre')

    def save_mode_2(self):
        save_path = QW.QFileDialog.getSaveFileName(self, "Save File", f'{self.input.text()}_mode_2', '.xlsx')
        if not save_path[0]: return
        with pd.ExcelWriter(''.join(save_path), engine='openpyxl') as writer:
            data = {'x': [], 'y': []} | {nm_i: [] for nm_i in self.plot.hsi.wavelengths}
            
            flex_lumen = self.plot.mode_object
            points = flex_lumen.points
            for point in points:
                x, y = flex_lumen.get_xy(point)
                lumen = flex_lumen.get_lumen(x, y)
                
                data['x'].append(x)
                data['y'].append(y)
                for i, nm_i in enumerate(self.plot.hsi.wavelengths):
                    data[nm_i] = lumen[i]

            pd.DataFrame(data).to_excel(writer, sheet_name='spectre')

    def save(self):
        match self.plot.mode:
            case 1:
                self.save_mode_1()
            case 2:
                self.save_mode_2()
            case 3:
                self.save_mode_3()

    def parse(self):
        expression = self.input.text()
        self.plot.redraw(expression)

        
def main():
    app = QW.QApplication([])
    application = Interface()
    application.show()
 
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
        

