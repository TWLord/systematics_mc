import math
import environment
import run
import config
import copy
import glob

def do_one(config):
    my_env = environment.Environment(config)
    my_env.setup_environment()
    my_run = run.Run(my_env)
    my_run.prefix = "simulation"
    my_run.run_many()
    my_run.prefix = "reconstruction"
    my_run.run_many()

def get_iteration():
    key = '_systematics_v'
    valid_folders = glob.glob('*'+key+'*')
    iteration_number = 1
    for folder in valid_folders:
        index = folder.find(key)+len(key)
        iteration_number = max(iteration_number, int(folder[index:]))
    return iteration_number+1


def main():
    ten_mrad = math.degrees(0.01)
    iteration = get_iteration()
    print "Running systematics mc iteration", iteration
    for run in [10051, 10052, 10069]:
        my_config = config.build_config(run, "tku", "base", iteration)
        do_one(my_config)
        for tracker in ["tku", "tkd"]:
              position = {"x":1., "y":0., "z":0.}
              my_config = config.build_config(run, tracker, "pos_plus", iteration, position = position)
              do_one(my_config)
              #position = {"x":-1., "y":0., "z":0.}
              #my_config = config.build_config(run, tracker, "pos_minus", iteration, position = position)
              #do_one(my_config)
              rotation = {"x":ten_mrad, "y":0., "z":0.}
              my_config = config.build_config(run, tracker, "rot_plus", iteration, rotation = rotation)
              do_one(my_config)
              #rotation = {"x":-ten_mrad, "y":0., "z":0.}
              #my_config = config.build_config(run, tracker, "rot_minus", iteration, rotation = rotation)
              #do_one(my_config)
              base_scale = {"E2":1., "E1":1., "C":1.}
              for key in base_scale.keys():
                  scale = copy.deepcopy(base_scale)
                  scale[key] = 1.05
                  name = "scale_"+key+"_plus"
                  my_config = config.build_config(run, tracker, name, iteration, currents = scale)
                  do_one(my_config)
                  #scale[key] = 0.95
                  #name = "scale_"+key+"_minus"
                  #my_config = config.build_config(run, tracker, name, iteration, currents = scale)
                  #do_one(my_config)
              my_config = config.build_config(run, tracker, "density_plus", iteration, density = 2.5)
              do_one(my_config)
              #my_config = config.build_config(run, tracker, "density_minus", iteration, density = 1.5)
              #do_one(my_config)


if __name__ == "__main__":
    main()
