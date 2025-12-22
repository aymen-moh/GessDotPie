import discord
from discord.ext import  commands
from discord import app_commands
from datetime import datetime
import json
import os 
import random
from config import TOKEN
import asyncio
import re
# i will add so
balF = "balances.json"
Fbal = 30000
housingEdge = 0.97
blocked = [1445414674433572956]


logF = "logs.json"
if os.path.exists(logF):
  try:
    with open(logF, "r") as f:
      logs = json.load(f)
  except:
    logs = []
else: 
  logs = []
def saveLogs():
  with open(logF, "w") as f:
    json.dump(logs, f, indent=4)
def new_log(user=None, note=None):
  loge = {
    "note": note,
    "TIME": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  }
  logs.append(loge)
  saveLogs()
    




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

async def NEB(inter):#not enough bal
  await inter.response.send_message("You don't have enough money.", ephemeral=True)

async def IBA(inter): # invalid bet amount
  await inter.response.send_message("Invalid amount.", ephemeral=True)

class DiceBot(commands.Bot):
  def __init__(self):
    intents = discord.Intents.default()
    intents.members = True
    super().__init__(command_prefix="!", intents=intents)
  async def setup_hook(self):
    await self.tree.sync()
  
bot = DiceBot()

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
    self.rolls = 1
  async def interaction_check(self, inter):
    if inter.user.id == self.user_id:
      return True
    else:
      return False
  @discord.ui.button(label="Roll Again", style=discord.ButtonStyle.green)
  async def roll_again(self, inter, _):
    roll = random.randint(1, 100)
    win = False
    self.rolls += 1
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
      new_log(inter.user, f"The user {inter.user.display_name} lost {self.bet:,} abandoning his last multi x{self.mult:.2f}, after rolling {self.rolls} times betting on {self.direction} {self.target}, User id: {self.user_id}, current user balance after playing {getBal(str(self.user_id)):,}")
      self.clear_items()
      await inter.response.edit_message(embed=embed, view=None)
  @discord.ui.button(label="Cash Out", style=discord.ButtonStyle.red)
  async def cash_out(self, inter, _):
    winAMT = int(self.bet * self.mult)
    currentBal = getBal(str(self.user_id))
    new_bal = currentBal + winAMT
    new_log(inter.user, f"The user {inter.user.display_name} Played roll and cashed out with {winAMT:,} at a x{self.mult:.2f} Multiplier after betting on {self.target} {self.direction}, and rolling {self.rolls} times. User Id: {self.user_id}, initial bet: {self.bet}, current balance after bet: {currentBal:,}")
    setBal(str(self.user_id), new_bal)
    embed = discord.Embed(
      title="Cashed Out!",
      description=f"You cashed out With **{winAMT}**!",
      color=discord.Color.gold(),
      )
    await inter.response.edit_message(embed=embed, view=None)
    
    
@bot.tree.command(name='roll', description="please go to #help for more information!")
@app_commands.describe(amount='How Much To Roll.', target='3-97, higher risk higher reward.', choice="over/under")
async def roll_cmd(inter, amount: str, target: int, choice: str):
  if inter.channel.id in blocked:
        return await inter.response.send_message(
            "You can't do that here ❌", ephemeral=True
        )
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
    await NEB(inter)
    return
  if amt <= 0:
    await IBA(inter)
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
    embed = discord.Embed() # eventually came back to the old methodbecause i got confused i was confused cuz i didnt know how to add fields that way :p
    embed.title = "Roll Game:"
    embed.description = f"You rolled **{roll}** - lost."
    embed.color = discord.Color.red()
    embed.add_field(name="Final Winnings", value="0")
    view = None
    
  await inter.response.send_message(embed=embed, view=view)
@bot.tree.command(name="balance", description="Check your balance")
async def balance(inter):
  if inter.channel.id in blocked:
        return await inter.response.send_message(
            "You can't do that here ❌", ephemeral=True
        )
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
  if inter.channel.id in blocked:
        return await inter.response.send_message(
            "You can't do that here ❌", ephemeral=True
        )
  top = sorted(balances.items(), key=lambda x: x[1], reverse=True)[:10] # ai was used right here please forgive me 
  desc = ""
  for i, (uid, bal) in enumerate(top):
    try:
      name = (await inter.client.fetch_user(uid)).display_name # this was causing it to show user id's instead of the display name, i gave up.
    except:
      name = f"User {inter.user.display_name}"
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
  if inter.channel.id in blocked:
        return await inter.response.send_message(
            "You can't do that here ❌", ephemeral=True
        )
  uid = str(user.id)
  a = parse(amt)
  current = getBal(uid)
  new_bal = current + a 
  setBal(uid, new_bal)
  new_log(uid, f"The owner used /admingivemoney and gave {user.display_name} ${a:,}, user id: {uid}, User balance after: ${new_bal:,}.")
  await inter.response.send_message(f"Gave **{a:,}** to {user.mention}.")
  
@bot.tree.command(name="admintakemoney", description="if you were a MODERATOR or OWNER, you can take money of any member")
@app_commands.checks.has_permissions(administrator=True)
async def take(inter, user: discord.Member, amt: str, reason: str):
  if inter.channel.id in blocked:
        return await inter.response.send_message(
            "You can't do that here ❌", ephemeral=True
        )
  uid = str(user.id)
  a = parse(amt)
  current = getBal(uid)
  new_bal = current - a
  if new_bal < 0:
    new_bal = 0 
  setBal(uid, new_bal)
  new_log(uid, f"The owner used /admintakemoney and took ${a:,} from {user.display_name}, user id: {uid}, balance after: {new_bal:,}, reason: {reason}")
  await inter.response.send_message(f'Removed **{a:,}** coins from {user.mention}.')
  

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
      new_log(inter.user.id, f"The user {inter.user.display_name} played hilo and won, he got away with a x{self.mult:.2f} Multiplier, winning {(self.bet * self.mult):,}, --- initial bet: {self.bet}, user id: {inter.user.id}, Current Balance after bet: {getBal(inter.user.id):,}")
      await inter.response.edit_message(embed=embed, view=self)
    
    else:
      embed = discord.Embed(
        title="Hilo",
        description=f"You Chose `{choice}`.\nCard: **{new}**\nYou **LOSE!**",
        color=discord.Color.red(),
      )
      new_log(inter.user.id, f"The user {inter.user.display_name} played hilo and lost {self.bet:,}, abandoning his last multi of x{self.mult:.2f}, user id: {inter.user.id}, currentBal after bet: {getBal(inter.user.id):,}")
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
  if inter.channel.id in blocked:
        return await inter.response.send_message(
            "You can't do that here ❌", ephemeral=True
        )
  uid = str(inter.user.id)
  amt = parse(amount)
  bal = getBal(uid)
  
  if amt <= 0:
    await IBA(inter)
    return
  
  if amt > bal:
    await NEB(inter)
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
  
