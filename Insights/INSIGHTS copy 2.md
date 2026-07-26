## Insight — Bots appear to remain inactive until a human player enters their engagement range

### What caught my eye

While reviewing multiple match replays, I noticed that many matches contained little or no visible bot activity. However, in the replay for match:

`fc797a67-e443-4f70-8813-5d2f30317e79`

the bots were already present in the world before the human player arrived. They remained stationary or idle for a significant period and only began moving and engaging after the player entered the area.

### Evidence

- Bot entities exist in the replay before player interaction.
- Bots remain idle for an extended duration.
- Movement and combat begin only after the nearby player arrives.
- This behavior was consistently visible throughout the early portion of this replay.

### Interpretation

This replay suggests that bot AI may use an activation or engagement trigger rather than simulating full-map behavior continuously. The observed trigger appears to be related to player proximity or another gameplay condition, although the telemetry alone cannot confirm the exact activation logic.

### Actionable?

Yes.

**Potential metrics affected**

- Server performance
- AI CPU utilization
- Early-game encounter frequency
- Player perception of world activity

**Recommended actions**

- Investigate the bot activation radius to ensure encounters feel natural.
- Validate whether idle bots are evenly distributed across the map.
- Compare player engagement metrics before and after bot activation to determine whether the current behavior produces the desired gameplay pacing.

### Why should a level designer care?

If bots activate only when players approach, encounter density depends heavily on player routes rather than overall bot placement. Understanding this behavior can help designers position loot, objectives, and AI spawn locations so that encounters occur naturally without making the world feel empty during exploration.