# BCOG200_project
Repository for my BCOG 200 final project

# Installation

1. Create and activate a Python virtual environment (recommended):
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install the project in editable mode:
   ```sh
   pip install -e .
   ```

3. Run the program:
   ```sh
   python -m zooma
   ```

# Instructions

Work in progress.  Draw a path for the zooma balls to follow.  Still to be done, shooting balls into chain, splitting chain, scoring, etc..

## Controls

- **p**: Toggle draw mode to draw a path with your mouse.
- **a**: Append a new ball to the chain at the mouse position.
- **space**: Pause or resume the game.
- **esc**: Quit/close the game.


# Project Check-In 4/21/25
Most recently, I created ball_game.py which is a game that spawns target balls and you shoot at them by clicking the mouse which creates a ball at the location of the mouse, moving upwards. I did some work on collisions and scores, so I have a little bit of a better idea of how different parts of a pygame program work together. I used copilot to incrementally build ball_game.py and understand each step of the process.

test.py is an exploratory program created by my dad who is tutoring me throughout the project.

# Project Check-In 4/6/25
I've switched my project to making a game inspired by PopCap's Zuma game. As of 4/6/25 this week I spent time looking at the details of the game and figuring out what the mechanics are. Then I discussed which mechanics are integral to the game, and which ones I can look at later on. 


# ZUMA BCOG
Complex ball movement
- balls slow down after being moved backwards
- If any gap has the same color on either side, the line is pulled together
- After balls are moved back, movement starts slowly and then speeds up
- Adding a ball always pushes the line forward


Ball assets static vs animated?

Ball collisions
- Balls only land in line if they hit another ball
- how to detect collisions e.g. which side should the ball land on
- how to delineate prospective place in line based on angle
- If a ball doesnt hit another ball, it goes off screen and **disappears** (important so as to not affect runtime)

Chain generation
- Line is made of segments of varying lengths with random colors. Difficulty depends on segment lengths?
- Balls stop getting added once certain score is reached
- score is unnecessary, chain should be a fixed length for now

Shot generation
- Press space to swap to secondary ball
- Next ball is randomized based on colors currently on screen
- is it easier to have the balls swap colors when they swap?
	e.g. shot ball gets up next color, up next color becomes shot ball color


Score stuff and extras
- Combos push the line backwards
- Powerups such as slow, explosion, reverse, etc.
- Gap bonus - shoot between gaps for more points, smaller gaps are more points



# Investigatory Projects

✅ Render a game window in 2D perspective. 1hr

✅ Render a sphere. 10m

✅ Make sphere into an object with physics, have it move, maybe respond to keyboard input.  (Flush out the game loop, input process, decision making, render)

✅ Have two spheres and when one collides with another, disappear the hit sphere.

✅ What does pygame look like and what does it provide for us.

Next Set of work is how to make the game….

Parts of the game design (IN CODE)

- What is a ball object?
- How to represent an ordered list of balls?  (Perhaps a linked list?  Perhaps a list)
- Animating a [E] chain of balls… how do we ripple physics from ball to ball.
- [E] Shootable ball and [E?] on deck ball…
- Ball generator (routine)
- What does the game board look like in code…?
    - How do we model the path?  List of points?  Splines?
    - Where is the shooter?  Point?  Sphere?  Where is the fire location and how does it rotate with shooter.
    - [E] Terminal point on path?  Is this entity?
    - Secondary concerns..
        - Score board display
        - Next ball display
        - Other visual game state? Level number etc..
    - Game termination conditions…. Progress bar?
- Controlling Logic
    - Determining if a color is eliminated? Get rid of up next.
    - Why do balls move… how are they pushed?
    - How are gaps handled..
    - Collision types
        - With terminal ball ends game
        - Chain balls?  Connect chains?
        - With shooter ball?
            - Determine insertion point
            - Walk the chain and determine effect?  Is match? Is Insert?  Is cluster…
            - Conceptually leave room for larger effects?
    - Did ball exit the screen….

Future parts
- Sound design
- Art Design?
- Sound Design
- Art Design
    - Balls with cool skins
    - Game board backgrounds..
    - Partical effects..
- Explosive balls, power ups..
 

MVC - Model , View, Controller?  
Model - is the data that holds the object state
View - how does the user perceive that object?
Controller - decides what do things do?

Ball
	COLOR
	position
	speed
	vector
	
Shot ball
	color
	SPEED
	vector
	
Frog
	POSITION
	rotation
	shot ball
	up next color



Five maps

colors: red blue green yellow (purple) (white)

Add to list and pop from list

If no ball behind, bring this ball up to speed and adjust others 

Test Change
