import environment
import run
import config

def do_one(config):
    my_env = environment.Environment(config)
    my_env.setup_environment()

    my_run = run.Run(my_env, 2)
    my_run.prefix = "simulation"
    my_run.run_many()
    my_run.prefix = "reconstruction"
    my_run.run_many()


def main():
    my_config = config.Config()
    do_one(my_config)
    return

    vary_field_magnitude()
    do_simulation()
    put_back_defaults()
    do_reconstruction() # this is field magnitude systematic

    vary_field_tilt()
    do_simulation()
    put_back_defaults()
    do_reconstruction() # this is field tilt systematic

    vary_material_budget()
    do_simulation()
    put_back_defaults()
    do_reconstruction() # this is material budget


if __name__ == "__main__":
    main()
