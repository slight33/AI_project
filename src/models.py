import polars as pl
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

# start in 2012 so that elo has had some time
TRAIN_START, TRAIN_END = 2012, 2019   
# testing on years 2020 and 2021
TEST_START, TEST_END = 2020, 2021                   

# input list so nothing else can slip in
FEATURES = [
    "off_epa_diff", "def_epa_diff", "point_diff_diff",
    "rest_diff", "div_game", "neutral_site", "elo_diff",
]
# reads in the data and filters to the season wanted
game_table = pl.read_parquet("data/processed/game_table.parquet")
train = game_table.filter(pl.col("season").is_between(TRAIN_START, TRAIN_END))
val = game_table.filter(pl.col("season").is_between(TEST_START, TEST_END))

# splits up the data into testing and traing data
X_train, y_train = train.select(FEATURES).to_numpy(), train["home_win"].to_numpy()
X_test, y_test = val.select(FEATURES).to_numpy(), val["home_win"].to_numpy()

# sets up the obj
model = make_pipeline(StandardScaler(), LogisticRegression())
# trains
model.fit(X_train, y_train)
# predicts
pred = model.predict_proba(X_test)[:, 1]

print("log loss:", log_loss(y_test, pred))
print("Brier:", brier_score_loss(y_test, pred))
print("accuracy:", accuracy_score(y_test, pred > 0.5))