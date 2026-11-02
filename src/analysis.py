import polars as pl
#first 20 games in schedule
#print(pl.read_parquet("data/raw/schedules.parquet").head(20))

#displays the amount of plays in each year.
pbp = pl.read_parquet("data/raw/pbp.parquet")
print(pbp.height)
print(pbp.group_by("season").len().sort("season"))