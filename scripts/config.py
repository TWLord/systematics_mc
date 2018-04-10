import copy

class Config(object):
    def __init__(self):
        self.run_number = 10052
        self.n_jobs = 3
        self.simulation_geometry = {
            "tracker":"tku",
            "tilt":{"x":0., "y":0., "z":0.},
            "position":{"x":0., "y":0., "z":0.},
            "magnitude":{"End2":1., "End1":1., "Centre":1.},
            "density":{2.0}, #g/cm^3
        }
        self.reconstruction_geometry = copy.deepcopy(self.simulation_geometry)
        self.beam_input_file = "beams/"+str(self.run_number)+"/tku_5.json"
        self.beam_format = "icool_for003"
        self.n_events = 99
        self.config_in = "config_"+str(self.run_number)+".in"
        self.job_name = "normal"
