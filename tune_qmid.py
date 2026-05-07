"""
Find optimal Q_MID_RED and Q_MID_BLUE for blocks at z=0.10.

Target: gripper site at (block_x, block_y, block_z + ABOVE_HEIGHT)
        with fingers level (finger z-diff ≈ 0).

Usage:
    cd ~/Desktop/saniya_ws/pi0.5_mujoco/openpi
    uv run python ~/Desktop/saniya_ws/baxter_pickplace/tune_qmid.py
"""

import pathlib
import numpy as np
import mujoco

XML_PATH  = pathlib.Path(__file__).parent / "models" / "baxter_twoblocks.xml"

QPOS_RARM = slice(22, 29)
QVEL_RARM = slice(19, 26)

BLOCK_Z    = 0.285
ABOVE_H    = 0.14
TARGET_Z   = BLOCK_Z + ABOVE_H   # 0.24

KP_CART  = 5.0
K_NULL   = 0.3
LAMBDA   = 0.05
VEL_LIMIT= 1.5
N_SUB    = 5
DT       = 0.002

def set_arm(data, q):
    data.qpos[QPOS_RARM] = q
    mujoco.mj_forward(model, data)

def dls_ik(model, data, site_id, target, q_mid):
    jacp = np.zeros((3, model.nv))
    mujoco.mj_jacSite(model, data, jacp, None, site_id)
    J = jacp[:, QVEL_RARM]
    J_dls = J.T @ np.linalg.inv(J @ J.T + LAMBDA**2 * np.eye(3))
    err   = target - data.site_xpos[site_id]
    qdot  = J_dls @ (KP_CART * err)
    N     = np.eye(7) - J_dls @ J
    qdot += N @ (K_NULL * (q_mid - data.qpos[QPOS_RARM]))
    return np.clip(qdot, -VEL_LIMIT, VEL_LIMIT)

def ik_to(model, data, site_id, target, q_init, q_null, steps=2000, tol=0.003):
    data.qpos[QPOS_RARM] = q_init.copy()
    mujoco.mj_forward(model, data)
    for _ in range(steps):
        err = np.linalg.norm(target - data.site_xpos[site_id])
        if err < tol:
            break
        vel = dls_ik(model, data, site_id, target, q_null)
        data.qpos[QPOS_RARM] += vel * N_SUB * DT
        mujoco.mj_forward(model, data)
    return data.qpos[QPOS_RARM].copy(), np.linalg.norm(target - data.site_xpos[site_id])

def finger_zdiff(model, data):
    """Z difference between left and right finger tips — want this near 0."""
    fl = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "right_l_finger_tip")
    fr = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "right_r_finger_tip")
    if fl < 0 or fr < 0:
        # fall back: check geom named finger
        return 0.0
    return float(data.site_xpos[fl][2] - data.site_xpos[fr][2])

model = mujoco.MjModel.from_xml_path(str(XML_PATH))
data  = mujoco.MjData(model)
site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "right_grip_site")

home_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_KEY, "home")

KP_ROT = 2.0

def dls_ik_6d(model, data, site_id, target_pos, target_quat, q_mid):
    jacp = np.zeros((3, model.nv))
    jacr = np.zeros((3, model.nv))
    mujoco.mj_jacSite(model, data, jacp, jacr, site_id)
    Jp = jacp[:, QVEL_RARM]
    Jr = jacr[:, QVEL_RARM]
    J6 = np.vstack([Jp, Jr])
    pos_err = target_pos - data.site_xpos[site_id]
    curr_quat = np.zeros(4)
    mujoco.mju_mat2Quat(curr_quat, data.site_xmat[site_id])
    inv_curr = np.zeros(4)
    mujoco.mju_negQuat(inv_curr, curr_quat)
    diff_quat = np.zeros(4)
    mujoco.mju_mulQuat(diff_quat, target_quat, inv_curr)
    rot_vel = np.zeros(3)
    mujoco.mju_quat2Vel(rot_vel, diff_quat, 1.0)
    err6  = np.concatenate([KP_CART * pos_err, KP_ROT * rot_vel])
    J_dls = J6.T @ np.linalg.inv(J6 @ J6.T + LAMBDA**2 * np.eye(6))
    qdot  = J_dls @ err6
    N     = np.eye(7) - J_dls @ J6
    qdot += N @ (K_NULL * (q_mid - data.qpos[QPOS_RARM]))
    return np.clip(qdot, -VEL_LIMIT, VEL_LIMIT)

