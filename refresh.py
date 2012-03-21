import sys
import os
import subprocess
import getopt
import shutil
import re
import time
from datetime import datetime 

LATEX_LOG = "refresh.out"
EXEC_LOG = "refresh.log"
MASTER = ""
        
def make_serial(root):
    return '-' + str(time.time())
        
def make_environ(latex_dir):
    env = os.environ
    path = env['PATH']
    path += ':' + latex_dir
    env['PATH'] = path
    return env
    
def do_call(myargs, myenv, mylog):
    mylog.write("Calling '" + reduce(lambda x, y : x + ' ' + y, myargs) + "'...\n")
    mylog.flush()
    p = subprocess.Popen(myargs, env=myenv, stdout=mylog, stderr=mylog)
    p.wait()
    if p.returncode == 0:
        mylog.write("OK.\n")
        return True
    else:
        mylog.write("Error calling " + myargs[0] + "\n")
        return False

def call_pdflatex(env, log, serial):
    return do_call(
        ['pdflatex', '-halt-on-error', 'dissertation' + serial], 
        env, log)

def call_bibtex(env, log, serial): 
    return do_call(['bibtex', 'dissertation' + serial], 
        env, log)
        
def call_cvs(root):
    os.chdir(root)
    p = subprocess.Popen(['cvs', 'up'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.wait()
    return p.stdout.read()
    
def call_git(root):
    os.chdir(root)
    p = subprocess.Popen(['git', 'pull', 'origin'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.wait()
    return p.stdout.read()

def refresh(env, root, serial):
    with open(root + '/' + LATEX_LOG, 'wa') as log:
        log.write("Refreshing document...\n")
        log.flush()
        if call_pdflatex(env, log, serial): 
            if call_bibtex(env, log, serial):
                if call_pdflatex(env, log, serial): 
                    return call_pdflatex(env, log, serial)
        print "Error compiling document!"
        return False
                
def setup(root, serial):
    shutil.copyfile(root + '/dissertation.tex', 
        root + '/dissertation' + serial + '.tex')
    shutil.copyfile(root + '/dissertation.bib', 
        root + '/dissertation' + serial + '.bib')
                
def swing_link(root, serial):
    os.rename(root + '/dissertation' + serial + '.pdf', 
        root + '/dissertation' + MASTER + '.pdf')
    
def cleanup(root, serial):
    for f in os.listdir(root): 
        head, tail = os.path.split(f)
        if re.match("^dissertation" + serial, tail):
            os.remove(f)

if __name__ == '__main__': 
    opts, args = getopt.getopt(sys.argv[1:],'d:l:')
    
    root = latex_dir = ''
    for (k,v) in opts:
        if (k == '-d'): 
            root = v
        elif (k == '-l'):
            latex_dir = v

    if (root == '') | (latex_dir == ''): 
        print "Usage: refresh.py -d <root_dir> -l <latex_bin_dir>"

    with open(root + '/' + EXEC_LOG, 'a') as log:
        log.write(str(datetime.now()) + ': Starting execution...\n')
    
        env = make_environ(latex_dir)   
    
        cvs_output = call_git(root).split('\n')
        for word in cvs_output: 
            if word.endswith('tex') | word.endswith('bib'): 
                serial = make_serial(root)
                setup(root, serial)
                log.write(str(datetime.now()) + ': Refreshing document...\n')
                if refresh(env, root, serial): 
                    swing_link(root, serial)
                cleanup(root, serial)
                break

        log.write(str(datetime.now()) + ': Finished.\n')
    