# Starship game.
# (Pygame) A game of 3 levels, where the starship collects words from different word classes, nouns 
#in the first level, verbs in the second level and adjectives in the third level.

#import necessary libraries
import nltk
import random, sys, time, math, pygame
from nltk.corpus import brown
from pygame.locals import *

# Constants defining game parameters
FPS = 30                              # frames per second to update the screen
WINWIDTH = 640                        # width of the games window in pixels
WINHEIGHT = 480                       # height of the game's window in pixels
HALF_WINWIDTH = int(WINWIDTH / 2)     # half width of the window
HALF_WINHEIGHT = int(WINHEIGHT / 2)   # half height of the window

# Color constants
GREEN = (24, 255, 0)                  #RGB value for green colour
WHITE = (255, 255, 255)               #RGB value for white colour
RED = (255, 0, 0)                     #RGB value for red colour

# Gameplay parameters
CAMERASLACK = 90      # how far from the center the word moves before moving the camera
MOVERATE = 9          # how fast the player moves
STARTSIZE = 40        # how big the player is
TEXTSIZE = 30         # how big the text is
INVULNTIME = 2        # how long the player is invulnerable after being hit in seconds
GAMEOVERTIME = 4      # how long the "game over" text stays on the screen in seconds
MAXHEALTH = 10        # how much health the player starts with

NUMSENEMIES = 20      # number of words in the active area
WORDMINSPEED = 1      # slowest word speed
WORDMAXSPEED = 3      # fastest word speed
DIRCHANGEFREQ = 2     # % chance of direction change per frame
LEFT = 'left'         #moving left by pressing on the left arrow
RIGHT = 'right'       #moving right by pressing on the right arrow
gameOverStartTime = 0 # time the player lost

"""
This program has three data structures to represent the player, words, and space background objects. The data structures are dictionaries with the following keys:

Keys used by all three data structures:
    'x' - the left edge coordinate of the object in the game world (not a pixel coordinate on the screen)
    'y' - the top edge coordinate of the object in the game world (not a pixel coordinate on the screen)
    'rect' - the pygame.Rect object representing where on the screen the object is located.
Player data structure keys:
    'surface' - the pygame.Surface object that stores the image of the spaceship which will be drawn to the screen.
    'facing' - either set to LEFT or RIGHT, stores which direction the player is facing.
    'size' - the width and height of the player in pixels. (The width & height are always the same.)
    'speed' - represents how fast  the player is in. 0 means standing (no movement).
    'health' - an integer showing how many more times the player can collect wrong words before dying.
Words data structure keys:
    'surface' - the pygame.Surface object that stores the image of the word which will be drawn to the screen.
    'movex' - how many pixels per frame the word moves horizontally. A negative integer is moving to the left, a positive to the right.
    'movey' - how many pixels per frame the word moves vertically. A negative integer is moving up, a positive moving down.
    'width' - the width of the word's image, in pixels
    'height' - the height of the word's image, in pixels
    'speed' - represents how fast the words are. 0 means standing (no movement).
background data structure keys:
    'spaceImage' - an integer that refers to the index of the pygame.Surface object in SPACEIMAGES used for this space object
"""


#words tags according to the word class downloaded from brown corpus
words_with_tags = brown.tagged_words(tagset='universal')
nouns = [word for word, tag in words_with_tags if tag == 'NOUN']
verbs = [word for word, tag in words_with_tags if tag == 'VERB']
adjectives = [word for word, tag in words_with_tags if tag == 'ADJ']
properNouns = [word for word, tag in words_with_tags if tag == 'NOUN' and word.istitle()]

#image used for the starship
intro_alien = pygame.image.load('START_UP_ALIEN.png') #Image taken from https://charatoon.com/?id=2409
#image displayed when level is passed
win_alien = pygame.image.load('THUMBS_UP_ALIEN.png') #Image taken from https://charatoon.com/?id=2407

#font size used for words
pygame.font.init()
BASICFONT = pygame.font.Font('freesansbold.ttf', 32)


