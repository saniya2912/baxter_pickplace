import cv2, os

VIDEO = "/home/robotlab/Desktop/saniya_ws/baxter_pickplace/videos/checkpoint_comparison/pos_v3_199999/task_0_move_the_red_block_to_the_far_side/trial_00.mp4"
OUT_DIR = "/home/robotlab/Desktop/saniya_ws/baxter_pickplace/figures/exec_sequence"
os.makedirs(OUT_DIR, exist_ok=True)

# (frame_number, label, caption_note)
frames = [
    (0,   "a_initial",   "Initial config — arm at home, block at x=0.600 m"),
    (20,  "b_approach",  "Pre-grasp approach — arm translating toward block"),
    (35,  "c_descent",   "Descent — gripper aligned above block centre"),
    (55,  "d_lift",      "Lift — block airborne at z=0.35 m, gripper closed"),
    (160, "e_carry",     "Carry — block at far side, x=0.747 m"),
    (180, "f_place",     "Placement — gripper opens, block at x=0.753 m"),
]

cap = cv2.VideoCapture(VIDEO)
total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(f"Video: {total} frames @ {cap.get(cv2.CAP_PROP_FPS):.0f} fps")

for fnum, label, note in frames:
    cap.set(cv2.CAP_PROP_POS_FRAMES, fnum)
    ret, frame = cap.read()
    if not ret:
        print(f"  WARN: could not read frame {fnum}")
        continue
    out = os.path.join(OUT_DIR, f"{label}.png")
    cv2.imwrite(out, frame)
    print(f"  frame {fnum:3d} → {out}  [{note}]")

cap.release()
print("Done.")
