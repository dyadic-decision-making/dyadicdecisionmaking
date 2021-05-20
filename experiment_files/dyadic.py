# 11 April 2021

'''
    Naming Convention:
        The subjects are either refered to as 'sone' or 'stwo'
        The variables for each are prepended with `sone_` or `stwo_`

    To Do:
        - There is a warning that a providing data file can prevent data loss in case of crash. Is it writing to the disk and should we have this?
'''

from typing import Any, Callable

import os
import sys
from subprocess import run
import numpy as np
import psychtoolbox as ptb
from psychopy import visual, event, core, gui, data, prefs
from stimuli import stimulus
from random import choice
#from titration import calculate_threshold

# setting PTB as our preferred sound library and then import sound

'''
To obtain your sounddevices run
from psychopy.sound.backend_sounddevice import getDevices
getDevices()
Copy the `name` attribute of your device to the audioDevice
'''

prefs.hardware['audioLib'] = ['PTB']

from psychopy import sound
sound.setDevice('USB Audio Device: - (hw:3,0)')

from psychopy.sound import Sound
from numpy.random import random


# get pair id via GUI
#name = 'Experiment: Dyadic Decision Making'
#info = {'pair ID':''}
#while (info['pair ID']==''):
#    dlg = gui.DlgFromDict(dictionary=info, sortKeys=False, title=name)
#    if dlg.OK == False:
#        core.quit()
#pair_id = int(info['pair ID'])

# copied to titration
# get pair id via command-line argument
try:
    pair_id = int(sys.argv[1])
except:
    print('Please enter a number as pair id as command-line argument!')
    sys.exit(0)
    #pair_id=2

# set yesfinger as global variables
if (pair_id % 2) == 0:
    mapping = 'index' # yes finger
    instrmapping = ['upper', 'lower'] # variable for instructions
else:
    mapping = 'middle'
    instrmapping = ['lower', 'upper']

# monitor specs global variables
M_WIDTH = 1920
M_HEIGHT = 1200
REFRESH_RATE = 60

# Gabor patch global variables
CYCLES = 10 # required cycles for the whole patch
X = 256; # size of texture in pixels, needs to be to the power of 2!
sf = CYCLES/X; # spatial frequency for texture, cycles per pixel

gabortexture = (
    visual.filters.makeGrating(res=X, cycles=X * sf) *
    visual.filters.makeMask(matrixSize=X, shape="circle", range=[0, 1])
)

window = visual.Window(size=(2048, 768), units='pix', fullscr=False)

noisetexture = random([X,X])*2.-1. # a X-by-X array of random numbers in [-1,1]


class subject:
    def __init__(self, sid, threshold, xoffset, position, keys):
        '''
            state is either 0 or 1 for observing or acting conditions, respectively
            xoffset is the constant added to all stimuli rendered for the subject
            signal is the signal according to the subjects threshold
            position is either left of right. it is used to determine the speaker of the subject
            keys is a list of keys expected from the user. it has to be in the order of yes and no
        '''
        self.id = sid
        self.state = 0
        self.xoffset = xoffset
        self.response = None
        self.actingheadphonebalance = "100%,0%" if position == "left" else "0%,100%"

        stimuli = stimulus(X=X, window=window, xoffset=xoffset, gabortexture=gabortexture, threshold=threshold)

        if (pair_id % 2) == 0:
            self.buttons = {
                    keys[0] : "yes",
                    keys[1] : "no",
                    None : "noresponse"
                    }
        else:
            self.buttons = {
                keys[1]: "yes",
                keys[0]: "no",
                None: "noresponse"
            }

        # signal
        self.signal = stimuli.signal

        # the annulus is created by passing a matrix of zeros to the texture argument
        self.annulus = stimuli.annulus

        # noise patch
        self.noise = stimuli.noise

        # red fixation dot for decision phase
        self.reddot = stimuli.reddot

        # green fixation dot for pre trial and inter trial condition
        self.greendot = stimuli.greendot

        # a dot which indicates to the subject they are in the observation state
        self.indicatordict = {
                "yes" : visual.TextStim(
                            win = window, text="Yes", units='pix', pos=[0 - xoffset, 0]
                        ),
                "no" : visual.TextStim(
                            win = window, text="No", units='pix', pos=[0 - xoffset, 0]
                        ),
                "noresponse" : visual.TextStim(
                            win = window, text="No Response", units='pix', pos=[0 - xoffset, 0]
                        ),
                }

    def __repr__ (self):
        return str(self.id)




