# 11 April 2021

'''
    Naming Convention:
        The subjects are either refered to as 'sone' or 'stwo'
        The variables for each are prepended with `sone_` or `stwo_`
'''

import os
import numpy as np
import psychtoolbox as ptb
from psychopy import visual, event, core, gui, data, prefs

# setting PTB as our preferred sound library and then import sound
prefs.hardware['audioLib'] = ['PTB']

from psychopy.sound import Sound
from numpy.random import random

# Gabor patch global variables
X = 512; # width of the gabor patch in pixels
sf = .02; # spatial frequency, cycles per pixel

gabortexture = (
    visual.filters.makeGrating(res=X, cycles=X * sf) *
    visual.filters.makeMask(matrixSize=X, shape="circle", range=[0, 1])
)

class subject:
    def __init__(self, sid, state, threshold, inputdevice):
        '''
            state is either 'obs' or 'act' for observing or acting conditions, respectively
            window is the psychopy window object for the subject
            signal is the signal according to the subjects threshold
            inputdevice is the pyusb connector to the subject's buttonbox
        '''
        self.id = sid
        self.state = state
        self.window = visual.Window(size=(1024,768), units='pix', fullscr=False)
        self.signal = visual.GratingStim(
            win = self.window, tex = gabortexture, mask = 'circle',
            size = X, contrast = 1.0, opacity = threshold,
        )
        self.inputdevice = inputdevice

    def __repr__ (self):
        return str(self.id)


### Global variables for rendering stimuli
sone = subject(1, "act", 0.3, None)
stwo = subject(2, "obs", 0.3, None)
subjects = [sone, stwo]

blocks = range(2)
ntrials = 2

noisetexture = random([X,X])*2.-1. # a X-by-X array of random numbers in [-1,1]

window = visual.Window(size=(1024,768), units='pix', fullscr=False)

# the annulus is created by passing a matrix of zeros to the texture argument
annulus = visual.GratingStim(
    win = window, mask='circle', tex=np.zeros((64,64)),
    size = 50, contrast = 1.0, opacity = 1.0,
)

# noise patch
noise = visual.RadialStim(
    win = window, mask='none', tex = noisetexture,
    size = X, contrast = 1.0, opacity = 1.0,
)

# red fixation dot for decision phase
reddot = visual.GratingStim(
    win = window, size=5, units='pix', pos=[0,0],
    sf=0, color='red', mask='circle'
)

# green fixation dot for pre trial and inter trial condition
greendot = visual.GratingStim(
    win = window, size=5, units='pix', pos=[0,0],
    sf=0, color='green', mask='circle'
)

# a dot which indicates to the subject they are in the observation state
obsindicator = visual.GratingStim(
    win = window, size=50, units='pix', pos=[250, 250],
    sf=0, color='blue', mask='circle'
)

# create beep for decision interval
beep = Sound('A', secs=0.5)


def geninstruction (window):
    instructions = "Instructions:\n\
    Your task is to indicate if you see a vertical grating or not.\n\
    1. At the start of each trial, a red dot is shown in the middle of the screen.\n\
    2. When you hear a beep, you may press one of the buttons to indicate if you saw a vertical grating or not.\n\
    3. Press the left key for 'yes' and the right key for 'no'.\n\
    4. After a short break, the procedure will be repeated from step 1.\n\
    5. After 80 trials, you will have a break.\n\
    6. After the break, press the spacebar when ready to continue.\n\
    7. There will be a total of 6 blocks. \n\n\
    Press spacebar when ready."

    instructions = visual.TextStim(window,
                                    text=instructions,
                                    color='black', height=20)


def genbaseline (subjects):
    for s in subjects:
        noise.draw(s.window)
        annulus.draw(s.window)
        reddot.draw(s.window)

        if s.state == 'obs':
            obsindicator.draw(s.window)

    subjects[0].window.flip()
    subjects[1].window.flip()

