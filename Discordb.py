import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import os 
from config import TOKEN

BALS = "balances.json" # i am aware of whay you might think of this name
firstBal = 25000
housingEdge = 0.97

if os.path.exists(BALS):
  try:
    with open(BALS, "r") as f:
      balances = json.load(f)
  except:
    balances = {}
else:
  balances = {}

def saveBals():
  f = open(BALS, "w")
  json.dump(balances, f, indent=4)
  f.close()
  
def parseAmount(x):       # i sacraficed mynfingers for yours 🖤 (my fingers: gifted power, yours: pure effort)
  x = x.lower().replace(",", "")
  if x.endswith("k"):
    
    num = float(x[:-1])
    num = num * 1000              
    return int(num)
  if x.endswith("m"):
    num = float(x[:-1])
    num = num * 1000000
    return int(num)
  if x.endswith('b'):
    num = float(x[:-1])
    num * 1000000000
    return int(x)
  return int(x)
  
def getBal(uid):
  if uid in balances:
    return balances[uid]
  elif uid not in balances:
    return firstBal
def setBal(uid, amt):
  balances[uid] = amt
  saveBals()
  
    