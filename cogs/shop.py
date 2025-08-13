from discord.ext import commands
import discord
from p2e_backend_client import P2EClient, with_retries


class Shop(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client = P2EClient()

    @commands.command()
    async def shop(self, ctx: commands.Context):
        try:
            data = await with_retries(lambda: self.client.get_incentives())
            items = data if isinstance(data, list) else data.get('results', [])
            if not items:
                return await ctx.send("The shop is currently empty!")
            embed = discord.Embed(title="🛍️ Available Rewards", color=0x0099ff)
            for item in items:
                embed.add_field(name=f"#{item.get('id')} — {item.get('name')}", value=f"Cost: {item.get('cost')} points", inline=False)
            embed.set_footer(text="Use `!redeem <id>` to redeem a reward")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Failed to fetch shop: {e}")

    @commands.command()
    async def redeem(self, ctx: commands.Context, incentive_id: int):
        try:
            data = await with_retries(lambda: self.client.redeem(str(ctx.author.id), incentive_id))
            msg = data.get('message', 'Redeemed successfully!') if isinstance(data, dict) else 'Redeemed successfully!'
            await ctx.send(f"{ctx.author.mention} {msg}")
        except Exception as e:
            await ctx.send(f"Redeem failed: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Shop(bot))


