# This script is used to train Poker_Bot against an instance of itself

from deuces import Card
from deuces import Deck
from deuces import Evaluator
from Poker_Bot import Game_State
from Poker_Bot import Policy
from Poker_Bot import State_Action_Value_Function
import os
import pickle

# Define bot names and load them if they already exist
# Bot policy will be saved as bot_name.policy
# Bot state action value function will be saved as bot_name.savf
policy_suffix = ".policy"
savf_suffix = ".savf"
obj_path = "obj/"

bot_name_1 = "bot_1"
bot_name_2 = "bot_2"

# Load/create first bot
if os.path.isfile(obj_path + bot_name_1 + policy_suffix) and os.path.isfile(obj_path + bot_name_1 + savf_suffix):
	print("Loading existing data for " + bot_name_1 + "...")
	p1 = Policy.create_from_file(bot_name_1 + policy_suffix)
	print("Loaded " + bot_name_1 + " policy file")
	q1 = State_Action_Value_Function.create_from_file(bot_name_1 + savf_suffix)
	print("Loaded " + bot_name_1 + " state action value function file")
else:
	print("Policy and state action value function files don't exist for " + bot_name_1 + ". Create new ones...")
	p1 = Policy.create_uniform()
	print("New policy function created for " + bot_name_1)
	q1 = State_Action_Value_Function.create_uniform()
	print("New policy function created for " + bot_name_1)

# Load/create second bot
if os.path.isfile(obj_path + bot_name_2 + policy_suffix) and os.path.isfile(obj_path + bot_name_2 + savf_suffix):
	print("Loading existing data for " + bot_name_2 + "...")
	p2 = Policy.create_from_file(bot_name_2 + policy_suffix)
	print("Loaded " + bot_name_2 + " policy file")
	q2 = State_Action_Value_Function.create_from_file(bot_name_2 + savf_suffix)
	print("Loaded " + bot_name_2 + " state action value function file")
else:
	print("Policy and state action value function files don't exist for " + bot_name_2 + ". Create new ones...")
	p2 = Policy.create_uniform()
	print("New policy function created for " + bot_name_2)
	q2 = State_Action_Value_Function.create_uniform()
	print("New policy function created for " + bot_name_2)

# Main training loop
# The program will conduct no_rounds training rounds, and then check if the file "quit" is present in
# the same folder as this script
# Note that bot 1 is treated as "player" and bot 2 is treated as the opponent
gs = Game_State()
learning_rate = 0.05
epsilon = 0.20
player_turn = 0 # Player 1 starts if 0, otherwise player 2 starts

no_training_rounds = 100000
while True:
	for training_round in range(no_training_rounds):
		# Start new round and deal cards
		gs.clear_state()
		deck = Deck()
		gs.set_player_cards(deck.draw(2))
		gs.set_opponent_cards(deck.draw(2))
		gs.set_flop(deck.draw(3))
		pot = 0.0
	
		# Go through betting
		visited_action_states_1 = []
		visited_action_states_2 = []
		intermediate_payoffs_1 = []
		intermediate_payoffs_2 = []
		player_1_fold_f = False # Flag for keeping track of if player 1 has folded
		player_2_fold_f = False # Flag for keeping track of if player 2 has folded
		raise_f = False # Flag for keeping track of if any subsequent "bets" are in fact raises
		while gs.get_possible_actions():
			cs = gs.get_current_state_id()
			if player_turn == 0:
				action = p1.draw_action(cs)
				gs.append_action(action)
				visited_action_states_1.append((cs[0], cs[1], cs[2], cs[3], action))
				if action == 'B' and raise_f:
					pot += 2.0
					intermediate_payoffs_1.append(-2.0)
				elif action == 'B' and not raise_f:
					pot += 1.0
					intermediate_payoffs_1.append(-1.0)
					raise_f = True
				elif action == 'C':
					pot += 1.0
					intermediate_payoffs_1.append(-1.0)
				elif action == 'F':
					player_1_fold_f = True
					intermediate_payoffs_1.append(0.0)
					break
				elif action == 'Ch':
					intermediate_payoffs_1.append(0.0)
				else:
					print('ERROR: No valid action taken by ' + bot_name_1 + '. The taken action is: ' + str(action) + '. Current state is: ' + str(cs))

			else:
				action = p2.draw_action(cs)
				gs.append_action(action)
				visited_action_states_2.append((cs[0], cs[1], cs[2], cs[3], action))
				if action == 'B' and raise_f:
					pot += 2.0
					intermediate_payoffs_2.append(-2.0)
				elif action == 'B' and not raise_f:
					pot += 1.0
					intermediate_payoffs_2.append(-1.0)
					raise_f = True
				elif action == 'C':
					pot += 1.0
					intermediate_payoffs_2.append(-1.0)
				elif action == 'F':
					player_2_fold_f = True
					intermediate_payoffs_2.append(0.0)
					break
				elif action == 'Ch':
					intermediate_payoffs_2.append(0.0)
				else:
					print('ERROR: No valid action taken by ' + bot_name_2 + '. The taken action is: ' + str(action))
			player_turn = (player_turn + 1) % 2

		# Evaluate result
		if player_1_fold_f:
			intermediate_payoffs_2[-1] += pot
		elif player_2_fold_f:
			intermediate_payoffs_1[-1] += pot
		elif gs.is_winner() == 1: # Player 1 wins
			intermediate_payoffs_1[-1] += pot
		elif gs.is_winner() == -1: # Player 2 wins
			intermediate_payoffs_2[-1] += pot
		elif gs.is_winner() == 0: # Draw
			intermediate_payoffs_1[-1] += pot/2.0
			intermediate_payoffs_2[-1] += pot/2.0

		# Update player 1 policy and state action value function
		G = 0.0
		for i, s in reversed(list(enumerate(visited_action_states_1))):
			G += intermediate_payoffs_1[i]
			q1.update(s, G, learning_rate)
			greedy_action = q1.greedy_action(visited_action_states_1[i])
			p1.update(greedy_action, epsilon)
	
		# Update player 2 policy and state action value function
		G = 0.0
		for i, s in reversed(list(enumerate(visited_action_states_2))):
			G += intermediate_payoffs_2[i]
			q2.update(s, G, learning_rate)
			greedy_action = q2.greedy_action(visited_action_states_2[i])
			p2.update(greedy_action, epsilon)
	
		if (training_round % 1000) == 0:
			print("Training round " + str(training_round) + " complete...")
	
	if os.path.isfile("quit"):
		break
# End while

# Save policies and state action value functions to disk
print('Saving policies and state action value functions...')
p1.save_to_file(bot_name_1 + policy_suffix)
q1.save_to_file(bot_name_1 + savf_suffix)
p2.save_to_file(bot_name_2 + policy_suffix)
q2.save_to_file(bot_name_2 + savf_suffix)
print('Policies and state action value functions saved')