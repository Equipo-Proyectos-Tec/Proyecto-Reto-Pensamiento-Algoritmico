import track_trackspoint as tt
import matplotlib.pyplot as plt
import folium
from textwrap import fill
import pandas as pd
from math import ceil

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
    histograma_velocidades(averages)
    velocidades_tercios = boxplots_tercios(matrix, point_distances)
    print(velocidades_tercios.head().round(2))
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
        plt.ylim(0, 25)
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

def boxplots_tercios(matrix, point_distances):
    # Une la hora de cada punto con la distancia desde el punto anterior
    claves = ["track_id", "id"]
    datos = matrix[claves + ["time"]].merge(
        point_distances[claves + ["Distance(m)"]],
        on=claves,
        validate="one_to_one",
    )
    datos["time"] = pd.to_datetime(datos["time"])
    datos = datos.sort_values(["track_id", "time", "id"])

    filas = []
    for track_id, ruta in datos.groupby("track_id", sort=False):
        metros = ruta["Distance(m)"].cumsum().to_numpy()
        segundos = (ruta["time"] - ruta["time"].iloc[0]).dt.total_seconds().to_numpy()
        tercio_m = metros[-1] / 3

        # Encuentra en qué segundo se alcanzó 1/3 y 2/3 de la distancia
        cruces = []
        for corte in (tercio_m, 2 * tercio_m):
            j = metros.searchsorted(corte)
            fraccion = (corte - metros[j - 1]) / (metros[j] - metros[j - 1])
            tiempo_cruce = segundos[j - 1] + fraccion * (segundos[j] - segundos[j - 1])
            cruces.append(tiempo_cruce)

        t1, t2 = cruces
        duraciones = [t1, t2 - t1, segundos[-1] - t2]
        velocidades = [tercio_m / dt if dt > 0 else float("nan") for dt in duraciones]
        filas.append([track_id, *velocidades])

    # Una fila por ruta y una columna por tercio
    etapas = ["Inicio", "Mitad", "Final"]
    resumen = pd.DataFrame(filas, columns=["track_id", *etapas]).set_index("track_id")

    fig, ax = plt.subplots(figsize=(8, 5))
    resumen.boxplot(column=etapas, ax=ax, grid=False, showmeans=True)
    ax.set_title(f"Velocidad media por tercio del recorrido ({len(resumen)} rutas)")
    ax.set_ylabel("Velocidad media (m/s)")
    fig.tight_layout()

    return resumen

def histograma_velocidades(averages):
    velocidades = (averages["Distance(m)"] / averages["tseconds"]).dropna()
    if velocidades.empty:
        print("No hay rutas para graficar.")
        return

    # Elige un ancho entero que permita incluir la ruta más rápida
    intervalos = 10
    ancho = max(1, ceil(velocidades.max() / intervalos))
    limite = intervalos * ancho

    fig, ax = plt.subplots(figsize=(9, 5))
    _, bordes, barras = ax.hist(
        velocidades, bins=intervalos, range=(0, limite),
        color="teal", edgecolor="white",
    )

    ax.set_xticks(bordes)
    ax.bar_label(barras, fmt="%.0f", padding=3)
    ax.set_title(f"Velocidad media por ruta ({len(velocidades)} rutas)")
    ax.set_xlabel("Velocidad media de la ruta (m/s)")
    ax.set_ylabel("Número de rutas")
    fig.tight_layout()
#test
if __name__ == "__main__":
    main()