@bot.tree.command(name="givemoney", description="Give money to fellow members.")
async def givemoney(inter, user: discord.Member, amount: str):
  if inter.channel.id in blocked:
        return await inter.response.send_message(
            "You can't do that here ❌", ephemeral=True
        )
  sender_id_but_not_a_string_for_logging = inter.user
  reciever_id_but_not_a_string_for_logging = user
  SID = str(inter.user.id)
  RID = str(user.id)
  
  if SID == RID:
    await inter.response.send_message("You **__Cannot__** Send money to __yourself__", ephemeral=True)
    return
  
  amt = parse(amount)
  sBal = getBal(SID)
  
  if amt <= 0:
    await IBA(inter)
    return
  
  if sBal < amt:
    await NEB(inter)
    return
  
  
  setBal(SID, sBal - amt)
  setBal(RID, getBal(RID) + amt)
  new_log(SID, f"The user {sender_id_but_not_a_string_for_logging.display_name} gave {reciever_id_but_not_a_string_for_logging.display_name} ${amt:,}, sender id: {SID}, reciever id: {RID}, current sender balance (after Interaction): {getBal(SID):,}, current reciever balance (after Interaction): {getBal(RID):,}, total amount transferred: {amt:,}")
  
  await inter.response.send_message(f"<@{SID}> sent **__{amt:,}__** Coins to {user.mention}.")
  
  # if you're wondering why there are a quintilliun amount of Your hand: Dealer hand: because one for every scenario.

card_shape = (":spades:", ":diamonds:", ":hearts:", ":clubs:")
card_deck = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 11]

class blackjackView(discord.ui.View):
  def __init__(self, bet, user_id):
    super().__init__(timeout=60)
    self.bet = bet 
    self.user_id = user_id
    self.deck = [(v, s) for v in card_deck for s in card_shape]
    random.shuffle(self.deck)
    self.player_hand = [self.draw_card(), self.draw_card()]
    self.dealer_hand = [self.draw_card()]
    self.finish = False
  
  def draw_card(self):
    v, s = self.deck.pop()
    return (v, s)
  
  def hand_display(self, hand):
    total = sum(card[0] for card in hand)
    cards = ",".join(f"{s}{v}" for v, s in hand)
    return f"{cards}  ({total})"
  
  @discord.ui.button(label="Hit", style=discord.ButtonStyle.green)
  async def hit(self, inter: discord.Interaction, _):
    if inter.user.id != self.user_id or self.finish:
      return
    self.player_hand.append(self.draw_card())
    total = sum(c[0] for c in self.player_hand)
    if (total > 21):
      self.finished = True
      self.clear_items()
      embed = discord.Embed(title="You lost.", color=discord.Color.red())
      embed.add_field(name="Your Hand: ", value=self.hand_display(self.player_hand))
      embed.add_field(name="Dealer Hand: ", value=f"{self.dealer_hand[0][1]}({self.dealer_hand[0][0]})")
      embed.description  = f"Busted! - You Lost"
      new_log(inter.user.id, f"The user {inter.user.display_name} played blackjack and Lost {self.bet:,}, current bal: {getBal(str(inter.user.id)):,}, user id: {inter.user.id}.")
      await inter.response.edit_message(embed=embed, view=None)
      return
\    embed = discord.Embed(title="Blackjack", color=discord.Color.blue())
    embed.add_field(name="Your Hand: ", value=self.hand_display(self.player_hand))
    embed.add_field(name="Dealer showing: ", value=f"{self.dealer_hand[0][1]}({self.dealer_hand[0][0]})")
    await inter.response.edit_message(embed=embed, view=self)
  
  @discord.ui.button(label="Stand", style=discord.ButtonStyle.red)
  async def stand(self, inter: discord.Interaction, _):
    if inter.user.id != self.user_id or self.finish:
      return
    self.finished = True
    self.clear_items()
    
    
    player_total = sum(c[0] for c in self.player_hand)
    dealer_hand = [self.dealer_hand[0]]
    
    embed = discord.Embed(title="Blackjack", color=discord.Color.blue())
    embed.add_field(name="Your hand:", value=self.hand_display(self.player_hand))
    embed.add_field(name="Dealer Hand:", value=self.hand_display(dealer_hand))
    await inter.response.edit_message(embed=embed, view=self)
    await asyncio.sleep(0.5)
    
    while sum(c[0] for c in dealer_hand) < player_total and sum(c[0] for c in dealer_hand) <= 21:
      dealer_hand.append(self.draw_card())
      embed = discord.Embed(title="Blackjack", color=discord.Color.blue())
      embed.add_field(name="Your Hand: ", value=self.hand_display(self.player_hand))
      embed.add_field(name="Dealer hand", value=self.hand_display(dealer_hand))
      
      await inter.edit_original_response(embed=embed)
      await asyncio.sleep(0.5)
    
    dealer_total = sum(c[0] for c in dealer_hand)
    
    
    dealer_total == sum(c[0] for c in dealer_hand)
      
    
    if dealer_total > 21:
      msg = f"You **WON {self.bet*2:,}**"
      color = discord.Color.gold()
      setBal(str(self.user_id), getBal(str(self.user_id)) + self.bet*2)
      new_log(self.user_id, f"The user {inter.user.display_name} played blackjack and Won {self.bet*2:,}, user id: {inter.user.id}, currentBal: {getBal(str(inter.user.id)):,}.")
    elif dealer_total > player_total:
      msg = f"You Lost."
      color = discord.Color.red()
      new_log(self.user_id, f"The user {inter.user.display_name} played blackjack and Lost {self.bet:,}, user id: {inter.user.id}, currentBal: {getBal(str(inter.user.id)):,}.")
    else:
      msg = "Push! (draw)"
      color = discord.Color.green()
      setBal(str(self.user_id), getBal(str(self.user_id)) + self.bet)
      # i didnt want to log the push since i only want to log stuff that changes and modifies the currency in the server, i will probably use the whole logging system to make some analysis and use this it for some machine learning stuff that i will get into hopefuly when i get a pc. (android is so limited :(   )
    LASTE = discord.Embed(title="Blackjack", color=color)       # yes, my friend taught me that I can do this.
    LASTE.description = msg 
    LASTE.add_field(name="Your Hand", value=self.hand_display(self.player_hand))
    LASTE.add_field(name="Dealer hand", value=self.hand_display(dealer_hand))
    
    
    await inter.edit_original_response(embed=LASTE, view=None)

