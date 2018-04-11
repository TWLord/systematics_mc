#!/usr/env python

import subprocess
import time
import os

class Run(object):
    def __init__(self, environment):
        self.prefix = 'simulation'
        self.environment = environment
        self.n_procs = environment.config.run['n_procs']
        self.extra_args = environment.config.run['extra_args']
        self.delta_t = environment.config.run['delta_t']
        self.max_t = environment.config.run['max_t']
        self.processes = []
        
    def run_many(self):
        run_number = self.environment.run_number
        print 'Running', self.environment.n_jobs, self.prefix, 'jobs for run', run_number,
        if self.is_scarf():
            print "on scarf"
        else:
            print "locally"
        timer = 0
        job_list = range(self.environment.n_jobs)

        self.processes = []
        while len(self.processes) > 0 or len(job_list) > 0:
            print round(timer/60., 1), '    ',
            self.poll()
            print len(self.processes)
            while len(self.processes) < self.n_procs and len(job_list) > 0:
                job = job_list.pop(0)
                self.processes.append(self.run_one(job))
            timer += self.delta_t
            if timer > self.max_t:
                print 'Out of time ... killing all jobs'
                self.kill_all()
                job_list = []
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
        return subproc, self.environment.get_dir_name(unique_id)

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

    def get_bjob_number(self, dir_name):
        line = open(dir_name+"/"+self.prefix+"_bsub.log").readline()
        if line == "":
            return None
        bjob_number = line.split(' ')[1]
        bjob_number = bjob_number.rstrip('>')
        bjob_number = bjob_number.lstrip('<')
        return int(bjob_number)

    def poll(self, verbose = False):
        if verbose:
            print '\nPolling local'
        processes_update = self.poll_local(verbose)
        if self.is_scarf():
            if verbose:
                print 'Polling scarf'
            processes_update += self.poll_scarf(verbose)
        # remove duplicates
        processes_update = list(set(processes_update))
        self.processes = processes_update
            
    def poll_local(self, verbose):
        processes_update = []
        for proc, dir_name in self.processes:
            if proc.returncode == None:
                proc.poll()
                if proc.returncode == None:
                    processes_update.append((proc, dir_name))
            if verbose:
                print '   ', proc.pid, dir_name, proc.returncode
        return processes_update

    def poll_scarf(self, verbose):
        processes_update = []
        for proc, dir_name in self.processes:
            bjob_number = self.get_bjob_number(dir_name)
            output = subprocess.check_output(['bjobs', '-prw', str(bjob_number)])
            for line in output.split('\n'):
                is_alive = False
                for alive_key in ['PEND', 'RUN']:
                    is_alive = is_alive or alive_key in line
                if self.prefix+".py" in line and str(bjob_number) in line and is_alive:
                    processes_update.append((proc, dir_name))
                    break
            short_text = subprocess.check_output(['bjobs', str(bjob_number)])
            if verbose:
                print '   ', proc.pid, dir_name, bjob_number, short_text 

        return processes_update

    def kill_all(self):
        self.kill_all_local()
        if self.is_scarf():
            self.kill_all_scarf()
    
    def kill_all_local(self):
        for proc, dir_name in self.processes:
            if proc.returncode != None:
                continue # proc has returned
            pid_str = str(proc.pid)
            subprocess.check_output(['kill', '-9', pid_str])
            
    def kill_all_scarf(self):
        for proc, dir_name in self.processes:
            bjob_number = self.get_bjob_number(dir_name)
            try:
                output = subprocess.check_output(['bkill', str(bjob_number)])
            except Exception:
                pass