#main function to initialize the game
def main():
    global FPSCLOCK, UFO_IMG                                    # Declare global variables for the clock and UFO image
    currentLevel = 1                                            #initialize the current level variable to 1
    pygame.init()                                               #initialize the game
    FPSCLOCK = pygame.time.Clock()                              # Create a Pygame clock object for controlling the frame rate
    pygame.display.set_icon(pygame.image.load('gameicon.png'))  #set the game icon
    pygame.display.set_caption('Star Words')                    #set the game caption
    # load the background image file for the player
    UFO_IMG = pygame.image.load('ufo.png') #Image taken from https://www.google.com/search?sca_esv=274934f892c43701&sxsrf=ACQVn0_b2_oa0caGMv1AwHSAx4HXkfcIrw:1709891630204&q=ufo+png&tbm=isch&source=lnms&sa=X&ved=2ahUKEwjA2ePZsuSEAxUmGRAIHapmAnoQ0pQJegQIDBAB&biw=1440&bih=825&dpr=1.5#imgrc=w-kOSaVgzeqkKM
    

    while True:                                                # Loop indefinitely to keep running the game
        currentLevel = runGame(currentLevel)                   # Call the runGame function to start or continue the game, updating the current level

#function to run the run through the levels
def runGame(currentLevel):
    global count, winMode, startTime                            #global variables used in the function
    startTime = pygame.time.get_ticks()                         #Record the start time of the game
    count = 0                                                   # Initialize the count variable to keep track of collected words
    levelConfig = getLevelConfig(currentLevel)                  #get configurations for current level
    #set variables for displaying the count graph
    countGraphWidth = 20                                        #determines the width of the graph
    topmargin = 10                                              #determines the  position of the graph
    rightmargin = 15                                            #determines the  position of the graph
    #calculate the cordinates for displaying the count graph
    x_coordinate = countGraphWidth - rightmargin
    y_coordinate = topmargin

    # set up variables for the start of a new game
    backgroundImg = pygame.image.load('space-png2.png') #Image taken from https://www.freepik.com/free-photo/beautiful-shining-stars-night-sky_7631083.htm#page=2&query=space%20png&position=51&from_view=keyword&track=ais&uuid=57b59b85-9a47-421e-ac45-1aeb6c6e4bc3

    invulnerableMode = False  # if the player is invulnerable
    invulnerableStartTime = 0 # time the player became invulnerable
    gameOverMode = False      # if the player has lost     
    winMode = False           # if the player has won

    # create the surfaces to hold game text
    gameOverSurf = BASICFONT.render('Game Over', True, WHITE)  #rendering the text on the surface
    gameOverRect = gameOverSurf.get_rect()                     #retriving the rectangle object
    gameOverRect.center = (HALF_WINWIDTH, HALF_WINHEIGHT)      #centering "Game Over" on the screen
    

    # camerax and cameray are the top left of where the camera view is
    camerax = int(backgroundImg.get_width() // 2)  #calculating x-coordinates
    cameray = int(backgroundImg.get_height() // 2) #calculating y-coordinates


    #checking if the the current level is 1, make the displayed words nouns.
    if currentLevel == 1:
        wordsObjs = list(makeWords(levelConfig['words'], levelConfig['numWords'], 'noun', camerax, cameray))
        #checking if the the current level is 2, make the displayed words verbs.
    elif currentLevel == 2:
        wordsObjs = list(makeWords(levelConfig['words'], levelConfig['numWords'], 'verbs', camerax, cameray))
        #checking if the the current level is 3, make the displayed words adjectives.
    elif currentLevel == 3:
        wordsObjs = list(makeWords(levelConfig['words'], levelConfig['numWords'], 'adjectives', camerax, cameray))
    

    # stores the player object:
    playerObj = {'surface': pygame.transform.scale(UFO_IMG, (STARTSIZE, STARTSIZE)), #image of the player
                 'facing': LEFT,                  #the direction the player is facing
                 'size': STARTSIZE,               #size of the player
                 'x': WINWIDTH + HALF_WINWIDTH,   #initial position of the player
                 'y': WINHEIGHT + HALF_WINHEIGHT, #initial position of the player
                 'bounce':0,                      #bouncing behaviour
                 'health': MAXHEALTH}             #state of the initial health state

#movement variables initialized at false at the beging of the game loop (still not moving untill reciving the player's commands) 
    moveLeft  = False  
    moveRight = False
    moveUp    = False
    moveDown  = False

    # start off with some words images on the screen
    while True: # main game loop
        #variables are calculated to check the camera's view
        camerax = max(0, min(playerObj['x'] - HALF_WINWIDTH, backgroundImg.get_width() - WINWIDTH))
        cameray = max(0, min(playerObj['y'] - HALF_WINHEIGHT, backgroundImg.get_height() - WINHEIGHT))

#Drawing background image onto the display surface, specifying portion of the background to be displayed
        DISPLAYSURF.blit(backgroundImg, (0, 0), (camerax, cameray, WINWIDTH, WINHEIGHT))

        #condition checking if the player is in the invulnerability mode
        if invulnerableMode and time.time() - invulnerableStartTime > INVULNTIME:
            invulnerableMode = False

        # draw all the words on the screen, as well as make them move
          for wObj in wordsObjs:
            wObj['rect'] = pygame.Rect(  #for calculating the size of the rectangles that contains the words
                (wObj['x'] - camerax,    #rendering the camera view
                 wObj['y'] - cameray,    #rendering the camera view
                wObj['width'],           #specifying the width of the words' surface
                wObj['height']))         #specifying the height of the words' surface
            
           #updating words' position by adding its movement in x and y axis 
            wObj['x'] += wObj['movex']
            wObj['y'] += wObj['movey']
            
            # Draw the word's surface onto the display surface at the specified rectangle position
            DISPLAYSURF.blit(wObj['surface'], wObj['rect']) 
        
        
            #Check if the word should change its direction randomly
        if random.randint(0, 99) < DIRCHANGEFREQ: # If the random number is less than DIRCHANGEFREQ, change the word's movement direction
           # Set a new random velocity for horizontal movement (x direction)
            wObj['movex'] = getRandomVelocity()
           # Set a new random velocity for horizontal movement (y direction)
            wObj['movey'] = getRandomVelocity()
            
        
        
        
        # Check if the word has reached or exceeded the left or right edge of the window
        if wObj['x'] < 0 or wObj['x'] > WINWIDTH - wObj['surface'].get_width():
            # If the word has reached the left or right edge, reverse its horizontal movement direction
            wObj['movex'] *= -1
            # Check if the word has reached or exceeded the top or bottom edge of the window
        if wObj['y'] < 0 or wObj['y'] > WINHEIGHT - wObj['surface'].get_height():
            # If the word has reached the top or bottom edge, reverse its vertical movement direction
            wObj['movey'] *= -1
        
        
        # go through all the objects and see if any need to be deleted.
        for i in range(len(wordsObjs) - 1, -1, -1):
            if isOutsideActiveArea(camerax, cameray, wordsObjs[i]): # Check if the word at index i is outside the active area of the camera view
                del wordsObjs[i]  # If the word is outside the active area, remove it from the wordsObjs list
        

        # add more words if we don't have enough.
        while len(wordsObjs) < NUMSENEMIES:
            # Extend the wordsObjs list with additional words of each word type (nouns, verbs, adjectives)
            # The number of words added for each type is specified as 6 in this case
            wordsObjs.extend(list(makeWords(nouns, 6, 'noun', camerax, cameray)))
            wordsObjs.extend(list(makeWords(verbs, 6, 'verb', camerax, cameray)))
            wordsObjs.extend(list(makeWords(adjectives, 6, 'adjective', camerax, cameray)))

        # adjust camera-x and camera-y if beyond the "camera slack"
        playerCenterx = playerObj['x'] + int(playerObj['size'] / 2)
        playerCentery = playerObj['y'] + int(playerObj['size'] / 2)
        # Adjust camerax if the player is beyond the camera slack on the x-axis
        if (camerax + HALF_WINWIDTH) - playerCenterx > CAMERASLACK:
            camerax = playerCenterx + CAMERASLACK - HALF_WINWIDTH
        elif playerCenterx - (camerax + HALF_WINWIDTH) > CAMERASLACK:
            camerax = playerCenterx - CAMERASLACK - HALF_WINWIDTH
        # Adjust cameray if the player is beyond the camera slack on the y-axis
        if (cameray + HALF_WINHEIGHT) - playerCentery > CAMERASLACK:
            cameray = playerCentery + CAMERASLACK - HALF_WINHEIGHT
        elif playerCentery - (cameray + HALF_WINHEIGHT) > CAMERASLACK:
            cameray = playerCentery - CAMERASLACK - HALF_WINHEIGHT

# Draw the player UFO
# Calculate whether to flash the player UFO based on time
        flashIsOn = round(time.time(), 1) * 10 % 2 == 1
        # Check if the game is not over and the player is not in invulnerable mode or not flashing
        if not gameOverMode and not (invulnerableMode and flashIsOn):
         # Create a Rect object representing the player's position and size
            playerObj['rect'] = pygame.Rect( (playerObj['x'] - camerax,
                                              playerObj['y'] - cameray, 
                                              playerObj['size'],
                                              playerObj['size']) )
            # Draw the player UFO on the screen using its surface and position Rect
            DISPLAYSURF.blit(playerObj['surface'], playerObj['rect'])

        ## Draw the health meter based on the player's current health
        drawHealthMeter(playerObj['health'])
        # Show the player's current score at the specified coordinates
        showScore(x_coordinate, y_coordinate)

        for event in pygame.event.get(): # event handling loop
            if event.type == QUIT: # Check if the user clicked the window's close button
                terminate()        # Terminate the game if the close button is clicked

            elif event.type == KEYDOWN:          # Check if a key has been pressed down
                if event.key in (K_UP, K_w):     # Check if the UP arrow key or 'W' key is pressed
                    moveDown = False             #stop moving down
                    moveUp = True                #start moving up
                elif event.key in (K_DOWN, K_s): # Check if the DOWN arrow key or 'S' key is pressed
                    moveUp = False               #stop moving up
                    moveDown = True              #start moving down
                elif event.key in (K_LEFT, K_a): # Check if the LEFT arrow key or 'A' key is pressed
                    moveRight = False            #stop moving right
                    moveLeft = True              #start moving left
                elif event.key in (K_RIGHT, K_d):# Check if the RIGHT arrow key or 'D' key is pressed
                    moveLeft = False             #stop moving left
                    moveRight = True             #start moving right

                # Check if the player has won and pressed the SPACE key
                elif winMode and event.key == K_SPACE:
                    currentLevel += 1      # Increment the current level
                    return currentLevel    #return the updated level number
                
            
            elif event.type == KEYUP:               # Check if a key has been pressed up
                if event.key in (K_LEFT, K_a):      # Check if the LEFT arrow key or 'A' key is pressed
                    moveLeft = False                #stop moving left
                elif event.key in (K_RIGHT, K_d):   # Check if the RIGHT arrow key or 'D' key is pressed
                    moveRight = False               #stop moving right
                elif event.key in (K_UP, K_w):      # Check if the UP arrow key or 'W' key is pressed
                    moveUp = False                  #stop moving up
                elif event.key in (K_DOWN, K_s):    # Check if the DOWN arrow key or 'S' key is pressed
                    moveDown = False                #stop moving down

            # Check if the ESCAPE key is pressed
                elif event.key == K_ESCAPE:
                    terminate()    #terminate the game of escape key is pressed

     # Display the task information for the current level and the elapsed time since the game started       
        showTask(currentLevel, startTime)
        if not gameOverMode: #check if the game is over or not

            # actually move the player
            if moveLeft:                    # Check if the left movement key is pressed
                playerObj['x'] -= MOVERATE  #move the player left
            if moveRight:                   # Check if the right movement key is pressed
                playerObj['x'] += MOVERATE  #move the player right
            if moveUp:                      # Check if the up movement key is pressed
                playerObj['y'] -= MOVERATE  #move the player up
            if moveDown:                    # Check if the down movement key is pressed
                playerObj['y'] += MOVERATE  #move the player down

            # check if the player has collided with any wordclasses for given level
            for i in range(len(wordsObjs)-1, -1, -1): # Iterate over the word objects in reverse order to safely remove collided objects
                wObj = wordsObjs[i]   #get the current word object
                if 'rect' in wObj and playerObj['rect'].colliderect(wObj['rect']): #check if a word in rect. and player in rect. collide
                    # a player/correct word type collision has occurred

                #checking levels and the specified word class for each 
                    if currentLevel == 1:                            #check if the current level is 1
                        if wObj['type'] == 'noun':                   #check if the word object is noun
                            del wordsObjs[i]                         #Delete the collided word object
                            count += 1                               #Increment the count of collected words
                            showScore(x_coordinate, y_coordinate)    #show the updated score
                        if count == 10:                              #if count of collected words = 10
                            winMode = True                           #set win mode to true
                        elif wObj['type'] in ['verb', 'adjective']:  # If the word type is verb or adjective
                            if not invulnerableMode:                 #if the player is not in the invulnerable mode
                                invulnerableMode = True              #set invulnerable mode to true
                                invulnerableStartTime = time.time()  # Record the start time of invulnerability
                                playerObj['health'] -= 1             #decrease player's health
                            if playerObj['health'] == 0:             #if player's health reaches 0
                                gameOverMode = True                  # turn on "game over mode"
                                gameOverStartTime = time.time()      # Record the start time of game over mode
    
                    elif currentLevel == 2:                          #check if the current level is 2
                        if wObj['type'] == 'verb':                   #if the word type is verb
                            del wordsObjs[i]                         #Delete the collided word object
                            count += 1                               #Increment the count of collected words
                            showScore(x_coordinate, y_coordinate)    #show the updated score
                        if count == 10:                              #if count of collected words = 10
                            winMode = True                           #set win mode to true
                        elif wObj['type'] in ['noun', 'adjective']:  #check If the word type is noun or adjective
                            if not invulnerableMode:                 #if the player is not in the invulnerable mode
                                invulnerableMode = True              #set invulnerable mode to true
                                invulnerableStartTime = time.time()  # Record the start time of game over mode
                                playerObj['health'] -= 1             #decrease player's health
                            if playerObj['health'] == 0:             #if player's health reaches 0
                                gameOverMode = True                  # turn on "game over mode"
                                gameOverStartTime = time.time()      # Record the start time of game over mode

                    elif currentLevel == 3:                          #check if the current level is 3
                        if wObj['type'] == 'adjective':              #check if the word type is adjective
                            del wordsObjs[i]                         #delete the collided word object
                            count += 1                               #Increment the count of collected words
                            showScore(x_coordinate, y_coordinate)    #show the updated score
                        if count == 10:                              #if the count of collected words = 10
                            winMode = True                           #set win mode to true
                        elif wObj['type'] in ['noun', 'verb']:       #check if the word type is noun or verb
                            if not invulnerableMode:                 #if the player is not in the invulnerable mode
                                invulnerableMode = True              #set invulnerable mode to true
                                invulnerableStartTime = time.time()  # Record the start time of game over mode
                                playerObj['health'] -= 1             #decrease player's health
                            if playerObj['health'] == 0:             #if player's health reaches 0
                                gameOverMode = True                  # turn on "game over mode"
                                gameOverStartTime = time.time()      # Record the start time of game over mode

                            
      #if none of the previous condiontions are met          
        else:
            DISPLAYSURF.blit(gameOverSurf, gameOverRect)        #display "game over" text on the screen 
            if time.time() - gameOverStartTime > GAMEOVERTIME:  #If the time since the game over started is greater than the game over time limit
                return                                          # end the current game

        # check if the player has won the level
        if winMode:                              #if player won
            count = 0                            #reset the word count
            winScreen(currentLevel, startTime)   #display the win screen with the current level information
            

        pygame.display.update()                  #update the game display to show any updates
        FPSCLOCK.tick(FPS)                       #pausing the game to achieve the target frames per secons


# Define a dictionary mapping level numbers to their corresponding word lists and number of words
def getLevelConfig(level):
    levelConfigs = {
        1: {'words': nouns, 'numWords': 10},      #level 1: 10 nouns
        2: {'words': verbs, 'numWords': 10},      #level 2: 10 verbs 
        3: {'words': adjectives, 'numWords': 10}  #level 3: 10 adjectives
    }
    return levelConfigs.get(level, None)          # Return the level configuration for the given level number, or None if the level number is invalid

# health meter
def drawHealthMeter(currentHealth):  #draw health bar based on current health
    for i in range(currentHealth):   # draw red health bar based on curred health
        # The position, colour (red) and size of the rectangle are calculated based on the loop index and the maximum health
        pygame.draw.rect(DISPLAYSURF, RED,   (15, 5 + (10 * MAXHEALTH) - i * 10, 20, 10))
 # Draw white outlines for the health bars
    for i in range(MAXHEALTH):        #draw the white outlines based on max health
     # The position, colour (white) and size of the rectangle are calculated based on the loop index and the maximum health
        pygame.draw.rect(DISPLAYSURF, WHITE, (15, 5 + (10 * MAXHEALTH) - i * 10, 20, 10), 1)

#showing score as text graphic
def showScore(x, y):                                         #function to show player's score
    global count                                             #access the global variable count
    countGraphic = BASICFONT.render(str(count), True, WHITE) #render the current score as a white text graphic
    DISPLAYSURF.blit(countGraphic, (x, y))                   #display the score graphic  at the specified positions (x,y)

# Define a function to display the task for the current level
def showTask(currentLevel, startTime):                                    # Define tasks for each level using a dictionary where the level number is the key
    tasks = {
        1: 'Collect 10 nouns, but stay away from other wordclasses!',     #task for level 1
        2: 'Collect 10 verbs, but stay away from other wordclasses!',     #task for level 2
        3: 'Collect 10 adjectives, but stay away from other wordclasses!' #task for level 3
    }
    taskMessage = tasks.get(currentLevel, "")                             #Retrieve the task message for the current level
    taskLines = taskMessage.split(', ')                                   #split the task message into 2 separate lines

# setting up the display of the task message and the image
    startY = HALF_WINHEIGHT - (len(taskLines) - 1) * 15                   # Calculate the starting Y-coordinate for displaying the task text
    imageY = startY - 100                                                 # Calculate the Y-coordinate for displaying the image above the task text
    scaled_intro_alien = pygame.transform.scale(intro_alien, (120, 120))  # Resize the intro alien image to the specified dimensions (it can be Resized to 300x150 or any size you want)
    alien_rect = scaled_intro_alien.get_rect()                            # Get the rectangle representing the resized intro alien image
    alien_rect.center = (HALF_WINWIDTH, imageY)                           # Center the image above the text

    for i, line in enumerate(taskLines):                                  # Iterate over each line in the task message
        lineSurf = BASICFONT.render(line, True, GREEN)                    #render the line of the text
        lineRect = lineSurf.get_rect()                                    #get the rectangle of the rendered text
        lineRect.center = (HALF_WINWIDTH, startY + i * 30)                #center the image

        if pygame.time.get_ticks() - startTime <= 3000:                   #check if it's less than 3 sec. since the start time
            DISPLAYSURF.blit(lineSurf, lineRect)                          #display the line of the text on the screen 
            DISPLAYSURF.blit(scaled_intro_alien, alien_rect)              #display the alien image on the screen



# ^ idea for function setup from Chat-GPT. Modified variable names to fit our game.           
#displaying a message when winning the level and proceeding to the next level
def winScreen(currentLevel, startTime):  #define win message for each level
    winMessages = {
        1: 'Level 1 complete, good job!. Hit space to go to level 2',       #passing level 1
        2: 'Level 2 complete, good job!. Hit space to go to level 3',       #passing level 2
        3: 'Level 3 complete, good job!. Now maybe its time to go outside', #passing level 3
    }
    winMessage = winMessages.get(currentLevel)                              #get a win message for current level
    winSurfaces = [BASICFONT.render(line, True, GREEN) for line in winMessage.split('. ')] #specifing the text colour (green), split message into two lines and render them

    if winMode:                                                               # Display the win screen if winMode is True
        startY = HALF_WINHEIGHT - (len(winSurfaces) - 1) * 15                 # Calculate the starting y-coordinate for displaying the win message
        imageY = startY - 100                                                 # Calculate the starting y-coordinate for displaying the win message
        global scaled_win_alien, alien_rect                                   #define global variable for alien image and alien rect.
        scaled_win_alien = pygame.transform.scale(win_alien, (120, 120))      # Resize to 300x150 or any size you want
        alien_rect = scaled_win_alien.get_rect(center = (HALF_WINWIDTH, imageY)) #get the rect. for the alien image and center it

        for i, surf in enumerate(winSurfaces):                                # Display each line of the win message on the screen
            rect = surf.get_rect(center = (HALF_WINWIDTH, startY + i * 30))   # Get the rectangle of the rendered text and center it horizontally
            DISPLAYSURF.blit(surf, rect)                                      #display rendered text                          
        if pygame.time.get_ticks() - startTime <= 100000:                     ## Display the alien image on the screen if less than 100000 milliseconds since the game started
            DISPLAYSURF.blit(scaled_win_alien, alien_rect)                    #display scaled alien image

# ^ idea for function setup from Chat-GPT. Modified variable names to fit our game. 


#function to terminate the game
def terminate():   #function to terminate the game
    pygame.quit()  #terminate the game
    sys.exit()     #exit the game

#function to get random velocity for words
def getRandomVelocity():                                 #defining function of random velocity 
    speed = random.randint(WORDMINSPEED, WORDMAXSPEED)   #generating random speed within specified limits (min,max)
    if random.randint(0, 1) == 0:                        #chances for positive speed
        return speed                                     #return to positive speed
    else:
        return -speed                                    #return to negative speed

#generating random off camera positions
def getRandomOffCameraPos(camerax, cameray, objWidth, objHeight):          #defining the function
    cameraRect = pygame.Rect(camerax, cameray, WINWIDTH, WINHEIGHT)        #create a Rect of the camera view
    while True:                                                            #while true generate random x and y cordinates
        x = random.randint(camerax - WINWIDTH, camerax + (2 * WINWIDTH))   #calculating x coordinates
        y = random.randint(cameray - WINHEIGHT, cameray + (2 * WINHEIGHT)) #calculating y coordinates
        # create a Rect object with the random coordinates and use colliderect()
        # to make sure the right edge isn't in the camera view.
        objRect = pygame.Rect(x, y, objWidth, objHeight)
        if not objRect.colliderect(cameraRect):                            #Check if the object Rect does not collide with the camera view
            return x, y                                                    #if not colliding returny x,y coordinates


#funtion to create words based on word class, word type, camera x, camera y
def makeWords(wordclass, num, wordtype, camerax, cameray):                        #defining the function 
    global objWidth, objHeight                                                    #defining global variables
    words = random.sample(wordclass, num)                                         #generating random number of samples of a given word class
    font_size = 40                                                                #setting font size to render the sampled words
    word_font = pygame.font.Font('freesansbold.ttf', font_size)                   #setiing font type
    word_Objs = []                                                                #initializing empty list to store word objects
    for word in words:                                                            # Iterate over each word in the selected sample.
        word_surface = word_font.render(word, True, WHITE)                        #render word on the surface with the specified font
        objWidth, objHeight = word_surface.get_size()                             # Get the width and height of the rendered word surface.
        x, y = getRandomOffCameraPos(camerax, cameray, objWidth, objHeight)       # Get random off-camera position coordinates for the word object.
        word_obj = {
            'surface': pygame.transform.scale(word_surface, (objWidth, objHeight)), #Scale the word surface to match the object width and height.
            'facing' : LEFT,                                                      # Set the initial facing direction of the word object
            'size': font_size,                                                    #set the font size of the word object 
            'width': objWidth,                                                    #set the width of the word object
            'height': objHeight,                                                  #set the height of the word object
            'x': x,                                                               #set initial x-coordinate of the word object
            'y': y,                                                               #set initial y-coordinate of the word object
            'movex': getRandomVelocity(),                                         #set initial x-velocity of the word object
            'movey': getRandomVelocity(),                                         #set the initial y-velocity of the word object
            'health': MAXHEALTH,                                                  #set initial health of the player
            'type': wordtype                                                      #assign the type of the word object
        }
        word_Objs.append(word_obj)                                                # Add the created word object to the list of word objects.                                                                                            
    return word_Objs                                                              #return the list of the created word object

# Check object position and execute main function if this script is run directly.
def isOutsideActiveArea(camerax, cameray, obj):                                   # Define a function to check if an object is outside the active area of the game window.
    boundsRect = pygame.Rect(camerax, cameray, WINWIDTH + HALF_WINWIDTH, WINHEIGHT + HALF_WINHEIGHT) #Create bounding rectangle for active window area.
    objRect = pygame.Rect(obj['x'], obj['y'], obj['width'], obj['height'])        # Create rectangle for object's position and size.
    return not boundsRect.colliderect(objRect)                                    # return false if camerax and cameray exceed half-window length beyond the window edge 

# Check if this script is being run directly as the main program.
if __name__ == '__main__':
    main()
    
STAR_WORDS.py
Displaying STAR_WORDS.py.