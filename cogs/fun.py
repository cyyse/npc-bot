import discord
from discord.ext import commands
import random
from helper import load_balances, save_balances, init_user_balance, get_user_balance, modify_user_balance

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_balances = load_balances()

    def init_balance(self, user_id):
        init_user_balance(user_id, self.user_balances)

    @commands.command(name="balance", help="Check current balance.", aliases=["bal"])
    async def balance(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        
        user_id = str(member.id)
        self.user_balances = load_balances()
        user_bal = get_user_balance(user_id, self.user_balances)
        
        formatted_balance = f"{user_bal:,}"

        await ctx.send(f"**{member.name}**'s balance is **${formatted_balance}**.")

    @commands.command(name="pray", help="Drops a random amount of money.")
    @commands.cooldown(1, 3600, commands.BucketType.user)  # allows 1 use every hour per user
    async def pray(self, ctx):
        user_id = str(ctx.author.id)
        self.init_balance(user_id)

        amt = random.randint(0, 1000)
        modify_user_balance(user_id, amt, self.user_balances)

        await ctx.send(f"✨ Pray and you shall receive... **${amt}** ✨")

    @pray.error
    async def pray_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            remainder = round(error.retry_after)
            hours, rmd = divmod(remainder, 3600)
            minutes, seconds = divmod(rmd, 60)

            time_format = []
            if hours > 0:
                time_format.append(f"{hours} hour{"s" if hours > 1 else ""}")
            if minutes > 0:
                time_format.append(f"{minutes} minute{"s" if minutes > 1 else ""}")
            if seconds > 0:
                time_format.append(f"{seconds} second{"s" if seconds > 1 else ""}")
            
            time_format = ', '.join(time_format)

            await ctx.send(f"You can use this command again in **{time_format}**.")

    @commands.command(name="wipeout", aliases=["wo", "clear"])
    @commands.has_role("(ꈍᴗꈍ)")  # Change this to your actual admin role name
    async def wipeout(self, ctx, member: discord.Member):
        user_id = str(member.id)

        if user_id in self.user_balances:
            modify_user_balance(user_id, -get_user_balance(user_id, self.user_balances), self.user_balances)
            
            await ctx.send(f"**{member.name}**\'s balance has been successfully wiped out.")
        else:
            await ctx.send(f"**{member.name}** has no balance to wipe.")

    @wipeout.error
    async def wipeout_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            await ctx.send(f"{ctx.author.mention}, you do not have permissions to use the command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"{ctx.author.mention}, please mention a user to wipe out.")
        else:
            await ctx.send(f"An error has occurred: {error}")

async def setup(bot):
    await bot.add_cog(Fun(bot))