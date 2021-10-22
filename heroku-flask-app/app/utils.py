import random
import os
import json
# from collections import namedtuple


# resultTuple = namedtuple("ResultStore","id path class confidence")

def rand_run_name():
    ran = random.randrange(10**80)
    myhex = "%064x" % ran
    #limit string to 64 characters
    myhex = myhex[:10]
    return myhex