# this file is responsible for pulling and cacheing the data
from pathlib import Path
import nflreadpy as nfl
import polars as pl

#schedule = nfl.load_schedules([2024])
#pbp = nfl.load_schedules([2024])

# seasons we grab the data from
SEASONS = list(range(2010,2026))
# creates the path for the data
RAW_DIR = Path("data/raw")


# play by play columns we want, add or take away from here
PBP_COLUMNS = [
    "game_id", "season", "week", "season_type",
    "posteam", "defteam", "play_type",
    "epa", "success", "interception", "fumble_lost",
    "qb_kneel", "qb_spike",
]

# creates and writes the schedule of a season to the file "schedules.parquet"
def ingest_schedules():
    schedules = nfl.load_schedules(SEASONS)
    schedules.write_parquet(RAW_DIR / "schedules.parquet")

# creates and writes the play by play data to the file "pbp.parquet"
def ingest_pbp():
    frame = []
    for season in SEASONS:
        frame.append(nfl.load_pbp([season]).select(PBP_COLUMNS))
    # combines the frames:
    plays = pl.concat(frame)
    plays.write_parquet(RAW_DIR / "pbp.parquet")


def main():
    # creates the folder data/raw
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ingest_schedules()
    print("getting play by play data")
    ingest_pbp()

if __name__ == "__main__":
    main()

