# GessDotPie
These are some games from a gambling discord bot, here are the commands and here are their descriptions:


# Roll
usage: /roll amount:(bet) target:(target) choice:(over/under)


The roll game is a game where a random number generator (1-100) generates a random number, to win: the number needs to be (higher or lower than your target depending on your choice) after winning, you have the option to roll again or cash out, your multiplier is calculated based on how risky your bet was, you can roll as much as you want.

# Balance
usage: /balance


A command that displays the user's balance.

# Leaderboard
usage: /leaderboard


This command is used to display the leaderboard (money wise).

# admingivemoney
usage: /admingivemoney user:(discord user) amount:(amount)


An admin can use this command to give money of any amount to any member (even themselves).

# admintakemoney
usage: /admintakemoney user:(discord user) amount:(amount) reason:(reason for the logs, for example: withdrawl, fraud etc.)

# Hilo
usage: /hilo amount:(bet)


Hilo is a game where a random number generator (1-13) will generate a number at first, you will guess if the number is going to be higher or lower for example the first number was 8, your best chance will be to choose lower. if the number was lower than 8 you'll win, the number cannot be 8, and if the random number generator generates 8, it will be 50/50 to be 9 or 7.

# givemoney
usage: /givemoney user:(discord user) amount(amount)


/givemoney is often used to exchange server currency between members.

# Blackjack
usage: /blackjack amount(bet)


Blackjack is a rather complicated game where you get two poker cards automatically drawn at the start, you can hit (draw again) or stand (stop drawkng and confirming your hand), your goal is to get as close to 21 as possible without going over it, as well as trying to get higher than what the dealer gets after you stand, the dealer will hit until he is closer tl 21 than you or he goes over 21 and you win, if the dealer gets closer to 21 than you you lose, if you hit and get more than 21 you lose, if the dealer gets the same as you it prefers to draw, giving you your bet untouched.

# PaperRedstone
usage: /paper amount:(bet)


Paper game is a Minecraft inspired game where two (paper and redstone) random number generators (1-9) generate a number and you have to choose either paper or redstone and hope you get a higher number than the other thing you didnt choose, tie = loss btw (house edge).

# Mines
usage: /mines amount:(bet) bombs:(1-24)


Mines is a game where you pick tiles and hope that the tile you chose didnt have a bomb in it, the multiplier varies depending on the risk, if you pick all on 1 bomb you get a 24x ish multiplier, but you can get it way higher with another number of bombs (bug). The grid size is 5x5

# Chicken Road 
usage: /chicken amount:(bet)


Chicken is a game where you jump and hope you dont crashor get hit by a car, jumping increases a multiplier and you can choose three difficulties: easy, medium and hard, the harder the difficulty the better the multiplier. here are the chances and multiplier of each difficulty: easy: 7% chance of losing each jump, jumping multiplies the multiplier by x1.065, so first it will be 1.0 then 1.065 then 1.134 etc, medium: 12% chance of losing each jump, jumping multiplies the multiplier by x1.11, hard: 20% chance of losing each jump, jumping multiplies the multiplier by x1.19. the road length is 35 jumps wide.

# GenCode
usage: /gencode amount:(amount) uses:(amount lf uses) OPTIONAL custom_message:(string) silent:(true/false)


This command is used to generate a code that can be used by any users and gain money from the code, a 5% tax will be taken from people who redeem the code, the code must match a very specific critrea: total cost must be more than 1 million and the amount per use must be 250k or more to prevent spam pinging the role. The code contains the alphabet (in capitals) and numbers 1-9.

# Redeem 
usage: /redeem code:(code)


Redeem a code aquired from the quick drops channel, a 5% tax will be applied to the amount recieved.

# Slots
usage: /slots amount:(amount)


A 3 slot game where 2 pieces match (except for bad) you get x2.0 and if you get 3 matches you get x5.0, if you get one netherite (the black ingot) in one of the slots, you get 2x, if you get 2 netherite you will get x8.0, if you get one neth6\erite and 2 normal ores you get x4.0, if you get 3 netherite you get x100!! 

# Crash 
usage: /crash amount:(amount)


A multiplier rises every 0.35 seconds (it somewhat depends on the speed of your machine) by 0.1, each time there is a 10% chance of losing, unlike roll, instead of multipling the multiplier, it adds 0.1 to the multiplier which... who cares man if you dont have to press roll 1000 times it's worth it. also there is a 5% tax, you need to press stop before it stops and you crash, if you stop you will see how much have you gotten.

# General info and features about my bot

## 1:
You can end amount bets or basically anything about money with "k", "m" and "b" and "k" = "thousand", "m" = "million", "b" = "billion", you can also put "all" to bet on all of your balance, "half" to bet half of your balance.

## 2:
Every thing that change the balance of any player or the member count, will get logged in a "wierd" way because it makes it easier for the machine learning in the future because sometimes its a bet and sometimes its not, so i decided to make it so it's easy to read

## 3:
all the bot commands are slash commant and have auto complete for the amount and any other fields needed.

## 4:
i didnt want to make a bot with a strong influence with real life gambling mechanics, this bot is not supposed to have any association with real life gambling.