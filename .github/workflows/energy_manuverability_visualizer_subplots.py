import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button

# --- Initial parameter values ---
init_Aso = 20.0          # AoA at stall (breakpoint)
init_Clmax = 1.0         # max lift coefficient
init_a2 = -0.05          # stall abruptness (post-stall curvature)
init_b1 = 0.0001         # zero-lift-drag-related coefficient
init_a3 = 0.5            # zero lift drag coefficient
init_d = 45.0            # Max G (breakpoint used in turnrate)

x = np.linspace(0, 45, 2000)


def Cl(x, Aso, Clmax, a2, b1, a3, d):
    a2 = -a2
    return np.piecewise(
        x,
        [x < Aso, (x >= Aso)],
        [
            lambda x: Clmax * (x / Aso),
            lambda x: a2 * x * x + (Clmax / Aso - 2 * a2 * Aso) * x + a2 * Aso * Aso,
        ],
    )


def Cd(x, b1, a3):
    return x * x * b1 + a3


def ratio(x, Aso, Clmax, a2, b1, a3, d):
    return Cl(x, Aso, Clmax, a2, b1, a3, d) / Cd(x, b1, a3) / 100


def turnrate(v, Clift, vmax):
    ind = min(range(len(v)), key=lambda i: abs(v[i] - vmax))
    #return np.where(
    #    v < vmax,
    #    Clift * v,
    #    Clift[ind] * vmax * vmax / v,
    #)
    w = Clift * v
    return w


def instant_turnrate(v, Clift, vmax):
    Clmax = max(Clift)
    ind = min(range(len(v)), key=lambda i: abs(v[i] - vmax))
    # Breakpoint chosen so the two branches meet with no jump:
    # Clmax*vmaxg == Clift[ind]*vmax**2/vmaxg  =>  vmaxg = vmax*sqrt(Clift[ind]/Clmax)
    vmaxg = vmax# * np.sqrt(Clift[ind] / Clmax)
    return np.where(
        v < vmaxg,
        Clmax * v,
        Clmax * vmaxg * vmaxg / v,
    )


def compute_all(Aso, Clmax, a2, b1, a3, d):
    """Compute every curve from current slider values, return as a dict."""
    y = Cl(x, Aso, Clmax, a2, b1, a3, d)
    z = Cd(x, b1, a3)
    r = ratio(x, Aso, Clmax, a2, b1, a3, d)
    v = np.reciprocal(np.sqrt(z))
    w = turnrate(v, y, d)
    w_inst = instant_turnrate(v, y, d)
    # Wherever instantaneous turn rate is lower, turn rate is capped to it
    w = np.minimum(w, w_inst)
    return {"x": x, "Cl": y, "Cd": z, "ratio": r, "v": v, "w": w, "w_inst": w_inst}


# --- Set up the figure: 1 row, 2 subplots ---
fig, axs = plt.subplots(1, 2, figsize=(13, 6))
plt.subplots_adjust(left=0.08, right=0.97, bottom=0.42, wspace=0.3)

ax_vs_x, ax_vs_v = axs

data = compute_all(init_Aso, init_Clmax, init_a2, init_b1, init_a3, init_d)

# --- All lines managed in one dict ---
lines = {}

# Left subplot: Cl, Cd, and ratio, all vs AoA (x)
lines["Cl_vs_x"], = ax_vs_x.plot(data["x"], data["Cl"], lw=2, color="C0", label="Cl")
lines["Cd_vs_x"], = ax_vs_x.plot(data["x"], data["Cd"] * 10, lw=2, color="C2", label="Cd x10")
lines["ratio_vs_x"], = ax_vs_x.plot(data["x"], data["ratio"], lw=2, color="C3", label="Cl/Cd (ratio)")
ax_vs_x.set_xlabel("AoA, x (au)")
ax_vs_x.set_ylabel("Value (au, scaled)")
ax_vs_x.set_title("Cl, Cd, and Ratio vs AoA")
ax_vs_x.legend(loc="upper right")
ax_vs_x.grid(True, alpha=0.3)

