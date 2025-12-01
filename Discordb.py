import discord
from discord.ext import  commands
from discord import app_commands
import json
import os 
import random
from config import TOKEN
import asyncio
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
  
@bot.tree.command(name="givemoney", description="Give money to fellow members.")
async def givemoney(inter, user: discord.Member, amount: str):
  SID = str(inter.user.id)
  RID = str(user.id)
  
  if SID == RID:
    await inter.response.send_message("You **__Cannot__** Send money to __yourself__", ephemeral=True)
    return
  
  amt = parse(amount)
  sBal = getBal(SID)
  
  if amt <= 0:
    await inter.response.send_message("Invalid Amount.", ephemeral=True)
    return
  
  if sBal < amt:
    await inter.response.send_message("Not Enough **__Credits__**.", ephemeral=True)
    return
  
  
  setBal(SID, sBal - amt)
  setBal(RID, getBal(RID) + amt)
  
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
    if inter.user.id != self.user_id or self.finished:
      return
    self.player_hand.append(self.draw_card())
    total = sum(c[0] for c in self.player_hand)
    if (total > 21):
      self.finished = True
      self.clear_items()
      embed = discord.Embed(title="You lost.", color=discord.Color.red())
      embed.add_field(name="Your Hand: ", value=self.hand_display(self.player_hand))                    
      embed.add_field(name="Dealer Hand: ", value=f"{self.dealer_hand[0][1]}({self.dealer_hand[0][0]})")
      embed.description = f"Busted! - You Lost"
      await inter.response.edit_message(embed=embed, view=self)
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
      await inter.response.edit_message(embed=embed, view=None)
      return
    embed = discord.Embed(title="Blackjack", color=discord.Color.blue())
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
    elif dealer_total > player_total:
      msg = f"You Lost."
      color = discord.Color.red()
    else:
      msg = "Push! (draw)"
      color = discord.Color.green()
      setBal(str(self.user_id), getBal(str(self.user_id)) + self.bet)
    
    LASTE = discord.Embed(title="Blackjack", color=color)       # yes, my friend taught me that I can do this.
    LASTE.description = msg 
    LASTE.add_field(name="Your Hand", value=self.hand_display(dealer_hand))
    LASTE.add_field(name="Dealer hand", value=self.hand_display(dealer_hand))
    
    
    await inter.edit_original_response(embed=LASTE, view=None)

@bot.tree.command(name="blackjack", description="Play blackjack (x2), PLEASE USE #HELP FOR MORE INFO OR OPEN A SUPPORT TICKET.")
async def blackjack(Interaction: discord.Interaction, bet: str):
  user_id = str(Interaction.user.id)
  betAMT = parse(bet)
  bal = getBal(user_id)
  
  if betAMT > bal:
    await Interaction.response.send_message("You Do Not Have Enough Balance.", ephemeral=True)
    return
  setBal(user_id, bal - betAMT)
  view = blackjackView(betAMT, Interaction.user.id)
  await Interaction.response.send_message(embed=discord.Embed(
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
    else:
      embed = discord.Embed(
        title="PaperRedstone",
        description=f"You Chose **{choice.capitalize()}**!\nPaper: {paper_roll}\nRedstone: {redstone_roll}\n\n**You lost.**",
        color=discord.Color.red()
      )
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
  user_id = str(inter.user.id)
  bet = parse(amount)
  bal = getBal(user_id)
  
  if bet <= 0:
    await inter.response.send_message("Invalid bet Amount", ephemeral=True)
    return
  if bet > bal:
    await inter.response.send_message("You Do NOT Have enough coins.", ephemeral=True)
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
                    title="**:dollar: Mines**",
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

        if self.cashout_msg and finMSG.startswith(f"{notSafeEmo}"):
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
                await parent_view.revealBoard(f"<:UnsafeTile:1444726698301198439> **You Hit a Bomb **")
                final_embed = discord.Embed(
                    title=f"{safeEmo} Cashed Out!",
                    description=final_text,
                    color=discord.Color.gold()
                )
                await inter.response.edit_message(embed=final_embed, view=None)

        c_view = CashoutView()
        iembed = discord.Embed(
            title=f"**Mines** -- {self.bombs} Bombs",
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
    uid = str(inter.user.id)
    bet = parse(amount)
    bal = getBal(uid)
    if bet <= 0:
        await inter.response.send_message("You Need Atleast $1 to bet.", ephemeral=True)
        return
    if bet > bal:
        await inter.response.send_message("you DO NOT have enough money.", ephemeral=True)
        return
    if bombs < 1 or bombs > 24:
        await inter.response.send_message("Bombs need to be more than zero and less thah 25", ephemeral=True)
        return
    setBal(uid, bal - bet)
    mv = MinesView(inter.user.id, bet, bombs)
    await inter.response.send_message(content=None, view=mv)
    mv.msg = await inter.original_response()
    await mv.spawn_cashout(inter)



bot.run(TOKEN)