# propel2excel-points-system
Propel2Excel is a career-focused Discord bot that motivates and rewards student achievement through a points system, real-time activity tracking, moderation tools, and interactive reward-creating an engaging, supportive, and growth-driven online community.

## Cloud Backend Setup

This bot uses the Propel2Excel Cloud Backend. Configure the following in `.env`:

- DISCORD_TOKEN=<discord bot token>
- BACKEND_API_URL=https://propel2excel-points-system.onrender.com
- BOT_SHARED_SECRET=<provided secret>

All points/state are managed by the backend via `POST /api/bot/` and `GET /api/incentives/`.

Key commands:
- !points, !pointshistory, !leaderboard, !rank
- !resume, !event, !resource <desc>, !linkedin
- !shop, !redeem <id>
- !link <code>
- Admin: !addpoints, !removepoints, !suspend, !unsuspend, !clearwarnings, !activitylog
