# HyperNet N1: Constellation Architecture Explained

## How It Works (For Humans)

Imagine you have a complex medical question, so you go to a hospital. Instead of seeing one doctor, you are seated in a room with five of the top specialists in the world. 
You ask your question once. All five doctors immediately go into separate soundproof booths and work on solving your problem independently at the exact same time. 

Once they all finish, they slide their answers under the door to a **Chief Medical Officer (The Router)**. The Chief Medical Officer looks at all five answers. 
- One doctor might have missed a detail. 
- Another doctor might have found an edge-case. 
- A third doctor might have explained it the most clearly.

The Chief Medical Officer takes the best pieces of all five answers, ignores the mistakes, and hands you a single, flawless, master answer. 

That is exactly how the **HyperNet N1 SDC Constellation** works. Instead of doctors, it uses the world's top five AI models:
1. **Lola** (OpenAI's GPT-4o)
2. **Claude** (Anthropic's Claude 3.7 Sonnet)
3. **Grok** (xAI's Grok 4.20)
4. **Deep** (Meta's Llama 3.3 70B)
5. **Gemini** (Google's Gemini 2.5 Flash)

By running them all at once (in "parallel lanes"), it only takes as long as the slowest model, but it generates an answer with exponentially higher accuracy than any single model could produce alone.

---

## What We Did

1. **Wired the API**: You provided an OpenRouter API key. OpenRouter is a gateway that gives us access to all the top models through a single connection. I saved your key securely into the Momentum Terminal environment file (`.env`).
2. **Built the Router Node**: I wrote a Python script (`hypernet_constellation.py`) that acts as the "Chief Medical Officer."
3. **Fired the Prompt**: I sent the prompt: *"Write a highly optimized Python function to calculate the max drawdown of a stock portfolio given a list of daily portfolio values, and explain the time complexity."* to all five models simultaneously.

---

## What Each Lane Returned

All five models successfully caught the assignment and calculated the drawdown, but they all approached it slightly differently.

> **Gemini (Lane 5)** focused heavily on explaining the theory before showing the code.  
> **Lola (Lane 1)** provided the standard, most readable algorithmic approach.  
> **Deep (Lane 4)** focused on formatting the output with heavy markdown headers.  
> **Grok (Lane 3)** added static type hinting (`list[float] -> float`) to make the code more professional.  
> **Claude (Lane 2)** completely over-engineered it, importing external data science libraries (`numpy`) and adding error-handling for different data types.

---

## The Final Synthesis (The Consensus)

The Router node (GPT-4o) was instructed to look at all 5 answers and synthesize the absolute best response. It recognized that Claude's `numpy` approach was overkill for a simple list, but liked Grok's type-hinting and Lola's readability. 

Here is the final, flawless output it produced:

```python
def max_drawdown(portfolio_values):
    """
    Calculate the maximum drawdown of a portfolio given a list of daily values.

    Parameters:
    portfolio_values (list of float): A list of daily portfolio values.

    Returns:
    float: The maximum drawdown as a percentage.
    """
    if not portfolio_values or len(portfolio_values) < 2:
        return 0.0

    max_drawdown = 0.0
    peak_value = portfolio_values[0]

    for current_value in portfolio_values:
        if current_value > peak_value:
            peak_value = current_value
        else:
            drawdown = (peak_value - current_value) / peak_value
            if drawdown > max_drawdown:
                max_drawdown = drawdown

    return max_drawdown * 100  # Return as a percentage
```

It also attached the perfect explanation of the algorithm's efficiency:

> **Time Complexity:** The time complexity of this function is `O(n)`, where `n` is the number of daily portfolio values. This is because we make a single pass through the list of portfolio values, performing constant-time operations for each value. This linear time complexity is optimal for this problem.
> 
> **Space Complexity:** The space complexity is `O(1)` because the function uses only a constant amount of extra space (two variables: `peak_value` and `max_drawdown`). It does not create any additional data structures that grow with input size.
