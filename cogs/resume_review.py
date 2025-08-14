from discord.ext import commands
import discord
from typing import List, Optional
from p2e_backend_client import P2EClient, with_retries
import asyncio
from datetime import datetime


class ResumeReview(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client = P2EClient()
        self.form_url = "https://forms.gle/EKHLrqhHwt1bGQjd6"  # Resume review form

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.user)  # 30 second cooldown
    async def resume_review(self, ctx: commands.Context):
        """Start resume review process - sends DM with form link and instructions"""
        try:
            embed = discord.Embed(
                title="📋 Resume Review Request",
                description="I'll help you get a professional resume review!",
                color=0x0099ff
            )
            embed.add_field(
                name="📝 Next Steps", 
                value="1. Click the form link below\n2. Fill out your details\n3. Upload your resume\n4. Select your target industry\n5. Choose your availability",
                inline=False
            )
            embed.add_field(
                name="🔗 Form Link",
                value=f"[Resume Review Form]({self.form_url})",
                inline=False
            )
            embed.add_field(
                name="⏰ Sessions",
                value="30-minute slots between 9 AM - 5 PM",
                inline=True
            )
            embed.add_field(
                name="📧 Contact",
                value="Email: propel@propel2excel.com",
                inline=True
            )
            embed.add_field(
                name="💡 Tips",
                value="• Have your resume ready as PDF\n• Be specific about your target role\n• Choose multiple time slots for better matching",
                inline=False
            )
            
            await ctx.author.send(embed=embed)
            await ctx.send(f"✅ {ctx.author.mention} Check your DMs for the resume review form!")
            
        except discord.Forbidden:
            await ctx.send("❌ I can't send you a DM. Please enable DMs from server members and try again.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def review_status(self, ctx: commands.Context):
        """Check status of your resume review request"""
        try:
            # Get status from backend
            data = await with_retries(lambda: self.client._post({
                "action": "review-status",
                "discord_id": str(ctx.author.id)
            }))
            
            status = data.get("status", "No request found")
            submitted_time = data.get("submitted_at", "")
            matched_professional = data.get("professional_name", "")
            scheduled_time = data.get("scheduled_time", "")
            
            embed = discord.Embed(
                title="📊 Review Status",
                description=f"{ctx.author.mention}'s resume review status",
                color=0x0099ff
            )
            embed.add_field(
                name="Status", 
                value=status,
                inline=True
            )
            
            if submitted_time:
                embed.add_field(
                    name="Submitted", 
                    value=f"<t:{int(datetime.fromisoformat(submitted_time).timestamp())}:R>",
                    inline=True
                )
            
            if matched_professional:
                embed.add_field(
                    name="Professional",
                    value=matched_professional,
                    inline=True
                )
                
            if scheduled_time:
                embed.add_field(
                    name="Scheduled",
                    value=f"<t:{int(datetime.fromisoformat(scheduled_time).timestamp())}:F>",
                    inline=True
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error checking status: {e}")

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def cancel_review(self, ctx: commands.Context):
        """Cancel your pending resume review request"""
        try:
            # Confirmation step
            await ctx.send("⚠️ Are you sure you want to cancel your resume review request? Type `yes` to confirm.")
            
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == 'yes'
            
            try:
                await self.bot.wait_for('message', timeout=30.0, check=check)
                
                # Cancel the review via backend
                await with_retries(lambda: self.client._post({
                    "action": "cancel-review-request",
                    "discord_id": str(ctx.author.id)
                }))
                
                embed = discord.Embed(
                    title="❌ Review Cancelled",
                    description="Your resume review request has been cancelled.",
                    color=0xff0000
                )
                embed.add_field(
                    name="Note",
                    value="You can request a new review anytime with `!resume-review`",
                    inline=False
                )
                
                await ctx.send(embed=embed)
                
            except asyncio.TimeoutError:
                await ctx.send("⏰ Cancellation timed out. Your review request is still active.")
                
        except Exception as e:
            await ctx.send(f"❌ Error cancelling review: {e}")

    # Admin commands for managing professionals
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def add_professional(self, ctx: commands.Context, name: str, industry: str, email: str):
        """Add a professional to the review database"""
        try:
            # Add professional via backend
            data = await with_retries(lambda: self.client._post({
                "action": "add-professional",
                "name": name,
                "industry": industry,
                "email": email
            }))
            
            professional_id = data.get("professional_id", "Unknown")
            
            embed = discord.Embed(
                title="✅ Professional Added",
                description=f"Added {name} to the professional database",
                color=0x00ff00
            )
            embed.add_field(name="Name", value=name, inline=True)
            embed.add_field(name="Industry", value=industry, inline=True)
            embed.add_field(name="Email", value=email, inline=True)
            embed.add_field(name="ID", value=professional_id, inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error adding professional: {e}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def list_professionals(self, ctx: commands.Context):
        """List all available professionals"""
        try:
            # Fetch professionals from backend
            data = await with_retries(lambda: self.client._post({
                "action": "list-professionals"
            }))
            
            professionals = data.get("professionals", [])
            
            if not professionals:
                await ctx.send("❌ No professionals found in the database.")
                return
            
            embed = discord.Embed(
                title="👥 Available Professionals",
                description="Professionals available for resume reviews",
                color=0x0099ff
            )
            
            # Group by industry
            by_industry = {}
            for prof in professionals:
                industry = prof.get("industry", "Other")
                if industry not in by_industry:
                    by_industry[industry] = []
                by_industry[industry].append(f"• {prof['name']} ({prof.get('expertise', 'General')}) - ID: {prof['id']}")
            
            for industry, profs in by_industry.items():
                embed.add_field(
                    name=industry,
                    value="\n".join(profs[:5]),  # Limit to 5 per field
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error listing professionals: {e}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def match_review(self, ctx: commands.Context, student_id: str, professional_id: str):
        """Manually match a student with a professional"""
        try:
            # Match via backend
            data = await with_retries(lambda: self.client._post({
                "action": "match-review",
                "student_id": student_id,
                "professional_id": professional_id
            }))
            
            scheduled_time = data.get("scheduled_time", "TBD")
            meeting_link = data.get("meeting_link", "Will be sent via email")
            
            embed = discord.Embed(
                title="🤝 Review Matched",
                description="Successfully matched student with professional",
                color=0x00ff00
            )
            embed.add_field(name="Student ID", value=student_id, inline=True)
            embed.add_field(name="Professional ID", value=professional_id, inline=True)
            embed.add_field(name="Scheduled", value=scheduled_time, inline=True)
            embed.add_field(name="Meeting Link", value=meeting_link, inline=False)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error matching review: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(ResumeReview(bot))
