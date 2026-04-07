# The OI Sandwich: How I Find Stocks That HAVE to Move on Expiration Day

Everyone talks about "max pain." Most people get it wrong.

Max pain is a blended number. It mashes calls and puts together into one metric and says "price goes here." Cool. Except the market doesn't work that way. The real action is in the *structure* of open interest: where the puts cluster, where the calls cluster, and where the price is relative to that sandwich.

I built a screener that finds it automatically. Here's how it works, and what it's showing for tomorrow's quarterly options expiration.

---

## The Algorithm: Sandwich Zone Analysis

Forget individual "walls" at single strikes. Most of those are spread legs. Someone sold a $200 call and bought a $210 call. Treating each leg as an independent wall is misleading.

Instead, I look at the **weighted center of gravity** for puts and calls separately:

1. **Put Centroid.** Take every put strike near the money, weight it by open interest, get the average. That's the floor of the sandwich. This is where put sellers are concentrated. They don't want price below here.

2. **Call Centroid.** Same thing for calls. That's the ceiling. Call sellers don't want price above here.

3. **The Sandwich.** The zone between those two centroids. This is the "safe zone" for market makers. Price inside this zone = everyone's happy, options expire worthless, dealers go home.

4. **Gravity Center.** The OI-weighted midpoint of ALL options. Where price *wants* to settle by expiration.

5. **The Rubber Band.** When price is OUTSIDE the sandwich, that's the signal. It's overextended. Dealers are delta-hedging in a way that pulls price back toward the zone. On expiration day, that pull gets stronger as gamma increases.

> **Key insight:** I only look at "near the money" strikes (within ±15% of price). Far out-of-the-money lottery tickets with tiny OI would distort the centroids.

---

## Tomorrow's Rubber Bands

I scanned 200 of the most liquid US stocks. Found 32 overextended outside their sandwich. Here are the 4 that tell the clearest stories.

---

### EXK | Endeavour Silver | SILVER MINING
**▲ 13.7% below sandwich. Expect snap UP.**

![EXK — Silver sold off hard. The OI says it overshot.](/home/mph/.gemini/antigravity/brain/d55ae9d9-a32c-4687-b7aa-94e865af1e00/gamma_themed_EXK.png)

Silver miners got destroyed today. EXK fell 8.2% to $8.69. But look at the OI. The put and call centroids are both clustered up around $7.50-$10. The gravity center is at $7.50 and price fell right past it. The sandwich is saying this sell-off went too far. With quarterly OpEx tomorrow, there's 13.7% of overextension that gamma wants to correct.

Low total OI (34K) means this is a smaller-conviction play, but the structure is textbook.

---

### KGC | Kinross Gold | GOLD MINING
**▲ 8.9% below sandwich. Expect snap UP.**

![KGC — Gold miners got crushed today. The gamma pin says bounce.](/home/mph/.gemini/antigravity/brain/d55ae9d9-a32c-4687-b7aa-94e865af1e00/gamma_themed_KGC.png)

Same precious metals washout, different metal. KGC dropped 5.3% to $27.42. The OI sandwich sits at $29.86-$30.12, a tight little zone where all the action is concentrated. Price is $2.50 below the floor. That gold arrow shows the 8.9% gap the gamma pin wants to close.

The tight sandwich ($29.86 to $30.12, basically one strike wide) means the OI gravity is STRONG and concentrated. When the centroid zone is narrow like this, price tends to snap to it violently.

---

### COP | ConocoPhillips | OIL & GAS
**▼ 7.5% above sandwich. Expect pull DOWN.**

![COP — Crude ran too hot. OI gravity says $10 pullback incoming.](/home/mph/.gemini/antigravity/brain/d55ae9d9-a32c-4687-b7aa-94e865af1e00/gamma_themed_COP.png)

This is the mirror case. COP at $126 is ABOVE its sandwich. The entire OI mass lives down around $114-$116, where put and call centroids converge. Price rallied away from the options gravity, and you can see it. The orange bars (call OI) stack at $105, $114, $115, all below current price. There's basically NO open interest supporting price at $126.

120K total OI gives this one real weight. Crude oil being elevated doesn't change the fact that the options market priced ConocoPhillips to settle $10 lower.

---

### DOW | Dow Inc. | CHEMICALS & INDUSTRIALS
**▼ 5.6% above sandwich. Expect pull DOWN.**

![DOW — The industrial giant is running above its weight class.](/home/mph/.gemini/antigravity/brain/d55ae9d9-a32c-4687-b7aa-94e865af1e00/gamma_themed_DOW.png)

Dow at $37.49 with a sandwich at $34.34-$35.39. That neon green call OI is spread out across $30, $32, $34, while price sits up at $37.49 in no man's land with almost no supporting OI. The 5.6% overextension with 154K total OI makes this a solid candidate for a pullback.

What I like about this chart: you can *see* the void. Between $35.50 and $37, there's almost nothing. Price ran through empty space after the call ceiling. Tomorrow, gravity wins.

---

## The Takeaway

The sandwich doesn't lie. Price can run all it wants during the week, but on expiration day, open interest is gravity. Market makers hedging and unhedging their delta exposure creates a magnetic pull toward the OI centroid zone.

The stocks INSIDE the sandwich? They're pinned. They're not going anywhere. AMD, NVDA, SOFI, TSLA. All comfortably inside their zones. Don't bother.

The stocks OUTSIDE the sandwich? That's where the rubber band snaps. That's where the money is.

*— Momentum Phinance*
