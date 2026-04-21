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
bounds = np.array([0.0001, 0.001, 0.005, 0.01, 0.05, 1])

labels = [
    "Very strong",
    "Strong",
    "Moderate",
    "Weak",
    "Little or none"
]

fig, ax = plt.subplots(figsize=(4, 5))


# Draw colored regions
norm = mpl.colors.LogNorm(vmin=bounds[0], vmax=bounds[-1])
cmap = plt.cm.viridis_r
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
ax.yaxis.tick_left()
ax.set_yticks(bounds)
ax.set_yticklabels(["0.0001", "0.001", "0.005", "0.01", "0.05", "1"])

# ax.set_ylabel(r"$BF_{10}$")

# Optional: remove unused spines
ax.spines["left"].set_visible(False)
ax.spines["top"].set_visible(False)
ax.spines["bottom"].set_visible(False)

plt.tight_layout()

plt.savefig("output/p_values_scale.png")
