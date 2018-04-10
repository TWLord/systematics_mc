import json
import copy

class Config(object):
    def __init__(self):
        self.run_number = 10052
        self.n_jobs = 3
        self.simulation_geometry = {
            "tracker":"tku",
            "position":{"x":0., "y":0., "z":0.},
            "rotation":{"x":0., "y":0., "z":0.},
            "scale":{"E2":1., "E1":1., "C":1.},
            "density":2.0, #g/cm^3
        }
        self.reconstruction_geometry = copy.deepcopy(self.simulation_geometry)
        self.beam_input_file = "beams/"+str(self.run_number)+"/tku_5.json"
        self.beam_format = "icool_for003"
        self.n_events = 999
        self.config_in = "config_"+str(self.run_number)+".in"
        self.job_name = "normal"

def build_config(run_number, tracker, job_name, position = None, rotation = None, density = None, currents = None):
    config = Config()
    config.run_number = run_number
    config.job_name = job_name
    if position == None:
        position = {"x":0., "y":0., "z":0.}
    if rotation == None:
        rotation = {"x":0., "y":0., "z":0.}
    if density == None:
        density = 2.0
    if currents == None:
        currents = {"E2":1., "E1":1., "C":1.}
    config.simulation_geometry["tracker"] = tracker
    config.simulation_geometry["position"] = position
    config.simulation_geometry["rotation"] = rotation
    config.simulation_geometry["density"] = density
    config.simulation_geometry["scale"] = currents
    print "Building config", job_name
    print json.dumps(config.simulation_geometry, indent = 2)
    return config