def ik_6d_to(model, data, site_id, target_pos, target_quat, q_init, q_null,
             steps=3000, tol=0.005):
    data.qpos[QPOS_RARM] = q_init.copy()
    mujoco.mj_forward(model, data)
    for _ in range(steps):
        pos_err = np.linalg.norm(target_pos - data.site_xpos[site_id])
        if pos_err < tol:
            break
        vel = dls_ik_6d(model, data, site_id, target_pos, target_quat, q_null)
        data.qpos[QPOS_RARM] += vel * N_SUB * DT
        mujoco.mj_forward(model, data)
    return data.qpos[QPOS_RARM].copy(), np.linalg.norm(target_pos - data.site_xpos[site_id])

print("=" * 60)
print(f"Tuning Q_MID for block z={BLOCK_Z}, pregrasp z={TARGET_Z}")
print("(6D IK: position + orientation locked to old Q_MID orientation)")
print("=" * 60)

# Old Q_MID — read the EXACT gripper orientation from each
Q_OLD_RED   = np.array([0.409,  0.667, -0.333, 0.0,   0.5,   2.0,   -1.78])
Q_OLD_BLUE  = np.array([-0.298, 1.048, -0.714, 0.790, 1.453, 1.615, -1.632])
Q_OLD_GREEN = np.array([0.409,  0.667, -0.333, 0.0,   0.5,   2.0,   -1.78])  # same seed as red

results = {}

for block, bx, by, q_old in [("red",   0.70, -0.15, Q_OLD_RED),
                               ("blue",  0.70, -0.35, Q_OLD_BLUE),
                               ("green", 0.70,  0.05, Q_OLD_GREEN)]:
    target_pos = np.array([bx, by, TARGET_Z])

    # Extract gripper orientation from old Q_MID
    set_arm(data, q_old)
    target_quat = np.zeros(4)
    mujoco.mju_mat2Quat(target_quat, data.site_xmat[site_id])
    print(f"\n── {block.upper()} block  target={target_pos} ──")
    print(f"  target_quat (from old Q_MID): {target_quat.round(4)}")

    best_fdiff = 1e9
    best_q     = None
    best_err   = None
    best_s0    = None

    # Use 3D IK (position only) + fdiff check; orientation comes from Q_MID naturally
    for s0_try in np.linspace(-1.0, 1.2, 45):
        q_null = q_old.copy()
        q_null[0] = s0_try
        q_sol, err = ik_to(model, data, site_id, target_pos, q_null.copy(), q_null,
                           steps=3000, tol=0.003)
        set_arm(data, q_sol)
        fdiff = abs(finger_zdiff(model, data))

        if err < 0.006 and fdiff < best_fdiff:
            best_fdiff = fdiff
            best_q     = q_sol.copy()
            best_err   = err
            best_s0    = s0_try

    if best_q is None:
        print("  WARNING: no solution within tolerance — taking best")
        for s0_try in np.linspace(-1.0, 1.2, 45):
            q_null = q_old.copy()
            q_null[0] = s0_try
            q_sol, err = ik_to(model, data, site_id, target_pos, q_null.copy(), q_null,
                               steps=3000, tol=0.003)
            set_arm(data, q_sol)
            fdiff = abs(finger_zdiff(model, data))
            if best_q is None or (fdiff < best_fdiff and err < 0.02):
                best_fdiff, best_q, best_err, best_s0 = fdiff, q_sol.copy(), err, s0_try
        if best_q is None:  # absolute fallback
            best_q, best_err, best_s0 = q_sol.copy(), err, s0_try
            set_arm(data, best_q)
            best_fdiff = abs(finger_zdiff(model, data))

    results[block] = best_q
    set_arm(data, best_q)
    grip_pos = data.site_xpos[site_id].copy()
    print(f"  best s0_try={best_s0:.3f}  pos_err={best_err:.4f}  fdiff={best_fdiff:.4f}")
    print(f"  grip site at: {grip_pos.round(4)}")
    print(f"  Q_MID_{block.upper()} = np.array({best_q.round(4).tolist()})")

print("\n" + "=" * 60)
print("COPY THESE INTO record_demos_pos.py:")
print("=" * 60)
for block in ["red", "blue", "green"]:
    q = results[block]
    print(f"Q_MID_{block.upper():5s} = np.array({q.round(4).tolist()})")
