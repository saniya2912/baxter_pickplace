import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

tasks = ['T0\nred→far', 'T1\nred→near', 'T2\nblue→far', 'T3\nblue→near', 'T4\ngreen→far', 'T5\ngreen→near']
checkpoints = ['pi05\nbase', 'vel\n100k', 'pos\n200k', 'pos_v2\n500k', 'pos_v3']

# success / 10 trials → percentage
data = [
    [70,  0, 10, 60, 90],   # T0
    [20,  0, 20, 40, 40],   # T1
    [ 0,  0, 80, 70, 90],   # T2
    [ 0,  0,  0, 50, 40],   # T3
    [ 0, None, 10, 20,  0], # T4  (vel N/A)
    [ 0, None,  0,  0,  0], # T5  (vel N/A)
]

colors = [
    '#e15759',  # base    – muted red
    '#f28e2b',  # vel     – orange
    '#4e79a7',  # pos200k – blue
    '#59a14f',  # pos_v2  – green
    '#76b7b2',  # pos_v3  – teal
]

x = np.arange(len(tasks))
n_ckpts = len(checkpoints)
width = 0.14
offsets = np.linspace(-(n_ckpts-1)/2, (n_ckpts-1)/2, n_ckpts) * width

fig, ax = plt.subplots(figsize=(9, 4.5))

for ci, (label, color, offset) in enumerate(zip(checkpoints, colors, offsets)):
    vals = [data[ti][ci] if data[ti][ci] is not None else 0 for ti in range(len(tasks))]
    hatch = ['///' if data[ti][ci] is None else '' for ti in range(len(tasks))]
    bars = ax.bar(x + offset, vals, width, label=label.replace('\n', ' '),
                  color=color, edgecolor='white', linewidth=0.6)
    # mark N/A bars
    for ti, h in enumerate(hatch):
        if h:
            ax.bar(x[ti] + offset, 0, width, color='lightgrey',
                   edgecolor='grey', linewidth=0.6, hatch='///')

# success threshold line
ax.axhline(100, color='black', linewidth=0.5, linestyle='--', alpha=0.3)

# block colour bands (background shading)
for ti, c in enumerate(['#ffcccc', '#ffcccc', '#cce0ff', '#cce0ff', '#ccffcc', '#ccffcc']):
    ax.axvspan(ti - 0.45, ti + 0.45, color=c, alpha=0.18, zorder=0)

ax.set_xticks(x)
ax.set_xticklabels(tasks, fontsize=9)
ax.set_ylabel('Trial success rate (%)', fontsize=10)
ax.set_ylim(0, 108)
ax.set_yticks([0, 20, 40, 60, 80, 100])
ax.set_xlabel('Task', fontsize=10)
ax.legend(fontsize=8, ncol=5, loc='upper center', bbox_to_anchor=(0.5, 1.12),
          framealpha=0.8, columnspacing=0.8)
ax.spines[['top', 'right']].set_visible(False)
ax.tick_params(axis='both', labelsize=9)

# annotate N/A
for ti in [4, 5]:
    ax.text(ti + offsets[1], 3, 'N/A', ha='center', va='bottom',
            fontsize=6, color='grey', rotation=90)

plt.tight_layout()

out_dir = os.path.join(os.path.dirname(__file__), 'figures')
os.makedirs(out_dir, exist_ok=True)
out_pdf = os.path.join(out_dir, 'success_bar_chart.pdf')
out_png = os.path.join(out_dir, 'success_bar_chart.png')
plt.savefig(out_pdf, bbox_inches='tight', dpi=300)
plt.savefig(out_png, bbox_inches='tight', dpi=300)
print(f"Saved: {out_pdf}")
print(f"Saved: {out_png}")