@bot.tree.command(name="blackjack", description="Play blackjack (x2), PLEASE USE #HELP FOR MORE INFO OR OPEN A SUPPORT TICKET.")
async def blackjack(inter: discord.Interaction, bet: str):
  if inter.channel.id in blocked:
        return await inter.response.send_message(
            "You can't do that here ❌", ephemeral=True
        )
  user_id = str(inter.user.id)
  betAMT = parse(bet)
  bal = getBal(user_id)
  
  if betAMT > bal:
    await NEB(inter)
    return
  if betAMT <= 0:
    await IBA(inter)
    return
  setBal(user_id, bal - betAMT)
  view = blackjackView(betAMT, inter.user.id)
  await inter.response.send_message(embed=discord.Embed(
    title="Blackjack",
    description=f"Your hand: {view.hand_display(view.player_hand)}\nDealer showing: {view.dealer_hand[0][1]}{view.dealer_hand[0][0]}",
    color=discord.Color.blue()
    ), view=view)

class PaperRedstoneView(discord.ui.View):
  def __init__(self, bet, user_id):
    super().__init__(timeout=60)
    self.bet = bet 
    self.user_id = user_id
  
  async def interaction_check(self, inter: discord.Interaction):
    return inter.user.id == self.user_id
  
  async def play_g(self, inter: discord.Interaction, choice: str):
    paper_roll = random.randint(1, 9)
    redstone_roll = random.randint(1, 9)
    win = False
    
    if (choice == "paper"):
      if paper_roll > redstone_roll:
        win = True
    elif (choice == "redstone"):
      if paper_roll < redstone_roll:
        win = True
    
    if win:
      Winnings = self.bet * 2 
      setBal(str(self.user_id), getBal(str(self.user_id)) + Winnings)
      embed = discord.Embed(
        title="PaperRedstone",
        description=f"You Chose **{choice.capitalize()}**!\nPaper: {paper_roll}\nRedstone: {redstone_roll}\n\n**YOU WON {Winnings:,}!**",
        color=discord.Color.green()
      )
      new_log(self.user_id, f"The user {inter.user.display_name} played PaperGame and Chose {choice}, he Won {paper_roll} (paper) to {redstone_roll} (redstone), user id: {self.user_id}, currentBal (: {getBal(str(self.user_id)):,}, bet: {self.bet:,}.")
    else:
      embed = discord.Embed(
        title="PaperRedstone",
        description=f"You Chose **{choice.capitalize()}**!\nPaper: {paper_roll}\nRedstone: {redstone_roll}\n\n**You lost.**",
        color=discord.Color.red()
      )
      new_log(self.user_id, f"The user {inter.user.display_name} played PaperGame and Chose {choice}, he Lost {paper_roll} (paper) to {redstone_roll} (redstone), user id: {self.user_id}, currentBal (after bet): {getBal(str(self.user_id)):,}, bet: {self.bet:,}")
    self.clear_items()
    await inter.response.edit_message(embed=embed, view=None)
  
  @discord.ui.button(label="", emoji="<:emoji_1:1443963800091889796>", style=discord.ButtonStyle.blurple)
  async def paper_btn(self, inter: discord.Interaction, button: discord.ui.Button):
    await self.play_g(inter, "paper")
  
  @discord.ui.button(label="", emoji="<:emoji_2:1443964408874139669>", style=discord.ButtonStyle.blurple)
  async def redstone_btn(self, inter: discord.Interaction, button: discord.ui.Button):
    await self.play_g(inter, "redstone")


@bot.tree.command(name="paper", description="play paper game (x2) - PLEASE USE #HELP OR OPEN A TICKET FOR FURTHER ASSISTANCE!!!")
@app_commands.describe(amount="bet")
async def paper_cmd(inter: discord.Interaction, amount: str):
  if inter.channel.id in blocked:
        return await inter.response.send_message(
            "You can't do that here ❌", ephemeral=True
        )
  user_id = str(inter.user.id)
  bet = parse(amount)
  bal = getBal(user_id)
  
  if bet <= 0:
    await IBA(inter)
    return
  if bet > bal:
    await NEB(inter)
    return
  
  
  setBal(user_id, bal - bet)
  
  embed = discord.Embed(
    title="PaperRedstone",
    description=f"Choose Paper or Redstone:",
    color=discord.Color.blue()
  )
  
  view = PaperRedstoneView(bet, inter.user.id)
  await inter.response.send_message(embed=embed, view=view)


