import random
import math
import matplotlib.pyplot as plt



def monty_hall(switch=False):
    doors = [1, 2, 3]
    car = random.choice(doors)
    choice = random.choice(doors)

    # Host opens a door that:
    #  1. Is not the player's choice
    #  2. Does not contain the car
    remaining = [d for d in doors if d != choice and d != car]
    host_opens = random.choice(remaining)

    # If switching, player picks the last unopened door
    if switch:
        final_choice = [d for d in doors if d not in (choice, host_opens)][0]
    else:
        final_choice = choice

    return final_choice == car


def monte_carlo_simulation(n=100000):
    switch_wins = 0
    stay_wins = 0
    for _ in range(n):
        if monty_hall(switch=True):
            switch_wins += 1
        if monty_hall(switch=False):
            stay_wins += 1
    return switch_wins/n, stay_wins/n


def visualize_results(wins_switch: float, wins_no_switch: float, n: int) -> None:
  plt.figure(figsize=(10, 6))
  plt.bar(['Switch', 'No Switch'], [wins_switch, wins_no_switch])
  plt.xlabel('Strategy')
  plt.ylabel('Win Rate')
  plt.title(f'Monty Hall Problem (Trials={n})')
  plt.show()

if __name__ == "__main__":
  n = 1000
  wins_switch, wins_no_switch = monte_carlo_simulation(n)
  print(f"Wins with switch: {wins_switch}")
  print(f"Wins without switch: {wins_no_switch}")
  visualize_results(wins_switch, wins_no_switch,n)  

