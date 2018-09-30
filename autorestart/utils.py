__doc__ = "a module that houses utilities for the autorestart library"
__author__ = "Reed Essick (reed.essick@ligo.org)"

#-------------------------------------------------

import os
import logging

### non-standard libraries
import psutil # use this to re-launch processes as well (similar syntax to subprocess)

#-------------------------------------------------

DEFAULT_NUM_INSTANCES = 1
DEFAULT_NUM_TRIALS = 1
DEFAULT_CADENCE = 0.1

DEFAULT_RECIPIENTS = []

DEFAULT_LOG_LEVEL = 10
DEFAULT_LOG_DIR = '.'
DEFAULT_TAG = ''

DEFAULT_FORMATTER = logging.Formatter('%(asctime)s | %(name)s : %(levelname)s : %(message)s')

#-------------------------------------------------

def logname(tag=DEFAULT_TAG):
    if tag:
        tag = "_"+tag
    return "autrestart%s"%tag

def logpath(name, directory=DEFAULT_LOG_DIR):
    return os.path.join(directory, name+'.log')

def logger(tag=DEFAULT_TAG, directory=DEFAULT_LOG_DIR, log_leval=DEFAULT_LOG_LEVEL, verbose=False):
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except OSError: ### already exists, may be due to another process creating the directory
            pass

    name = logname(tag=tag)
    path = logpath(name, directory=directory)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    handlers = [logging.FileHander(path)]
    if verbose:
        handlers.append( logging.StreamHandler() )

    for handler in handlers:
        handler.setFormatter(DEFAULT_FORMATTER)
        logger.addHandler(handler)

    return logger

#-------------------------------------------------

def grep(cmd, logger=None):
    raise NotImplementedError

def restart(cmd, logger=None):
    raise NotImplementedError

def autorestart(cmd, num_instances=DEFAULT_NUM_INSTANCES, recipients=[], logger=None):
    num_found = grep(cmd, logger=logger)

    if num_found != num_instances:
        logger.warn('found %d instances when we expected %d'%(num_found, num_instances))

        if num_found < num_instances:
            num_new = num_instances - num_found
            logger.info('launching %d new instances'%num_new)
            for _ in range(num_new):
                restart(cmd, logger=None)

        logger.info('alerting: %s'%recipients)
        alert(recipients, num_new, cmd)