safeEmo = "<:safeTile:1444726813158015150>"
notSafeEmo = "<:UnsafeTile:1444726698301198439>"
unknownEmo = "<:unOpenedTile:1444382155693097141>"
notSafeEmo2 = "<a:emoji_19:1447239945428144231>"
class MinesButton(discord.ui.Button):
    def __init__(self, index: int):
        super().__init__(style=discord.ButtonStyle.secondary, emoji=unknownEmo, row=index // 5)
        self.index = index

    async def callback(self, inter: discord.Interaction):
        mv: 'MinesView' = self.view
        if inter.user.id != mv.user_id:
            await inter.response.send_message("You lost.", ephemeral=True)
            return
        if mv.tiles[self.index]:
            mv.game_over = True
            new_log(inter.user.id, f"The user {inter.user.display_name} played mines with {mv.bombs} bombs, he lost {mv.bet:,} currentBal (after bet): {getBal(str(mv.user_id)):,}, user_id: {mv.user_id}")
            self.emoji = notSafeEmo
            self.style = discord.ButtonStyle.danger
            self.disabled = True
            finMSG = f"{notSafeEmo} **You Hit a BOMB!**"
            await mv.revealBoard(finMSG)
            if mv.cashout_msg:
                try:
                    await mv.cashout_msg.edit(view=None)
                except:
                    pass
            await inter.response.edit_message(view=mv)
            return

        self.emoji = safeEmo
        self.style = discord.ButtonStyle.success
        self.disabled = True
        mv.opened.add(self.index)

        total_tiles = 25
        safe_tiles = 25 - mv.bombs
        currenO = 1.0
        for i in range(len(mv.opened)):
            currT = total_tiles - i
            currS = safe_tiles - i
            currenO *= (currT / currS)

        mv.mult = currenO * housingEdge
        await inter.response.edit_message(view=mv)

        if mv.cashout_msg:
            try:
                embed = discord.Embed(
                    title=f"**Mines**",
                    description=f"Current Multiplier **x{mv.mult:.2f}**\nWinnings: **{int(mv.bet * mv.mult):,}**",
                    color=discord.Color.green()
                )
                await mv.cashout_msg.edit(embed=embed)
            except:
                pass

class MinesView(discord.ui.View):
    def __init__(self, user_id: int, bet: int, bombs: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.bet = bet
        self.bombs = bombs
        self.tiles = [False] * 25
        self.opened = set()
        self.mult = 1.0
        self.game_over = False
        self.msg = None
        self.cashout_msg = None
        placed = 0
        while placed < bombs:
            i = random.randint(0, 24)
            if not self.tiles[i]:
                self.tiles[i] = True
                placed += 1

        for i in range(25):
            self.add_item(MinesButton(i))

    async def revealBoard(self, finMSG: str):
        for child in self.children:
            if isinstance(child, MinesButton):
                child.disabled = True
                is_bomb = self.tiles[child.index]
                if child.style == discord.ButtonStyle.danger:
                    continue
                if child.index in self.opened:
                    child.style = discord.ButtonStyle.success
                    child.emoji = safeEmo
                else:
                    child.style = discord.ButtonStyle.secondary
                    if is_bomb:
                        child.emoji = notSafeEmo
                        
                    else:
                        child.emoji = safeEmo

        if self.cashout_msg and finMSG.startswith(f"{notSafeEmo2}"):#hi
            try:
                embed = discord.Embed(
                    title=f"{notSafeEmo} Mines",
                    description=finMSG,
                    color=discord.Color.red()
                )
                await self.cashout_msg.edit(embed=embed, view=None)
            except:
                pass

    async def spawn_cashout(self, inter: discord.Interaction):
        parent_view = self

        class CashoutView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=300)

            @discord.ui.button(label="Cash Out", emoji="<:emoji_10:1444986106188796035>", style=discord.ButtonStyle.green)
            async def cash(self, inter: discord.Interaction, button: discord.ui.Button):
                if inter.user.id != parent_view.user_id:
                    await inter.response.send_message("this isn't your game", ephemeral=True)
                    return
                if parent_view.game_over:
                    return
                parent_view.game_over = True
                win_amt = int(parent_view.bet * parent_view.mult)
                setBal(str(parent_view.user_id), getBal(str(parent_view.user_id)) + win_amt)
                final_text = f"{safeEmo} **CASHED OUT!** You Cashed Out With a {parent_view.mult:.2f} multi and **{win_amt:,}** Coins"
                await parent_view.revealBoard(f"{notSafeEmo2} **You Hit a Bomb **")
                final_embed = discord.Embed(
                    title=f"{safeEmo} Cashed Out!",
                    description=final_text,
                    color=discord.Color.gold()
                )
                new_log(inter.user.id, f"The user {inter.user.display_name} played Mines with {parent_view.bombs} bombs, he cashed out with a {parent_view.mult:.2f} multi and won {win_amt:,}, user id: {inter.user.id}, currentBal (after bet): {getBal(str(inter.user.id)):,}")
                await inter.response.edit_message(embed=final_embed, view=None)

        c_view = CashoutView()
        iembed = discord.Embed(
            title=f"**Mines**",
            description=f"Current Multiplier: **x1.00**\nWinnings: **{self.bet:,}**",
            color=discord.Color.green()
        )
        try:
            parent_view.cashout_msg = await inter.followup.send(
                embed=iembed,
                view=c_view
            )
        except:
            pass

@bot.tree.command(name="mines", description="Play mines game, 5x5, Multiplier depends on the qmount bombs, PLEASE GO TO #help FOR MORE INFO!")
@app_commands.describe(amount="bet amount", bombs="Number of bombs, more bombs = more money per click")
async def minesCMD(inter: discord.Interaction, amount: str, bombs: int):
  if inter.channel.id in blocked:
        return await inter.response.send_message(
            "You can't do that here ❌", ephemeral=True
        )
  uid = str(inter.user.id)
  bet = parse(amount)
  bal = getBal(uid)
  if bet <= 0:
    await IBA(inter)
    return
  if bet > bal:
      await NEB(inter)
      return
  if bombs < 1 or bombs > 24:
      await inter.response.send_message("Bombs need to be more than zero and less thah 25", ephemeral=True)
      return
  setBal(uid, bal - bet)
  mv = MinesView(inter.user.id, bet, bombs)
  await inter.response.send_message(content=None, view=mv)
  mv.msg = await inter.original_response()
  mv.user = inter.user
  await mv.spawn_cashout(inter)


# i willmmakemthe multipliers in a functiin so i can chqnge them easily
# i will also f9cus more on the nammes of the variables and functions to make it easier to review unlike my other projects :p
C_Conifg = {
  "easy": {"risk": 7, "mult": 1.065},
  "medium": {"risk": 12, "mult": 1.11},
  "hard": {"risk": 20, "mult": 1.19},
} #
roadlength = 5

class ChickenView(discord.ui.View):
  def __init__(self, bet, user_id, difficulty):
    super().__init__(timeout=300)
    self.bet = bet 
    self.user_id = user_id
    self.difficulty = difficulty
    self.config = C_Conifg[difficulty]
    self.current_mult = 1.0
    self.stepsTaken = 0 
    self.game_over = False
    self.safeJumps = 0 
    self.max_multiplier = 1.0 
    self.predetairmain() # i need this so i can display how muxh the user could have stayed and jumped for, like how much money you couldve got if stayed 
  def predetairmain(self):
    risk = self.config["risk"]
    mult_step = self.config["mult"]
    while True:
      roll = random.randint(1, 100)
      if roll <= risk:
        break
      else:
        self.safeJumps += 1 
        self.max_multiplier *= mult_step
  def ProgressBar(self, lostAtStep=None): # Progress Bar
    bar = []
    for i in range(roadlength):
      step_index = i + 1 
      if lostAtStep is not None and step_index == lostAtStep:
        bar.append("🟥")
      elif step_index <= self.stepsTaken:
        bar.append("🟩")
      elif step_index == self.stepsTaken + 1 and not self.game_over:
        bar.append("🐔")
      else:
        bar.append("⬜")
    if self.stepsTaken == roadlength and not self.game_over:
      return "".join(["🟩"] * roadlength)
  
    return "".join(bar)
  async def interaction_check(self, inter):
    return inter.user.id == self.user_id
  def createE(self, title, description, color, lostAtStep = None):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.add_field(name="Road Progress", value=self.ProgressBar(lostAtStep), inline=False)
    embed.add_field(name="Multiplier", value=f"x{self.current_mult:.2f}")
    if not self.game_over:
      embed.description += f"\nDifficulty: {self.difficulty.capitalize()}"
      return embed
  @discord.ui.button(label="Jump", style=discord.ButtonStyle.green, emoji="🐔")
  async def jump_btn(self, inter: discord.Interaction, _):
    if self.game_over:
      return
    self.stepsTaken += 1
    if self.stepsTaken > self.safeJumps:
      self.game_over = True
      self.clear_items()
      embed = discord.Embed(
        title="Chicken got ran over",
        description="You jumped and got ran over.",
        color=discord.Color.red()
      )
      new_log(self.user_id, f"The user {inter.user.display_name} played ChickenRoad with {self.difficulty} difficulty, he lost after {self.stepsTaken} jumps, leaving away a x{self.current_mult:.2f}, user id: {self.user_id}, currentBal (after bet): {getBal(str(inter.user.id)):,} ")
      embed.add_field(name="Progress", value=self.ProgressBar(lostAtStep=self.stepsTaken), inline=False)
      await inter.response.edit_message(embed=embed, view=None)
    else:
      self.current_mult *= self.config["mult"]
      if self.stepsTaken == roadlength:
        self.game_over = True
        self.clear_items()
        win_amt = int(self.bet * self.current_mult)
        uid = str(self.user_id)
        setBal(uid, getBal(uid) + win_amt)
        embed = discord.Embed()
        embed.title="End of the road"
        embed.description=f"You reached the end of the road, You cashed out with **{win_amt:,}** coins! x**{self.current_mult:.2f}** multi!"
        embed.color=discord.Color.gold()
        win_amt = round(self.bet * self.current_mult)
        new_log(inter.user.id, f"The user {inter.user.display_name} played ChickenRoad with {self.difficulty} difficulty, he reached the end of the road and automatically cashed out with {win_amt:,} and a {self.current_mult:.2f} multi, initial bet: {self.bet:,} user id: {inter.user.id}, currentBal (after bet): {getBal(str(inter.user.id)):,}")
        await inter.response.edit_message(embed=embed, view=None)
      else:
        embed = self.createE(
          
          "Chicken Road",
          "The chicken successfully crossed the road",
          discord.Color.gold()
        )
        win_amt = round(self.bet * self.current_mult)
        await inter.response.edit_message(embed=embed, view=self)
  @discord.ui.button(label="Cashout", style=discord.ButtonStyle.red, emoji="💰")
  async def cashoutBtn(self, inter: discord.Interaction, _):
    if self.game_over:
      return
    self.game_over = True
    self.clear_items()
    win_amt = int(self.bet * self.current_mult)
    uid = str(self.user_id)
    setBal(uid, getBal(uid) + win_amt)
    
    embed = discord.Embed(
      title=f"💰 Cashed Out",
      description=f"You cashed out with **{win_amt:,}** coins at a **x{self.current_mult:.2f}** Multiplier",
      color=discord.Color.gold()
    )
    new_log(inter.user.id, f"The user {inter.user.display_name} played ChickenRoad on {self.difficulty} difficulty, he cashed out with {win_amt:,} and a x{self.current_mult:.2f} multi, initial bet: {self.bet:,}, user id: {inter.user.id}, currentBal (after bet): {getBal(str(self.user_id)):,}")
    embed.add_field(name="Potential Winnings", value=f"You could Jumped **{self.safeJumps}** and got a **x{self.max_multiplier:.2f}** Multi!", inline=False)
    await inter.response.edit_message(embed=embed, view=None)

class ChickenStartView(discord.ui.View):
  def __init__(self, bet, user_id):
    super().__init__(timeout=300)
    self.bet = bet 
    self.user_id = user_id
  async def interaction_check(self, inter):
    return inter.user.id == self.user_id
  async def start_game(self, inter: discord.Interaction, difficulty: str):
    uid = str(self.user_id)
    bal = getBal(uid)
    if self.bet > bal:
      await inter.response.send_message("You do not have enough money", embed=None, view=None)
      return
    setBal(uid, bal - self.bet)
    game_view = ChickenView(self.bet, self.user_id, difficulty)
    embed = game_view.createE(
      f"Chicken Road",
      f"Difficulty: **{difficulty.capitalize()}**",
      discord.Color.blue()
    )
    await inter.response.edit_message(embed=embed, view=game_view)
  @discord.ui.button(label="Easy", style=discord.ButtonStyle.green, emoji="<:emoji_11:1445342239583899791>")
  async def easy_btn(self, inter: discord.Interaction, _):
    await self.start_game(inter, "easy")
  @discord.ui.button(label="Medium", style=discord.ButtonStyle.blurple, emoji="<:emoji_12:1445342413043269663>")
  async def medium_btn(self, inter: discord.Interaction, _):
    await self.start_game(inter, "medium")
  @discord.ui.button(label="Hard", style=discord.ButtonStyle.red, emoji="<:emoji_13:1445342515346800670>")
  async def hard_btn(self, inter: discord.Interaction, _):
    await self.start_game(inter, "hard")
@bot.tree.command(name="chicken", description="go to #chances for multipliers and chances info")
@app_commands.describe(amount="Bet")
async def chicken(inter: discord.Interaction, amount: str):
  if inter.channel.id in blocked:
        return await inter.response.send_message(
            "You can't do that here ❌", ephemeral=True
        )
  uid = str(inter.user.id)
  amt = parse(amount)
  bal = getBal(uid)
  if amt <= 0:
    await IBA(inter)
    return
  if amt > bal:
    await NEB(inter)
    return
  view = ChickenStartView(amt, inter.user.id)
  embed = discord.Embed(
    title="<:emoji_14:1445349973272166490> Chicken Road",
    description=f"Choose difficulty, go to #chances if you need to know more about each difficulties",
    color=discord.Color.blue()
  )
  await inter.response.send_message(embed=embed, view=view)


CodesF = "codes.json"
TARGET_CHANNEL_ID = 1445414674433572956
if os.path.exists(CodesF):
  try:
    with open(CodesF, "r") as f:
      codes = json.load(f)
  except:
    codes = {}
else:
  codes = {}
def saveCodes():
  f = open(CodesF, "w")
  json.dump(codes, f, indent=4)
  f.close()
def generate_code(length=10):
  characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  while True:
    code = ''.join(random.choice(characters) for _ in range(length))
    if code not in codes:
      return code
@bot.event 
async def on_message(message):
  if message.author == bot.user:
    return
  if message.channel.id == TARGET_CHANNEL_ID:
    if not message.content.lower().startswith('/gencode'):
      try:
        await message.delete()
        try:
          await message.author.send(
            f"Your message in <#{TARGET_CHANNEL_ID}> was deleted. This channel is **ONLY USED FOR GENERATING AND SHARING CODES.**",
          )
        except discord.Forbidden:
          await message.channel.send(
            f"Your message in <#{TARGET_CHANNEL_ID}> was deleted. This channel is **ONLY USED FOR GENERATING AND SHARING CODES.**",
            delete_after=3.854838332206783
          )
      except discord.Forbidden:
        print(f"Bot doesn't have premssion to delete the message")
  await bot.process_commands(message)
def block_channel():
    async def predicate(inter: discord.Interaction):
        # Block all commands in this channel
        return inter.channel_id != TARGET_CHANNEL_ID
    return app_commands.check(predicate)
@bot.tree.command(name="gencode", description="generate a code, $1M minimum, 1-30 Uses. PLEASE USE #HELP FOR ANY QUESTIONS.")
@app_commands.describe(
  amount="amount of money per use",
  uses="How many times the code can be used by differnt people",
  custom_message="Message You Want alot of People To see",
  silent="Weather to Ping The Role When Creating The Code.",
)
async def gencode_cmd(inter: discord.Interaction, amount: str, uses: int, custom_message: str = "", silent: bool = False):
  is_admin = inter.user.guild_permissions.administrator
  if inter.channel_id != TARGET_CHANNEL_ID and not is_admin:
    channelm = f"<#{TARGET_CHANNEL_ID}>"
    await inter.response.send_message(f"This command can only be used in {channelm}.", ephemeral=True)
    return
  uid = str(inter.user.id)
  try:
    amtV = parse(amount)
    
  except:
    await inter.response.send_message("invalid amount.", ephemeral=True)
    return
  maxUSES = 30
  if not is_admin:
    if uses < 1 or uses > 30:
      await inter.response.send_message(f"uses must be between 1 and 30", ephemeral=True)
      return
  elif uses < 1:
    await inter.response.send_message("Uses must be greater than Zero.", ephemeral=True)
    return
  if len(custom_message) > 100 and not is_admin:
    await inter.response.send_message("The custom message can't be longer than 100 characters.", ephemeral=True)
    return
  if amtV <= 0:
    await IBA(inter)
    return
  totalV = amtV * uses 
  MPU = 250000
  if not is_admin and amtV < MPU:
    await NEB(inter)
    return
  MTV = 1000000 
  if not is_admin and totalV < MTV:
    await inter.response.send_message(f"The total value of your code needs to be more than $1M.", ephemeral=True)
    return
  cost = totalV
  cost_msg = f"Cost: {cost:,} coins"
  if not is_admin:
    currentB = int(getBal(uid))
    if currentB < cost:
      await inter.response.send_message(f"You do not have enough money for this code, it costs **{cost:,}**", ephemeral=True)
      return
    setBal(uid, currentB - cost)
  newCode = generate_code()
  new_log(inter.user.id, f"The user {inter.user.display_name} generated a code: {newCode},  it gives {amtV:,} per use ({amtV * 0.95:,.0f} after 5% tax) and it has {uses}, total cost: {totalV}, currentBal (after making this code): {getBal(str(inter.user.id)):,}, user id: {inter.user.id}")
  pingP = "<@&1445664081187967137>" if not silent else ""
  customMsg = f"\n\n## *{custom_message}*" if custom_message else ""

  msg_txt = (
    f"{pingP} **NEW CODE** has just been posted by {inter.user.mention}!\n"
    f"Show him some love in chat! ❤️<a:emoji_15:1445685849407750227>\n"
    f"Value: **{amtV:,}** Per Use!\n\n"
    f"# `/redeem code:{newCode}` - `/redeem code:{newCode}` - `/redeem code:{newCode}`"
    f"\n\n## {inter.user.mention} says: {customMsg}"
  )
  await inter.response.send_message(msg_txt)
  response_message = await inter.original_response()
  puplicMID = str(response_message.id)
  codes[newCode] = {
    "amount": amtV,
    "uses": uses,
    "generated_by": uid,
    "redeemed_by": [],
    "message_id": puplicMID,
  }
  saveCodes()
  titleT = f"Code ---- {amtV:,} Per!"
  color_code = discord.Color.green()
  pembed = discord.Embed(
    title=titleT,
    color=color_code,
    description=""
  )
  pembed.add_field(name="Value", value=f"{amtV:,}", inline=True)
  pembed.add_field(name="Uses Left:", value=f"{uses}", inline=True)
  pembed.add_field(name="Total Value", value=f"{totalV:,}")
  pembed.set_footer(text=cost_msg)
  await inter.edit_original_response(content=msg_txt, embed=pembed)
  



@bot.tree.command(name="redeem", description="Redeem a code")
@app_commands.describe(code="Enter the code that you got from the cldes channel ")
async def redeem_cmd(inter: discord.Interaction, code: str):
  if inter.channel.id in blocked:
        return await inter.response.send_message(
            "You can't do that here ❌ (You need to redeem the code elsewhere.)", ephemeral=True
        )
  uid = str(inter.user.id)
  norm_code = code.upper()
  isInCodeChannel = inter.channel_id == TARGET_CHANNEL_ID
  if norm_code not in codes: # decided to make it so i can delete codes after they expire
    await inter.response.send_message("Invalid or expired code.", ephemeral=True)
    return
  code_data = codes[norm_code]
  if code_data["uses"] <= 0:
    await inter.response.send_message("This code has no uses left.", ephemeral=True)
    return
  if uid in code_data["redeemed_by"]:
    await inter.response.send_message("You have already redeemed this code.", ephemeral=True)
    return
  amount_gained = int(code_data["amount"] * 0.95) # %5 tax because the whole point of me making this bot is to make me money, obviously. this will not include real life money or something that can be valued at real life money like robux.
  setBal(uid, getBal(uid) + amount_gained)
  code_data["uses"] -= 1 
  code_data["redeemed_by"].append(uid)
  generator_id = int(code_data["generated_by"])
  generator = inter.guild.get_member(generator_id)
  new_log(uid, f"The user {inter.user.display_name} redeemed a code and got {amount_gained:,} from it (after 5% tax), it was generated_by {code_data["generated_by"]} it has {code_data["uses"]} uses after this usage, currentBal (after /redeeming the code): {getBal(str(inter.user.id)):,}, user id: {inter.user.id}")
  if generator is None:
    generatorNAME = f"<@{generator_id}>"
  else:
    generatorNAME = generator.mention
  current_uses = code_data["uses"]
  message_id = code_data.get("message_id")
  
  embed_color = discord.Color.green()
  display_uses = current_uses
  saveCodes()
  if message_id:
    try:
      channel = inter.guild.get_channel(TARGET_CHANNEL_ID)
      msg = await channel.fetch_message(int(message_id))
      uses_line = f'Uses: **{display_uses}**'
      if display_uses > 0:
        uses_line += " ツ"
        
      new_content = re.sub(r"Uses: \*\*\d+\*\*( ツ)?", uses_line, msg.content) # Unfortunately, i used chatgpt here, because i honestly don't want to learn another library just to use it once. i am already getting close to finishing my bot and reaching 120 hours in moonshot. i am also very tight on time with the 12 Dec deadline.
      await msg.edit(content=new_content)
      new_color = discord.Color.green() if display_uses > 0 else discord.Color.red()
      newEmbed = discord.Embed(
        title=f"Code - {code_data["amount"]:,} Per!",
        color=new_color
      )
      newEmbed.add_field(name="Value", value=f"{code_data['amount']:,}", inline=True)
      newEmbed.add_field(name="Uses", value=f"{display_uses}", inline=True)
      totalV = code_data['amount'] * code_data.get("maxUSES", display_uses)
      newEmbed.add_field(name="Total Value", value=f"{totalV:,}")
      await msg.edit(embed=newEmbed)
    except Exception as e:
      print("didnt update message ", e)
  embed = discord.Embed(
    title="<a:emoji_16:1445771098095616030> CODE REDEEMED!",
    color=embed_color,
    description=f"You got **{int(amount_gained):,}** coins from the code that was generated by <@{generator_id}>, 5% tax applied!"
  )
  await inter.response.send_message(embed=embed)
slotEmos = {
  "GOLD": "<:gold:1447910070980575336>",
  "EMERALD": "<:emerald:1447910031818489906>",
  "DIAMOND": "<:diamond:1444330316528488579>",
  "QUARTZ": "<:quartz:1447910566680334478>",
  "REDSTONE": "<:redstone:1447910240485117993>",
  "COPPER": "<:copper:1447910285246468207>",
  "COAL": "<:coal:1447910373280841769>",
  "BAD": ":no_entry:",
  "NETH": "<:neth:1447910452334952449>"
}
slotsATM = ["GOLD", "EMERALD", "DIAMOND", "QUARTZ", "REDSTONE", "COPPER", "COAL", "BAD", "NETH"]
slotchance = (13.857, 13.857, 13.857, 13.857, 13.857, 13.857, 13.857, 14.5, 3)
def spin(prev=None):
  while True:
    s = random.choices(slotsATM, weights=slotchance, k=1)[0]
    if s != prev:
      return s 
def FR(reels):
  out = []
  for r in reels:
    if r in slotEmos:
      out.append(slotEmos[r])
    else:
      out.append(str(r))
  return "  |  ".join(out)
def eReel(reels):
  counts = {s: reels.count(s) for s in slotsATM}
  if counts["NETH"] == 3:
    return 100.0, "JACKPOT - 3x NETH!"
  if counts["NETH"] == 2:
    return 8.0, "Mini Jackpot - 2 NETH"
  if counts["NETH"] == 1:
    for s in ("GOLD", "EMERALD", "DIAMOND", "QUARTZ", "REDSTONE", "COPPER", "COAL"):
      if counts[s] == 2:
        return 4.0, f"Two {s.title()} + NETH"
    return 2.0, "One Neth"
  for s in ("GOLD", "EMERALD", "DIAMOND", "QUARTZ", "REDSTONE", "COPPER", "COAL"):
    if counts[s] == 3:
      return 5.0, f"Triple {s.title()}"
    if counts[s] == 2:
      return 2.0, f"Two {s.title()}"
  return 0.0, "No combination."
async def de_es(inter, amount_str):
  if inter.channel.id in blocked:
    await inter.response.send_message("You can't do that here", ephemeral=True)
    return
  u_i_d = str(inter.user.id)
  try:
    bet = parse(amount_str)
  except:
    await inter.response.send_message("Invalid bet amount.", ephemeral=True)
  if bet  <= 0:
    await IBA(inter)
    return
  bal = getBal(u_i_d)
  if bet > bal:
    await NEB(inter)
    return # you cant be seeing this XD
  setBal(u_i_d, bal - bet)
  embed = discord.Embed(title="Slots", color=discord.Color.blue())
  embed.description = "**Spinning..**\n" + FR(["?", "?", "?"])
  embed.add_field(name="Bet", value=f"{bet:,}")
  embed.set_footer(text=inter.user.name)
  await inter.response.send_message(embed=embed)
  msg = await inter.original_response()
  final = ["?", "?", "?"]
  prev = [None, None, None]
  spinsT = 4 
  try:
    for r in range(3):
      for _ in range(spinsT):
        final[r] = spin(prev[r])
        prev[r] = final[r]
        anim = discord.Embed(title="Slots", color=discord.Color.blue())
        anim.description = f"**Spinning**...\n {FR(final)}"
        anim.add_field(name="Bet", value=f"{bet:,}")
        anim.set_footer(text=inter.user.name)
        try:
          await msg.edit(embed=anim) 
        except:
          pass 
        await asyncio.sleep(0.1)
    mult, reason = eReel(final)
    win = int(bet * mult)
    resultttt = discord.Embed(title="Slots", color=discord.Color.gold() if mult > 0 else discord.Color.red())
    resultttt.description = FR(final)
    if mult > 0:
      setBal(u_i_d, getBal(u_i_d) + win)
      resultttt.add_field(name="Slots", value=f"You **WON**! x{mult} - {reason}")
      resultttt.add_field(name="Winnings", value=f"{win:,}")
      resultttt.set_footer(text=inter.user.name)
      new_log(u_i_d, f"The user {inter.user.display_name} played Slots and won with {win:,} at a x{mult} multi, bet: {bet:,}, currentBal (after playing): {getBal(u_i_d):,} user id: {u_i_d} ----- Wheels: {final}")
    else:
      resultttt.add_field(name="Slots", value="You Lost - Zero Match.")
      resultttt.set_footer(text=inter.user.name)
      new_log(u_i_d, f"The user {inter.user.display_name} played Slots and Lost, bet: {bet:,}, currentBal (after bet): {getBal(u_i_d):,}, uid: {u_i_d} ----- Wheels: {final}")
    await msg.edit(embed=resultttt)
  except Exception as errrr:
    print(errrr)
@bot.tree.command(name="slots", description="Play slot machine. #help for chances and overall help.")
@app_commands.describe(amount="bet")
async def sm(inter, amount: str):
  await de_es(inter, amount)
@bot.event
async def on_member_join(member: discord.Member):
  try:
    new_log(None, f"The user {member.display_name} joined the server, user id: {member.id}")
  except Exception as er:
    print(f"Failed: {er}")
@bot.event 
async def on_member_remove(memberr: discord.Member):
  try:
    new_log(None, f"The user {memberr.display_name} left/got kicked/got banned from the server. user id: {memberr.id}")
  except Exception as err:
    print(f"Failed: {err}")
class CrashView(discord.ui.View):
  def __init__(self, u_id, bet__amt):
    super().__init__(timeout=None)
    self.u_id = u_id
    self.bet__amt = bet__amt
    self.isCashed = False
    self.currMulti = 1.0
  @discord.ui.button(label="Stop", emoji="✋", style=discord.ButtonStyle.red)
  async def Stop(self, inter: discord.Interaction, button: discord.ui.Button):
    if not self.isCashed:
      self.isCashed = True
      button.disabled = True
      await inter.response.defer()
@bot.tree.command(name="crash", description="Crash")
@app_commands.describe(amount="bet amount")
async def crashCMD(inter: discord.Interaction, amount: str):
  u_id = str(inter.user.id)
  bett = parse(amount)
  bal = getBal(u_id)
  if bett <= 0:
    await IBA(inter)
    return
  if bett > bal:
    await NEB(inter)
    return
  setBal(u_id, bal - bett)
  CL = 1.1 
  while random.randint(1, 100) > 10:
    CL += 0.1 
  CL = round(CL, 1)
  view = CrashView(u_id, bett)
  result = discord.Embed(title="Crash", color=discord.Color.green())
  result.add_field(name="Multiplier", value="x1.0")
  result.add_field(name="Winnings", value=f"{int(bett):,}")
  result.set_footer(text=f"{inter.user.name}")
  await inter.response.send_message(embed=result, view=view)
  msg = await inter.original_response()
  while not view.isCashed:
    await asyncio.sleep(0.35)
    if view.currMulti >= CL:
      result = discord.Embed(title="Crash", color=discord.Color.red())
      result.add_field(name="Multiplier", value=f"x{view.currMulti:.1f}")
      result.add_field(name="Winnings", value=f"~~{bett:,}~~")
      view.stop()
      new_log(u_id, f"The user {inter.user.display_name} played crash and lost {bett:,}, last multiplier: {view.currMulti}, bet: {bett:,}, uid: {inter.user.id}, currentBal: {getBal(u_id)}")
      return await msg.edit(embed=result, view=None)
    
    
    
    
    
    if not view.isCashed:
      pp = int(bett * view.currMulti)
      result = discord.Embed(title="Crash", color=discord.Color.green())
      result.add_field(name="Multiplier", value=f"x{view.currMulti:.1f}")
      result.add_field(name="Winnings", value=f"{pp:,}")
      result.set_footer(text=f"{inter.user.name}")
      await msg.edit(embed=result)
      view.currMulti = round(view.currMulti + 0.1, 1)
  if view.isCashed:
    ATW = int((bett * view.currMulti) * 0.95)
    setBal(u_id, bal + ATW)
    result = discord.Embed(title="Crash", color=discord.Color.gold(), description=f"You cashed out in crash! You could have reached x**{CL:.1f}**")
    result.add_field(name="Multiplier", value=f"{view.currMulti:.1f}")
    result.add_field(name="Winnings", value=f"**{ATW:,}** (5% Tax)")
    result.add_field(name="Profit", value=f"**{ATW - bett:,}**")
    result.set_footer(text=f"{inter.user.name}")
    new_log(u_id, f"The user {inter.user.display_name} played crash and won, he cashed ojt with {ATW:,} (5% Tax), bet: {bett:,}, currentBal: {bal:,}, user id: {inter.user.id}"
    ) # i think the tax will mess up the ai and machine learning but idk bout that maybe after i get a machine learnig device or so, after learning more about machine learning, dude why am i telling my life story???
    await msg.edit(embed=result, view=None)
  
  
bot.run(TOKEN)