import discord
from discord.ext import commands
import random
import asyncio
from helper import load_balances, save_balances, init_user_balance, get_user_balance, modify_user_balance, load_bets, save_bets, load_channel_ids, save_channel_ids
import aiocron
from datetime import datetime

MAX_BETS = 3

class Lottery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_balances = load_balances()
        self.user_bets, self.all_bets = load_bets()
        self.betting_open = True
        self.channel_ids = load_channel_ids()

        # takes local system timezone
        aiocron.crontab('55 20 * * *', func=self.close_betting_window)
        aiocron.crontab('00 21 * * *', func=self.release_results)

    def classify_bet(self, amount):
        if 1 <= amount <= 10:
            return "Small Bet"
        elif 11 <= amount <= 50:
            return "Ordinary Bet"
        elif amount > 50:
            return "Big Bet"
        else:
            return None
        
    def validate_bet_input(self, bet_input):
        errors = []
        parts = bet_input.split()
        
        # checks for correct number of inputs
        if len(parts) != 2:
            errors.append("Please enter exactly 2 inputs: ``[bet amount] [4-digit number]``")
            return None, None, errors
    
        try:
            amount = int(parts[0])
        except ValueError:
            errors.append("The bet amount must be a number.")
            return None, None, errors
        
        number = parts[1]
        if len(number) != 4 or not number.isdigit():
            errors.append("The bet number must be a 4-digit number.")
            return None, None, errors
        
        bet_class = self.classify_bet(amount)
        if bet_class is None:
            errors.append("The bet amount must be in the range: **Small Bet ($1-$10), Ordinary Bet ($11-$50), Big Bet ($51 and above)**.")
            return None, None, errors
        
        # everything is valid
        return amount, number, None

    async def confirmation_prompt(self, ctx, bet_amount, number, bet_class):
        confirmation_message = f"Please confirm your bet: **${bet_amount}** on **{number} ({bet_class})**. **(Y/N)**"
        await ctx.send(confirmation_message)

        def check_confirm(m):
            return m.author == ctx.author and m.content.upper() in ['Y', 'N']
        
        try:
            confirmation = await self.bot.wait_for('message', check=check_confirm, timeout=30)
            return confirmation.content.upper() == 'Y'
        except asyncio.TimeoutError:
            await ctx.send("**You took too long to confirm! Cancelling the bet...**")
            return False
        
    async def prompt_bet(self, ctx):
        
        while True:
            await ctx.send("Please place your bet in the following format: ``[bet amount] [4-digit number] (e.g.: 50 4985)``")

            def check_bet(m):
                return m.author == ctx.author
            
            try:
                bet_message = await self.bot.wait_for('message', check=check_bet, timeout=30)
                amount, number, errors = self.validate_bet_input(bet_message.content)

                if errors:
                    await ctx.send("\n".join(errors))  # Send all error messages
                    continue
                
                bet_class = self.classify_bet(amount)

                if bet_class is None:
                    errors.append("The bet amount must be in the range: **Small Bet ($1-$10), Ordinary Bet ($11-$50), Big Bet ($51 and above)**.")
                    await ctx.send("\n".join(errors))
                    continue

                return amount, number, bet_class
            
            except asyncio.TimeoutError:
                await ctx.send("**You took too long to confirm! Cancelling the bet...**")
                return None, None, None

    async def handle_sequence(self, ctx, user_id):
        user_id_str = str(user_id)
        
        self.user_balances = load_balances()
        user_balance = get_user_balance(user_id_str, self.user_balances)
        
        if user_balance <= 0:
            await ctx.send("You do not have enough balance to place a bet.")
            return
 
        if user_id_str not in self.user_bets:
            self.user_bets[user_id_str] = []

        if len(self.user_bets[user_id_str]) >= MAX_BETS and self.betting_open is True:
            await ctx.send(f"You have reached your limit of __**{MAX_BETS}**__ bet(s) today.")
            return
        elif (len(self.user_bets[user_id_str]) >= MAX_BETS or len(self.user_bets[user_id_str]) < MAX_BETS or self.user_balances <= 0) and self.betting_open is False:
            await ctx.send("The betting window is now closed. Please wait for the results!")
            return
        
        while len(self.user_bets[user_id_str]) < MAX_BETS:
            amount, number, bet_class = await self.prompt_bet(ctx)

            if not amount:
                return
            
            if amount > user_balance:
                await ctx.send(f"You don't have enough balance to place a bet of __**${amount}**__! Your current balance is __**${user_balance}**__.")
                return
            
            confirmed = await self.confirmation_prompt(ctx, amount, number, bet_class)

            if confirmed:
                
                if modify_user_balance(user_id_str, -amount, self.user_balances):
                    self.user_bets[user_id_str].append((amount, number, bet_class))

                if number not in self.all_bets:
                    self.all_bets[number] = []
                self.all_bets[number].append(user_id_str)
                
                save_bets(self.user_bets, self.all_bets)

                user_balance = get_user_balance(user_id_str, self.user_balances)

                bets_left = MAX_BETS - len(self.user_bets[user_id_str])
                if bets_left > 0 and self.betting_open is True:
                    await ctx.send(f"Number bought. You have __**{bets_left}**__ bet(s) left. Would you like to bet again? **(Y/N)**")

                    def check_again(m):
                        return m.author == ctx.author and m.content.upper() in ['Y', 'N']
                    
                    try:
                        again = await self.bot.wait_for('message', check=check_again, timeout=30)
                        if again.content.upper() == 'N':
                            await ctx.send("Thank you! Please wait for the results at **9PM**. Feel free to bet again till **5 minutes** before the results.")
                            return
                    except asyncio.TimeoutError:
                        await ctx.send("**You took too long to respond! Ending interaction...**")
                        return
                else:
                    await ctx.send("Thank you! You have reached your limit of bets today. Please wait for the next cycle to bet again. Results will be out at **9PM**.")
                    return
            else:
                await ctx.send("**Bet cancelled. Please try again.**")

    @commands.command(name="bet")
    async def lottery(self, ctx):
        user_id = ctx.author.id
        await self.handle_sequence(ctx, user_id)

    @commands.command(name="bets")
    async def show_bets(self, ctx):
        user_id = str(ctx.author.id)

        if user_id in self.user_bets and self.user_bets[user_id]:
            bet_list = "\n".join([f"**${bet[0]}** on **{bet[1]}** (**{bet[2]}**)" for bet in self.user_bets[user_id]])
            await ctx.send(f"**Your current bets:**\n{bet_list}")
        else:
            await ctx.send("You have no bets placed.")

    @commands.command(name="allbets")
    async def show_all_bets(self, ctx):
        if self.all_bets:
            all_bets_msg = "\n".join([f"**{num}:** __**{len(users)}**__ time(s)" for num, users in self.all_bets.items()])
            await ctx.send(f"**Current bets placed:**\n{all_bets_msg}")
        else:
            await ctx.send("No bets have been placed yet.")

    def generate_random_numbers(self):
        return [str(num).zfill(4) for num in random.sample(range(10000), 50)]
    
    def check_winning_numbers(self, random_numbers, user_numbers, user_bet_details, user_id_str):
        results = []
        total_prize = 0

        prize_structure = {
            "Small Bet": {
                "1st": 700,
                "2nd": 600,
                "3rd": 580,
                "starter": 400,
                "consolation": 300
            },
            "Ordinary Bet": {
                "1st": 3000,
                "2nd": 1500,
                "3rd": 1000,
                "starter": 800,
                "consolation": 600
            },
            "Big Bet": {
                "1st": 5000,
                "2nd": 2500,
                "3rd": 2000,
                "starter": 1800,
                "consolation": 1600
            }
        }

        for number in user_numbers:
            if number in random_numbers:
                bet_amount, bet_type = user_bet_details[number]
                index = random_numbers.index(number)

                prize = 0
            
                if index == 0:
                    prize = prize_structure[bet_type]["1st"] * bet_amount
                    place_message = "1st"
                elif index == 1:
                    prize = prize_structure[bet_type]["2nd"] * bet_amount
                    place_message = "2nd"
                elif index == 2:
                    prize = prize_structure[bet_type]["3rd"] * bet_amount
                    place_message = "3rd"
                elif 3 <= index <= 12:  # Starter prizes (1st 10 numbers after top 3)
                    prize = prize_structure[bet_type]["starter"] * bet_amount
                    place_message = "starter"
                else:  # Consolation prizes (last 10 numbers)
                    prize = prize_structure[bet_type]["consolation"] * bet_amount
                    place_message = "consolation"

                total_prize += prize

                results.append(f"Congratulations, {number} is a {place_message} prize winner. You win ${prize}!")
            else:
                results.append(f"Sorry, {number} is not a winning number.")

        if total_prize > 0:
            results.append(f"Your total winnings of ${total_prize} have been added to your balance!")
        
        modify_user_balance(user_id_str, total_prize, self.user_balances)
        return results
    
    def validate_input(self, user_inputs):
        return [num for num in user_inputs if num.isdigit() and len(num) == 4]
    
    async def display_results(self, ctx, random_numbers):
        embed = discord.Embed(
            title="--- Lottery Numbers ---",
            color=0xFFD1DC
        )
        for idx, num in enumerate(random_numbers, start=1):
            position_str = f" {idx}" if idx < 10 else str(idx)
            embed.add_field(name=f"{position_str}. {num}", value="", inline=False)
        await ctx.send(embed=embed)
    
    async def close_betting_window(self):
        self.betting_open = False

        print(f"{self.channel_ids.keys()}")
        
        for guild_id in self.channel_ids.keys():
            channel_id = self.channel_ids[str(guild_id)]
            channel = self.bot.get_channel(channel_id)

            if channel:
                await channel.send("**Betting window is now closed. Please wait for the results at __9PM__!**")

    async def release_results(self):

        combination_chance = random.randint(1, 10)
        gauge = random.randint(1, 5)

        for guild_id in self.channel_ids.keys():
            channel_id = self.channel_ids[guild_id]
            channel = self.bot.get_channel(channel_id)

            if channel:
                await channel.send(f"Gauge: **{gauge}%**, Combination Chance: **{combination_chance}%**")

                user_numbers = list(self.all_bets.keys())

                if not user_numbers:
                    await channel.send("No bets were placed.")
                    return

                random_numbers = self.generate_random_numbers()

                if gauge < combination_chance:
                    await channel.send("Numbers are included.")
                    random_numbers.extend(user_numbers)

                random_numbers = list(set(random_numbers))
                if len(random_numbers) > 23:
                    random_numbers = random.sample(random_numbers, 23)

                random.shuffle(random_numbers)

                await self.display_results(channel, random_numbers)

                user_results = {}

                for number, users in self.all_bets.items():
                    for user_id_str in users:
                        user_bets = self.user_bets[user_id_str]
                        user_id = int(user_id_str)

                        user_numbers = []
                        user_bet_details = {}

                        for bet in user_bets:
                            bet_amount, user_number, bet_type = bet
                            user_numbers.append(user_number)
                            if user_number not in user_bet_details:
                                user_bet_details[user_number] = (bet_amount, bet_type)

                        results = self.check_winning_numbers(random_numbers, user_numbers, user_bet_details, user_id_str)

                        if results:
                            user_results[user_id_str] = results

                for user_id_str, results in user_results.items():
                    if results:
                        user_id = int(user_id_str)
                        result_message = "\n".join(results)
                        await channel.send(f"**<@{user_id}>, here are your results:**\n{result_message}")
                    else:
                        await channel.send(f"<@{user_id}>, unfortunately, none of your bets won this time.")

                self.user_bets, self.all_bets = {}, {}
                save_bets(self.user_bets, self.all_bets)
                await channel.send("Bets have been reset for the next round. You can start betting again!")

    @commands.command(name="setchannel")
    @commands.has_role("(ꈍᴗꈍ)")
    async def set_channel(self, ctx):
        channel_id = ctx.channel.id
        guild_id = ctx.guild.id

        self.channel_ids[str(guild_id)] = channel_id
        save_channel_ids(str(guild_id), channel_id)
        await ctx.send(f"Notification channel is set to <#{channel_id}> for **{ctx.guild.name}**.")

async def setup(bot):
    await bot.add_cog(Lottery(bot))