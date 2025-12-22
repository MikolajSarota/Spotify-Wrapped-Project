import pandas as pd
import glob

# Data Collection 

parent_folder = r"Your Spotify History File"
file_pattern = "Streaming_History_Audio_*.json"

dfs = [
    pd.read_json(file)
    for file in glob.glob(f"{parent_folder}/{file_pattern}")
]

df = pd.concat(dfs, ignore_index=True)

# Preparation of Data

df = df[["ts", "master_metadata_album_artist_name", "master_metadata_track_name", "ms_played", "reason_start", "skipped"]]
df.rename(
    columns={
        "ts": "time_stamp",
        "master_metadata_album_artist_name": "artist_name",
        "master_metadata_track_name": "track_name",
        "ms_played": "time_ms"
    },
    inplace=True
)

df["time_min"] = df["time_ms"] / 60 / 1000
df.drop("time_ms", inplace=True, axis=1)

df["time_stamp"] = pd.to_datetime(df["time_stamp"])

df["date_only"] = df["time_stamp"].dt.date
df["year"] = df["time_stamp"].dt.year
df["month"] = df["time_stamp"].dt.month
df["weekday"] = df["time_stamp"].dt.day_name()
df["hour"] = df["time_stamp"].dt.hour

df = df.sort_values("year", ascending=True)

# Defining seasons

def season(month):
    if month in [3,4,5]:
        return "Spring"
    elif month in [6,7,8]:
        return "Summer"
    elif month in [9,10,11]:
        return "Autumn"
    else:
        return "Winter"

df["season"] = df["month"].apply(season)

# Seasonal Songs

seasonal_songs = (
    df.groupby(["season", "artist_name", "track_name"])
    .size()
    .sort_values(ascending=False)
    .reset_index(name="plays")
)

print("\n", seasonal_songs.groupby("season").head(3).sort_values(by="season").set_index("season"))

# Most listened song

most_listened_song = df["track_name"].mode()[0]
most_listened_artist = (
    df.loc[df["track_name"] == most_listened_song, "artist_name"].mode()[0]
)

print("\n", f"Your most listened song of all time is: {most_listened_song} by {most_listened_artist}.")

# Top 10 most listened song vs time listened in summer

summer_df = df[df["season"] == "Summer"]

top_10_summer_songs = (
    summer_df
    .groupby(["artist_name", "track_name"])["time_min"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index(name="total_time_min")
)

print("\nTop 10 most listened songs in summer:")
print(top_10_summer_songs)

# Morning or evening listener 

morning = df[(df["hour"] >= 5) & (df["hour"] <= 11)]
evening = df[(df["hour"] >= 18) & (df["hour"] <= 23)]

morning_time = morning["time_min"].sum()
evening_time = evening["time_min"].sum()
total_time = df["time_min"].sum()

morning_time_ratio = (morning_time / total_time) * 100
evening_time_ratio = (evening_time / total_time) * 100

if morning_time > evening_time:
    print("\n", f"You are a mornning listener. {morning_time_ratio.round(2)}% of your total listening time was spent in the mornings")
if morning_time < evening_time:
    print("\n", f"You are an evening listener. {evening_time_ratio.round(2)}% of your total listening time was spent in the evenings")
else:
    print("\n", "You do not have preferred listening time")

# Listening Streak

dates = sorted(df["date_only"].unique())

streak = 1
max_streak = 1

for i in range(1, len(dates)):
    if (dates[i] - dates[i-1]).days == 1:
        streak += 1
        if streak > max_streak:
            max_streak = streak
    else:
        streak = 1

print(f"\nLongest listening streak: {max_streak} days")

# Top 3 most often selected song by clicks

most_selected_song = (
    df[df["reason_start"] == "clickrow"]
    .groupby(["artist_name", "track_name"])
    .size()
    .sort_values(ascending=False)
    .reset_index(name="click_count")
)

print("\n", most_selected_song.head(3).set_index("track_name"))

# Saving to CSV for Power BI visualisations

most_listened_df = pd.DataFrame({
    "track_name": [most_listened_song],
    "artist_name": [most_listened_artist]
})

listening_time_df = pd.DataFrame({
    "metric": [
        "morning_time_min",
        "evening_time_min",
        "total_time_min",
        "morning_time_ratio_percent",
        "evening_time_ratio_percent"
    ],
    "value": [
        morning_time,
        evening_time,
        total_time,
        morning_time_ratio,
        evening_time_ratio
    ]
})

streak_df = pd.DataFrame({
    "longest_listening_streak_days": [max_streak]
})

most_clicked_df = most_selected_song.head(3)

seasonal_top_df = seasonal_songs.groupby("season").head(3)

most_listened_df.to_csv("most_listened_song.csv", index=False)
top_10_summer_songs.to_csv("top_10_summer_songs_by_time.csv", index=False)
listening_time_df.to_csv("listening_time_distribution.csv", index=False)
streak_df.to_csv("longest_listening_streak.csv", index=False)
most_clicked_df.to_csv("top_3_most_clicked_songs.csv", index=False)
seasonal_top_df.to_csv("top_3_seasonal_songs.csv", index=False)

