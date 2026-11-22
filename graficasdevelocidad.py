import track_trackspoint as tt
import matplotlib.pyplot as plt
import folium
from textwrap import fill


#main will call all the graph creation
def main():
    mspeeds, averages, point_times, point_distances, sample_ids, points = tt.calcs()
    matrix = tt.m()
    print(averages)
    print(averages.describe())
    print(matrix.columns.tolist())
    matrix = tt.m()
    matrix, averages = dropreport(matrix, averages)
    print(averages.describe())
    map(matrix)
    samplegraphs(mspeeds, point_distances, sample_ids)

def dropreport(matrix, averages):
    min_meters = 100
    min_seconds = 30
    manual_ids = [31, 51, 38039, 38018, 54, 55, 56]  # Use [] for cutoffs alone

    # One row per track, including tracks with only one recorded point
    track_ids = matrix["track_id"].drop_duplicates()
    report = averages[["Distance(m)", "tseconds"]].reindex(track_ids).fillna(0)

    #returns true or false, if true it its under the cut off line
    under_distance = report["Distance(m)"] < min_meters
    under_time = report["tseconds"] < min_seconds
    on_manual_list = report.index.isin(manual_ids)
    #check what is under the cutooff | meas or.
    below_cutoff = under_distance | under_time
    dropped = report.loc[below_cutoff | on_manual_list]
    #len report give the total amount of routes first argument give how many are dropped
    print(f"{below_cutoff.sum()} of {len(report)} routes are below a cutoff.")
    #how many are dropped in total including manual
    print(f"{len(dropped)} routes dropped in total.")

    eligible_for_cutoffs = ~on_manual_list #prioritizes manual cut offi n the table if its on the list it wont be checked for the other options

    #dictionary
    groups = {
        "Manual exclusion": on_manual_list,
        f"Under {min_meters} m only": eligible_for_cutoffs & under_distance & ~under_time,
        f"Under {min_seconds} s only": eligible_for_cutoffs & under_time & ~under_distance,
        "Under both cutoffs": eligible_for_cutoffs & under_distance & under_time,
    }

    #table heater
    width = 80
    print(f"\n{'Reason':<24} {'Listed':>6} {'Dropped':>7}  Track IDs")
    print("-" * width)

    for reason, matches in groups.items(): # cheacks each dictionary entry. for the reason and value
        matched_ids = report.index[matches].sort_values() # selects coditiosn which have True. sor values put it in ascending order
        if reason == "Manual exclusion": # if manual excluded it is ecual to manual id
            listed_ids = manual_ids
        else:
            listed_ids = matched_ids
        # convertis each id to text and joins it with a comma, if no ids = -
        ids_text = ", ".join(str(i) if i in report.index else f"{i} (absent)"for i in listed_ids) or "—"
        label = f"{reason:<24} {len(listed_ids):>6} {len(matched_ids):>7}  "

        print(fill(ids_text,width=width,initial_indent=label,subsequent_indent=" " * len(label),))

    dropped_ids = dropped.index
    return (matrix.loc[~matrix["track_id"].isin(dropped_ids)].copy(), averages.loc[~averages.index.isin(dropped_ids)].copy(),)

def samplegraphs(mspeeds,totaldistance, sample_ids):
    plt.figure(figsize=(12, 7)) # to show case all six graphs at once

    for panel, i in enumerate(sample_ids, start=1):
        track = mspeeds.loc[mspeeds["track_id"] == i]
        elapsed = track["seconds"].cumsum()

        plt.subplot(2, 3, panel)
        plt.plot(elapsed, track["speed"])
        plt.title(f"Track {i}")
        plt.xlabel("Elapsed time (s)")
        plt.ylabel("Speed (m/s)")

    plt.tight_layout()
    plt.show()

def map(points):
    route_map = folium.Map(tiles="OpenStreetMap") #creates the map

    tracks = points.groupby("track_id", sort=False)

    for number, (track_id, track) in enumerate(tracks):
        hue = (number * 137) % 360
        route_color = f"hsl({hue}, 75%, 40%)"
        # Connect the GPS points in the order they were recorded.
        track = track.sort_values("time", kind="stable")
        coordinates = list(zip(track["latitude"], track["longitude"]))
        label = f"Track {track_id}"

        if len(coordinates) == 1:
            folium.CircleMarker(
                location=coordinates[0],
                radius=5,
                color=route_color,
                fill=True,
                fill_opacity=1,
                tooltip=label,
            ).add_to(route_map)
        else:
            folium.PolyLine(
                locations=coordinates,
                color=route_color,
                weight=3,
                tooltip=label,
            ).add_to(route_map)

    (south, west), (north, east) = route_map.get_bounds()

    if south is not None and west is not None and north is not None and east is not None:
        route_map.fit_bounds([[south, west], [north, east]])

    route_map.save("gps_routes.html")


if __name__ == "__main__":
    main()
