#---------------------
# This file will turn play by play data into a "report card" for every team.
# Each row is one game per team and describes how well the offense and defence played,
# along with the score.  

# overall goal in this is to record what happend in each game represented as epa's
#---------------------

from pathlib import Path
import nflreadpy as nfl
import polars as pl

# load the data from pbp and scheduels
pbp = pl.read_parquet("data/raw/pbp.parquet")
# fitlers out non regular season games
pbp = pbp.filter(pl.col("season_type") == "REG")
schedules = pl.read_parquet("data/raw/schedules.parquet")
schedules = schedules.filter(pl.col("game_type") == "REG")


# filter by real offensive plays (not inculding qb kneel, spikes, etc):
plays = pbp.filter(
    pl.col("play_type").is_in(["pass", "run"]),
    pl.col("epa").is_not_null(),
    pl.col("posteam").is_not_null(),
    pl.col("qb_kneel") == 0,
    pl.col("qb_spike") == 0,
).with_columns(
    # fill empty null with 0's:
    pl.col("interception").fill_null(0),
    pl.col("fumble_lost").fill_null(0),)


# average out the offensive EPA to find efficiy numbers
offense_avg_epa = plays.group_by(["game_id", "posteam"]).agg(
    # avg offensive epa, puts them in a col named "off_epa"
    pl.col("epa").mean().alias("off_epa"),    
     # numbers of plays, puts this in a col named "off_plays"    
    pl.len().alias("off_plays"),                 
    (pl.col("interception") + pl.col("fumble_lost")).sum().alias("turnovers")    
).sort(["game_id", "posteam"]) # readiblity


#print(offense_avg_epa.head(20))


# fiter defensive plays
defense_avg_epa = plays.group_by(["game_id", "defteam"]).agg(
    # avg defensive epa, puts them in a col named "def_epa"
    pl.col("epa").mean().alias("def_epa"),
    # numbers of plays, puts this in a col named "def_plays" 
    pl.len().alias("def_plays"),
    (pl.col("interception") + pl.col("fumble_lost")).sum().alias("takeaways")
).sort(["game_id", "defteam"])

#print(defense_avg_epa)


# standerize name for join
defense_avg_epa = defense_avg_epa.rename({"defteam": "team"})
offense_avg_epa = offense_avg_epa.rename({"posteam": "team"})

# join the offensive and defensive plays:
stats = offense_avg_epa.join(defense_avg_epa, on=["game_id", "team"])
#print(stats.head(20))


# each game in the schedule, home team perspective
# renames are for the below combination, otherwise they will not stack right
home_team_rows = schedules.select(
    "game_id",
    "season",
    "week",
    pl.col("home_team").alias("team"),      
    pl.col("away_team").alias("opponent"),
    pl.lit(1).alias("is_home"),
    pl.col("home_score").alias("points_for"),
    pl.col("away_score").alias("points_against")
)


# same games and shedule as above, but from the away team perspective
away_team_rows = schedules.select(
    "game_id",
    "season",
    "week",
    pl.col("away_team").alias("team"),
    pl.col("home_team").alias("opponent"),
    pl.lit(0).alias("is_home"),
    pl.col("away_score").alias("points_for"),
    pl.col("home_score").alias("points_against")
).sort(["game_id"])


# combines the 2 tables into one
team_games = (
    # each game becomes 2 rows, one per team
    pl.concat([home_team_rows, away_team_rows]).join(stats, on=["game_id", "team"])
    # added net averages from the research article related work
    .with_columns(
        (pl.col("points_for") - pl.col("points_against")).alias("point_diff"),
        (pl.col("off_epa") - pl.col("def_epa")).alias("net_epa"),
        (pl.col("takeaways") - pl.col("turnovers")).alias("turnover_margin")
        )
    .sort(["season", "week", "game_id", "team"])
)

#print(team_games.head(5))

# saves the data in a parquet file called team_games.parquet
PROC_DIR = Path("data/processed")
PROC_DIR.mkdir(parents=True, exist_ok=True)

team_games.write_parquet(PROC_DIR / "team_games.parquet")