### Global variables for rendering stimuli
ofs = window.size[0] / 4 # determine the offset once, assign it as neg or pos next

sone = subject(1, 0.3, ofs, "right", ["9", "0"])
stwo = subject(2, 0.7, -ofs, "left", ["1", "2"])
subjects = [sone, stwo]

#expinfo = {'date': data.getDateStr(), 'pair': pair_id, 'participant1': sone.id, 'participant2': stwo.id, 'yesfinger': mapping}
expinfo = {'pair': pair_id}

blocks = range(6)
ntrials = 2 # trials per block

'''
# make an array of 0 and 1, denoting observe and act, respectively and scale it up by half of the number of trials
states = [0, 1] * int(ntrials/2)
# shuffle the array using Fischer-Yates shuffling
np.random.shuffle(states)
'''

# create beep for decision interval
beep = Sound('A', secs=0.5)

def genstartscreen ():
    instructions = f"Welcome to our experiment! \n\n\
    Your task is to indicate whether you see a vertical grating or not.\n\
    If you have any questions after reading the instructions on the next screen, please feel free to ask the experimenter.\n\n\
    Press the {instrmapping[0]} key to continue"

    visual.TextStim(window,
                    text=instructions, pos=[0 + sone.xoffset,0],
                    color='black', height=20).draw()

    visual.TextStim(window,
                    text=instructions, pos=[0 + stwo.xoffset,0],
                    color='black', height=20).draw()

def geninstructionspractice ():
    instructions = f"Please read the instructions carefully.\n\
    1. Place your index finger on the upper key and your middle finger on the lower key.\n\
    2. First, you will have a few practice trials to see how the experiment works.\n\
    3. You will do the task together with your partner.\n\
    4. At the start of each trial, a red dot is shown in the middle of the screen, surrounded by a circular pattern that looks similar to white noise.\n\
    5. When you hear a beep, it’s your turn to indicate whether you saw a vertical grating on top of the noise.\n\
    6. Press the {instrmapping[0]} key for 'yes' and the {instrmapping[1]} key for 'no'.\n\
    7. It’s very important that you respond as fast and as accurate as possible! You only have a limited amount of time for your response.\n\
    8. If you don’t hear a beep, it’s the other person’s turn to respond. You will both see the grating (or not) and you will also see their response on your screen.\n\n\
    Press yes to continue"

    visual.TextStim(window,
                    text=instructions, pos=[0 + sone.xoffset,0],
                    color='black', height=20).draw()

    visual.TextStim(window,
                    text=instructions, pos=[0 + stwo.xoffset,0],
                    color='black', height=20).draw()

def geninstructionstitration ():
    instructions = f"Please read the instructions carefully.\n\
    1. Now we will determine your individual threshold for recognizing the vertical grating.\n\
    2. The procedure is the same as before: when you hear a beep, press the {instrmapping[0]} key if you saw a grating, and the {instrmapping[1]} key if you didn’t.\n\
    3. The visibility of the grating will be adjusted throughout the trials.\n\n\
    Press yes to continue"

    visual.TextStim(window,
                    text=instructions, pos=[0 + sone.xoffset,0],
                    color='black', height=20).draw()

    visual.TextStim(window,
                    text=instructions, pos=[0 + stwo.xoffset,0],
                    color='black', height=20).draw()

def geninstructionsexperiment ():
    instructions = f"Now you’re ready to start the experiment. Please remember:\n\
    1. Place your index finger on the upper key and your no on the lower key.\n\
    2. When you hear a beep it’s your turn. If you don’t hear a beep, you will see your partner’s response.\n\
    3. Press the {instrmapping[0]} key for 'yes' and the {instrmapping[1]} key for 'no'.\n\
    4. Please respond as fast as and as accurate possible! \n\
    5. Once you finished one block, you’ll be asked if you’re ready for the next block.\n\
    6. After every second block, you will have a break.\n\
    7. There will be a total of 12 blocks.\n\n\
    Press yes when you’re ready to start the experiment"

    visual.TextStim(window,
                    text=instructions, pos=[0 + sone.xoffset,0],
                    color='black', height=20).draw()

    visual.TextStim(window,
                    text=instructions, pos=[0 + stwo.xoffset,0],
                    color='black', height=20).draw()

def genendscreen ():
    visual.TextStim(window,
                    text="Thank you for your time.", pos=[0 + sone.xoffset,0],
                    color='black', height=20).draw()

    visual.TextStim(window,
                    text="Thank you for your time.", pos=[0 + stwo.xoffset,0],
                    color='black', height=20).draw()

