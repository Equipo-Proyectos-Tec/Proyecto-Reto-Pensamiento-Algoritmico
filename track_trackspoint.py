import pandas as pd
from math import dist
#reads file with the data
matrix = pd.read_csv("/Users/gabrielburbano/Desktop/Situacion problema/go_track_trackspoints.csv")

def main():
    matrixcoordiantes = matrix.drop(columns=["time"])
    time = matrix.drop(columns=["longitude", "latitude"])
    convert_time(time)




#get time taken in seconds form each point and overall per track
def convert_time(time):
    timestamps = pd.to_datetime(time["time"])
    time["seconds_between"] = timestamps.diff().dt.total_seconds()
    time = time.dropna()
    overall_times = pd.DataFrame(columns=["Track","Overalltime"])


# gets distance between points and give the overall
def get_distance(matrixcoordiantes):
    points = [(1, 2), (4, 6), (4, 9)]

    total = 0
    for start, end in zip(points, points[1:]):
        distance = dist(start, end)
        print(f"{start} → {end}: {distance:.2f} units")
        total += distance

    print(f"Total distance: {total:.2f} units")

if __name__ == "__main__":
    main()