# this file will create the features that the models are trained on

import polars as pl

# pulls in the data needed
team_games = pl.read_parquet("data/processed/team_games.parquet")
elo = pl.read_parquet("data/processed/elo.parquet")
schedule = (pl.read_parquet("data/raw/schedules.parquet").filter(pl.col("game_type")=="REG"))


# creates the pre_game_stats dataframe
# it creates a new col called roll_... which is the average of epa/points so far in the season
# will add more columns later to see if it increase performace 
pre_game_stats = (
    team_games.sort(["team", "season", "week"])
    .with_columns(
        pl.col("off_epa").shift(1).rolling_mean(window_size=5, min_samples=1)
            .over(["team", "season"]).alias("roll_off_epa"),
        pl.col("def_epa").shift(1).rolling_mean(window_size=5, min_samples=1)
                    .over(["team", "season"]).alias("roll_def_epa"),
        pl.col("net_epa").shift(1).rolling_mean(window_size=5, min_samples=1)
                    .over(["team", "season"]).alias("roll_net_epa"),
        pl.col("point_diff").shift(1).rolling_mean(window_size=5, min_samples=1)
                    .over(["team", "season"]).alias("roll_point_diff"),
    ).with_columns(
        pl.col("roll_off_epa", "roll_def_epa", "roll_point_diff").fill_null(0)
        )
)

#print(pre_game_stats.filter(pl.col("team") == "KC", pl.col("season") == 2022))

# pre game stats of home team
home_stats = pre_game_stats.select(
    "game_id",
    pl.col("team").alias("home_team"),
    pl.col("roll_off_epa").alias("home_off_roll_epa"),
    pl.col("roll_def_epa").alias("home_def_roll_epa"),
    pl.col("roll_net_epa").alias("home_net_roll_epa"),
    pl.col("roll_point_diff").alias("home_point_roll_diff")
    )

# pre game stats of away team
away_stats = pre_game_stats.select(
    "game_id",
    pl.col("team").alias("away_team"),
    pl.col("roll_off_epa").alias("away_off_roll_epa"),
    pl.col("roll_def_epa").alias("away_def_roll_epa"),
    pl.col("roll_net_epa").alias("away_net_roll_epa"),
    pl.col("roll_point_diff").alias("away_point_roll_diff")
    )

# this is the dataframe the the model will be given
game_table = (
    # cols we want
    schedule.select(
        "game_id", "season", "week", "home_team", "away_team", "home_score", 
        "away_score", "home_rest", "away_rest", "div_game", "location",
    )

    # makes each game one row:
    .join(home_stats, on=["game_id", "home_team"])
    .join(away_stats, on=["game_id", "away_team"])
    # adds the cols
    .with_columns(
        (pl.col("home_off_roll_epa") - pl.col("away_off_roll_epa")).alias("off_epa_diff"),
        (pl.col("home_def_roll_epa") - pl.col("away_def_roll_epa")).alias("def_epa_diff"),
        (pl.col("home_point_roll_diff") - pl.col("away_point_roll_diff")).alias("point_diff_diff"),
        (pl.col("home_rest") - pl.col("away_rest")).alias("rest_diff"),
        (pl.col("location") == "Neutral").cast(pl.Int8).alias("neutral_site"),
    )
    # joins the fram with the pre-game Elo
    .join(elo, on="game_id")
    .with_columns((pl.col("home_cur_elo") - pl.col("away_cur_elo")).alias("elo_diff"))
    # 1 if the home team won, droping the score from the df
    .filter(pl.col("home_score") != pl.col("away_score"))
    .with_columns((pl.col("home_score") > pl.col("away_score")).cast(pl.Int8).alias("home_win"))
    # what we will keep and save to the parquet
    .select(
        "game_id", "season", "week", "home_team", "away_team",
        "off_epa_diff", "def_epa_diff", "point_diff_diff",
        "rest_diff", "div_game", "neutral_site", "elo_diff",
        "home_win_prob", "home_win",
    )

)

game_table.write_parquet("data/processed/game_table.parquet")


