# elo refernce: https://web.archive.org/web/20250306215142/https://fivethirtyeight.com/methodology/how-our-nfl-predictions-work/


k = 20       # how fast the ratings move (tuned later)
hfa = 48     # home field advantage (typically inpacts spreed by 3) (tuned later)
hfa_covid = 33  # games during covid did not have fans
bye_week = 25    # teams coming off a bye
starting = 1505   # inital elo rating
regress = 1/3     # new season refresh



