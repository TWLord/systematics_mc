import sys
import json
import bisect

import numpy
import numpy.random
import scipy.stats

from xboa.hit import Hit
from xboa.bunch import Bunch
import xboa.common

import ROOT
import libMausCpp
import maus_cpp.converter

"""
Generate a beam from input json file, using smear and sample technique

This replaces the MapPyBeamMaker AND MapCppMCReconSetup because we have to build
TOF hits as well.

The mc event is generated by forming a kde distribution from the input events and
resampling.

The TOF0/TOF1 hits are generated by a lookup from 2d distributions in (p, tof) space
assuming a gaussian distribution
"""

class MapPySmearAndSample(object):
    def __init__(self):#, input_file, output_file, fmt, n_events):
        self.fin = None #open(input_file)
        self.n_events_per_spill = 0 #n_events
        self.n_momentum_slices = 1 #n_events
        self.momentum_min = 0.
        self.momentum_max = 0.
        self.momentum_bin_lower = []
        self.z_position = 0.
        self.tof0_offset = 0.
        self.tof1_offset = 0.
        self.metadata = None
        self.random_seed = 0
 
    def birth(self, config_str): #pylint: disable=W0613, R0201
        """
        Just returns true
        """
        config_json = json.loads(config_str)
        if "smear_and_sample" not in config_json.keys():
            raise KeyError("No smear and sample data set for MapPySmearAndSample")
        config_json = config_json["smear_and_sample"]
        self.n_events_per_spill = config_json["n_events_per_spill"]
        self.fin = open(config_json["input_file"])
        self.n_momentum_slices = config_json["n_momentum_slices"]
        self.tof0_offset = config_json["tof0_offset"]
        self.tof1_offset = config_json["tof1_offset"]
        self.momentum_min = config_json["momentum_min"]
        self.momentum_max = config_json["momentum_max"]
        self.random_seed = config_json["seed"]
        self.z_position = config_json["z_position"]
        self.momentum_step = (self.momentum_max-self.momentum_min)/float(self.n_momentum_slices)
        self.momentum_bin_lower = [self.momentum_min+i*self.momentum_step for i in range(self.n_momentum_slices)]
        print self.momentum_bin_lower
        self.build_kernel()
        return True

    def death(self):
        return True

    def process(self, data):
        print "MAP PY SMEAR AND SAMPLE PROCESSING EVENT"
        data = maus_cpp.converter.data_repr(data)
        spill = data.GetSpill()
        spill.SetDaqEventType("physics_event")
        spill = data.GetSpill()
        if not spill.GetReconEvents():
            reco_events = ROOT.MAUS.ReconEventPArray()
            spill.SetReconEvents(reco_events)

        if not spill.GetMCEvents():
            mc_events = ROOT.MAUS.MCEventPArray()
            spill.SetMCEvents(mc_events)

        psv_list = self.generate_psv_list()
        for i, psv in enumerate(psv_list):
            mc_event = self.generate_mc_event(i, psv)
            reco_event = self.generate_reco_event(i, psv)
            spill.GetReconEvents().push_back(reco_event)
            spill.GetMCEvents().push_back(mc_event)
        #data = maus_cpp.converter.json_repr(data)
        #print >> self.fout, json.dumps(data, indent=1)
        return data

    def generate_psv_list(self):
        psv_list = []
        while len(psv_list) < self.n_events_per_spill:
            n_events = self.n_events_per_spill - len(psv_list)
            new_psv_list = self.psv_kernel.resample(n_events).transpose()
            new_psv_list = [psv for psv in new_psv_list \
                   if psv[4] > self.momentum_min and psv[4] <= self.momentum_max]
            psv_list += new_psv_list
        return psv_list

    def generate_mc_event(self, ev_number, psv):
        mc_event = ROOT.MAUS.MCEvent()
        primary = ROOT.MAUS.Primary()
        primary.SetRandomSeed(self.random_seed)
        self.random_seed += 1
        primary.SetParticleId(-13)
        primary.SetTime(0)
        position = ROOT.MAUS.ThreeVector(psv[0], psv[2], self.z_position)
        primary.SetPosition(position)
        momentum = ROOT.MAUS.ThreeVector(psv[1], psv[3], psv[4])
        primary.SetMomentum(momentum)
        mass_sq = xboa.common.pdg_pid_to_mass[13]**2
        primary.SetEnergy((momentum.Mag2()+mass_sq)**0.5)
        mc_event.SetPrimary(primary)
        return mc_event

    def generate_reco_event(self, ev_number, psv):
        pz = psv[4]
        tof0_sp = self.sample_distribution(pz, self.tof0_dist, self.tof0_offset)
        tof1_sp = self.sample_distribution(pz, self.tof1_dist, self.tof1_offset)
        tof0_sp_array = ROOT.MAUS.TOF0SpacePointArray()
        tof0_sp_array.push_back(tof0_sp)
        tof1_sp_array = ROOT.MAUS.TOF1SpacePointArray()
        tof1_sp_array.push_back(tof1_sp)
        tof_sp_collection = ROOT.MAUS.TOFEventSpacePoint()
        tof_sp_collection.SetTOF0SpacePointArray(tof0_sp_array)
        tof_sp_collection.SetTOF1SpacePointArray(tof1_sp_array)
        tof_event = ROOT.MAUS.TOFEvent()
        tof_event.SetTOFEventSpacePoint(tof_sp_collection)

        reco_event = ROOT.MAUS.ReconEvent()
        reco_event.SetPartEventNumber(ev_number);

        reco_event.SetTOFEvent(tof_event);
        reco_event.SetTriggerEvent(ROOT.MAUS.TriggerEvent());
        reco_event.SetSciFiEvent(ROOT.MAUS.SciFiEvent());
        reco_event.SetCkovEvent(ROOT.MAUS.CkovEvent());
        reco_event.SetKLEvent(ROOT.MAUS.KLEvent());
        reco_event.SetEMREvent(ROOT.MAUS.EMREvent());
        reco_event.SetGlobalEvent(ROOT.MAUS.GlobalEvent());
        reco_event.SetCutEvent(ROOT.MAUS.Cuts());

        return reco_event

    def build_kernel(self):
        line = self.fin.readline()
        self.metadata = json.loads(line)
        src_dist = [json.loads(line) for line in self.fin]
        # kde smeared distribution
        psv_dist = [variables[:5] for variables in src_dist] # x,px,y,py,pz
        psv_dist = numpy.array(psv_dist).transpose()
        self.psv_kernel = scipy.stats.gaussian_kde(psv_dist)
        # list of (mean, std)
        tof0_dist = [[variables[4], variables[5]] for variables in src_dist] # pz, tof0
        self.tof0_dist = self.get_distribution(tof0_dist)
        # list of (mean, std)
        tof1_dist = [[variables[4], variables[6]] for variables in src_dist] # pz, tof1
        self.tof1_dist = self.get_distribution(tof1_dist)

    def get_distribution(self, input_tof_dist):
        bin_list = [[] for i in range(self.n_momentum_slices)]

        for [pz, tof] in input_tof_dist:
            if pz < self.momentum_min or pz >= self.momentum_max:
                continue
            bin = int((pz-self.momentum_min)/self.momentum_step)
            bin_list[bin].append(tof)
        tof_dist = []
        for bin_contents in bin_list:
            mean = numpy.mean(bin_contents)
            std = numpy.std(bin_contents)
            tof_dist.append((mean, std))
        #print tof_dist
        return tof_dist

    def sample_distribution(self, pz, tof_dist, tof_offset):
        pz_bin = bisect.bisect_right(self.momentum_bin_lower, pz)-1
        mean, std = tof_dist[pz_bin]
        #print "mean : " + str(mean)
        #print "tof_offset : " + str(tof_offset)
        tof = numpy.random.normal(mean+tof_offset, std)
        tof_sp = ROOT.MAUS.TOFSpacePoint()
        tof_sp.SetTime(tof)
        return tof_sp

    def write(self, z_position = 0., seed = None, output_file = None):
        if seed != None:
            numpy.random.seed(seed=seed)
        if output_file != None:
            self.output_file = output_file
        hit_list = []
        self.tgt_dist = self.kernel.resample(self.n_events).transpose()
        for item in self.tgt_dist:
            my_dict = {"mass":self.mu_mass, "pid":-13, "z":z_position}
            for i, key in enumerate(self.keys):
                my_dict[key] = item[i]
            hit_list.append(Hit.new_from_dict(my_dict, "energy"))
        bunch = Bunch.new_from_hits(hit_list)
        bunch.hit_write_builtin(self.format, self.output_file)
        print "Writing bunch of length", len(bunch)

    keys = ("x", "px", "y", "py", "pz")
    mu_mass = xboa.common.pdg_pid_to_mass[13]

