# BCOG200_project
Repository for my BCOG 200 final project

For my project I want to make the game Mastermind. It seems like a fairly reasonable goal, and I will have to work with tk or something similar to make an interface for it. I'll have to check each color selected to see if it's found in the answer and then I'll need to check if it's in the right position. I might do some UI design.

prospective functions--------------
# generate_code()
randomly generate a secret code of a given length from a given set of colors
will use "random_choice"

# get_player_guess()
prompts player for input and check if it's a valid guess

# evaluate_guess(code, guess)
compare each item in guess and see if it is found in the code and if it is in the same place in the code
return 1-4 pegs of black (correct color and position) or white (correct color and wrong position)

