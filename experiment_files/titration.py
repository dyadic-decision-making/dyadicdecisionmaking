import sys
import os
import json
import time
import numpy as np
import psychopy
from psychopy import visual
from psychopy.data import QuestHandler
from psychopy import core


"""
Set-up section:
    1. Create the screen
    2. Create the instructions message to be shown on intial screen
    3. Create the stimulus. This needs to be replcaed with the stimulus being used in the experiment
    4. Create the ladder object for controlling stimulus and measuring threshold. The ladder has to be updated to match the experiment needs.
"""

# get pair id via command-line argument
try:
    pair_id = int(sys.argv[1])
except:
    print('Please enter a number as pair id as command-line argument!')
    sys.exit(0)

#pair_id = 12


# Directory Specs
HOME = os.getcwd()
DATA = '/data/'

thresholds = dict(chamber1=0,chamber2=0)

pairData = { 'subject1': {'chambername':1, 'threshold': 0, 'threshold_list': [] },
                     'subject2': {'chambername':2, 'threshold': 0, 'threshold_list': [] }
                    }


screens = [0]#,1]
for screen in screens:
    """
    Opening section:
        1. Show subject instructions and give option to not continue
    """
        
    # screen
    SCREEN = psychopy.visual.Window(size=(1920, 1080), units='pix', screen=screen, fullscr = False, pos = None) 
    m = psychopy.event.Mouse(win=SCREEN)
    m.setVisible(0)

    # message for initial screen
    message1 = visual.TextStim(SCREEN, pos=(0,0),
                                text="Instruction:\n"
                                    "Press Right when you see vertical lines, Left when you don't\n \n"
                                    "Hit a key when ready.\n\n"
                                    "Press ESC to escape" ) 

    # the stimulus
    stimulus = visual.GratingStim(
                                SCREEN,
                                opacity=1,
                                contrast=1
                                ,mask='circle',
                                tex="sin",
                                units='pix',
                                color=[1,1,1],
                                size=800,
                                sf=0.02, 
                                ori=0
                                )   
    #the ladder
    staircase = QuestHandler(
                                startVal=0.5,
                                startValSd=0.2,
                                pThreshold=0.75, #was 0.63 
                                gamma=0.01,
                                nTrials=10,
                                minVal=0,
                                maxVal=1
                                )   
     
    while True:
        message1.draw()
        SCREEN.flip()
        key = psychopy.event.getKeys()
        if len(key) > 0:
            if 'escape' in key:
                SCREEN.close()
                core.quit()
            else:
                break

    """
    Main section:
        1. use the ladder already created to change the contrast of the grating
        2. Show the patch to subject
        3. Collect response-left is subject can see the grating, right otherwise
        4. Pass on reponse evaluation to ladder (0 if subject responded correctly, 1 if subject did not)
        5. Do 1 to 4 for ntimes set in ladder constructor
    """
    staircase_means = []
    for contrast in staircase:
        key = []
        stimulus.opacity = contrast #update the difficulty or contrast from the staircase
        while not key:
            stimulus.draw() #draw the stimulus
            SCREEN.flip()
            key = psychopy.event.getKeys(keyList=['left','right'])
        if 'left' in key:
            response = 0
            staircase_means.append(staircase.mean())
        else:
            response = 1
            staircase_means.append(staircase.mean())
        staircase.addResponse(response)

    """
    End section:
        1. Show the threshold to subject. 
        This part will be changed for the experiment. 
        We will store the threshold in a variable for the next core block to use. 
    """
    if screen == 0:
        pairData['subject1']['threshold'] = staircase.mean()
        pairData['subject1']['threshold_list'] = staircase_means
    else:
        pairData['subject2']['threshold'] = staircase.mean()
        pairData['subject2']['threshold_list'] = staircase_means
        
    
    print(pairData)

# Create directory and save as JSON
DATAPATH = HOME+DATA+str(pair_id)
if not os.path.exists(DATAPATH):
    os.makedirs(DATAPATH)
os.chdir(DATAPATH)
with open('pairData.json', 'w') as fp:
    json.dump(pairData, fp)



result = 'The threshold is %0.4f' %(staircase.mean())
message2 = visual.TextStim(SCREEN, pos=(0,0), text=result)
message2.draw()
SCREEN.flip()
core.wait(2)
#SCREEN.close()
    
#print(thresholds)
print(staircase_means)
