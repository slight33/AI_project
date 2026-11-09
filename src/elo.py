# elo refernce: https://web.archive.org/web/20250306215142/https://fivethirtyeight.com/methodology/how-our-nfl-predictions-work/

import polars as pl
import math

k = 20       # how fast the ratings move (tuned later)
hfa = 48     # home field advantage (typically inpacts spreed by 3) (tuned later)
hfa_covid = 33  # games during covid did not have fans
bye_week = 25    # teams coming off a bye
starting = 1505   # inital elo rating
regress = 2/5     # new season refresh
rested = 13       # if a team has a rest_time > than 13, they had a bye week


# ------load the data, filter by season, and sort:---------
schedules = (
    pl.read_parquet("data/raw/schedules.parquet").filter(pl.col("game_type") == "REG").sort(["season", "week", "gameday"])
)


# -------creates a list of all teams:----------
teams = schedules["home_team"].unique().to_list()
ratings = {}
# assings the team the base starting elo rating:
for team in teams:
    ratings[team] = starting


current_season = None
results = []

# --------loop runs each game and updates the elo:----------
for game in schedules.iter_rows(named=True): # returns a dict
    # new season refresh:
    if game["season"] != current_season:
        for team in ratings:
            ratings[team] += regress * (starting - ratings[team])
        # sets next season
        current_season = game["season"]

    # grabs the teams playing along with the elo before the game occurs
    home = game["home_team"]
    away = game["away_team"]
    home_cur_elo = ratings[home]
    away_cur_elo = ratings[away]

    # adjust the elo for home vs away games as well as rest time
    net_elo_diff = home_cur_elo - away_cur_elo
    if game["location"] == "Home":
        # covid year had less fans, so hfa is lowered
        if game["season"] == 2020:
            net_elo_diff += hfa_covid
        # non covid year
        else:
            net_elo_diff += hfa

        # adjust for rest week:
        # if home team had a rest week, add the bonus
        if game["home_rest"] >= rested:
            net_elo_diff += bye_week
        # if away team had a rest week, subtract the bonus
        if game["away_rest"] >= rested:
            net_elo_diff -= bye_week

    # find the win probablity of home team
    # from the article reference:
    home_win_prob = 1 / (10**(-net_elo_diff/400) + 1)

    # save the results:
    results.append({
        "game_id": game["game_id"],
        "home_cur_elo": home_cur_elo,
        "away_cur_elo": away_cur_elo,
        "home_win_prob": home_win_prob,
        })

    # update the elo after result:
    score_margin = game["home_score"] - game["away_score"]
    if score_margin > 0:
        result = 1              # home team won
        winner_diff = net_elo_diff
    elif score_margin < 0:
        result = 0              # home team lost
        winner_diff = -net_elo_diff
    else:   
        result = .5             # the game tied
        winner_diff = net_elo_diff      # will be zero 

    # elo multiplier from article
    mult = math.log(abs(score_margin) + 1) * (2.2 / (winner_diff * 0.001 + 2.2))

    # elo change formula (from refrence)
    elo_change = k * mult * (result - home_win_prob)
    # apply the elo change:
    ratings[home] += elo_change
    ratings[away] -= elo_change
    
    # save the results in a parquet file
    frame = pl.DataFrame(results)
    frame.write_parquet("data/processed/elo.parquet")
    









