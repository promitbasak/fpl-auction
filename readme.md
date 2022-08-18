# FPL Auction mode

## Description
This is an auction mode for the renowned [Fantasy Premier League](https://fantasy.premierleague.com/). In this mode, you are a manager of your team and can buy players in an auction with your friends. Your points will be calculated from the actual Premier League games. For example, if your player do well in actual games, you will get more points. Then, after a gameweek ends, you can buy/sell players from other managers as well as from the auction. Most of the FPL rules are applicable in this mode.

` `  
` `  

## How to use
This project is deployed in heroku. You can try it out by going to [https://fpl-auction.herokuapp.com](https://fpl-auction.herokuapp.com). But, as there are currently no active managers, you cannot do certain tasks like take part in auction.
  
` `  
` `    


## Rules
  

#### General

- You must sign up and then create a manager first in order to participate in game.
- You nedd to choose your public manager name and team name to create a manager profile.
- After that you will buy players and prepare your squad.

#### Auction

- Initially players can be be bought only through the auction room.
- In the auction room, the league manager will raise each player to the bidding platform one by one and the managers will bid for the players. Top bidder wwill get the player.
- If no manager bids for any player, he will remain unsold and can be bought directly after the auction.
- Players can be bought or transferred directly only after the auction is over.

#### Forming a team

- Initially you need to do bid in the auction room, and each of the player will go to the top bidder.
- Before auction, each player will have (price - 1) as bid cost. After bidding is done the players will go back to their original price.
- You can buy any of the unsold players after the auction, or sell any of your player at the price you bought.
- You can offer a bid price other managers to sell you any of their player. If the manager accepts the offer, the player will be added to your team.
- Buy/Sell/Transfer can be penalized by points.

#### Squad Rules

- Each manager will be given a balance of 105.0. You have to buy players within this limit
- You team should contain at least 15 players. Otherwise some of the players will automatically be benched after deadlines and their points will not be added. For example, if you have 13 players, 9 players will be in squad and 4 in bench after the deadline.
- You can add 11 of your players to your playing squad, whose points will be added. The squad may have:
    - 1 Goalkeeper
    - Minimum 3 defenders to maximum 5 defenders
    - Minimum 3 midfielders to maximum 5 midfielders
    - Minimum 1 forwards to maximum 3 forwards
- Minimum 4 players should be in bench whose points will not be added. If not, players from squad will automatically be benched. Players with higher price will be benched first.
- Players will automacally added to playing squad/bench as you buy players. You can swap players from bench to squad as long as that follows the squad rules.

#### Points

- Points will be calculated as per official fpl rules.
- There are no chips/additional powers as of now.

#### Deadlines

- Each gameweek will have a deadline. You have to buy/sell/offer/substitute players before this deadline.
- Player points will not be updated live. Rather they will be calculated after the gameweek ends.
- After the gameweek ends, you can transfer players again after all the points are calculated.
  
  
` `  
` `  
  
  
## Disclaimer

- This is not a stable version. Feel free to report a bug if you see any issue.
