import discord
from discord.ext import  commands
from discord import app_commands
import json
import os 
import random
from config import TOKEN

balF = "balances.json"
Fbal = 30000
housingEdge = 0.97

if os.path.exists(balF):
  try:
    with open(balF, "r") as f:
      balances = json.load(f)
  except:
    balances = {}
else:
  balances = {}

def saveBals():
  f = open(balF, "w")
  json.dump(balances, f, indent=4)
  f.close()

def parse(x):
  x = x.lower()
  x = x.replace(",", "")
  if x.endswith("k"):
    num = float(x[:-1])
    num = num * 1000
    return int(num)
  if x.endswith('m'):
    num = float(x[:-1])
    num = num * 1000000
    return int(num)
  if x.endswith("b"):
    num = float(x[:-1])
    num = num * 1000000000
    return int(num)
  return int(x)
  
def getBal(uid):
  if uid in balances:
    return balances[uid]
  else:
    return Fbal

def setBal(uid, amt):
  balances[uid] = amt
  saveBals()
  
def multF(target, direction):
  chance = 0 
  if direction == "over":
    chance = 100 - target
  else:
    chance = target
  if chance < 1:
    chance = 1 
  mult = 100 / chance
  mult = mult * housingEdge
  mult = round(mult, 2)
  return mult

class RollView(discord.ui.View):
  def __init__(self, bet, target, direction, mult, user_id):
    super().__init__(timeout=60)
    self.bet = bet
    self.target = target
    self.direction = direction
    self.mult = mult 
    self.user_id = user_id
  
  async def interaction_check(self, inter):
    if inter.user.id == self.user_id:
      return True
    else:
      return False
  @discord.ui.button(label="Roll Again", style=discord.ButtonStyle.green)
  async def roll_again(self, inter, _):
    roll = random.randint(1, 100)
    win = False
    if self.direction == "over":
      if roll > self.target:
        win = True
      else:
        win = False
    else:
      if roll < self.target:
        win = True
      else:
        win = False
        
    if win:
      new_mult = multF(self.target, self.direction)
      self.mult = self.mult * new_mult
      embed = discord.Embed()
      embed.title = ":game_die: Roll"
      embed.description = f"Roll: {roll}\nYou **Won** again!"
      embed.color = discord.Color.green()
      embed.add_field(name="Current Multiplier", value=f"x{self.mult:.2f}")
      await inter.response.edit_message(embed=embed, view=self)
    else:
      embed = discord.Embed(
        title=":game_die: Roll",
        description=f"Roll: {roll}\nYou Lost.",
        color=discord.Color.red(),
        )
      self.clear_items()
      await inter.response.edit_message(embed=embed, view=None)
  @discord.ui.button(label="Cash Out", style=discord.ButtonStyle.red)
  async def cash_out(self, inter, _):
    winAMT = int(self.bet * self.mult)
    currentBal = getBal(str(self.user_id))
    new_bal = currentBal + winAMT
    setBal(str(self.user_id), new_bal)
    embed = discord.Embed(
      title="Cashed Out!",
      description=f"You cashed out With **{winAMT}**!",
      color=discord.Color.gold(),
      )
    await inter.response.edit_message(embed=embed, view=None)
      
class DiceBot(commands.Bot):
  def __init__(self):
    intents = discord.Intents.default()
    super().__init__(command_prefix="!", intents=intents)
    
  async def setup_hook(self):
    await self.tree.sync()
  
bot = DiceBot()

@bot.tree.command(name="balance", description="Check your balance")
async def balance(inter):
  uid = str(inter.user.id)
  b = getBal(uid)
  embed = discord.Embed(
    title="Balance:",
    description=f"You Have **{b:,}**",
    color=discord.Color.blue(),
      )
  await inter.response.send_message(embed=embed)
@bot.tree.command(name="leaderboard", description="Show top Players (money wise)")
async def leaderboard(inter):
  top = sorted(balances.items(), key=lambda x: x[1], reverse=True)[:10]
  desc = ""
  for i, (uid, bal) in enumerate(top):
    try:
      member = await inter.guild.fetch_members(int(uid))
      name = member.display_name
    except:
      name = f"User {uid}"
    desc += f"**{i + 1}. {name}** - {bal:,}\n"
  embed = discord.Embed(
    title="LeaderBoard",
    description=desc if desc != "" else "No players yet",
    color=discord.Color.gold(),     
    )
  await inter.response.send_message(embed=embed)

@bot.tree.command(name="admingivemoney", description="if you're an admin you can give members an infinite amount of money")
@app_commands.checks.has_permissions(administrator=True)
async def give(inter, user: discord.Member, amt: str):
  uid = str(user.id)
  a = parse(amt)
  current = getBal(uid)
  new_bal = current + a 
  setBal(uid, new_bal)
  await inter.response.send_message(f"Gave **{a:,}** to {user.mention}.")
  
@bot.tree.command(name="admintakemoney", description="if you were a MODERATOR or OWNER, you can take money of any member")
@app_commands.checks.has_permissions(administrator=True)
async def take(inter, user: discord.Member, amt: str):
  uid = str(user.id)
  a = parse(amt)
  current = getBal(uid)
  new_bal = current - a
  if new_bal < 0:
    new_bal = 0 
  setBal(uid, new_bal)
  await inter.response.send_message(f'Removed **{a:,}** coins from {user.mention}.')
  
