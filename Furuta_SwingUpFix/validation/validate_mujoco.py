"""Run from any directory: python validate_mujoco.py
Requires: pip install mujoco numpy matplotlib
Separate physics/controller verification, not a Simulink execution test.
"""
from pathlib import Path
import hashlib
import json
import math
import numpy as np
import mujoco as mj

BASE = Path(__file__).resolve().parents[1]
DT = 0.001
M, L, G, R = 0.014, 0.051, 9.81, 0.065
D = 8.06e-6 + M*L*L
C = M*R*L
B = 8.06e-6 + M*L*L - 1e-7
A0 = 1.05625e-5 + 0.03*0.035**2 + M*R*R + 1e-7
MG = M*G*L
RULES = np.array([[4,4,4,3,2],[4,4,3,2,1],[4,3,2,1,0],
                  [3,2,1,0,0],[2,1,0,0,0]])

def clip(x, lo=-1., hi=1.):
    return min(max(x, lo), hi)

def theta(phi):
    return math.atan2(math.sin(phi-math.pi), math.cos(phi-math.pi))

def memberships(x):
    return np.array([
        clip(min((x+1.5)/0.5, (-0.5-x)/0.25), 0., 1.),
        max(0., 1-abs(x+0.5)/0.5), max(0., 1-abs(x)/0.5),
        max(0., 1-abs(x-0.5)/0.5),
        clip(min((x-0.5)/0.25, (1.5-x)/0.5), 0., 1.)])

Y = np.linspace(-1, 1, 101)
OUT = np.array([memberships(y) for y in Y]).T

def fuzzy(e, de):
    strengths = np.minimum(memberships(e)[:, None], memberships(de)[None, :])
    levels = np.array([np.max(strengths[RULES == i]) for i in range(5)])
    agg = np.max(np.minimum(OUT, levels[:, None]), axis=0)
    return float(agg @ Y / agg.sum()) if agg.sum() else 0.

def original(x, t, balanced):
    a, ad, p, pd = x
    th = theta(p)
    if balanced:
        if abs(th)>0.3491 or abs(pd)>3.0 or abs(a)>1.8:
            balanced = False
    elif abs(th)<0.2094 and abs(pd)<1.5 and abs(a)<1.2:
        balanced = True
    if balanced:
        u = clip(-0.8*fuzzy(clip(-th/0.35), clip(-pd/3.0))-0.18*a-0.08*ad)
        return 0.008*u, balanced
    er = 1-(0.5*D*pd*pd+MG*(1-math.cos(p)))/(2*MG)
    u = -0.8*math.tanh(16*pd*math.cos(p))*math.tanh(5*er)
    if t<0.12 and abs(pd)<0.5 and abs(p)<0.5:
        u = 0.8
    if abs(a)>1.45:
        u = -0.5*a-0.2*ad
    return 0.010*clip(u), balanced

def corrected(x, t, balanced):
    a, ad, p, pd = x
    th = theta(p)
    if balanced:
        if abs(th)>0.45 or abs(pd)>5.0 or abs(a)>2.1:
            balanced = False
    elif abs(th)<0.25 and abs(pd)<2.5 and abs(a)<1.8:
        balanced = True
    if balanced:
        u = (-2*fuzzy(clip(-th/0.2470994590080727),
                      clip(-pd/2.508255952323903))
             +0.2828427124745972*a+0.14609231193200561*ad)
        return 0.010*clip(u), balanced
    sp, cp = math.sin(p), math.cos(p)
    er = 1.5-(0.5*D*pd*pd+MG*(1-cp))/(2*MG)
    v = -30*er*pd*cp-40*a-12*ad
    if t<0.1:
        v += 20*math.sin(math.pi*t/0.1)
    wall = max(abs(a)-1.5, 0.)
    v -= 40*math.copysign(wall*wall, a)
    v = clip(v, -150., 150.)
    m11, m12 = A0+B*sp*sp, C*cp
    h1 = 2*B*sp*cp*ad*pd-C*sp*pd*pd
    h2 = (-B*sp*cp*ad*ad+MG*sp+9.899130726538984e-6*pd
          +1.846467096315846e-5*math.tanh(pd/0.01))
    tau = (m11-m12*m12/D)*v+h1+0.0001*ad-m12*h2/D
    return clip(tau, -0.010, 0.010), balanced

