"""Plot a saved trace without repeating simulation or training."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def plot(record):
    rows = [json.loads(line) for line in (record/"trace.jsonl").read_text().splitlines()]
    t = np.array([r["t"] for r in rows])
    truth = np.array([r["truth"] for r in rows])
    motors = np.array([r["motor_duty"] for r in rows])
    alt_est = [r["estimated_alt_m"] for r in rows]
    fig, axes = plt.subplots(3, 1, figsize=(10, 10), constrained_layout=True)
    fig.suptitle("StampFly + ArduPilot: takeoff reached 1.20 m; hover FAILED\n52 g assumed assembly | GPS off | no VLA used", fontsize=14)
    ax = axes[0]
    ax.axhspan(.75, 1.25, color="#dddddd", label="Altitude scoring band (not position hold)")
    ax.plot(t, -truth[:,3], label="Physical altitude", color="#1976b8", lw=2)
    ax.plot(t, alt_est, label="EKF local altitude", color="#e17a20", alpha=.8)
    ax.set(xlabel="Simulation time [s]", ylabel="Height [m]")
    ax.legend(loc="upper left", fontsize=8)
    ax = axes[1]
    ax.plot(truth[:,2], truth[:,1], color="#1976b8", lw=2)
    ax.scatter(truth[[0,-1],2], truth[[0,-1],1], color=["#299457", "#d13f3f"], zorder=3)
    ax.annotate("Start", (truth[0,2],truth[0,1]), xytext=(5,7), textcoords="offset points")
    ax.annotate("End: 36.6 m from start", (truth[-1,2],truth[-1,1]), xytext=(-150,8), textcoords="offset points")
    ax.set(xlabel="East [m]", ylabel="North [m]", title="Horizontal drift; this check commanded attitude/climb, not horizontal velocity")
    ax = axes[2]
    for i,name in enumerate(["FR", "RR", "RL", "FL"]):
        ax.plot(t,motors[:,i],label=name,alpha=.8)
    ax.axhline(.95,color="#777777",ls="--",lw=.8)
    ax.set(xlabel="Simulation time [s]",ylabel="Motor duty [0..1]",ylim=(-.02,1.02))
    ax.legend(ncol=4,loc="upper left")
    for ax in axes: ax.grid(alpha=.2)
    fig.savefig(record/"flight_diagnosis.png",dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("record",type=Path)
    plot(p.parse_args().record)