@bot.tree.command(name='roll', description="please go to #help for more information!")
@app_commands.describe(amount='How Much To Roll.', target='3-97, higher risk higher reward.', choice="over/under")
async def roll_cmd(inter, amount: str, target: int, choice: str):
  direction = choice.lower()
  if direction != "over" and direction != 'under':
    await inter.response.send_message('Choice must be over or under.', ephemeral=True)
    return
  if target < 3 or target > 97:
    await inter.response.send_message('Please use Numbers 3-97!', ephemeral=True)
    return
  uid = str(inter.user.id)
  amt = parse(amount)
  bal = getBal(uid)
  if uid not in balances:
    setBal(uid, bal)
  if amt > bal:
    await inter.response.send_message("Not enough Coins.", ephemeral=True)
    return
  new_bal = bal - amt 
  setBal(uid, new_bal)
  
  roll = random.randint(1, 100)
  won = False
  if (direction == 'over'):
    if roll > target:
      won = True
    else:
      won = False
  elif (direction == "under"):
    if roll < target:
      won = True
    else:
      won = False
  mult = multF(target, direction)
  
  if won:
    embed = discord.Embed()
    embed.title="Roll Game:"
    embed.description=f"You rolled **{roll}** -- **WIN!**"
    embed.color=discord.Color.green()
    embed.add_field(name="Multiplier", value=f"x{mult:.2f}")

    view = RollView(amt, target, direction, mult, inter.user.id)
  else:
    embed = discord.Embed() # eventually came back to the old methodbecause i got confused
    embed.title = "Roll Game:"
    embed.description = f"You rolled **{roll}** - lost."
    embed.color = discord.Color.red()
    embed.add_field(name="Final Winnings", value="0")
    view = None
  
  await inter.response.send_message(embed=embed, view=view)
class HiloView(discord.ui.View):
  def __init__(self, bet, last_num, user_id):
    super().__init__(timeout=60)
    self.bet = bet 
    self.last = last_num
    self.user_id = user_id
    self.mult = 1.0
  
  async def interaction_check(self, inter):
    return inter.user.id == self.user_id
    
  def roll_card(self):
    new = random.randint(1, 13)
    if new == self.last and new not in (1, 13):
      new += random.choice([-1, 1])
    return new
  
  def WoL(self, new, choice):   # Wint or Loze
    if choice == "higher":
      return new > self.last 
    if choice == "lower":
      return new < self.last 
    
  async def play(self, inter, choice):
    new = self.roll_card()
    win = self.WoL(new, choice)
    if win:
      self.mult *= 1.2 
      self.last = new 
      embed = discord.Embed(
      title="Hilo",
      description=f"You Chose `{choice}`.\nCard: **{new}**\nYou **WIN!**",
      color=discord.Color.green()
      )
      embed.add_field(name="Multiplier", value=f"x{self.mult:.2f}")
      embed.add_field(name="Last Card", value=str(self.last))
      await inter.response.edit_message(embed=embed, view=self)
    
    else:
      embed = discord.Embed(
        title="Hilo",
        description=f"You Chose `{choice}`.\nCard: **{new}**\nYou **LOSE!**",
        color=discord.Color.red(),
      )
      self.clear_items()
      await inter.response.edit_message(embed=embed, view=None)
  
  @discord.ui.button(label="Higher", style=discord.ButtonStyle.green)
  async def higher_btn(self, inter, _):
    await self.play(inter, "higher")
  
  @discord.ui.button(label="Lower", style=discord.ButtonStyle.red)
  async def lowerBtn(self, inter, _):
    await self.play(inter, "lower")
  
  @discord.ui.button(label="Cash Out", style=discord.ButtonStyle.grey)
  async def CashoutBtn(self, inter, _):
    win_amt = int(self.bet * self.mult)
    uid = str(self.user_id)
    setBal(uid, getBal(uid) + win_amt)
    
    embed = discord.Embed(
      title="Hilo",
      description=f"You Cashed out with: **{win_amt}** coins.",
      color=discord.Color.gold(),
    )
    self.clear_items()
    await inter.response.edit_message(embed=embed, view=None)
  
@bot.tree.command(name="hilo", description="Hilo game, Please go to #help for further explanation.")
@app_commands.describe(amount="Enter Bet Amount")
async def hilo_cmd(inter, amount: str):
  uid = str(inter.user.id)
  amt = parse(amount)
  bal = getBal(uid)
  
  if amt <= 0:
    await inter.response.send_message("Invalid amount.", ephemeral=True)
    return
  
  if amt > bal:
    await inter.response.send_message("Not Enough **__Credit__**", ephemeral=True)
    return
  
  setBal(uid, bal - amt)
  
  start_card = random.randint(1, 13)
  embed = discord.Embed(
    title="Hilo",
    description=f"Starting Card: **{start_card}**",
    color=discord.Color.blue()
  )
  embed.add_field(name="Multiplier", value="x1.00")
  
  view = HiloView(amt, start_card, inter.user.id)
  await inter.response.send_message(embed=embed, view=view)

bot.run(TOKEN)