def genbreakscreen ():
    '''
        Generate the screen shown when the break is in progress
    '''
    instructions = "Are you ready for the next block?\n\n\
    Press yes when you're ready to resume"

    visual.TextStim(window,
                    text=instructions, pos = [0 + sone.xoffset, 0],
                    color='black', height=20).draw()

    visual.TextStim(window,
                    text=instructions, pos = [0 + stwo.xoffset, 0],
                    color='black', height=20).draw()

def genmandatorybreakscreen ():
    '''
        Generate the screen shown when the mandatory break is in progress
    '''
    instructions = "Enjoy your break. The experimenter will resume the experiment."

    visual.TextStim(window,
                    text=instructions, pos = [0 + sone.xoffset, 0],
                    color='black', height=20).draw()

    visual.TextStim(window,
                    text=instructions, pos = [0 + stwo.xoffset, 0],
                    color='black', height=20).draw()

def genbaseline (subjects):
    for s in subjects:
        s.noise.draw()
        s.noise.updateNoise()
        s.annulus.draw()
        s.reddot.draw()

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
            s.noise.draw()
            s.noise.updateNoise()
            s.signal.draw()
            s.annulus.draw()
            s.reddot.draw()
    else:
        raise NotImplementedError

def genintertrial (subjects):
    for s in subjects:
        s.noise.draw()
        s.noise.updateNoise()
        s.annulus.draw()
        s.greendot.draw()

    # if subject one/two is in an acting state, add their response to the response box of subject two/one
    if stwo.state == 1:
        sone.indicatordict[stwo.response].draw()
    if sone.state == 1:
        stwo.indicatordict[sone.response].draw()


def fetchbuttonpress (subjects, clock):
    '''
        Looks for input from a pyserial connector
        Args:
            connector: PySerial object of connection to button box
            clock: PsychoPy clock object
    '''
    for s in subjects:
        if s.state == 0:
            continue
        else:
            # How do I tell waitKeys to look for input from the specific subject input device and not the other?
            response = event.getKeys(timeStamped=clock, keyList=s.buttons.keys())

            if len(response) == 0: response = [(None, 0)]
            keystroke = response[0][0]
            s.response = s.buttons[keystroke]
    return response

def updatespeakerbalance ():
    # we can a terminal command to shift the balance. it does not work if both the subject are acting (in the individual condition)
    # but it is a more efficient solution if we don't have a condition where both are acting
    for s in subjects:
        if s.state == 1:
            run(["amixer", "-D", "pulse", "sset", "Master", s.actingheadphonebalance, "quiet"])
            #pass

def updatestate ():
    '''
        Which dyad makes the button box
    '''
    sone.state = next(iterstates)
    stwo.state = 1 - sone.state

def secondstoframes (seconds):
    return range( int( np.rint(seconds * REFRESH_RATE) ) )

def getacknowledgements ():
    sone_ack, stwo_ack = None, None

    while (sone_ack != 'yes') or (stwo_ack != 'yes'):
        response = event.getKeys()
        for r in response:
            if sone_ack != 'yes': sone_ack = sone.buttons.get(r)
            if stwo_ack != 'yes': stwo_ack = stwo.buttons.get(r)

def getexperimenterack ():
    event.waitKeys(keyList=["space"])

def genactingstates ():
    return np.random.randint(0, 2, ntrials)

# update speaker balance for the first time
updatespeakerbalance()

# preparing the clocks
responsetime = core.Clock()

# specifications of output file
_thisDir = os.path.dirname(os.path.abspath(__file__))
expName = 'DDM'
filename = _thisDir + os.sep + u'data/%s_pair%s_%s' % (expName, expinfo['pair'], data.getDateStr())


