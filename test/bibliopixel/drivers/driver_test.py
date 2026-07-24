import unittest

from bibliopixel.colors import gamma
from bibliopixel.drivers.driver_base import DriverBase, ChannelOrder
from bibliopixel.drivers.SPI import SPI, SPI_INTERFACES
from bibliopixel.drivers.ledtype import LEDTYPE
from bibliopixel.project import data_maker


class DriverTest(unittest.TestCase):
    COLORS = [(0, 0, 0),
              (1, 8, 64),
              (2, 16, 128),
              (3, 24, 192)]

    SPD = dict(interface=SPI_INTERFACES.DUMMY)

    def do_test(self, driver, expected):
        driver.set_colors(self.COLORS, 0)
        driver._render()
        self.assertEqual(list(driver._buf), expected)

    def test_trivial(self):
        driver = DriverBase(num=4)
        for i in range(len(driver._buf)):
            driver._buf[i] = 23  # randomize
        self.assertTrue(all(driver._buf))
        driver.set_colors([(0, 0, 0)] * 4, 0)
        driver._render()
        self.assertFalse(any(driver._buf))  # It wrote zeroes!

    def test_simple(self):
        driver = DriverBase(num=4)
        expected = [0, 0, 0, 1, 8, 64, 2, 16, 128, 3, 24, 192]
        self.do_test(driver, expected)

    def test_permute(self):
        driver = DriverBase(num=4, c_order=ChannelOrder.GRB)
        expected = [0, 0, 0, 8, 1, 64, 16, 2, 128, 24, 3, 192]
        self.do_test(driver, expected)

    def test_permute2(self):
        driver = DriverBase(num=4, c_order=ChannelOrder.BRG)
        expected = [0, 0, 0, 64, 1, 8, 128, 2, 16, 192, 3, 24]
        self.do_test(driver, expected)

    def test_gamma1(self):
        driver = DriverBase(num=4, gamma=gamma.LPD8806)
        expected = [128, 128, 128, 128, 128, 132, 128, 128, 151, 128, 128, 190]
        self.do_test(driver, expected)

    def test_apa102(self):
        driver = SPI(ledtype=LEDTYPE.APA102, num=4, **self.SPD)
        expected = [0, 0, 0, 0, 0, 8, 0, 0, 46, 0, 1, 125]
        self.do_test(driver, expected)

    def test_lpd8806(self):
        driver = SPI(ledtype=LEDTYPE.LPD8806, num=4, **self.SPD)
        expected = [
            128, 128, 128, 128, 128, 132, 128, 128, 151, 128, 128, 190, 0]
        self.do_test(driver, expected)

    def test_ws2801(self):
        driver = SPI(ledtype=LEDTYPE.WS2801, num=4, **self.SPD)
        expected = [0, 0, 0, 0, 0, 8, 0, 0, 45, 0, 0, 125]
        self.do_test(driver, expected)


class NumpyDriverTest(DriverTest):
    """Run every DriverTest case again over a numpy-backed color list.

    `DriverBase._render` takes a separate numpy code path, which needs to
    produce the same bytes as the plain-list path it accelerates.
    """
    DTYPE = 'float32'

    def do_test(self, driver, expected):
        color_list = data_maker.Maker(numpy_dtype=self.DTYPE).color_list(
            len(self.COLORS))
        for i, color in enumerate(self.COLORS):
            color_list[i] = color

        driver.set_colors(color_list, 0)
        driver._render()
        self.assertEqual(list(driver._buf), expected)

    def test_trivial(self):
        pass  # Assigns a plain list, so it does not exercise the numpy path.

    def test_brightness_does_not_consume_colors(self):
        # Rendering applies brightness to the output, not to the stored
        # colors, so repeated renders of one frame stay identical.
        driver = DriverBase(num=4)
        color_list = data_maker.Maker(numpy_dtype=self.DTYPE).color_list(4)
        for i, color in enumerate(self.COLORS):
            color_list[i] = color

        driver.set_colors(color_list, 0)
        driver._brightness = 128

        driver._render()
        first = list(driver._buf)
        driver._render()
        self.assertEqual(list(driver._buf), first)
        self.assertEqual(list(color_list[3]), list(self.COLORS[3]))


class Uint8NumpyDriverTest(NumpyDriverTest):
    DTYPE = 'uint8'


class Int8NumpyDriverTest(NumpyDriverTest):
    DTYPE = 'int8'

    def test_brightness_does_not_consume_colors(self):
        pass  # int8 cannot round-trip the color values used above.
