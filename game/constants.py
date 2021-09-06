squad_rules = {
    "squad_size": 11,
    "DEF_min": 3,
    "DEF_max": 5,
    "MID_min": 3,
    "MID_max": 5,
    "FWD_min": 1,
    "FWD_max": 3,
    "GKP_min": 1,
    "GKP_max": 1 
}

manager_max_balance = 105.0         # the total balance of a manager
max_bid = 15.0                      # max bid can be offered in auction 

player_buy_penalty = 2.0            # point penalty when a manager buys a player after auction 
player_sell_penalty = 2.0           # point penalty when a manager sells a player after auction 
player_offer_buy_penalty = 0.0      # point penalty when a manager buys a player from another manager 
player_offer_sell_penalty = 0.0     # point penalty when a manager sells a player to another manager 

player_sell_cost_decrease = 0.2     # Decrease in sell cost when a manager sells the player directly

min_benched_player = 4

fwd = "FWD"
mid = "MID"
df = "DEF"
gkp = "GKP"