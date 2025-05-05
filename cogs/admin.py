import discord
from discord.ext import commands
import json

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="admin")
    async def admin(self, ctx):
        user = ctx.author
        server_owner = ctx.guild.owner

        if user == server_owner:
            await ctx.send(f"{user.mention}, you are the server owner!")
        else:
            await ctx.send(f"{user.mention}, you are a member of the server.")

async def setup(bot):
    await bot.add_cog(Admin(bot))