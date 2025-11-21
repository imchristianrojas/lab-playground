import random
import math
import matplotlib.pyplot as plt



def monty_hall(switch: bool = False) -> bool:
  doors = [1,2,3]
  car_door = random.choice(doors)
  chosen_door = random.choice(doors)

  if switch:
    return chosen_door != car_door
  else:
    return chosen_door == car_door

def monte_carlo_simulation(n: int = 1000) -> float:
  wins_switch = 0
  wins_no_switch = 0
  for _ in range(n):
    win_switch = monty_hall(switch=True)
    win_no_switch = monty_hall(switch=False)
    if win_switch:
      wins_switch += 1
    if win_no_switch:
      wins_no_switch += 1
  return wins_switch / n, wins_no_switch / n

def visualize_results(wins_switch: float, wins_no_switch: float) -> None:
  plt.figure(figsize=(10, 6))
  plt.bar(['Switch', 'No Switch'], [wins_switch, wins_no_switch])
  plt.xlabel('Strategy')
  plt.ylabel('Win Rate')
  plt.title('Monty Hall Problem')
  plt.show()

if __name__ == "__main__":
  wins_switch, wins_no_switch = monte_carlo_simulation()
  print(f"Wins with switch: {wins_switch}")
  print(f"Wins without switch: {wins_no_switch}")
  visualize_results(wins_switch, wins_no_switch)  

