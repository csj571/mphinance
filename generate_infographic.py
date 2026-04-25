import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patheffects import withStroke

# Setup figure
fig, ax = plt.subplots(figsize=(14, 18), facecolor='#0d1117')
ax.set_facecolor('#0d1117')
ax.axis('off')

# Title
plt.text(0.5, 0.96, "THE 35-STOCK PROTOCOL", fontsize=36, color='#ffffff', ha='center', fontweight='bold', alpha=0.9, fontfamily='monospace')
plt.text(0.5, 0.93, "ASYMMETRICAL MATH | 60/40 CORE-SATELLITE ARCHITECTURE", fontsize=16, color='#00ff41', ha='center', fontweight='bold', fontfamily='monospace', alpha=0.8)

def draw_box(x, y, w, h, title, tickers, color, title_color):
    # Glow effect
    for i in range(1, 4):
        rect_glow = patches.Rectangle((x-0.002*i, y-0.002*i), w+0.004*i, h+0.004*i, linewidth=1, edgecolor=color, facecolor='none', alpha=0.1)
        ax.add_patch(rect_glow)
    
    # Main box
    rect = patches.Rectangle((x, y), w, h, linewidth=2, edgecolor=color, facecolor='#161b22', alpha=0.9)
    ax.add_patch(rect)
    
    # Title
    plt.text(x + w/2, y + h - 0.03, title, fontsize=16, color=title_color, ha='center', fontweight='bold', fontfamily='monospace')
    
    # Tickers
    for i, ticker in enumerate(tickers):
        col = i % 2
        row = i // 2
        px = x + 0.1 + col * (w/2)
        py = y + h - 0.08 - row * 0.04
        plt.text(px, py, ticker, fontsize=14, color='#c9d1d9', ha='left', va='center', fontfamily='monospace', fontweight='bold')

# Core 15 (60%)
plt.text(0.5, 0.88, "THE STARTING 15 (4% ALLOCATION EACH)", fontsize=22, color='#ffffff', ha='center', fontweight='bold', fontfamily='monospace')

draw_box(0.1, 0.73, 0.38, 0.13, "MEGA-CAP TECH", ["NVDA", "AVGO", "MU", "TSM", "GOOGL"], '#f0b400', '#f0b400')
draw_box(0.52, 0.73, 0.38, 0.13, "DISRUPTION / VALUE", ["TER", "RDDT", "HIMS", "COST"], '#00ff41', '#00ff41')
draw_box(0.1, 0.58, 0.8, 0.13, "HIGH-BETA VOLATILITY (THE WHEEL)", ["GLXY", "ASTS", "RKLB", "ONDS", "NBIS", "UAMY"], '#e53935', '#e53935')

# Satellites 20 (40%)
plt.text(0.5, 0.53, "THE SATELLITE BENCH (2% ALLOCATION EACH)", fontsize=22, color='#ffffff', ha='center', fontweight='bold', fontfamily='monospace')

draw_box(0.1, 0.38, 0.38, 0.13, "SPACE & DEFENSE", ["LUNR", "UMAC", "BBAI", "PL", "KTOS"], '#58a6ff', '#58a6ff')
draw_box(0.52, 0.38, 0.38, 0.13, "INFRASTRUCTURE & ENERGY", ["SMR", "UEC", "AMPX", "OUST", "PTRN"], '#ff7b72', '#ff7b72')
draw_box(0.1, 0.23, 0.38, 0.13, "RETAIL / MOAT", ["TJX", "WMT", "BRK-B", "MLI", "BULL"], '#3fb950', '#3fb950')
draw_box(0.52, 0.23, 0.38, 0.13, "TECH / HEALTH / EV", ["ACHR", "CLS", "TSLA", "UBER", "LLY"], '#d2a8ff', '#d2a8ff')

# Footer
plt.text(0.5, 0.15, "RULE 1: A satellite must gain 40% AND a core must drop 30% to trigger a promotion.", fontsize=12, color='#8b949e', ha='center', fontfamily='monospace', style='italic')
plt.text(0.5, 0.12, "NOT FINANCIAL ADVICE. PURE MOMENTUM MATH.", fontsize=14, color='#e53935', ha='center', fontweight='bold', fontfamily='monospace')

# Add subtle grid lines for HUD effect
for y in [0.2, 0.4, 0.6, 0.8]:
    plt.axhline(y=y, color='#ffffff', alpha=0.02, linestyle='--')
for x in [0.25, 0.5, 0.75]:
    plt.axvline(x=x, color='#ffffff', alpha=0.02, linestyle='--')

plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
plt.savefig('docs/substack/musings/35_stock_protocol_infographic.png', dpi=300, bbox_inches='tight', facecolor='#0d1117')
print("Infographic saved.")
