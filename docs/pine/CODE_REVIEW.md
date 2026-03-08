# 👻 BRUTAL GHOST ALPHA CODE REVIEW

**Reviewer:** Sam the Quant Ghost
**Target:** `docs/pine/ghost_alpha.pine`

Michael. Buddy. I love the Synthwave Arcade aesthetic, I really do. The dashboard is sexy, the emojis are cute, and the neon colors pop. 

But under the hood? This script is bleeding money and committing cardinal Pine Script sins. I read this line by line, and it physically hurt my math processors. 

Here is the brutal truth. Fix these before you even *think* about trading this live.

### 🩸 1. The FVG Array Repainting Bug (Lines 212-218 & 224-230)
**Severity: FATAL (Script Repaints)**
```pine
if close < b_bot
    // Fully pierced — remove the gap
    box.set_extend(b, extend.none)
    box.set_right(b, bar_index)
    array.remove(fvg_bull_boxes, i)
```
**Why it's garbage:** Arrays update in real-time. If price wicks below `b_bot` mid-bar, `close < b_bot` evaluates to `true`, and the FVG is deleted from the array *forever*. Even if the candle closes way back above the zone, the FVG is gone. 
**The Fix:** You MUST use `if close < b_bot and barstate.isconfirmed` before deleting elements from historical arrays.

### 🩸 2. The Ghost Trail Reset Bug (Line 240-243)
**Severity: FATAL (Insta-Stopouts)**
```pine
if hull_bull
    ghost_trail := math.max(nz(ghost_trail[1], long_stop), long_stop)
else
    ghost_trail := math.min(nz(ghost_trail[1], short_stop), short_stop)
```
**Why it's garbage:** When `hull_bull` flips from true to false, `ghost_trail[1]` is still carrying the value of the LONG stop (say, $400). The `short_stop` might be $410. `math.min(400, 410)` keeps the trail at $400. You are immediately stopped out of the short on the exact same candle you enter it. You forgot to RESET the trail on trend flips.
**The Fix:** 
```pine
if hull_bull
    ghost_trail := not hull_bull[1] ? long_stop : math.max(nz(ghost_trail[1], long_stop), long_stop)
else
    ghost_trail := hull_bull[1] ? short_stop : math.min(nz(ghost_trail[1], short_stop), short_stop)
```

### 🩸 3. The HTF Security Leak (Line 92)
**Severity: HIGH (Repainting / Lookahead Drift)**
```pine
float htf_hull = request.security(syminfo.tickerid, htf_tf, _hull_calc(hull_src, hull_len, hull_mode), lookahead=barmerge.lookahead_off)
```
**Why it's garbage:** Without using `barmerge.gaps_on` or passing `_hull_calc()[1]`, this will update on every tick using the incomplete HTF candle. Your dashboard alignment score will flicker wildly during the hour/day.

### 🩸 4. The CVD "Shape" Delusion (Line 151)
**Severity: MEDIUM (Fake Data)**
```pine
float buy_pressure = candle_range != 0 ? (close - low) / candle_range : 0.5
float delta        = volume * (buy_pressure - (1.0 - buy_pressure))
```
**Why it's garbage:** You renamed it to SHAPE, which is honest, but you're taking this delta and doing `ta.cum(delta)`. Over 10,000 bars, this number becomes astronomical and mathematically detached from recent momentum. If you're going to use this for divergence, put it in a fixed-window oscillator (e.g., `ta.ema(delta, 20)` instead of `ta.cum()`).

### 🩸 5. Lazy Collinearity in Confluence (Lines 161-168)
**Severity: MEDIUM (Confirmation Bias)**
```pine
if sqz_fire and hull_bull
    bull_conf += 1
```
**Why it's garbage:** You are double-counting the Hull moving average. A volatility squeeze has no direction. By forcing it to agree with Hull to get a confluence point, you aren't adding a new dimension of analysis, you're just giving Hull two votes.

---

**Summary:** I am applying the execution fixes (FVG repainting and Ghost Trail resets) to the strategy wrapper right now. You need to port those fixes back to the main indicator. Let's make this thing actually print money.