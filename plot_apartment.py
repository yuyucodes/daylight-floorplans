import sys
import pandas as pd
import plotly.graph_objects as go
from matplotlib import cm
from matplotlib.colors import Normalize, to_hex
from shapely import wkt
from shapely.ops import triangulate

# every daylight time slot in the dataset
HOURS = {
    "20180321": ["0800", "1000", "1200", "1400", "1600", "1800"],
    "20180621": ["0600", "0800", "1000", "1200", "1400", "1600", "1800", "2000"],
    "20181221": ["1000", "1200", "1400", "1600"],
}
SUN = [f"sun_{d}{h}" for d, hs in HOURS.items() for h in hs]
COLS = [s + "_median" for s in SUN]
HEIGHT = 2.5  # room height in meters
# optional apartment id from the command line
apt = sys.argv[1] if len(sys.argv) > 1 else None

# only the needed columns and first 200k rows (file is 1.5 GB)
sims = pd.read_csv("simulations.csv", usecols=["apartment_id", "area_id"] + COLS, nrows=200_000)
if apt is None:
    apt = sims["apartment_id"].sample(1).iloc[0]  # pick a random apartment
sims = sims[sims["apartment_id"] == apt].drop(columns="apartment_id")

# read the big geometry file in chunks, keep only this apartment's rooms
parts = []
cols = ["entity_type", "entity_subtype", "geometry", "apartment_id", "area_id"]
for chunk in pd.read_csv("geometries.csv", usecols=cols, chunksize=200_000):
    parts.append(chunk[(chunk["entity_type"] == "area") & (chunk["apartment_id"] == apt)])
# attach each room's daylight values to its shape
areas = pd.concat(parts).merge(sims, on="area_id").reset_index(drop=True)


def label(sun):
    return pd.to_datetime(sun[4:], format="%Y%m%d%H%M").strftime("%d %b %H:%M")


def colors(col):
    norm = Normalize(areas[col].min(), areas[col].max())
    return [to_hex(cm.YlOrRd(norm(v))) for v in areas[col]]


def names(col, sun):
    # shown on hover: room type and daylight value
    return [f"{t}<br>{label(sun)}: {v:.2f}" for t, v in zip(areas["entity_subtype"], areas[col])]


def room_mesh(poly):
    """walls, floor and ceiling of a polygon extruded up to HEIGHT"""
    ring = list(poly.exterior.coords)[:-1]
    n = len(ring)
    x = [p[0] for p in ring] * 2
    y = [p[1] for p in ring] * 2
    z = [0] * n + [HEIGHT] * n
    i, j, k = [], [], []
    for a in range(n):  # each wall is two triangles
        b = (a + 1) % n
        i += [a, a]
        j += [b, b + n]
        k += [b + n, a + n]
    for t in triangulate(poly):  # floor and ceiling, with their own vertices
        if poly.contains(t.centroid):
            pts = list(t.exterior.coords)[:3]
            for h in (0, HEIGHT):
                m = len(x)
                x += [p[0] for p in pts]
                y += [p[1] for p in pts]
                z += [h] * 3
                i.append(m)
                j.append(m + 1)
                k.append(m + 2)
    return x, y, z, i, j, k


all_colors = [colors(c) for c in COLS]
all_names = [names(c, s) for c, s in zip(COLS, SUN)]

fig = go.Figure()
for n, row in areas.iterrows():
    poly = wkt.loads(row["geometry"])  # parse the WKT text into a polygon
    x, y, z, i, j, k = room_mesh(poly)
    fig.add_trace(go.Mesh3d(
        x=x, y=y, z=z, i=i, j=j, k=k,
        color=all_colors[0][n], flatshading=True,
        name=all_names[0][n], hoverinfo="name", showlegend=False,
    ))

# dropdown: swap every room's color and hover text to the chosen time slot
buttons = [
    dict(label=label(s), method="restyle", args=[{"color": all_colors[m], "name": all_names[m]}])
    for m, s in enumerate(SUN)
]
fig.update_layout(
    title=f"Apartment {apt[:8]}",
    updatemenus=[dict(buttons=buttons, x=0, y=1.1)],
    scene=dict(aspectmode="data", xaxis_visible=False, yaxis_visible=False, zaxis_visible=False),
)
fig.write_html("apartment.html", auto_open=True)  # drag to rotate, hover a room to inspect