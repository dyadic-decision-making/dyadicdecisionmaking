import sys
import os
import json
import time
import numpy as np
import psychopy
from psychopy import visual, event, core, monitors
from psychopy.data import QuestHandler
import stimuli
from psychopy.sound import Sound

# set the number of trials
numberOfTrials = 100 # should be 100

# Directory Specs
HOME = os.getcwd()
DATA = '/data/'

# Subject data dictionary
subjectData = {'pair_id': [], 'titration_counter': [], 'chamber':[], 'threshold': [], 'threshold_list': [] }

# monitoring the while loop with..
titration_over = False

# monitoring how often the titration has been done
titration_counter = 0

# initial threshold
threshold = 0.01

# monitor specs global variables
M_WIDTH = stimuli.M_WIDTH
M_HEIGHT = stimuli.M_HEIGHT

myMon = monitors.Monitor('DellU2412M', width=M_WIDTH, distance=80)
myMon.setSizePix([M_WIDTH, M_HEIGHT])

# create beep for decision interval
beep = Sound('A', secs=0.5, volume=0.1)

# get pair id via command-line argument
try:
    pair_id = int(sys.argv[1])
except:
    print('Please enter a number as pair id as command-line argument!')
    pair_id = input()

subjectData['pair_id'] = pair_id

# stimulus draw function
def draw_stim(noise, signal, reddot):
    noise = stimulus.updateNoise()
    noise.draw()
    signal.draw()
    reddot.draw()

# stimulus draw function
def drawintertrial(noise, reddot):
    noise = stimulus.updateNoise()
    noise.draw()
    reddot.draw()


def genendscreen():
    instructions = "You have finished the titration.\n\n\
    Please wait"

    visual.TextStim(window,
                    text=instructions, pos=(0, 0),
                    color='black', height=20).draw()

def geninstrtitration():
    instructions = "Please read the instructions carefully.\n\
    1. Now we will determine your individual threshold for recognizing the vertical grating.\n\
    2. The procedure is the same as before: Press the green key if you saw a grating, and the red key if you didn’t.\n\
    3. Fixate on the red dot in the center of the circle.\n\
    4. The visibility of the grating will be adjusted throughout the trials.\n\n\
    Press yes to continue"

    visual.TextStim(window,
                    text=instructions, pos=(0, 0),
                    color='black', height=20).draw()

def geninstrfamiliarization():
    instructions = "Please read the instructions carefully.\n\
    1. Place your index finger on the left key and your middle finger on the right key.\n\
    2. First, you will become familiar with the stimulus and the handling of the button box.\n\
    3. For the stimulus, a red dot is shown in the middle of the screen, surrounded by a circular pattern that looks similar to white noise.\n\
    4. You need to indicate whether you saw a vertical grating on top of the noise.\n\
    5. Fixate on the dot in the center of the circular pattern.\n\
    6. Press the green key for 'yes' and the red key for 'no'.\n\n\
    Press yes to continue"

    visual.TextStim(window,
                    text=instructions, pos=(0, 0),
                    color='black', height=20).draw()

while titration_over == False:
    # input the chamber number in which titration takes place
    chamber = []
    if chamber == []:
        print("Enter chamber number (1 or 2):")
        chamber = input()

        if chamber not in ["1", "2"]:
            print("Wrong. Enter chamber number (1 or 2):")
            continue

    titration_counter += 1
    subjectData['titration_counter'] = titration_counter
    subjectData['chamber'] = chamber

    # variables for button box input
    keys = ["2", "1"] if chamber == "1" else ["7", "8"] # first one is yes

    # the screen
    window = psychopy.visual.Window(size=(M_WIDTH, M_HEIGHT), units='pix', screen=int(chamber), fullscr=False, pos=None, blendMode='add', useFBO=True, monitor=myMon)
    window.mouseVisible = False

    # the stimulus
    stimulus = stimuli.stim(window=window, xoffset=0, threshold=threshold)
    signal = stimulus.signal
    noise = stimulus.noise
    reddot = stimulus.reddot

    '''
    1. Familiarization
    '''
    geninstrfamiliarization() # display instructions
    window.flip()
    key = event.waitKeys(keyList=keys[:1])

    famcontrast = [0.00397,0.3619,0.01314]
    nfamtrials = len(famcontrast)

    for contr in famcontrast:
        key = []
        signal.opacity = contr
        while not key:
            draw_stim(noise, signal, reddot) # draw the stimulus
            window.flip()
            key = event.getKeys(keyList=keys)


    '''
    2. Titration
    '''

    #the ladder
    staircase = QuestHandler(
                                startVal=0.1,
                                startValSd=0.2,
                                pThreshold=0.63,  #because it is a one up one down staircase
                                gamma=0.01,
                                nTrials=numberOfTrials,
                                minVal=0.00005,
                                maxVal=0.1,
                                method='quantile'
                                )

    geninstrtitration() # display instructions
    window.flip()
    key = event.waitKeys(keyList=keys[:1])

    """
    Main section:
        1. use the ladder already created to change the contrast of the grating
        2. Show the patch to subject
        3. Collect response-left is subject can see the grating, right otherwise
        4. Pass on reponse evaluation to ladder (0 if subject responded correctly, 1 if subject did not)
        5. Do 1 to 4 for ntimes set in ladder constructor
    """
    # list that is filled with the staircase values
    staircase_means = []

    for contrast in staircase:
        key = []
        signal.opacity = contrast #update the difficulty or contrast from the staircase
        beep.play()
        while not key:
            draw_stim(noise, signal, reddot) # draw the stimulus
            window.flip()
            key = event.getKeys(keyList=keys)
        beep.stop()
        if keys[1] in key: # if they didn't see it
            print("no")
            response = 0
        else:
            print("yes")
            response = 1

        for _ in range(int(np.rint(2*60))):
            drawintertrial(noise, reddot)
            window.flip()

        #staircase_means.append(contrast)
        staircase_means.append(staircase.quantile(0.5))
        staircase.addResponse(response)

    # fill subject dictionary with threshold and staircase value list
    subjectData['threshold'] = staircase.quantile(0.5)
    subjectData['threshold_list'] = staircase_means

    print('The titration values are: ')
    for member in staircase_means:
        print("%.4f" % member)
    print('The subjects mean threshold is: ' + str(staircase.mean()))
    print('The subjects median threshold is: ' + str(staircase.quantile(0.5)))
    print('The subjects mode threshold is: ' + str(staircase.mode()))

    genendscreen()
    window.flip()
    core.wait(5)
    window.close()

    print('Titration result sufficient? Enter y/n')
    answer = input()

    # if the titration is sufficient the script stops, if not it repeats and increases the titration counter
    if answer !='y' and answer !='n':
        print("Enter yes(y) or no(n) !")
        answer = input()
    else:
        if answer == 'y':
            titration_over = True
            # Create directory and save as JSON
            DATAPATH = HOME+DATA+str(pair_id)
            if not os.path.exists(DATAPATH):
                os.makedirs(DATAPATH)
            os.chdir(DATAPATH)
            with open('data_chamber'+chamber+'.json', 'w') as fp:
                json.dump(subjectData, fp)
        elif answer == 'n':
            Titration_over = False