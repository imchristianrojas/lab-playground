import random
import math as m
import matplotlib.pyplot as plt
import numpy as np
def generate_random_list(n):
    rand_list = list(range(1, n + 1))
    random.shuffle(rand_list)
    return rand_list


def experiment(rand_list: list[int], cutoff_fraction: float = 1/m.e):
    n = len(rand_list)
    cutoff = int(n * cutoff_fraction)

    # Edge case: very small n
    if cutoff < 1:
        cutoff = 1

    best_so_far = max(rand_list[:cutoff])
    choice_index = None

    for i in range(cutoff, n):
        if rand_list[i] > best_so_far:
            choice_index = i
            break

    if choice_index is None:
        choice_index = n - 1

    choice_value = rand_list[choice_index]
    is_optimal = (choice_value == n)  # because n is the max rank
    is_top_10percent = (choice_value >= (int(n * 0.9)))
    return {
        "is_optimal": is_optimal,
        "choice_index": choice_index,
        "choice_value": choice_value,
        "n": n,
        "cutoff": cutoff,
        "is_top_10percent": is_top_10percent,
    }

def monte_carlo(n: int, cutoff_fraction: float, trials: int):
    successes = 0
    for _ in range(trials):
        rand_list = generate_random_list(n)
        result = experiment(rand_list, cutoff_fraction)
        # if result["is_optimal"]:
        #     successes += 1
        if result["is_top_10percent"]:
            successes += 1
    return successes / trials


def visualize_results(n: int = 100, cutoff_fractions: list = None, trials: int = 1000, 
                      show_optimal: bool = True):
    """
    Visualize secretary problem results by testing different cutoff fractions.
    
    Parameters:
        n: Number of candidates (default: 100)
        cutoff_fractions: List of cutoff fractions to test. If None, uses np.linspace(0.1, 0.5, 20)
        trials: Number of Monte Carlo trials per cutoff fraction (default: 1000)
        show_optimal: Whether to mark the optimal cutoff (1/e) on the plot (default: True)
    """
    if cutoff_fractions is None:
        # Default: test a range of cutoff fractions around 1/e
        cutoff_fractions = np.linspace(0.1, 0.5, 20)
    
    success_rates = []
    for cutoff_frac in cutoff_fractions:
        p_est = monte_carlo(n, cutoff_frac, trials)
        success_rates.append(p_est)
    
    plt.figure(figsize=(10, 6))
    plt.plot(cutoff_fractions, success_rates, 'b-', linewidth=2, marker='o', markersize=4)
    plt.xlabel('Cutoff Fraction', fontsize=12)
    plt.ylabel('Success Rate', fontsize=12)
    plt.title(f'Secretary Problem: Success Rate vs Cutoff Fraction (n={n}, trials={trials})', 
              fontsize=14)
    plt.grid(True, alpha=0.3)
    
    if show_optimal:
        optimal_cutoff = 1/m.e
        optimal_idx = np.argmin(np.abs(np.array(cutoff_fractions) - optimal_cutoff))
        optimal_rate = success_rates[optimal_idx]
        plt.axvline(x=optimal_cutoff, color='r', linestyle='--', linewidth=2, 
                   label=f'Optimal (1/e ≈ {optimal_cutoff:.3f})')
        plt.plot(optimal_cutoff, optimal_rate, 'ro', markersize=10, 
                label=f'Optimal point: {optimal_rate:.4f}')
    
    plt.legend()
    plt.tight_layout()
    plt.show()
    
    return cutoff_fractions, success_rates



if __name__ == "__main__":
    n = 100
    cutoff_fraction = 1/m.e
    #p_est = monte_carlo(n, cutoff_fraction, trials=1000)
    #print(f"n={n}, cutoff={cutoff_fraction:.3f}, estimated success={p_est:.4f}")
    
    # Visualize results
    # Uncomment the line below to see the visualization
    visualize_results(n=100, trials=1000)
