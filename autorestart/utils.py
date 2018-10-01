__doc__ = "a module that houses utilities for the autorestart library"
__author__ = "Reed Essick (reed.essick@ligo.org)"

#-------------------------------------------------

import os
import logging
import random
import time

import subprocess as sp

### non-standard libraries
import psutil # use this to re-launch processes as well (similar syntax to subprocess)

#-------------------------------------------------

DEFAULT_USERNAME=os.getenv('USER')

DEFAULT_NUM_INSTANCES = 1
DEFAULT_NUM_TRIALS = 1
DEFAULT_CADENCE = 0.1

DEFAULT_RECIPIENTS = []

#------------------------

DEFAULT_LOG_LEVEL = 10
DEFAULT_LOG_DIR = '.'
DEFAULT_TAG = ''

DEFAULT_FORMATTER = logging.Formatter('%(asctime)s | %(name)s : %(levelname)s : %(message)s')

#------------------------

DEFAULT_RAND_NUM = 6
CHOICES = '1 2 3 4 5 6 7 8 9 0 A B C D E F G H I J K L M N O P Q R S T U V W X Y Z a b c d e f g h i j k l m n o p q r s t u v w x y z'.split()

#-------------------------------------------------

RANDTEMP = '%s-%s-%d'
def randname(base, num=DEFAULT_RAND_NUM):
    return RANDTEMP%(base, ''.join(random.choice(CHOICES) for _ in range(num)), round(time.time(), 0))

def logname(tag=DEFAULT_TAG):
    if tag:
        tag = "_"+tag
    return "autorestart%s"%tag

#------------------------

PATHTEMP = "%s.%s"
def getpath(name, suffix, directory=DEFAULT_LOG_DIR):
    return os.path.join(directory, PATHTEMP%(name, suffix))

def outpath(name, directory=DEFAULT_LOG_DIR):
    return getpath(name, 'out', directory=directory)

def errpath(name, directory=DEFAULT_LOG_DIR):
    return getpath(name, 'err', directory=directory)

def logpath(name, directory=DEFAULT_LOG_DIR):
    return getpath(name, 'log', directory=directory)

#-------------------------------------------------

def logger(tag=DEFAULT_TAG, directory=DEFAULT_LOG_DIR, log_level=DEFAULT_LOG_LEVEL, verbose=False):
    name = logname(tag=tag)
    path = logpath(name, directory=directory)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    handlers = [logging.FileHandler(path)]
    if verbose:
        handlers.append( logging.StreamHandler() )

    for handler in handlers:
        handler.setFormatter(DEFAULT_FORMATTER)
        logger.addHandler(handler)

    return logger

#-------------------------------------------------

GREPTEMP='searching for username=%s; cmdline=%s'
FOUNDTEMP='found pid=%d'
def grep(cmdline, username=DEFAULT_USERNAME, logger=None):
    log = logger is not None
    if log:
        logger.info(GREPTEMP%(username, ' '.join(cmdline)))

    pids = []
    for proc in psutil.process_iter(attrs=['pid', 'cmdline', 'username']):
        if (proc.info['username']==username) and (proc.info['cmdline']==cmdline):
            pid = proc.info['pid']
            if log:
                logger.info(FOUNDTEMP%pid)
            pids.append(pid)
    return pids

ENVTEMP='establishing env via %s'
RESTARTTEMP='%s 1> %s 2> %s'
PIDTEMP='new process pid=%d'
def restart(cmdline, env=None, directory=DEFAULT_LOG_DIR, logger=None):
    log = logger is not None

    ### set up environment
    if env is not None:
        if log:
            logger.info(ENVTEMP%env)
        sp.Popen([env]).wait()

    ### generate new target process
    name = randname(os.path.basename(cmdline[0]))
    out = outpath(name, directory=directory)
    err = errpath(name, directory=directory)

    if log:
        logger.info(RESTARTTEMP%(' '.join(cmdline), out, err))

    out = open(out, 'a')
    err = open(err, 'a')
    proc = sp.Popen(cmdline, stdout=out, stderr=err)
    out.close()
    err.close()
    
    if log:
        logger.info(PIDTEMP%proc.pid)

YESALERTTEMP='alerting: %s'
MISSALERTTEMP='no one to alert'
SUBJECTTEMP='%(num_new)d %(name)s processes restarted on %(hostname)s'
BODYTEMP='''\
%(cmdline)s
hostname : %(hostname)s
username : %(username)s
sought : %(num_instances)d
found : %(num_found)d
date : %(date)s'''
def alert(cmdline, username, num_new, num_instances, recipients=DEFAULT_RECIPIENTS, logger=None):
    if recipients:
        if logger is not None:
            logger.info(YESALERTTEMP%(' '.join(recipients)))

        d = {
            'cmdline':' '.join(cmdline),
            'name':os.path.basename(cmdline[0]),
            'hostname':os.getenv('HOSTNAME'),
            'username':username,
            'num_new':num_new,
            'num_instances':num_instances,
            'num_found':num_instances-num_new,
            'date':time.ctime(), ### local time
        }
        subject = SUBJECTTEMP%d
        body = BODYTEMP%d

        proc = sp.Popen(['mailx', '-s', subject]+recipients, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
        out, err = proc.communicate(body)
        if proc.returncode: ### something bad happened
            logger.error('stdout: '+stdout)
            logger.error('stderr: '+stderr)

    elif logger is not None:
        logger.info(MISSALERT)

#------------------------

DIFFTEMP='found %d instances when we expected %d'
LAUNCHTEMP='launching %d new instances'
NOALERTTEMP='did not alert'
def autorestart(cmdline, env=None, username=DEFAULT_USERNAME, num_instances=DEFAULT_NUM_INSTANCES, directory=DEFAULT_LOG_DIR, recipients=[], logger=None):
    log = logger is not None
    found = grep(cmdline, logger=logger)
    num_found = len(found)
    if num_found != num_instances:
        if log:
            logger.warn(DIFFTEMP%(num_found, num_instances))

        if num_found < num_instances:
            num_new = num_instances - num_found
            if log:
                logger.info(LAUNCHTEMP%num_new)
            for _ in range(num_new):
                restart(cmdline, env=env, directory=directory, logger=logger)

            if recipients:
                alert(cmdline, username, num_new, num_instances, recipients=recipients, logger=logger)

        else:
            logger.info(NOALERTTEMP)
