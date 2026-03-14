from .nevermore_plot_sensor import NevermorePlotSensor

class NevermoreTempSensor(NevermorePlotSensor):

    def bind_sensor_update(self):
        if self.sensor_kind == "exhaust":
            self.nevermore.client.on_temp_exhaust_update(self.on_sensor_update)
        else:
            self.nevermore.client.on_temp_intake_update(self.on_sensor_update)