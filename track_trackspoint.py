import pandas as pd
from geopy.distance import geodesic
from pathlib import Path

#reads file with the data
def m():
    repo_root = Path(__file__).resolve().parent
    matrix = pd.read_csv(repo_root / "CSVS/go_track_trackspoints.csv")
    matrix["track_order"] = matrix.groupby("track_id", sort=False).ngroup()
    matrix = matrix.sort_values("track_order", kind="stable").drop(columns="track_order")
    return matrix

def calcs():
    matrix = m()
    matrixcoordiantes = matrix.drop(columns=["time"])
    time = matrix.drop(columns=["longitude", "latitude"])
    total_time, point_times = convert_time(time)
    total_distance, point_distances = get_distance(matrixcoordiantes)
    mspeeds, averages, sample_ids, points = calcspeed(point_times, point_distances, total_distance, total_time)
    return mspeeds, averages,point_times, point_distances, sample_ids, points


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

    return total, time
    #print matrix, there should be 38093 rows including titles. There is only 162221 = some # are skipepd in the csv
    #checking cvs there are jumps between id of up to 4, plus there is a couple hundred vlaues dropped due to drop.na

# gets distance between points and give the overall
def get_distance(points): # matrix has first id, then latitude, lognitude and lastly track_id.
    #creates matrix for the total
    totaldistance = pd.DataFrame()
    totaldistance["track_id"] = points["track_id"].unique()
    totaldistance["Distance(m)"] = 0.0 #sets all the rows to zero to be able to add, importnat to be a float
    totaldistance = totaldistance.set_index("track_id")

    #creates a matrix for the in point analisis
    perpoint = points.drop(columns=["longitude", "latitude"]) # only ids and distance to pair with seconds
    perpoint["Distance(m)"] = 0.0 # sets all zero to change as a float
    for i in range(1,len(points)):
        previous = points.iloc[i-1] # get the rpevious row
        current = points.iloc[i]# get the current row
        track_id = current["track_id"]
        if previous["track_id"] != track_id: #if previous row doesnt have the same track id continue
            continue
        start = (previous["latitude"], previous["longitude"])# Previous row as (latitude, longitude)
        end = (current["latitude"], current["longitude"])# Current row as (latitude, longitude)
        distance_m = geodesic(start, end).meters #calculates the lenght between points in meter

        point_row = points.index[i]
        perpoint.loc[point_row, "Distance(m)"] = distance_m
        totaldistance.loc[track_id, "Distance(m)"] += distance_m

    return totaldistance, perpoint

def calcspeed(times, distances, totaldistance, totaltime):
    sample_positions = [11, 77, 131]
    track_ids = totaldistance.index.tolist()
    #match is, and do every point in that id
    sample_ids = [track_ids[i - 1] for i in sample_positions]
    print(pd.DataFrame({"section": sample_positions, "track_id": sample_ids}))

    points = distances.merge(
        times[["track_id", "id", "seconds"]],
        on=["track_id", "id"],
        how="left",
        validate="one_to_one",
    ) # new maitris, merges distnaces with respective times
    seconds = points["seconds"]
    points["speed"] = points["Distance(m)"] / seconds.where(seconds >0)
    # Keep every point belonging to the six selected tracks
    mspeeds = points.loc[points["track_id"].isin(sample_ids)].copy()

    #calcualtes avg speeds
    averages = totaldistance.join(totaltime)#joins both matrixes
    duration = averages["tseconds"]# makes a list of the vergaes
    averages["avg_speed"] = averages["Distance(m)"] / duration.where(duration > 0) #gets avg speeds
    return mspeeds, averages, sample_ids, points
    #calcualte avg vleocities and plot them

if __name__ == "__main__":
    calcs()