def gendecisionint (subjects, condition):
    '''
        Generate the stimulus
        condition:
            's' for Signal
            'n' for Noise
    '''
    if condition == 'noise':
        genbaseline(subjects)
    elif condition == 'signal':
        for s in subjects:
            noise.draw(s.window)
            s.signal.draw(s.window)
            annulus.draw(s.window)
            reddot.draw(s.window)

            if s.state == 'obs':
                obsindicator.draw(s.window)
    else:
        raise("Please provide s for signal and n for noise in condition argument")

    subjects[0].window.flip()
    subjects[1].window.flip()

def genintertrial (subjects):
    for s in subjects:
        noise.draw(s.window)
        annulus.draw(s.window)
        greendot.draw(s.window)

        if s.state == 'obs':
            obsindicator.draw(s.window)

    subjects[0].window.flip()
    subjects[1].window.flip()

def genbreakscreen (window):
    '''
        Generate the screen shown when the break is in progress
    '''
    instructions = "Instructions:\n\
    Enjoy your break. Press any key to resume."

    instructions = visual.TextStim(window,
                                    text=instructions,
                                    color='black', height=20)

    subjects[0].window.flip()
    subjects[1].window.flip()

def genendscreen (nextcondition):
    '''
        Generate the end screen
        Args:
            nextcondition:
                'd' : Go to the dyadic condition
                'i' : Go to the individual condition
                'e' : End the experiment
    '''
    instructions = "Thank you for your time."

    instructions = visual.TextStim(window,
                                    text=instructions,
                                    color='black', height=20)


def fetchbuttonpress (subjects, clock):
    '''
        Looks for input from a pyserial connector
        Args:
            connector: PySerial object of connection to button box
            clock: PsychoPy clock object
    '''
    for s in subjects:
        if s.state == 'obs':
            continue
        else:
            # we only need the first index of the event array
            # How do I tell waitKeys to look for input from the specific subject input device and not the other?
            response = event.waitKeys(maxWait=2.5, timeStamped=clock, clearEvents=True)
            # waitButtons is from the rucosci library
            # https://github.com/wilberth/RuSocSci/blob/18569aa014ff7e4be5f4aa6ddd0aa4202f601393/rusocsci/buttonbox.py#L116
            # need to add a mechanism where both subjects are acting, in such a condition response variable will be overwritten
            # response = s.inputdevice.waitButtons(maxWait=2.5, timeStamped=clock, flush=True)
    return response

def updatestate ():
    '''
        Which dyad makes the button box
    '''
    for s in subjects:
        if s.state == 'act':
            s.state = 'obs'
        else:
            s.state = 'act'


# generate file for storing data

# create trial handler
triallist = [
        {"condition": "signal"},
        {"condition": "noise"}
        ]

expinfo = {'participant1': sone.id, 'participant2' : stwo.id, 'pair': 1}

# preparing the clocks
responsetime = core.Clock()

trials = data.TrialHandler(triallist, nReps=ntrials, method='sequential', originPath=-1, extraInfo=expinfo)

for block in blocks:
    # traverse through trials
    for trial in trials:
        # display baseline
        genbaseline(subjects)
        # wait for a random time between 2 to 4 seconds
        core.wait( np.random.uniform(2,4) )

        # preparing time for next window flip, to precisely co-ordinate window flip and beep
        nextflip = window.getFutureFlipTime(clock='ptb')
        beep.play(when=nextflip)
        # display stimulus
        gendecisionint(subjects, trials.thisTrial['condition'])
        # we decided to reset the clock after flipping (redrawing) the window
        responsetime.reset()

        # fetch button press
        response = fetchbuttonpress(subjects, responsetime)
        print(response)

        # need to explicity call stop() to go back to the beginning of the track
        # we reset after collecting a response, otherwise the beep is stopped too early
        beep.stop()

        # display inter trial interval
        genintertrial(subjects)
        # inter trial interval is 2s
        core.wait(2)

        # state switch
        updatestate()

        # save data
        trials.addData('response', response)
    # decide between continuing with next block, take a break

# write to file
trials.saveAsWideText("data")