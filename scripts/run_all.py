import math
import environment
import run
import config
import copy

def do_one(config):
    my_env = environment.Environment(config)
    my_env.setup_environment()
    my_run = run.Run(my_env, 2)
    my_run.prefix = "simulation"
    my_run.run_many()
    my_run.prefix = "reconstruction"
    my_run.run_many()


def main():
    ten_mrad = math.degrees(0.01)
    for run in [10052]:
        my_config = config.build_config(run, "tku", "base")
        for tracker in ["tku"]:
              position = {"x":1., "y":0., "z":0.}
              my_config = config.build_config(run, tracker, "pos_plus", position = position)
              do_one(my_config)
              position = {"x":-1., "y":0., "z":0.}
              my_config = config.build_config(run, tracker, "pos_minus", position = position)
              do_one(my_config)
              rotation = {"x":ten_mrad, "y":0., "z":0.}
              my_config = config.build_config(run, tracker, "rot_plus", rotation = rotation)
              do_one(my_config)
              rotation = {"x":-ten_mrad, "y":0., "z":0.}
              my_config = config.build_config(run, tracker, "rot_minus", rotation = rotation)
              do_one(my_config)
              base_scale = {"E2":1., "E1":1., "C":1.}
              for key in base_scale.keys():
                  scale = copy.deepcopy(base_scale)
                  scale[key] = 1.05
                  name = "scale_"+key+"_plus"
                  my_config = config.build_config(run, tracker, name, currents = scale)
                  do_one(my_config)
                  scale[key] = 0.95
                  name = "scale_"+key+"_minus"
                  my_config = config.build_config(run, tracker, name, currents = scale)
                  do_one(my_config)
              my_config = config.build_config(run, tracker, "density_plus", density = 2.5)
              do_one(my_config)
              my_config = config.build_config(run, tracker, "density_minus", density = 1.5)
              do_one(my_config)


if __name__ == "__main__":
    main()
