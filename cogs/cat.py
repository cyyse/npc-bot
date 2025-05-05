import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import requests

class Cat(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv("CAT_TOKEN")
        self.base_url = "https://api.thecatapi.com/v1"

    # helper function to get cat image url from api
    def get_cat_image(self, params=None):
        headers = {
            'x-api-key': self.api_key
        }
        response = requests.get(f"{self.base_url}/images/search", headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data:
                return data[0]['url']
        return None

    # decorator
    @commands.command(name="awooga", help="Sends an image of a random cat.", aliases=["ooga", "dooga", "booga"])
    async def awooga(self, ctx):
        cat_image_url = self.get_cat_image()
        if cat_image_url:
            embed = discord.Embed(
                title='b o o g a',
                color=0xB3EBF2
            )
            embed.set_image(url=cat_image_url)
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("Couldn't fetch a cat image at the moment.")

    @commands.command(name="npc", help="Sends a random image of npc's cousins.")
    async def npc(self, ctx):
        params = {"breed_ids": "bomb"}
        cat_image_url = self.get_cat_image(params=params)
        if cat_image_url:
            embed = discord.Embed(
                color=0xB3EBF2
            )
            embed.set_image(url=cat_image_url)
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("Couldn't find npc's cousins at the moment.")
        
    @commands.command(name="cat", help="Lets you search for a breed and sends an image in return.")
    async def cat(self, ctx, *, breed: str = None):
        headers = {
            'x-api-key': self.api_key
        }

        if breed is None:
            await ctx.send("Please specify a breed name. **Usage:** `~cat <breed_name>`")
            return
        
        breed_response = requests.get(f"{self.base_url}/breeds/search?q={breed.lower()}", headers=headers)
        if breed_response.status_code == 200:
            breed_data = breed_response.json()
            if breed_data:
                breed_id = breed_data[0]['id']
                params = {"breed_id": breed_id}
                cat_image_url = self.get_cat_image(params=params)
                if cat_image_url:
                    embed = discord.Embed(
                        color=0xB3EBF2
                    )
                    embed.set_image(url=cat_image_url)
                    
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"Couldn't fetch an image for **'{breed.capitalize()}'**.")
            else:
                await ctx.send(f"Couldn't find any breed matching **'{breed.capitalize()}'**.")
        else:
            await ctx.send(f"Couldn't search for cat breeds at the moment.")

async def setup(bot):
    await bot.add_cog(Cat(bot))
