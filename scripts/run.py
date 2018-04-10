#!/usr/env python

import subprocess
import time
import os

class Run(object):
    def __init__(self, environment, extra_args = []):
        self.delta_t = 60
        self.prefix = 'simulation'
        self.environment = environment
        self.n_procs = environment.config.n_procs
        self.extra_args = extra_args

    def run_many(self):
        run_number = self.environment.run_number
        print 'Running', self.environment.n_jobs, self.prefix, 'jobs for run', run_number,
        if self.is_scarf():
            print "on scarf"
        else:
            print "locally"
        timer, bjobs, unique_id = 0, 0, 0
        job_list = range(self.environment.n_jobs)

        processes = []
        while len(processes) > 0 or len(job_list) > 0 or bjobs > 0:
            print round(timer, 1), '    ',
            processes = self.poll_local(processes)
            if self.is_scarf():
                bjobs = self.poll_bjobs()
            print bjobs, len(processes)
            while len(processes) < self.n_procs and len(job_list) > 0:
                job = job_list.pop(0)
                processes.append(self.run_one(job))
            timer += self.delta_t/60.
            time.sleep(self.delta_t)
        try:
            print subprocess.check_output(['bjobs'])
        except OSError:
            pass # not on scarf
        print "   ... Clearing links"
        for unique_id in range(self.environment.n_jobs):
            self.clear_links(unique_id)
        print "Done"

    def run_one(self, unique_id):
        here = os.getcwd()
        self.make_links(unique_id)
        log_name = self.prefix+".log"
        run = ['python', self.prefix+".py",
              '--configuration_file', self.prefix+'_config.py',
              ]+self.extra_args
        os.chdir(self.environment.get_dir_name(unique_id))
        if self.is_scarf():
            bsub = ['bsub',
                    '-n', '1',
                    '-W', '24:00',
                    '-q', 'scarf-ibis',
                    '-o', log_name,
                    '-e', log_name,
                    #'-K',
                ]
            run = bsub+run
            log_file = open(self.prefix+"_bsub.log", 'w')
        else:
            log_file = open(log_name, 'w')
        subproc = subprocess.Popen(run, stdout=log_file, stderr=subprocess.STDOUT)
        print "Running job id", unique_id, "in process id", subproc.pid
        os.chdir(here)
        return subproc

    def is_scarf(self):
        uname = subprocess.check_output(['uname', '-a'])
        return 'scarf.rl.ac.uk' in uname

    def make_links(self, unique_id):
        here = os.getcwd()+"/"
        run_number = str(self.environment.run_number)
        out_dir = self.environment.get_dir_name(unique_id)
        os.symlink(here+self.environment.get_output_geometry_filename(self.prefix),
                   out_dir+'/geometry_'+run_number)
        os.symlink(here+"scripts/"+self.prefix+".py",
                   out_dir+"/"+self.prefix+".py")

    def clear_links(self, unique_id):
        here = os.getcwd()
        os.chdir(self.environment.get_dir_name(unique_id))
        os.unlink('geometry_'+str(self.environment.run_number))
        os.unlink(self.prefix+".py")
        os.chdir(here)

    def poll_local(self, processes):
        processes_update = []
        for proc in processes:
            if proc.returncode == None:
                proc.poll()
                if proc.returncode == None:
                    processes_update.append(proc)
        return processes_update

    def poll_bjobs(self):
        output = subprocess.check_output(['bjobs', '-prw'])
        count = 0
        for line in output.split('\n'):
            if self.prefix+".py" in line:
                count += 1
        return count
