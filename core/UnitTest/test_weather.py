import unittest
import core.weather

class WeatherTest(unittest.TestCase):
    def setUp(self):
        self.app = core.weather.Application(is_test=True)
        self.app.load_sensors()

    def test_hall(self):
        self.assertIn(self.app.is_velux_open(), [True, False])

    def test_in_temp(self):
        self.assertIsNotNone(self.app.get_average_temp())

    def test_out_temp(self):
        self.assertIsNotNone(self.app.get_out_temp())

    def test_in_humidity(self):
        self.assertIsNotNone(self.app.get_humidity())

    def test_out_humidity(self):
        self.assertIsNotNone(self.app.get_out_humidity())

    def test_heater_state(self):
        state = self.app.get_heater_state()
        self.assertIsNotNone(state)
        self.assertIn(state,[0,1])