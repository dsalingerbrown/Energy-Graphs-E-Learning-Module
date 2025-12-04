import pandas as pd
import matplotlib.pyplot as plt

# Load CSV
df = pd.read_csv("/Users/dannysalingerbrown/Desktop/E-LearningModule_Project/International Energy Agency - electricity generation in World.csv")

# Clean column names
df.columns = df.columns.str.strip().str.lower()

# Latest year
latest_year = df["year"].max()
df_latest = df[df["year"] == latest_year]

# Group by source
mix = df_latest.groupby("electricity generation in world")["value"].sum()

# Remove unwanted sources
remove_sources = ["tide", "other sources", "solar thermal"]
mix = mix.drop(labels=[s for s in remove_sources if s in mix.index], errors='ignore')

total = mix.sum()
mix_pct = (mix / total) * 100
mix_pct = mix_pct.sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(12, 2.5))

left = 0
ypos = 0

for label, pct in mix_pct.items():
    ax.barh(
        y=ypos,
        width=pct,
        left=left,
        label=label
    )

    if pct > 3:
        x_pos = left + pct / 2
        if "solar pv" in label.lower():
            x_pos += 2  # nudge text right

        ax.text(
            x=x_pos,
            y=ypos,
            s=f"{label}: {pct:.1f}%",
            va="center",
            ha="center",
            fontsize=9,
            color="white",
            weight="bold"
        )

    left += pct

ax.set_xlim(0, 100)
ax.set_yticks([])
ax.set_xlabel("Share of Total Generation (%)", fontsize=12)
ax.set_title(f"Electricity Generation by Source, {df['year'].max()}", fontsize=14, weight="bold")

# Axes-level legend (recommended for short figures)
ax.legend(
    ncol=4,
    loc='upper center',
    bbox_to_anchor=(0.5, -0.25),  # negative moves it below x-axis
    frameon=False
)

# Adjust bottom margin so legend is fully visible
fig.subplots_adjust(bottom=0.35)  # increase from 0.3 to give extra space



plt.show()
