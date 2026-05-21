"""Generate the four dark-theme infographics for the institutional-position article.

Bloomberg-terminal aesthetic. Saves PNGs alongside the Substack draft.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle

BG = "#0a0a0a"
PANEL = "#15171c"
WHITE = "#e8e8e8"
DIM = "#8b949e"
GREEN = "#00ff41"
GOLD = "#f0b400"
RED = "#e53935"
MONO = "monospace"

OUT = "docs/substack/drafts"


def new_ax(w, h):
    fig, ax = plt.subplots(figsize=(w, h), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    return fig, ax


def hud_grid(ax, w, h):
    for gx in range(1, int(w)):
        ax.axvline(gx, color="#ffffff", alpha=0.02, lw=0.6)
    for gy in range(1, int(h)):
        ax.axhline(gy, color="#ffffff", alpha=0.02, lw=0.6)


def save(fig, name):
    path = f"{OUT}/{name}"
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(path, dpi=100, facecolor=BG)
    plt.close(fig)
    print(f"saved {path}")


# ---------------------------------------------------------------- HERO
def hero():
    w, h = 12.0, 6.3
    fig, ax = new_ax(w, h)
    hud_grid(ax, w, h)

    ax.text(w / 2, 5.62, "M O M E N T U M   P H I N A N C E", ha="center",
            va="center", color=GOLD, fontsize=14, family=MONO, fontweight="bold")

    ax.text(w / 2, 4.15, "THE FOUR-LAYER POSITION", ha="center", va="center",
            color=WHITE, fontsize=43, family=MONO, fontweight="bold")
    ax.plot([2.7, 9.3], [3.42, 3.42], color=GREEN, lw=2.5)
    ax.text(w / 2, 2.92, "HOW INSTITUTIONS ACTUALLY OWN A STOCK", ha="center",
            va="center", color=GREEN, fontsize=17, family=MONO, fontweight="bold")

    pills = [("CORE", WHITE), ("INCOME", GOLD),
             ("ACCUMULATE", GREEN), ("LEVERAGE", RED)]
    pw, gap = 2.45, 0.42
    start = (w - (4 * pw + 3 * gap)) / 2
    for i, (label, color) in enumerate(pills):
        cx = start + pw / 2 + i * (pw + gap)
        box = FancyBboxPatch((cx - pw / 2, 1.55), pw, 0.78,
                             boxstyle="round,pad=0.0,rounding_size=0.14",
                             facecolor=PANEL, edgecolor=color, linewidth=2)
        ax.add_patch(box)
        ax.text(cx, 1.94, label, ha="center", va="center", color=color,
                fontsize=14, family=MONO, fontweight="bold")
        ax.text(cx, 1.18, f"LAYER {i + 1}", ha="center", va="center",
                color=DIM, fontsize=10, family=MONO)

    ax.text(w / 2, 0.55, "Retail buys shares.  Institutions build positions.",
            ha="center", va="center", color=DIM, fontsize=15, family=MONO,
            style="italic")
    save(fig, "institutional_hero.png")


# ------------------------------------------------------------ LAYERS
def layers():
    w, h = 12.0, 9.6
    fig, ax = new_ax(w, h)
    hud_grid(ax, w, h)

    ax.text(w / 2, 9.05, "THE FOUR-LAYER POSITION", ha="center", va="center",
            color=WHITE, fontsize=30, family=MONO, fontweight="bold")
    ax.text(w / 2, 8.5, "every layer has one job // build it from the ground up",
            ha="center", va="center", color=DIM, fontsize=13, family=MONO)

    # bottom -> top
    rows = [
        ("01", "THE CORE", "Common shares, bought in tranches",
         "JOB:  foundation exposure + dividend income", "YEARS", WHITE),
        ("02", "INCOME OVERLAY", "Laddered covered calls",
         "JOB:  harvest premium, grind cost basis down", "WEEKS", GOLD),
        ("03", "ACCUMULATION LEG", "Cash-secured put below price",
         "JOB:  get paid to buy the dip in advance", "WEEKS", GREEN),
        ("04", "LEVERAGE SLEEVE", "LEAPS calls // near + far OTM",
         "JOB:  capital-efficient upside convexity", "1-2 YRS", RED),
    ]
    bx, bw = 0.7, 10.6
    bh, gap = 1.62, 0.26
    y0 = 0.85
    for i, (num, name, instrument, job, horizon, color) in enumerate(rows):
        y = y0 + i * (bh + gap)
        # glow
        for g in range(1, 4):
            ax.add_patch(Rectangle((bx - 0.03 * g, y - 0.03 * g),
                         bw + 0.06 * g, bh + 0.06 * g, fill=False,
                         edgecolor=color, alpha=0.05, lw=1))
        ax.add_patch(Rectangle((bx, y), bw, bh, facecolor=PANEL,
                     edgecolor=color, lw=2))
        # left accent spine
        ax.add_patch(Rectangle((bx, y), 0.16, bh, facecolor=color))
        # ghost number
        ax.text(bx + 1.05, y + bh / 2, num, ha="center", va="center",
                color=color, fontsize=40, family=MONO, fontweight="bold",
                alpha=0.28)
        # text block
        tx = bx + 2.25
        ax.text(tx, y + bh - 0.46, name, ha="left", va="center", color=color,
                fontsize=20, family=MONO, fontweight="bold")
        ax.text(tx, y + bh - 0.92, instrument, ha="left", va="center",
                color=WHITE, fontsize=13, family=MONO)
        ax.text(tx, y + 0.38, job, ha="left", va="center", color=DIM,
                fontsize=12, family=MONO)
        # horizon badge (right)
        ax.text(bx + bw - 0.45, y + bh - 0.5, "HORIZON", ha="right",
                va="center", color=DIM, fontsize=10, family=MONO)
        ax.text(bx + bw - 0.45, y + bh - 0.95, horizon, ha="right",
                va="center", color=color, fontsize=18, family=MONO,
                fontweight="bold")

    # ground line
    ax.plot([bx, bx + bw], [y0 - 0.16, y0 - 0.16], color=DIM, lw=2)
    ax.text(bx + bw / 2, y0 - 0.42, "FOUNDATION FIRST  //  PENTHOUSE LAST",
            ha="center", va="center", color=DIM, fontsize=11, family=MONO)
    save(fig, "institutional_layers.png")


# ------------------------------------------------------------ LADDER
def ladder():
    w, h = 12.0, 6.6
    fig, ax = new_ax(w, h)
    hud_grid(ax, w, h)

    ax.text(w / 2, 6.05, "LADDER THE EXPIRATIONS", ha="center", va="center",
            color=WHITE, fontsize=27, family=MONO, fontweight="bold")
    ax.text(w / 2, 5.55, "stagger every leg across the calendar // never all-in "
            "on one date", ha="center", va="center", color=DIM, fontsize=12,
            family=MONO)

    base = 1.45
    x0, x1 = 1.0, 11.2
    ax.annotate("", xy=(x1, base), xytext=(x0, base),
                arrowprops=dict(arrowstyle="-|>", color=DIM, lw=2))

    ticks = [(1.0, "NOW"), (2.2, "1 WK"), (3.3, "2 WK"), (4.6, "1 MO"),
             (6.0, "3 MO"), (8.2, "1 YR"), (10.5, "2 YR")]
    for tx, label in ticks:
        ax.plot([tx, tx], [base - 0.12, base + 0.12], color=DIM, lw=1.5)
        ax.text(tx, base - 0.38, label, ha="center", va="center", color=DIM,
                fontsize=11, family=MONO)

    # (x, stem height, color, label)
    legs = [
        (2.2, 2.55, GOLD, "COVERED CALL"),
        (3.3, 1.35, GOLD, "COVERED CALL x2"),
        (4.6, 2.55, GOLD, "COVERED CALL"),
        (5.3, 3.45, GREEN, "CASH-SECURED PUT"),
        (8.2, 1.85, RED, "LEAPS CALL"),
        (10.5, 1.85, RED, "LEAPS CALL x2"),
    ]
    for x, sh, color, label in legs:
        top = base + sh
        ax.plot([x, x], [base, top], color=color, lw=2, alpha=0.85)
        ax.add_patch(Circle((x, base), 0.07, color=color, zorder=5))
        ax.add_patch(Circle((x, top), 0.13, color=color, zorder=5))
        ax.add_patch(Circle((x, top), 0.13, fill=False, edgecolor=color,
                     lw=4, alpha=0.25, zorder=4))
        ax.text(x, top + 0.3, label, ha="center", va="center", color=color,
                fontsize=11, family=MONO, fontweight="bold")

    # legend
    leg = [(GOLD, "INCOME // covered calls", 1.35),
           (GREEN, "ACCUMULATION // cash-secured put", 4.95),
           (RED, "LEVERAGE // LEAPS calls", 9.25)]
    for color, text, lx in leg:
        ax.add_patch(Circle((lx, 0.5), 0.1, color=color))
        ax.text(lx + 0.27, 0.5, text, ha="left", va="center", color=DIM,
                fontsize=10, family=MONO)
    save(fig, "institutional_ladder.png")


# --------------------------------------------------------- BLUEPRINT
def blueprint():
    w, h = 12.0, 7.7
    fig, ax = new_ax(w, h)
    hud_grid(ax, w, h)

    ax.text(w / 2, 7.15, "THE POSITION BLUEPRINT", ha="center", va="center",
            color=WHITE, fontsize=28, family=MONO, fontweight="bold")
    ax.text(w / 2, 6.65, "size the whole thing first // every layer is a slice "
            "of one number", ha="center", va="center", color=DIM, fontsize=12,
            family=MONO)

    # capital allocation stacked bar
    ax.text(0.8, 5.95, "CAPITAL ALLOCATION", ha="left", va="center",
            color=WHITE, fontsize=14, family=MONO, fontweight="bold")
    bx, bw, by, bh = 0.8, 10.4, 5.0, 0.7
    segs = [("THE CORE", 0.65, WHITE), ("ACCUMULATION RESERVE", 0.22, GREEN),
            ("LEVERAGE SLEEVE", 0.13, RED)]
    cx = bx
    for name, frac, color in segs:
        sw = bw * frac
        ax.add_patch(Rectangle((cx, by), sw, bh, facecolor=color, alpha=0.85))
        ax.text(cx + sw / 2, by + bh / 2, f"{int(frac * 100)}%", ha="center",
                va="center", color=BG, fontsize=15, family=MONO,
                fontweight="bold")
        ax.text(cx + sw / 2, by - 0.32, name, ha="center", va="center",
                color=color, fontsize=9.5, family=MONO, fontweight="bold")
        cx += sw

    # worked example cards
    ax.text(0.8, 3.95, "WORKED EXAMPLE  //  ONE $5 GOLD MINER", ha="left",
            va="center", color=GOLD, fontsize=14, family=MONO,
            fontweight="bold")
    cards = [
        ("CORE", "800 shares", "the foundation", WHITE),
        ("INCOME", "4 covered calls", "3 laddered expiries", GOLD),
        ("ACCUMULATE", "1 cash-secured put", "a notch below price", GREEN),
        ("LEVERAGE", "3 LEAPS calls", "dated out to 2028", RED),
    ]
    cw, cgap = 2.62, 0.31
    cstart = (w - (4 * cw + 3 * cgap)) / 2
    cy, ch = 1.05, 2.45
    for i, (tag, big, sub, color) in enumerate(cards):
        x = cstart + i * (cw + cgap)
        ax.add_patch(Rectangle((x, cy), cw, ch, facecolor=PANEL,
                     edgecolor=color, lw=2))
        ax.add_patch(Rectangle((x, cy + ch - 0.12), cw, 0.12, facecolor=color))
        ax.text(x + cw / 2, cy + ch - 0.55, tag, ha="center", va="center",
                color=color, fontsize=13, family=MONO, fontweight="bold")
        ax.text(x + cw / 2, cy + ch - 1.18, big, ha="center", va="center",
                color=WHITE, fontsize=15, family=MONO, fontweight="bold")
        ax.text(x + cw / 2, cy + 0.62, sub, ha="center", va="center",
                color=DIM, fontsize=10.5, family=MONO)

    ax.text(w / 2, 0.5, "8 LINE ITEMS  //  1 TICKER  //  EVERY LEG HAS A JOB",
            ha="center", va="center", color=GREEN, fontsize=12, family=MONO,
            fontweight="bold")
    save(fig, "institutional_blueprint.png")


if __name__ == "__main__":
    hero()
    layers()
    ladder()
    blueprint()
    print("done")
