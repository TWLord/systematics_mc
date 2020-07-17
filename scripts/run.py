#!/usr/env python

import sys
import subprocess
import time
import os

SCRIPT_NAME = 'phumhf'

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
        if self.is_epp():
            print "on epp"
        else:
            print "locally"
        timer = 0
        job_list = range(self.environment.n_jobs)
        for unique_id in range(self.environment.n_jobs):
            self.clear_links(unique_id)

        self.processes = []
        while len(self.processes) > 0 or len(job_list) > 0:
            print round(timer/60., 1), '    ',
            self.poll()
            print len(self.processes)
            while len(self.processes) < self.n_procs and len(job_list) > 0:
                print len(self.processes), len(job_list)
                job = job_list.pop(0)
                self.processes.append(self.run_one(job))
            timer += self.delta_t
            if timer > self.max_t:
                print 'Run.run_many: Out of time ... killing all jobs'
                self.kill_all()
                job_list = []
            time.sleep(self.delta_t)
        try:
            print subprocess.check_output(['bjobs'])
        except OSError:
            pass # not on epp 
        print "   ... Clearing links"
        print "Done"

    def make_sbatch_file(self, unique_id, command, workdir):
        file_name = self.prefix+"_"+unique_id+".sh"
        fout = open(file_name, "w")
        #print >> fout, "#!/bin/sh\n#SBATCH"
        print >> fout, "#!/bin/sh\ncd "+str(workdir)+"\n . "+str(self.environment.mausdir)+"/env.sh" # TomL
        for item in command:
            print >> fout, item,
        print >> fout
        os.chmod(file_name, 509)
        return file_name

    def run_one(self, unique_id):
        here = os.getcwd()
        self.make_links(unique_id)
        log_name = self.prefix+".log"
        run = ['python', self.prefix+".py",
              '--configuration_file', self.prefix+'_config.py',
              ]+self.extra_args
        os.chdir(self.environment.get_dir_name(unique_id))
        workdir = os.getcwd() 
        if self.is_epp():
            sbatch_filename = self.make_sbatch_file(str(unique_id), run, workdir)
            #print sbatch_filename # TomL
            #if self.n_events > 2000 :
            #  queue = 'long'
            #else :
            #  queue = 'medium'
            #queue = 'medium'
            queue = 'long'
            run = ['bsub',
                    #'-n', '1',
                    #'--time', '2880', # minutes, 48 hrs
                    #'-q', 'xlong',
                    '-q', queue,
                    '-o', log_name,
                    '-e', log_name,
                    '-G', 'micegrp',
                    workdir+"/"+sbatch_filename
            ]
            log_file = open(self.prefix+"_sbatch.log", 'w')
        else:
            log_file = open(log_name, 'w')
        subproc = subprocess.Popen(run, stdout=log_file, stderr=subprocess.STDOUT)
        print "Running job id", unique_id, "in process id", subproc.pid
        os.chdir(here)
        return subproc, self.environment.get_dir_name(unique_id)

    def is_epp(self):
        uname = subprocess.check_output(['uname', '-a'])
        #uname = "blank"
        return 'epp-ui01' in uname

    def make_links(self, unique_id):
        here = os.getcwd()+"/"
        run_number = str(self.environment.run_number).zfill(5)
        out_dir = self.environment.get_dir_name(unique_id)
        link_list = [
            (self.environment.get_output_geometry_filename(self.prefix),
                                              out_dir+'/runnumber_'+run_number),
            (here+"scripts/"+self.prefix+".py", out_dir+"/"+self.prefix+".py"),
        ]
        for source, target in link_list:
            os.symlink(source, target)
            while not os.path.exists(target):
                time.sleep(0.1)

    def clear_links(self, unique_id):
        here = os.getcwd()
        try:
            os.chdir(self.environment.get_dir_name(unique_id))
        except OSError:
            pass # maybe the dir didn't exist
        try:
            os.unlink('runnumber_'+str(self.environment.run_number).zfill(5))
            #os.unlink('geometry_'+str(self.environment.run_number))
        except OSError:
            pass # maybe the links didn't exist
        try:
            os.unlink(self.prefix+".py")
        except OSError:
            pass # maybe the links didn't exist
        os.chdir(here)

    def get_bjob_number(self, dir_name):
        line = open(dir_name+"/"+self.prefix+"_sbatch.log").readline()
        if line == "":
            return None
        line = line.rstrip('\n')
        line = line.rstrip(' ')
        # bjob_number = line.split(' ')[-1]
        bjob_number = line.split('<')[1] # TomL
        bjob_number = bjob_number.split('>')[0] # TomL
        #print bjob_number
        return int(bjob_number)

    def poll(self, verbose = False):
        if verbose:
            print '\nPolling local'
        processes_update = self.poll_local(verbose)
        if self.is_epp():
            if verbose:
                print 'Polling epp'
            processes_update += self.poll_epp(verbose)
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

    def poll_epp(self, verbose):
        """processes_update = []
        global SCRIPT_NAME
        output = subprocess.check_output(['bjobs', '-prw'])
        count = 0
        for line in output.split('\n'):
            if SCRIPT_NAME in line:
                count += 1
                processes_update.append((count
        # return count"""

        processes_update = []
        for proc, dir_name in self.processes:
            bjob_number = self.get_bjob_number(dir_name)
            try:
                #output = subprocess.check_output(['squeue', '-u', 'phumhf'])
                output = subprocess.check_output(['bjobs', '-prw']) # TomL
                for line in output.split('\n'):
                    if str(bjob_number) in line:
                        processes_update.append((proc, dir_name))
                        break
                if verbose:
                    print '   ', proc.pid, dir_name, bjob_number, ':', line 
            except Exception:
                sys.excepthook(*sys.exc_info())
                print "Failed to check bjob", bjob_number, "in dir", dir_name
                print "    ... assume it is dead" 
        return processes_update

    def kill_all(self):
        self.kill_all_local()
        if self.is_epp():
            self.kill_all_epp()
    
    def kill_all_local(self):
        for proc, dir_name in self.processes:
            if proc.returncode != None:
                continue # proc has returned
            pid_str = str(proc.pid)
            subprocess.check_output(['kill', '-9', pid_str])
            
    def kill_all_epp(self):
        for proc, dir_name in self.processes:
            bjob_number = self.get_bjob_number(dir_name)
            try:
                output = subprocess.check_output(['scancel', str(bjob_number)])
            except Exception:
                pass

    def clear(self, file_name):
        for unique_id in range(self.environment.n_jobs):
            dir_name = self.environment.get_dir_name(unique_id)
            name = os.path.join(dir_name, file_name)
            try:
                os.unlink(name)
            except OSError:
                pass # maybe the links didn't exist