# Right subplot: turn rate (w) and instantaneous turn rate (w_inst) vs v
lines["w_vs_v"], = ax_vs_v.plot(data["v"], data["w"], lw=2, color="C1", label="Turn Rate")
lines["w_inst_vs_v"], = ax_vs_v.plot(data["v"], data["w_inst"], lw=2, color="C4", ls="--", label="Instantaneous Turn Rate")
ax_vs_v.set_xlabel("V (au)")
ax_vs_v.set_ylabel("Turn Rate (au)")
ax_vs_v.set_title("Turn rate vs v")
ax_vs_v.legend(loc="upper right")
ax_vs_v.grid(True, alpha=0.3)

# Vertical breakpoint markers, one per subplot, also tracked in the dict
lines["vline_d_x"] = ax_vs_x.axvline(init_Aso, color="gray", ls="--", alpha=0.5)
lines["vline_d_v"] = ax_vs_v.axvline(init_d, color="gray", ls="--", alpha=0.5)

# --- Slider axes (left, bottom, width, height) ---
ax_Clmax = plt.axes([0.15, 0.30, 0.7, 0.03])
ax_b1 = plt.axes([0.15, 0.25, 0.7, 0.03])
ax_a2 = plt.axes([0.15, 0.20, 0.7, 0.03])
ax_a3 = plt.axes([0.15, 0.15, 0.7, 0.03])
ax_Aso = plt.axes([0.15, 0.10, 0.7, 0.03])
ax_d = plt.axes([0.15, 0.05, 0.7, 0.03])

slider_Clmax = Slider(ax_Clmax, "Clmax", 0, 2, valinit=init_Clmax)
slider_b1 = Slider(ax_b1, "Drag Increase with AoA", 0, 0.001, valinit=init_b1)
slider_a2 = Slider(ax_a2, "Stall Abruptness", 0.001, 0.01, valinit=init_a2)
slider_a3 = Slider(ax_a3, "Zero Lift Drag Coefficient", 0, 0.01, valinit=init_a3)
slider_Aso = Slider(ax_Aso, "AoA at Stall", 0, 45, valinit=init_Aso)
slider_d = Slider(ax_d, "Max G", 0, 45, valinit=init_d)


# --- Update function called whenever a slider changes ---
def update(val):
    Aso = slider_Aso.val
    d = slider_d.val

    data = compute_all(
        Aso, slider_Clmax.val, slider_a2.val, slider_b1.val, slider_a3.val, d
    )

    # Left plot: Cl, Cd, ratio vs x (x-array never changes, only y-data does)
    lines["Cl_vs_x"].set_ydata(data["Cl"])
    lines["Cd_vs_x"].set_ydata(data["Cd"] * 10)
    lines["ratio_vs_x"].set_ydata(data["ratio"])
    ax_vs_x.relim()
    ax_vs_x.autoscale_view(scalex=False, scaley=True)

    # Right plot: w and w_inst vs v (both x and y data change, since v is computed)
    order = np.argsort(data["v"])           # keep the lines monotonic in x
    lines["w_vs_v"].set_xdata(data["v"][order])
    lines["w_vs_v"].set_ydata(data["w"][order])
    lines["w_inst_vs_v"].set_xdata(data["v"][order])
    lines["w_inst_vs_v"].set_ydata(data["w_inst"][order])
    ax_vs_v.relim()
    ax_vs_v.autoscale_view(scalex=True, scaley=True)

    # Breakpoint markers
    # Amax: AoA at max Cl, accounting for the a2 -> -a2 flip inside Cl()
    Amax = slider_Clmax.val / (2 * slider_Aso.val * slider_a2.val) + slider_Aso.val
    lines["vline_d_x"].set_xdata([Amax, Amax])
    lines["vline_d_v"].set_xdata([d, d])

    fig.canvas.draw_idle()


for s in (slider_Clmax, slider_b1, slider_a2, slider_a3, slider_Aso, slider_d):
    s.on_changed(update)

# --- Reset button ---
reset_ax = plt.axes([0.85, 0.005, 0.08, 0.04])
reset_button = Button(reset_ax, "Reset")


def reset(event):
    for s in (slider_Clmax, slider_b1, slider_a2, slider_a3, slider_Aso, slider_d):
        s.reset()


reset_button.on_clicked(reset)

plt.show()
