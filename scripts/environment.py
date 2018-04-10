import os
import sys
import copy
import time
import shutil

import xboa.common

import murgle_geometry
import smear_and_sample

class Environment(object):
    def __init__(self, config):
        self.config = config
        self.run_number = config.run_number
        self.n_jobs = config.n_jobs
        self.simulation_geometry = config.simulation_geometry
        self.reconstruction_geometry = config.reconstruction_geometry
        self.beam_input_file = config.beam_input_file
        self.beam_format = config.beam_format
        self.n_events = config.n_events
        self.config_in = config.config_in
        self.job_name = config.job_name

        self.iteration_number = 1


    def setup_environment(self):
        self.make_dirs()
        self.make_simulation_geometry()
        self.make_reconstruction_geometry()
        self.make_beams()
        self.make_config("simulation")
        self.make_config("reconstruction")
        # note that because of the way geometry works, we have to make links
        # at run time for each geometry (geometry_xxxxx/<filename> is hardcoded
        # into the geometry)

    def get_geometry_filename(self):
        filename = "geometry_"+str(self.run_number)+"/ParentGeometryFile.dat"
        return filename

    def get_output_geometry_filename(self, prefix):
        geometry = os.path.split(self.get_geometry_filename())[0]
        return self.get_dir_root()+'/'+prefix+'_'+geometry

    def copy_geometry(self, prefix):
        geometry = os.path.split(self.get_geometry_filename())[0]
        target = self.get_output_geometry_filename(prefix)
        shutil.copytree(geometry, target)

    def make_simulation_geometry(self):
        self.copy_geometry("simulation")
        murgler = murgle_geometry.GeometryMurgler(self.simulation_geometry,
                                                  self.get_output_geometry_filename("simulation"),
                                                  "geometry_"+str(self.run_number))
        murgler.murgle()
                                                  
    def make_reconstruction_geometry(self):
        self.copy_geometry("reconstruction")
        murgler = murgle_geometry.GeometryMurgler(self.simulation_geometry,
                                                  self.get_output_geometry_filename("reconstruction"),
                                                  "geometry_"+str(self.run_number))
        murgler.murgle()

    def get_beam_filename(self, index):
        return self.get_dir_name(index)+"/for003.dat"

    def make_beams(self):
        smear = smear_and_sample.SmearAndSample(self.beam_input_file, "", self.beam_format, self.n_events)
        for i in range(self.n_jobs):
            filename = self.get_beam_filename(i)
            smear.write(i, filename)

    def get_config(self, index, prefix):
        return self.get_dir_name(index)+"/"+prefix+"_config.py"

    def make_config(self, prefix):
        for index in range(self.n_jobs):
            subs = {
                "__geometry_filename__":self.get_geometry_filename(),
                "__run__":str(self.run_number),
                "__seed__":str(index),
                "__beam_filename__":os.path.split(self.get_beam_filename(index))[1],
                "__beam_format__":self.beam_format,
                "__n_spills__":self.n_events/100+1,
                "__output_filename__":"maus_"+prefix+".root",
            }
            xboa.common.substitute(self.config_in, self.get_config(index, prefix), subs)

    def get_dir_root(self):
        return str(self.run_number)+"_systematics_v"+str(self.iteration_number)+"/"+self.job_name+"/"

    def get_dir_name(self, job_id):
        return self.get_dir_root()+"/"+str(job_id)

    def make_dirs(self):
        while os.path.exists(self.get_dir_root()):
            self.iteration_number += 1
        print "Setting up dirs with name", self.get_dir_root()
        for i in range(self.n_jobs):
            os.makedirs(self.get_dir_name(i))
            print i,
            sys.stdout.flush()
        pause = 1
        print "\nPause for", pause, "seconds to give OS a chance to finish"
        for i in range(pause):
            time.sleep(1)
            print i+1,
            sys.stdout.flush()
        print
