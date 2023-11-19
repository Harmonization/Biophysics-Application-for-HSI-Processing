import numpy as np
from pysptools.util import load_ENVI_file as load_hsi
from scipy.signal import savgol_filter

from .Expressions.parse import Parser

class HSI:
    # Класс для работы с HSI
    RGB_BANDS = (70, 53, 19)

    def __init__(self):
        self._parser = Parser()
    
    def load(self, path='test_data/tobacco.hdr'):
        self.hsi = np.rot90(load_hsi(path)[0], k = 3)

    def calculate_channel(self, string: str | None = None) -> np.ndarray:
        # Вычислить одноканальное изображение из строки
        if string: self.string = string

        self.parser(self.string) # Парсинг мат. выражения
        function = self.parser.function # Функция (рез-т парсинга)

        channels = [self.hsi[:, :, b] for b in self.parser.bands] # Каналы (рез-т парсинга) 
        channel: np.ndarray[float | bool] = function(*channels) # Применение функции к каналам HSI

        if channel.dtype == bool: # Если мат. выражение это условие
            self.mask = channel
        else:
            self.channel = channel

        return self._channel

    def rot(self):
        # Поворот HSI
        self.hsi = np.rot90(self.hsi)
        self.mask_hsi
        self._mask_hsi = np.rot90(self._mask_hsi)
    
    def savgol(self):
        # Применение фильтра Савицкого-Голея для сглаживания спектров
        self.hsi = savgol_filter(self.hsi, window_length=5, polyorder=2, axis=2)
        self._mask_channel = self._channel.copy()
        self._mask_channel[~self._mask] = 0

    @property
    def height(self):
        return self.hsi.shape[0]
    
    @property
    def width(self):
        return self.hsi.shape[1]

    @property
    def mask(self) -> np.ndarray[bool]:
        if not hasattr(self, '_mask'):
            self._mask = np.ones((self.height, self.width), dtype=bool)
            self._mask_channel = self._channel
        return self._mask
    
    @mask.setter
    def mask(self, mask: np.ndarray[bool]):
        self._mask = mask.copy()
        self._mask_channel = self._channel.copy()
        self._mask_channel[~self._mask] = 0
        self._mask_hsi = self.hsi.copy()
        self._mask_hsi[~self._mask, :] = 0

    @property
    def wavelengths(self) -> np.ndarray[int]:
        return self.parser.wave

    @property
    def channel(self) -> np.ndarray[float]:
        return self._channel
    
    @channel.setter
    def channel(self, channel: np.ndarray[float]):
        self._channel = channel.copy()
        self._mask_channel[self.mask] = self._channel[self.mask]
    
    @property
    def mask_channel(self):
        if not hasattr(self, '_mask_channel'):
            self._mask_channel = self._channel.copy()
        return self._mask_channel
    
    @property
    def mask_hsi(self):
        if not hasattr(self, '_mask_hsi'):
            self._mask_hsi = self.hsi.copy()
            self._mask_hsi[~self._mask, :] = 0
        return self._mask_hsi
    
    @property
    def parser(self) -> Parser:
        return self._parser
    
    @property
    def rgb(self) -> np.ndarray[float]:
        return self.hsi[:, :, self.RGB_BANDS]
    
    def mean_sign(self, data: np.ndarray[float] | None = None) -> np.ndarray[float]:
        # Вычислить средний спектр по внутренним или внешним данным
        if data is None: data = self.mask_hsi
        return data.mean(axis=(0, 1))
    
    @staticmethod
    def mean_matrix(spectre: np.ndarray[float]) -> np.ndarray[float]:
        x, y = np.meshgrid(spectre, spectre)
        return np.fromfunction(lambda i, j: (x-y) / (x+y), (204, 204))
    
    def deep_roi(self, x0, y0, x1, y1):
        # Получить срез куба HSI
        return self.mask_hsi[y0:y1, x0:x1]
    

def main():
    hsi = HSI()
    hsi.load()
    channel = hsi.calculate_channel('b70 + b60 / 3')
    print(channel.shape)

if __name__ == '__main__':
    main()