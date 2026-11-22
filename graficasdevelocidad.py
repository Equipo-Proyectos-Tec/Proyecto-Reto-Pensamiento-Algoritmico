import track_trackspoint as tt
import matplotlib.pyplot as plt

#main will call all the graph creation
def main():
    mspeeds, averages, point_times, point_distances = tt.calcs()
    samplegraphs(mspeeds, point_distances)


def samplegraphs(mspeeds,totaldistance):
    sample_positions = [11, 53, 77, 82, 131, 140]
    track_ids = totaldistance.index.tolist()
    # match is, and do every point in that id
    sample_ids = [track_ids[i - 1] for i in sample_positions]
    for i in sample_ids["track_id"]:
        track = mspeeds.loc[mspeeds["track_id"] == i]  # filters our rows that dont have trac id 16
        elapsed = track["seconds"].cumsum()
        print(elapsed)
        print(track)
        plt.plot(elapsed, track["speed"])
        plt.xlabel("Elapsed Time")
        plt.ylabel("Speed")
        plt.title(f"Speed vs Elapsed Time sectio: {i}")
        plt.show()

if __name__ == "__main__":
    main()