def simulate(model, control, duration=30., q=(0., 0.), vel=(0., 0.)):
    data = mj.MjData(model)
    data.qpos[:] = q
    data.qvel[:] = vel
    mj.mj_forward(model, data)
    balanced = False
    rows = []
    for i in range(round(duration/DT)):
        x = [float(data.qpos[0]), float(data.qvel[0]),
             float(data.qpos[1]), float(data.qvel[1])]
        torque, balanced = control(x, i*DT, balanced)
        rows.append([i*DT, *x, torque, int(balanced), theta(x[2])])
        data.ctrl[0] = torque
        mj.mj_step(model, data)
    z = np.array(rows)
    capture = np.flatnonzero(z[:, 6])
    result = {
        'first_capture_s': float(z[capture[0], 0]) if len(capture) else None,
        'mode_switches': int(np.count_nonzero(np.diff(z[:, 6]))),
        'max_arm_deg': float(np.max(abs(z[:, 1]))*180/math.pi),
        'min_top_error_deg': float(np.min(abs(z[:, 7]))*180/math.pi),
        'tail_5s_max_top_error_deg': float(np.max(abs(z[-5000:, 7]))*180/math.pi),
        'peak_torque_Nm': float(np.max(abs(z[:, 5]))),
        'balanced_at_end': bool(z[-1, 6])}
    return result, z

def main():
    # This implementation mirrors the supplied, unchanged FIS exactly.
    fis = BASE/'Furuta_FuzzyPD25_Clean.fis'
    expected = 'aa96e9e712edf706b7a66a526b2da18fed1ccf8b9c5a53fba2737af97a7a880c'
    if hashlib.sha256(fis.read_bytes()).hexdigest() != expected:
        raise ValueError('FIS changed; this verification mirrors the original 25-rule FIS.')
    xml = (BASE/'furuta_simulink_torque_fixed.xml').read_text()
    fixed = mj.MjModel.from_xml_string(xml)
    old = mj.MjModel.from_xml_string(xml.replace('<compiler angle="radian"/>', ''))
    assert np.allclose(fixed.jnt_range[0], [-3*math.pi/4, 3*math.pi/4])
    assert abs(fixed.opt.timestep-DT)<1e-12
    output = Path(__file__).resolve().parent
    results = {'mujoco_version': mj.__version__, 'step_s': DT, 'tests': []}
    plots = []
    for name, model, ctrl in [('Original', old, original),
                              ('XML units only', fixed, original),
                              ('Full correction', fixed, corrected)]:
        r, z = simulate(model, ctrl)
        results[name] = r
        plots.append((name, z))
        print(name, json.dumps(r), flush=True)
    tests = [('nominal',(0.,0.),(0.,0.)),
             ('phi_plus',(0.,0.05),(0.,0.)),
             ('phi_minus',(0.,-0.05),(0.,0.)),
             ('arm_plus',(0.2,0.),(0.,0.)),
             ('arm_minus',(-0.2,0.),(0.,0.)),
             ('velocity',(0.,0.02),(0.1,-0.1))]
    for name, q, vel in tests:
        r, _ = simulate(fixed, corrected, q=q, vel=vel)
        r['case'] = name
        r['pass'] = (r['balanced_at_end'] and r['mode_switches']==1
                     and r['tail_5s_max_top_error_deg']<1
                     and r['max_arm_deg']<135)
        results['tests'].append(r)
        print(name, json.dumps(r), flush=True)
    (output/'rerun_results.json').write_text(json.dumps(results, indent=2))
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
        for name, z in plots:
            axes[0].plot(z[:,0], abs(z[:,7])*180/math.pi, label=name, linewidth=1.5)
            axes[1].plot(z[:,0], z[:,1]*180/math.pi, label=name, linewidth=1.2)
        axes[0].set_ylabel('Error from upright (deg)')
        axes[1].set_ylabel('Arm angle (deg)')
        axes[1].set_xlabel('Simulation time (s)')
        axes[1].axhline(135, color='gray', linestyle='--', linewidth=.8)
        axes[1].axhline(-135, color='gray', linestyle='--', linewidth=.8)
        axes[0].legend(loc='upper right')
        for ax in axes:
            ax.set_xlim(0, 8)
            ax.grid(alpha=.2)
        fig.suptitle('Furuta: original, angle-unit fix, full correction')
        fig.text(.5, .015, 'Python/MuJoCo at 1 ms. Simulink compilation/run remains to be checked in MATLAB.',
                 ha='center', fontsize=9, color='#555555')
        fig.tight_layout(rect=[0,.04,1,.95])
        fig.savefig(output/'comparison.png', dpi=160)
    except ImportError:
        print('Install matplotlib to create comparison.png')
    if not all(item['pass'] for item in results['tests']):
        raise SystemExit('A verification case failed; inspect rerun_results.json.')

if __name__ == '__main__':
    main()
