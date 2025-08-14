from discord.ext import commands
import discord
from typing import List
from p2e_backend_client import P2EClient, with_retries
import asyncio
from datetime import datetime


class Points(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client = P2EClient()
        self.processed_messages: set[str] = set()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        
        # Only process commands, don't award points for regular messages
        await self.bot.process_commands(message)

    # Removed automatic reaction points - users only get points from specific commands

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def points(self, ctx: commands.Context):
        data = await with_retries(lambda: self.client.summary(str(ctx.author.id), limit=1))
        total = int(data.get("total_points", 0))
        embed = discord.Embed(title="💰 Points Status", description=f"{ctx.author.mention}'s point information", color=0x00ff00)
        embed.add_field(name="Current Points", value=f"**{total}** points", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def pointshistory(self, ctx: commands.Context):
        data = await with_retries(lambda: self.client.summary(str(ctx.author.id), limit=10))
        rows: List[dict] = data.get("recent_logs", [])
        if not rows:
            return await ctx.send(f"{ctx.author.mention}, you have no point activity yet.")
        embed = discord.Embed(title="📊 Point History", description=f"Last 10 point actions for {ctx.author.mention}", color=0x0099ff)
        for r in rows[:10]:
            ts = r.get("timestamp", "")
            embed.add_field(name=f"{ts[:19]}", value=f"{r.get('action','')} (+{int(r.get('points',0))} pts)", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def resume(self, ctx: commands.Context):
        """Start resume review process - sends DM with form link and instructions"""
        try:
            # Create rich embed for resume review request
            embed = discord.Embed(
                title="📋 Resume Review Request",
                description="I'll help you get a professional resume review!",
                color=0x0099ff
            )
            embed.add_field(
                name="📝 What You'll Need", 
                value="• Your resume (PDF format)\n• Target industry/role\n• Your availability\n• Contact information",
                inline=False
            )
            embed.add_field(
                name="🔗 Form Link",
                value="[Resume Review Form](https://forms.gle/EKHLrqhHwt1bGQjd6)",
                inline=False
            )
            embed.add_field(
                name="⏰ Sessions",
                value="30-minute slots between 9 AM - 5 PM",
                inline=True
            )
            embed.add_field(
                name="📧 Contact",
                value="Email: reviews@propel2excel.com",
                inline=True
            )
            embed.add_field(
                name="💡 Tips for Great Matches",
                value="• Be specific about your target role\n• Choose multiple time slots\n• Have your resume ready as PDF\n• Include relevant experience",
                inline=False
            )
            embed.add_field(
                name="🔄 Next Steps",
                value="1. Fill out the form\n2. Upload your resume\n3. Select your availability\n4. Wait for professional match\n5. Receive calendar invite",
                inline=False
            )
            
            # Send DM to user
            await ctx.author.send(embed=embed)
            
            # Confirm in channel
            await ctx.send(f"✅ {ctx.author.mention} Check your DMs for the resume review form! I've sent you all the details to get started.")
            
            # Record the activity
            await with_retries(lambda: self.client.add_activity(str(ctx.author.id), "resume_review_request", "Resume review process started"))
            
        except discord.Forbidden:
            await ctx.send("❌ I can't send you a DM. Please enable DMs from server members and try again.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def event(self, ctx: commands.Context):
        """Single-message form: collect name, date/time, location; optional photos; award +2 bonus with photos."""
        def author_in_channel(m: discord.Message) -> bool:
            return m.author == ctx.author and m.channel == ctx.channel

        # Show a single form message
        form = (
            "Please reply in ONE message using this template (or type `cancel`):\n\n"
            "Event Name: <text>\n"
            "Event Date & Time (YYYY-MM-DD HH:MM): <text>\n"
            "Event Location: <text>\n\n"
            "Optionally attach 1+ event photos (JPG/PNG/GIF/WebP) to the SAME reply to earn a +2 bonus."
        )
        await ctx.send(form)

        try:
            reply = await self.bot.wait_for("message", timeout=240, check=author_in_channel)
        except asyncio.TimeoutError:
            return await ctx.send("⏰ Timed out. Please run `!event` again.")

        if reply.content.strip().lower() == "cancel":
            return await ctx.send("❌ Cancelled.")

        # Parse fields from the single reply
        content_lines = [ln.strip() for ln in reply.content.splitlines() if ln.strip()]
        fields = {"name": None, "dt": None, "location": None}
        for ln in content_lines:
            low = ln.lower()
            if low.startswith("event name:") and fields["name"] is None:
                fields["name"] = ln.split(":", 1)[1].strip()
            elif low.startswith("event date & time:") and fields["dt"] is None:
                fields["dt"] = ln.split(":", 1)[1].strip()
            elif low.startswith("event location:") and fields["location"] is None:
                fields["location"] = ln.split(":", 1)[1].strip()

        if not fields["name"] or not fields["dt"] or not fields["location"]:
            return await ctx.send("❌ Missing fields. Please match the template exactly and try again.")

        # Validate datetime
        try:
            event_dt = datetime.strptime(fields["dt"], "%Y-%m-%d %H:%M")
        except ValueError:
            return await ctx.send("❌ Invalid date/time format. Use `YYYY-MM-DD HH:MM` (24h).")

        # Optional photos from the same message
        valid_photos: List[discord.Attachment] = []
        if reply.attachments:
            valid_exts = (".jpg", ".jpeg", ".png", ".gif", ".webp")
            for att in reply.attachments:
                name = (att.filename or "").lower()
                content_type = (att.content_type or "").lower()
                if any(name.endswith(ext) for ext in valid_exts) or content_type.startswith("image/"):
                    valid_photos.append(att)

        # Build details and record activity
        photo_urls = [a.url for a in valid_photos[:3]]
        details = (
            f"Event attendance | Name: {fields['name']} | When: {event_dt.isoformat()} | "
            f"Location: {fields['location']} | Photos: {len(valid_photos)} | "
            f"Sample: {', '.join(photo_urls)}"
        )

        await with_retries(lambda: self.client.add_activity(str(ctx.author.id), "event_attendance", details))

        # Bonus +2 if photos included
        bonus_text = "No"
        if len(valid_photos) > 0:
            try:
                await with_retries(lambda: self.client.admin_adjust(str(ctx.author.id), 2, "Event photos bonus"))
                bonus_text = "+2"
            except Exception:
                bonus_text = "(bonus failed)"

        embed = discord.Embed(
            title="🎉 Event Attendance Recorded",
            description=f"{ctx.author.mention}, thanks! Your event details were recorded.",
            color=0x00ff00,
        )
        embed.add_field(name="Event", value=fields['name'], inline=True)
        embed.add_field(name="When", value=fields['dt'], inline=True)
        embed.add_field(name="Location", value=fields['location'], inline=True)
        embed.add_field(name="Photo bonus", value=bonus_text, inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def resource(self, ctx: commands.Context, *, description: str):
        if not description or len(description.strip()) < 10:
            return await ctx.send("❌ Please provide a detailed description (at least 10 characters).\n\nUsage: `!resource <description>`")
        await with_retries(lambda: self.client.add_activity(str(ctx.author.id), "resource_share", description.strip()))
        embed = discord.Embed(title="📚 Resource Submitted", description=f"{ctx.author.mention}, your resource was submitted for review!", color=0x0099ff)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def linkedin(self, ctx: commands.Context):
        await with_retries(lambda: self.client.add_activity(str(ctx.author.id), "linkedin_post", "LinkedIn update"))
        await ctx.send(embed=discord.Embed(title="💼 LinkedIn Update", description=f"{ctx.author.mention}, thanks for sharing your update!", color=0x00ff00))

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def pointvalues(self, ctx: commands.Context):
        embed = discord.Embed(title="🎯 Point Values", description="Earn points for these actions:", color=0x00ff00)
        embed.add_field(name="📄 Resume Upload", value="backend-defined", inline=True)
        embed.add_field(name="🎉 Event Attendance", value="backend-defined", inline=True)
        embed.add_field(name="📚 Resource Share", value="backend-defined", inline=True)
        embed.add_field(name="💼 LinkedIn Update", value="backend-defined", inline=True)
        embed.add_field(name="👍 Like/Interaction", value="backend-defined", inline=True)
        embed.add_field(name="💬 Message Sent", value="backend-defined", inline=True)
        await ctx.send(embed=embed)

    

    # Admin tools
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addpoints(self, ctx: commands.Context, member: discord.Member, amount: int):
        await with_retries(lambda: self.client.admin_adjust(str(member.id), int(amount), f"Admin by {ctx.author.display_name}"))
        await ctx.send(f"✅ Added {amount} points to {member.mention}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def removepoints(self, ctx: commands.Context, member: discord.Member, amount: int):
        await with_retries(lambda: self.client.admin_adjust(str(member.id), -int(amount), f"Admin by {ctx.author.display_name}"))
        await ctx.send(f"✅ Removed {amount} points from {member.mention}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def suspend(self, ctx: commands.Context, member: discord.Member, minutes: int):
        await with_retries(lambda: self.client.suspend_user(str(member.id), int(minutes)))
        await ctx.send(f"✅ Suspended {member.mention} for {minutes} minutes")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unsuspend(self, ctx: commands.Context, member: discord.Member):
        await with_retries(lambda: self.client.unsuspend_user(str(member.id)))
        await ctx.send(f"✅ Unsuspended {member.mention}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def clearwarnings(self, ctx: commands.Context, member: discord.Member):
        await with_retries(lambda: self.client.clear_warnings(str(member.id)))
        await ctx.send(f"✅ Cleared warnings for {member.mention}")

    @commands.command()
    async def activitylog(self, ctx: commands.Context, hours: int = 24, limit: int = 20):
        try:
            data = await with_retries(lambda: self.client.activitylog(int(hours), int(limit)))
            rows: List[dict] = data.get("results", data if isinstance(data, list) else [])
            if not rows:
                return await ctx.send("No recent activity found.")
            lines = []
            for r in rows[:limit]:
                ts = r.get("timestamp", "")
                did = r.get("discord_id", "")
                action = r.get("action", r.get("activity_type", "activity"))
                pts = r.get("points", "")
                who = f"<@{did}>" if did else ""
                pts_str = f" (+{pts} pts)" if isinstance(pts, int) else ""
                lines.append(f"{ts[:19]} {who} {action}{pts_str}")
            await ctx.send("Recent activity:\n" + "\n".join(lines))
        except Exception as e:
            await ctx.send(f"Failed to fetch activity log: {e}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def stats(self, ctx: commands.Context):
        """Show bot/server stats and backend connectivity."""
        try:
            # Backend check
            backend_ok = True
            try:
                await with_retries(lambda: self.client.summary(str(ctx.author.id), limit=1))
            except Exception:
                backend_ok = False

            gateway_ms = round(self.bot.latency * 1000)
            num_servers = len(self.bot.guilds)
            num_cogs = len(self.bot.cogs)
            num_commands = len(self.bot.commands)
            start_time = getattr(self.bot, "start_time", None)
            uptime_field = "Unknown"
            try:
                # Use Discord relative timestamp if available
                import datetime as _dt
                if start_time:
                    ts = int(getattr(start_time, "timestamp", lambda: 0)())
                    uptime_field = f"<t:{ts}:R>"
            except Exception:
                pass

            embed = discord.Embed(title="📊 Bot Stats", color=0x0099ff)
            embed.add_field(name="Servers", value=str(num_servers), inline=True)
            embed.add_field(name="Cogs", value=str(num_cogs), inline=True)
            embed.add_field(name="Commands", value=str(num_commands), inline=True)
            embed.add_field(name="Gateway Latency", value=f"{gateway_ms}ms", inline=True)
            embed.add_field(name="Uptime", value=uptime_field, inline=True)
            embed.add_field(name="Backend", value=("✅ Connected" if backend_ok else "❌ Error"), inline=True)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed to fetch stats: {e}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def topusers(self, ctx: commands.Context):
        """Show top 10 users from the backend leaderboard (page 1)."""
        try:
            data = await with_retries(lambda: self.client.leaderboard(page=1, page_size=10))
            items = data.get("results", [])
            if not items:
                return await ctx.send("No leaderboard data.")
            msg_lines = ["**🏆 Top Users (Top 10)**"]
            for item in items:
                pos = item.get("position")
                did = item.get("discord_id")
                pts = item.get("total_points", 0)
                msg_lines.append(f"{pos}. <@{did}> — {pts} points")
            await ctx.send("\n".join(msg_lines))
        except Exception as e:
            await ctx.send(f"❌ Failed to fetch top users: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Points(bot))