# set up trial handler and experiment handler
triallist=[]
# make sure signal is present on 50% of trials
for Idx in range(ntrials//2):
    triallist.append({"condition": "signal"})
    triallist.append({"condition": "noise"})

exphandler = data.ExperimentHandler(name=expName, extraInfo=expinfo, saveWideText=True, dataFileName=filename)
for b in blocks:
    exphandler.addLoop(data.TrialHandler(trialList=triallist, nReps=1, method='random', originPath=-1, extraInfo=expinfo) )


# diplay welcome screen
genstartscreen()
window.flip()
getacknowledgements()

# display instructions for practice trials
geninstructionspractice()
window.flip()
getacknowledgements()


# set up practice trials
npracticetrials = 2
cond=["signal", "noise"]
practicetriallist=[]
for Idx in range(npracticetrials):
    practicetriallist.append(choice(cond))
# make an iterator object
practicestates = np.random.randint(0, 2, npracticetrials)
iterstates = iter(practicestates)

# traverse through practice trials
for idx in range(npracticetrials):
    # subject state update
    updatestate()

    # display baseline
    # wait for a random time between 2 to 4 seconds
    for frame in secondstoframes( np.random.uniform(2, 4) ):
        genbaseline(subjects)
        window.flip()

    # preparing time for next window flip, to precisely co-ordinate window flip and beep
    nextflip = window.getFutureFlipTime(clock='ptb')
    beep.play(when=nextflip)
    # display stimulus
    responsetime.reset()

    response = None
    for frame in secondstoframes(2.5):
        gendecisionint(subjects, practicetriallist[idx])
        window.flip()
        # we decided to reset the clock after flipping (redrawing) the window

        # fetch button press
        if response is None:
            response = fetchbuttonpress(subjects, responsetime)

    # need to explicity call stop() to go back to the beginning of the track
    # we reset after collecting a response, otherwise the beep is stopped too early
    beep.stop()

    # display inter trial interval for 2s
    for frame in secondstoframes(2):
        genintertrial(subjects)
        window.flip()

    # update the speaker balance to play the beep for the right subject
    updatespeakerbalance()


# display instructions for titration
geninstructionstitration()
window.flip()
getacknowledgements()

### Starting threshold calculation routine
#threshold = calculate_threshold(window)

# display instructions for experiment
geninstructionsexperiment()
window.flip()
getacknowledgements()

# variables for data saving
block=0

def get_key(val, dict):
    for key, value in dict.items():
         if val == value:
             return key
    return "key doesn't exist"

# start experiment
for trials in exphandler.loops:

    # variables for data saving
    block+=1
    trialInBlock=0

    # make an iterator object
    states = genactingstates()
    iterstates = iter(states)

    # traverse through trials
    for trial in trials:

        # save trial data to file
        trialInBlock += 1
        exphandler.addData('block', block)
        exphandler.addData('trial', trialInBlock)
        exphandler.addData('totalTrials', (block-1)*ntrials+trialInBlock)
        #exphandler.addData('condition', trials.thisTrial['condition'])
        exphandler.addData('s1_state', sone.state)
        exphandler.addData('s2_state', stwo.state)

        # subject state update
        updatestate()

        # display baseline
        # wait for a random time between 2 to 4 seconds
        for frame in secondstoframes( np.random.uniform(2, 4) ):
            genbaseline(subjects)
            window.flip()

        # preparing time for next window flip, to precisely co-ordinate window flip and beep
        nextflip = window.getFutureFlipTime(clock='ptb')
        beep.play(when=nextflip)
        # display stimulus
        responsetime.reset()

        response = None
        for frame in secondstoframes(2.5):
            gendecisionint(subjects, trials.thisTrial['condition'])
            window.flip()
            # we decided to reset the clock after flipping (redrawing) the window

            # fetch button press
            if response is None:
                response = fetchbuttonpress(subjects, responsetime)

        # need to explicity call stop() to go back to the beginning of the track
        # we reset after collecting a response, otherwise the beep is stopped too early
        beep.stop()

        # display inter trial interval for 2s
        for frame in secondstoframes(2):
            genintertrial(subjects)
            window.flip()

        # update the speaker balance to play the beep for the right subject
        updatespeakerbalance()

        # save response to file
        if response[0][0] is not None:
            print(response[0][0])
            if response[0][0] == next(iter(sone.buttons)) or response[0][0] == next(iter(stwo.buttons)):
                response[0][0] = 1
            else:
                response[0][0] = 0
            exphandler.addData('response', response[0][0])
            exphandler.addData('rt', response[0][1])
        else:
            exphandler.addData('response', 'None')
            exphandler.addData('rt', 'None') # why does this write 0 now instead of None? used to be None

        # move to next row in output file
        exphandler.nextEntry()

    # decide between continuing with next block, take a break
    # after every second block, there will be a mandatory break which only the experimenter can end
    if block % 2 == 0:
        genmandatorybreakscreen()
        window.flip()
        keys = event.waitKeys(keyList=["space", "q"])
        if keys == ["q"]: # exit experiment
            win.close()
            core.quit()
        elif keys == "space":
            #getexperimenterack()
            continue
    # otherwise, wait for the subjects to start their next block
    elif block % 2 == 1:
        # after every block, wait for the subjects to start their next block
        genbreakscreen()
        window.flip()
        getacknowledgements()
        continue

genendscreen()
window.flip()


