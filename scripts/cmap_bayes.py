import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
font = {
    'family' : 'normal',
    #'weight' : 'bold',
    'size'   : 18
}

mpl.rc('font', **font)


# Lee & Wagenmakers evidence scale boundaries
bounds = np.array([1, 3, 10, 30, 100, 1000])

labels = [
    "Anecdotal",
    "Moderate",
    "Strong",
    "Very strong",
    "Extreme"
]

fig, ax = plt.subplots(figsize=(4, 5))
colors = plt.cm.viridis(np.linspace(0.05, 0.95, len(labels)))


# Draw colored regions
norm = mpl.colors.LogNorm(vmin=bounds[0], vmax=bounds[-1])
cmap = plt.cm.viridis
for bottom, top in zip(bounds[:-1], bounds[1:]):
    y = np.geomspace(bottom, top, 200)
    X, Y = np.meshgrid([0, 1], y)

    C = y[:-1, None]   # (199, 1)

    ax.pcolormesh(
        X,
        Y,
        C,
        shading="auto",
        cmap=cmap,
        norm=norm,
    )

# Label positions (geometric means)
centers = np.sqrt(bounds[:-1] * bounds[1:])
for c, lab in zip(centers, labels):
    ax.text(
        0.5, c, lab,
        ha="center", va="center",
        color="white", weight="bold",
        transform=ax.get_yaxis_transform()
    )

# Logarithmic y-axis
ax.set_yscale("log")
ax.set_ylim(bounds[0], bounds[-1])
ax.set_xlim(0, 1)

# Remove x-axis
ax.set_xticks([])

# Put ticks on the right
ax.yaxis.tick_right()
ax.yaxis.set_label_position("right")

ax.set_yticks(bounds)
ax.set_yticklabels(["1", "3", "10", "30", "100", "1000"])

# ax.set_ylabel(r"$BF_{10}$")

# Optional: remove unused spines
ax.spines["left"].set_visible(False)
ax.spines["top"].set_visible(False)
ax.spines["bottom"].set_visible(False)

plt.tight_layout()

plt.savefig("output/bayes_factors_scale.png")
