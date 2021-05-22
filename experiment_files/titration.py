import sys
import os
import json
import time
import numpy as np
import psychopy
from psychopy import visual
from psychopy.data import QuestHandler
from psychopy import core
from stimuli import stimulus


"""
Set-up section:
    1. Create the screen
    2. Create the instructions message to be shown on intial screen
    3. Create the stimulus. This needs to be replcaed with the stimulus being used in the experiment
    4. Create the ladder object for controlling stimulus and measuring threshold. The ladder has to be updated to match the experiment needs.
"""
 
# set the number of trials (for testing)!
numberOfTrials = 30 # should be 100


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
threshold = 1
# monitor specs global variables
M_WIDTH = 1920
M_HEIGHT = 1200

# Gabor patch global variables
CYCLES = 10 # required cycles for the whole patch
X = 256; # size of texture in pixels, needs to be to the power of 2!
sf = CYCLES/X; # spatial frequency for texture, cycles per pixel
gabortexture = (
    visual.filters.makeGrating(res=X, cycles=X * sf) *
    visual.filters.makeMask(matrixSize=X, shape="circle", range=[0, 1])
)

# stimulus draw function
def draw_stim(noise, signal, reddot, annulus):
    noise.draw()
    noise.updateNoise()
    signal.draw()
    annulus.draw()
    reddot.draw()


# get pair id via command-line argument
try:
    pair_id = int(sys.argv[1])
except:
    print('Please enter a number as pair id as command-line argument!')
    pair_id = input()


# variable for instructions
instrmapping = ['upper', 'lower'] if (int(pair_id) % 2) == 0 else ['lower', 'upper']

subjectData['pair_id'] = pair_id

def geninstrtitration():
    instructions = f"Please read the instructions carefully.\n\
    1. Now we will determine your individual threshold for recognizing the vertical grating.\n\
    2. The procedure is the same as before: when you hear a beep, press the {instrmapping[0]} key if you saw a grating, and the {instrmapping[1]} key if you didn’t.\n\
    3. The visibility of the grating will be adjusted throughout the trials.\n\n\
    Press yes to continue"

    visual.TextStim(window,
                    text=instructions, pos=(0, 0),
                    color='black', height=20).draw()

def geninstrfamiliarization():
    instructions = f"Please read the instructions carefully.\n\
    1. Place your middle finger on the upper key and your index finger on the lower key.\n\
    2. First, you will become familiar with the stimulus and the handling of the button box.\n\
    3. For the stimulus, a red dot is shown in the middle of the screen, surrounded by a circular pattern that looks similar to white noise.\n\
    4. You need to indicate whether you saw a vertical grating on top of the noise.\n\
    5. Press the {instrmapping[0]} key for 'yes' and the {instrmapping[1]} key for 'no'.\n\
    Press yes to continue"

    visual.TextStim(window,
                    text=instructions, pos=(0, 0),
                    color='black', height=20).draw()

while titration_over == False:
    titration_counter += 1
    subjectData['titration_counter'] = titration_counter

    # input the chamber number in which titration takes place
    chamber = []
    if chamber == []:
        print("Enter chamber number (1 or 2):")
        chamber = input()
    elif chamber != 1 & chamber != 2:
        print("Wrong! Enter chamber number (1 or 2):")
        chamber = input()
    else: 
        print("You already entered a chamber number! You entered:" + chamber)

    keys = ["8", "7"] if chamber == 1 else ["1", "2"]

    subjectData['chamber'] = chamber

    # the screen
    window = psychopy.visual.Window(size=(M_WIDTH, M_HEIGHT), units='pix', screen=int(chamber), fullscr=False, pos=None)
    m = psychopy.event.Mouse(win=window)
    m.setVisible(0)

    # the stimulus
    stimuli = stimulus(X=X, window=window, xoffset=0, gabortexture=gabortexture, threshold=threshold)
    stimulus = stimuli.signal
    noise = stimuli.noise
    reddot = stimuli.reddot
    annulus = stimuli.annulus

    '''
    1. Familiarization
    '''
    while True:
        geninstrfamiliarization() # display instructions
        window.flip()
        key = psychopy.event.getKeys()
        if len(key) > 0:
            print(key)
            if keys[0] in key:
                break

    nfamtrials = 3
    famcontrast = [0.15,0.005,0.08]

    for contr in famcontrast:
        key = []
        stimulus.opacity = contr
        while not key:
            draw_stim(noise, stimulus, reddot, annulus) # draw the stimulus 
            window.flip()
            key = psychopy.event.getKeys(keyList=keys)

    '''
    2. Titration
    '''
                                
    #the ladder
    staircase = QuestHandler(
                                startVal=0.5,
                                startValSd=0.2,
                                pThreshold=0.63,  #because it is a one up one down staircase 
                                gamma=0.01,
                                nTrials=numberOfTrials, 
                                minVal=0,
                                maxVal=1
                                )   
     
    while True:
        geninstrtitration() # display instructions
        window.flip()
        key = psychopy.event.getKeys()
        if len(key) > 0:
            if keys[0] in key:
                break


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

    print(keys[0])
    print(keys[1])
    for contrast in staircase:
        key = []
        stimulus.opacity = contrast #update the difficulty or contrast from the staircase
        while not key:
            draw_stim(noise, stimulus, reddot, annulus) # draw the stimulus
            window.flip()
            key = psychopy.event.getKeys(keyList=keys)
        print(key)
        if keys[1] in key: # if they didn't see it
            print("no")
            response = 0
            staircase_means.append(staircase.mean())
        else:
            response = 1
            print("yes")
            staircase_means.append(staircase.mean())
        staircase.addResponse(response)


    """
    End section:
        1. Show the threshold to subject. 
        This part will be changed for the experiment. 
        We will store the threshold in a variable for the next core block to use. 
    """

    # fill subject dictionary with threshold and staircase value list
    subjectData['threshold'] = staircase.mean()
    subjectData['threshold_list'] = staircase_means

    # currently printing the threshold to the subject
    #result = 'The threshold is %0.4f' %(staircase.mean())
    #message2 = visual.TextStim(SCREEN, pos=(0,0), text=result)
    #message2.draw()
    
    print('The subjects threshold is: ' + str(staircase.mean()))
    print('The titration values are: ')
    for member in staircase_means:
        print("%.4f" % member)

    window.flip()
    #core.wait(2)
    window.close()

    answer = []
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
