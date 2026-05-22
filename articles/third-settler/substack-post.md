# Substack post: What I build after the market closes (working draft)

> mphinance.substack.com, in MPH voice. Images in this folder (hero.png, board.png,
> game.png). Covers both repos: Third Settler and freshshot.

---

**Title:** What I build after the market closes

**Subtitle:** Market shut, no meetings, one evening. Out the other side: a board game for my son, and a tool I did not mean to make.

![Third Settler: the player who always shows up](hero.png)

I write here about algorithms that move money. Machines, models, the actual decisions. This one is different. This one is about a night.

The market closes. There are no meetings. It is just an evening, and the question every builder has to answer eventually: what do you actually do with it?

I build things. And tonight I can show you exactly what that looks like, because git keeps the receipts. By the time I shut the laptop there were two new repositories and a couple dozen commits. The first one is stamped 4:29pm. The last is stamped after midnight, and I did not make that one. Stay with me.

It started with my son.

A board game has been sitting on our shelf for weeks. Big box, wooden pieces, hexagons. It wants three or four players. Most nights it is just me and him. The math does not work, so the box stays shut.

A few weeks ago my almost-eight-year-old asked, again, if we could play. I started to say no, again. Then I remembered I have this fancy Claude thing.

So we built the missing player. It is called Third Settler, and the missing player is a Ghost.

You still play on your real board, with your real pieces, at your real table. The app just runs the empty chair. It deals a balanced board, rolls the dice, takes the Ghost's turns, keeps score. The Ghost is a friendly pain in the neck who hogs the good spots and never argues about whose turn it is.

![The app deals a balanced board. The glowing ghosts mark where the Ghost sets up.](board.png)

Third Settler is not a video game. It is the friend who said he would come over and bailed. It is live, it is free, and it will stay free.

Here is where the night forked.

I wanted Third Settler done properly, and done properly meant its homepage needed screenshots. Screenshots that would not quietly go stale the first time I moved a button. So I went to automate them, and I hit a wall that everyone hits and almost nobody bothers to fix.

Automated screenshots commit noise. Every run spits out a slightly different image, the repository history fills with junk, and you stop trusting it. So most people just let their screenshots rot.

That bothered me more than it should have. So I set the board game down for a bit, and I solved that one too.

It is called freshshot. It captures the screenshots, compares them the way an eye would instead of byte by byte, and saves only the ones that actually changed. It is published on npm now. Anyone can install it. Free, open, the works.

Here is the truth. This is just what I do.

One problem, worked honestly, hands you the next one. The board game needed screenshots. The screenshots needed a tool. The tool needed a real home. You pull one thread and three more come loose, and the good nights are the ones where you pull all of them. I like solving problems. I like solving several at once even more.

That commit stamped after midnight, the one I did not make. Third Settler's screenshot automation made that, on its own, while I was asleep. And that same little automation, quietly working at 12:50 in the morning, is the exact thing that became freshshot. I wrote it in the afternoon for a board game. By the next morning it was its own tool, with its own name.

My son does not know what any of that means. He does not know what a service worker is, or that his dad rewrote the dice logic twice. Here is what he saw: he asked for something, and it became real. The Ghost was his idea, more or less. He loves Halloween.

I spent a lot of years taking things apart. Myself, mostly. A night that ends with two things that did not exist that morning beats every kind of night I used to be good at.

So. No paywall on this one. I know. Out of character.

Third Settler is at third-settler.vercel.app. Play it with someone tonight, on a real table, with real pieces.

![A game in progress. You, your kid, and the Ghost.](game.png)

freshshot is on npm and on GitHub. If you build things, it will quietly save you a recurring annoyance. Also free, also yours.

The game night with my son is still coming. But the chair is not empty anymore. And neither was the evening.
