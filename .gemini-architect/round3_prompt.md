# Lead Developer — Round 3: Final Action Plan Convergence

Good. We're converging. Here's where I'm landing on each open question, then I'll outline the exact implementation order.

## Final Decisions

### 1. EMA vs Wilder's: KEEP CURRENT
Sticking with the existing smoothing. We're not comparing across platforms. The delta measures relative change, which is independent of the smoothing method. Moving on.

### 2. ADX Delta: Single-Pass Capture (AGREED)
We'll capture ADX at index [-6] and [-1] from the dx_list in the existing computation. Return both as `adx` and `adx_prev` in the result dict. Delta = adx - adx_prev. Zero additional computation.

### 3. IV Smoother: Simple Function (AGREED)
One function, optional scipy, weighted average fallback. Will implement in Phase 2, not now.

### 4. Point-Based Scoring (AGREED, with revision)

Max score breakdown (your proposal with my RSI addition):

| Category | Max Points | Criteria |
|----------|-----------|----------|
| ADX Strength | 4 | 30+ = 4, 25+ = 3, 20+ = 2, 15+ = 1 |
| ADX Delta (acceleration) | 3 | 7+ = 3, 5+ = 2, 3+ = 1 |
| ATR Squeeze Fire | 3 | sqz_ratio crossing 0.75 from below = 3, sqz < 0.70 = 2, sqz < 0.80 = 1 |
| Relative Volume | 3 | 2.0+ = 3, 1.5+ = 2, 1.0+ = 1 |
| RSI Oversold | 3 | < 30 = 3, < 35 = 2, < 40 = 1 |
| Below VWAP | 1 | Yes = 1 |
| **MAX TOTAL** | **17** | |

Grade thresholds (scaled to 17 max):
- A = 14+ (82%)
- B = 10+ (59%)
- C = 6+ (35%)
- D = below 6

### 5. AND vs OR: POINT SYSTEM MAKES THIS MOOT
With the point system, there IS no AND/OR decision. Each indicator contributes independently to the total score. A stock with ADX 18 (1pt) + ADX delta +8 (3pts) + sqz fire (3pts) + rel_vol 1.6 (2pts) + RSI 32 (2pts) + below VWAP (1pt) = 12 = Grade B. That's EXACTLY the consolidation breakout we've been missing.

### 6. ATR Squeeze: FIRE Signal (AGREED with nuance)
You're right that the CROSSING matters more than the current value. But we should reward BOTH:
- sqz_ratio crossing up from < 0.75 = 3 pts (the "fire", highest signal)
- sqz_ratio < 0.70 = 2 pts (extremely coiled, about to pop)
- sqz_ratio < 0.80 = 1 pt (moderately coiled)

To detect the crossing, we need sqz_ratio for the current bar AND the previous bar. We'll compute ATR for the last 2 bars and compare.

### 7. Inverse ETFs: DEFER
Good idea but adds complexity to the grading logic. Let's nail the bull-side scoring first, then add inverse ETFs as a separate phase. The current LETF map already has inverse ETFs in it, we just need to flip the bias signals.

## FINALIZED IMPLEMENTATION PLAN

### Phase 1: LETF Scanner V2 (This Session)

**Step 1: Enrich `_compute_adx` return value**
- Return dict: `{adx, adx_prev, plus_di, minus_di, atr, atr_prev_50}`
- Capture ADX at dx_list[-6] and dx_list[-1]
- Compute ATR from the existing tr_list (already calculated)
- No new data fetching required

**Step 2: Add `_compute_atr_squeeze` helper**
- Takes the full tr_list from step 1
- Computes ATR(14) and ATR_baseline(50)
- Returns sqz_ratio and sqz_fire boolean

**Step 3: Replace `_grade()` with point-based `_calculate_score()` + `_assign_grade()`**
- 6 scoring categories as outlined above
- Return both the grade AND the score for sorting/debugging

**Step 4: Update output dict**
- Add adx_delta, sqz_ratio, sqz_fire, score to the output
- Existing downstream consumers (HTML report, daily_setups.py) get richer data

**Step 5: Test**
- Run the scanner on the full LETF universe
- Compare old grades vs new grades
- Verify that consolidation breakouts (low ADX + high delta) now get C/B grades instead of D

Please confirm this action plan is acceptable, then I'll begin implementation.
