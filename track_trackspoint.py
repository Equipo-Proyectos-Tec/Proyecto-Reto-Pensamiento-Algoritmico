import pandas as pd
from math import dist
from geopy.distance import geodesic
#reads file with the data
matrix = pd.read_csv("/Users/gabrielburbano/Desktop/Situacion problema/go_track_trackspoints.csv")

def main():
    matrixcoordiantes = matrix.drop(columns=["time"])
    time = matrix.drop(columns=["longitude", "latitude"])
    convert_time(time)
    get_distance(matrixcoordiantes)


#get time taken in seconds form each point and overall per track
def convert_time(time):
    #convert dates into time in seconds
    timestamps = pd.to_datetime(time["time"])
    # check track are different, if not it will calculate times between tracks
    same_track = time["track_id"] == time["track_id"].shift()
    time["seconds"] = timestamps.diff().dt.total_seconds().where(same_track)# add the column to the matrix
    time = time.dropna(subset=["seconds"])#drops the first column which has an NA reading
    time = time.drop(columns=["time"])#drops the column of dates

    # adds times to a total
    total = pd.DataFrame(columns=["track_id", "tseconds"]) #creates a matrix with these 2 columns
    total["track_id"] = time["track_id"].unique()#adds the rows for track id, discard duplciates
    total["tseconds"] = 0.0 #sets seconds to a int to be able to add
    total = total.set_index("track_id")#needed to use track id as a row label in the for loop.
    #get the 2 values from orginal matrix, the id with its econds, and adds it to the new matriz with total times
    for track_id, seconds in zip(time["track_id"], time["seconds"]):
        if pd.notna(seconds):
            total.loc[track_id, "tseconds"] += seconds #gives a matrix with the total of seconds per track

    print(total.reset_index)
    #print matrix, there should be 38093 rows including titles. There is only 162221 = some # are skipepd in the csv
    #checking cvs there are jumps between id of up to 4, plus there is a couple hundred vlaues drop due to drop.na

# gets distance between points and give the overall
def get_distance(points): # matrix has first id, then latitude, lognitude and lastly track_id.
    totaldistance = pd.DataFrame(columns=["track_id","Distance(m)"])
    totaldistance["track_id"] = points["track_id"].unique()
    totaldistance["Distance(m)"] = 0.0
    perpoint = points.copy(points)
    perpoints = perpoint.drop(columns=["longitude", "latitude"])
    total = 0
    for i in range(1, len(points)):
        start = tuple((points.loc[i-1,"latitude"], points.loc[i-1, "longitude"])) # Previous row as (latitude, longitude)
        end = tuple((points.loc[i,"latitude"], points.loc[i, "longitude"]))  # Current row as (latitude, longitude)



if __name__ == "__main__":
    main()