import pandas as pd
import matplotlib.pyplot as plt

# every daylight time slot in the dataset
HOURS = {
    "20180321": ["0800", "1000", "1200", "1400", "1600", "1800"],
    "20180621": ["0600", "0800", "1000", "1200", "1400", "1600", "1800", "2000"],
    "20181221": ["1000", "1200", "1400", "1600"],
}
TITLES = {"20180321": "21 March", "20180621": "21 June", "20181221": "21 December"}
COLS = [f"sun_{d}{h}_median" for d, hs in HOURS.items() for h in hs]
SEG = "location_rating_NASE_W_DOM"
SEGMENTS = {
    1: "Rural-traditional", 2: "Modern worker", 3: "Transitional-alternative",
    4: "Traditional middle class", 5: "Liberal middle class", 6: "Established alternative",
    7: "Upper middle class", 8: "Professional elite", 9: "Urban elite",
}

sims = pd.read_csv("simulations.csv", usecols=["building_id", "layout_number_of_windows"] + COLS)
sims = sims[sims["layout_number_of_windows"] > 0]  # skip rooms without windows
# one value per building and time slot: mean over its rooms
daylight = sims.groupby("building_id")[COLS].mean()

ratings = pd.read_csv("location_ratings.csv", usecols=["building_id", SEG]).set_index("building_id")
df = ratings.join(daylight, how="inner").dropna()
df = df[df[SEG] <= 9]  # drop buildings with unknown segment

# mean daylight per segment for every time slot
by_seg = df.groupby(SEG)[COLS].mean()
by_seg.index = by_seg.index.map(lambda s: SEGMENTS[int(s)])
print(by_seg.round(2).T)

fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
for ax, (day, hours) in zip(axes, HOURS.items()):
    for n, seg in enumerate(by_seg.index):
        ax.plot([f"{h[:2]}:00" for h in hours], by_seg.loc[seg, [f"sun_{day}{h}_median" for h in hours]],
                marker="o", color=plt.cm.viridis(n / 8), label=seg)
    ax.set_title(TITLES[day])
axes[0].set_ylabel("mean daylight (klx)")
axes[-1].legend(fontsize=8)
plt.tight_layout()
plt.savefig("daylight_by_segment.png", dpi=150)