import matplotlib.pyplot as plt
import random
import numpy as np

# Inputs
num_simulations = 1000  # Reduced for plotting speed
max_num_rolls = 1000
starting_balance = 1000
bet = 1

def roll_dice():
    return random.randint(1, 6) == random.randint(1, 6)

fig, ax = plt.subplots(figsize=(10, 6))
end_balances = []

for i in range(num_simulations):
    balance = [starting_balance]
    for _ in range(max_num_rolls):
        if roll_dice():
            balance.append(balance[-1] + 4 * bet)
        else:
            balance.append(balance[-1] - bet)
    
    end_balances.append(balance[-1])
    ax.plot(balance, linewidth=0.5, alpha=0.3) # Alpha makes it look like a "cloud"

plt.title(f"Monte Carlo Dice Game ({num_simulations} simulations)")
plt.xlabel("Roll Number")
plt.ylabel("Balance ($)")
plt.axhline(y=starting_balance, color='r', linestyle='--') # Baseline
plt.show()

print(f"Average Ending Balance: ${np.mean(end_balances):.2f}")
