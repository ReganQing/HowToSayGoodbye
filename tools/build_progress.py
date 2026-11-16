# -*- coding: utf-8 -*-
"""整理比赛过程资料到 progress/（分类：剧本/角色/场景/预演/成片/质检）

用法：
  python tools/build_progress.py            # 增量补全归档（已有产物不覆盖）
  python tools/build_progress.py --check   # 只读校验索引引用的源文件，不写任何文件
"""
import os, shutil, json, subprocess, sys
import imageio_ffmpeg
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ff = imageio_ffmpeg.get_ffmpeg_exe()

def P(*a): return os.path.join(ROOT, *a)
def out(*a):
    d = P('progress', *a)
    os.makedirs(d, exist_ok=True)
    return d

def cp(src, dst, overwrite=True):
    """overwrite=False 保护归档里的同名异源文件（如手写审查报告 vs 渲染参数记录）"""
    src, dst = P(src), P(dst)
    if not os.path.exists(src):
        return
    target = os.path.join(dst, os.path.basename(src)) if os.path.isdir(dst) else dst
    if overwrite or not os.path.exists(target):
        shutil.copy(src, dst)

def frames_of(mp4, n=6):
    """ evenly spaced frame paths via temp extraction """
    tmp = P('tmp_qc', 'prog_strip')
    os.makedirs(tmp, exist_ok=True)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    paths = []
    for i in range(n):
        p = os.path.join(tmp, f'f{i}.png')
        subprocess.run([ff, '-y', '-ss', str(i * 1.0), '-i', mp4, '-frames:v', '1', p, '-loglevel', 'error'], check=False)
        if os.path.exists(p):
            paths.append(p)
    return paths

def contact_sheet(mp4, dst, cols=6, tw=320):
    """已有抽帧条不重生成：shot12-14 的抽帧条是人工目检过的版本，重跑不得覆盖"""
    if os.path.exists(dst):
        return True
    paths = frames_of(mp4, cols)
    if not paths: return False
    ims = [Image.open(p) for p in paths]
    w, h = ims[0].size
    th = int(h * tw / w)
    sheet = Image.new('RGB', (tw * len(ims), th))
    for i, im in enumerate(ims):
        sheet.paste(im.resize((tw, th)), (i * tw, 0))
    sheet.save(dst)
    return True

# ---------- 镜头索引：shot01–shot27 ----------
# 新增镜头时只需在下面三个字典各加一行；finals 与 wf 的 key 必须一一对应。
shots_prev = {
    'shot01': dict(frames='frames_v2', mp4='previs_shot01_v2.mp4', title='楼道口幻觉'),
    'shot02': dict(frames='frames02', mp4='previs_shot02.mp4', title='楼道口别发带'),
    'shot03': dict(frames='frames03', mp4='previs_shot03.mp4', title='病房捧手'),
    'shot04': dict(frames='frames04', mp4='previs_shot04.mp4', title='镜前梳头'),
    'shot05': dict(frames='frames05', mp4='previs_shot05.mp4', title='清晨递发带'),
    'shot06': dict(frames='frames06', mp4='previs_shot06.mp4', title='火车站送别'),
    'shot07': dict(frames='frames07', mp4='previs_shot07.mp4', title='南方线·找工友'),
    'shot08': dict(frames='frames08', mp4='previs_shot08.mp4', title='老照片·掏手机'),
    'shot10': dict(frames='frames10', mp4='previs_shot10.mp4', title='返校的车上'),
    'shot11': dict(frames='frames11', mp4='previs_shot11.mp4', title='夜里的电话'),
    'shot12': dict(frames='frames12', mp4='previs_shot12.mp4', title='晒书的人'),
    'shot13': dict(frames='frames13', mp4='previs_shot13.mp4', title='两只碗'),
    'shot14': dict(frames='frames14', mp4='previs_shot14.mp4', title='厨房的和好'),
    'shot15': dict(frames='frames15', mp4='previs_shot15.mp4', title='再攒两年'),
    'shot16': dict(frames='frames16', mp4='previs_shot16.mp4', title='婚礼·胸针与旧发带'),
    # shot17 脚本沿用 v4 版预演的帧目录；最终通过版 v6 预演单独归档在 04_白模预演/shot17b/
    'shot17': dict(frames='frames17', mp4='previs_shot17.mp4', title='我自己来'),
    'shot18': dict(frames='frames18', mp4='previs_shot18.mp4', title='楼下晨光·婴儿车'),
    'shot19': dict(frames='frames19', mp4='previs_shot19.mp4', title='报纸后面'),
    'shot20': dict(frames='frames20', mp4='previs_shot20.mp4', title='妈，你晚上吃什么'),
    'shot21': dict(frames='frames21', mp4='previs_shot21.mp4', title='一袋橘子'),
    'shot22': dict(frames='frames22', mp4='previs_shot22.mp4', title='阳台择豆角'),
    'shot23': dict(frames='frames23', mp4='previs_shot23.mp4', title='地址纸与盒子'),
    'shot24': dict(frames='frames24', mp4='previs_shot24.mp4', title='两碗面'),
    'shot25': dict(frames='frames25', mp4='previs_shot25.mp4', title='病房·跳舞之约'),
    'shot26': dict(frames='frames26', mp4='previs_shot26.mp4', title='跳一点给外婆看'),
    'shot27': dict(frames='frames27', mp4='previs_shot27.mp4', title='幕布拉开'),
    # shot09 无白模帧目录（assets/previs 仅有 previs_shot09.mp4），非遗漏，勿强加
}
finals = {
    'shot01': 'shot01_h3_v2_bright.mp4', 'shot02': 'shot02_h3_v2.mp4',
    'shot03': 'shot03_h3_v2.mp4', 'shot04': 'shot04_h3_v2.mp4',
    'shot05': 'shot05_h3.mp4', 'shot06': 'shot06_h3.mp4',
    'shot07': 'shot07_h3.mp4', 'shot08': 'shot08_h3.mp4',
    'shot09': 'shot09_h3.mp4', 'shot10': 'shot10_h3.mp4', 'shot11': 'shot11_h3.mp4',
    'shot12': 'shot12_h3.mp4', 'shot13': 'shot13_h3.mp4', 'shot14': 'shot14_h3.mp4', 'shot15': 'shot15_h3.mp4',
    'shot16': 'shot16_h3.mp4',
    'shot17': 'shot17_h3.mp4',
    'shot18': 'shot18_h3.mp4',
    'shot19': 'shot19_h3.mp4',
    'shot20': 'shot20_h3.mp4',
    'shot21': 'shot21_h3.mp4',
    'shot22': 'shot22_h3.mp4',
    'shot23': 'shot23_h3.mp4',
    'shot24': 'shot24_h3.mp4',
    'shot25': 'shot25_h3.mp4',
    'shot26': 'shot26_h3.mp4',
    'shot27': 'shot27_h3.mp4',
}
wf = {  # 工作流 json（含 seed/prompt，供溯源）
    'shot01': 'h3_r2v_workflow_shot01_v2.json', 'shot02': 'h3_r2v_workflow_shot02_v2.json',
    'shot03': 'h3_r2v_workflow_shot03.json', 'shot04': 'h3_r2v_workflow_shot04_v2.json',
    'shot05': 'h3_r2v_workflow_shot05.json', 'shot06': 'h3_r2v_workflow_shot06.json',
    'shot07': 'h3_r2v_workflow_shot07.json', 'shot08': 'h3_r2v_workflow_shot08.json',
    'shot09': 'h3_r2v_workflow_shot09c.json', 'shot10': 'h3_r2v_workflow_shot10d.json',
    'shot11': 'h3_r2v_workflow_shot11b.json',
    'shot12': 'h3_r2v_workflow_shot12.json', 'shot13': 'h3_r2v_workflow_shot13.json',
    'shot14': 'h3_r2v_workflow_shot14.json',
    'shot15': 'h3_r2v_workflow_shot15.json',
    # shot16 最终通过版是 v03（shot16c）；v01/v02 工作流作为判退过程素材保留
    'shot16': 'h3_r2v_workflow_shot16c.json',
    # shot17 一次提交即过审；旧 v4 预演版工作流备份为 h3_r2v_workflow_shot17_弃用_v4预演.json
    'shot17': 'h3_r2v_workflow_shot17.json',
    # shot18 一次提交即过审；初版未写 L311 亲额头的工作流备份为 h3_r2v_workflow_shot18_初版_未写亲额头.json
    'shot18': 'h3_r2v_workflow_shot18.json',
    # shot19 一次提交即过审；预演三轮判退稿与判定书见 progress/04_白模预演/shot19_测试帧_v1|_v2|_v3/
    'shot19': 'h3_r2v_workflow_shot19.json',
    # shot20 八轮预演返修（v1–v7 判退稿与判定书见 progress/04_白模预演/shot20_测试帧_v1..v7/）
    'shot20': 'h3_r2v_workflow_shot20.json',
    # shot21 三轮预演返修（v1/v2 判退稿与判定书见 progress/04_白模预演/shot21_测试帧_v1..v2/；v3 过审见 shot21_测试帧_v3/）
    'shot21': 'h3_r2v_workflow_shot21.json',
    # shot22 三轮预演返修 + 两轮探针判退（见 progress/04_白模预演/ 下各判定书）
    'shot22': 'h3_r2v_workflow_shot22.json',
    # shot23 一轮探针判退 + 三轮预演返修（见 progress/04_白模预演/ 下各判定书）
    'shot23': 'h3_r2v_workflow_shot23.json',
    # shot24 两轮探针判退 + 两轮测试帧返修（见 progress/04_白模预演/ 下各判定书）
    'shot24': 'h3_r2v_workflow_shot24.json',
    # shot25 两轮探针判退 + 两轮测试帧返修；18 节点 / 4 张 ref_images
    'shot25': 'h3_r2v_workflow_shot25.json',
    # shot26 椅位探针判退 + 两轮测试帧返修；18 节点 / 4 张 ref_images / Dance_Loop 实测
    'shot26': 'h3_r2v_workflow_shot26.json',
    # shot27 收束镜：两轮探针判退 + 三轮测试帧返修 + 全渲数值返修；17 节点 / 3 张 ref_images
    'shot27': 'h3_r2v_workflow_shot27.json',
}

# ---------- 只读校验：不创建目录、不复制、不抽帧 ----------
if '--check' in sys.argv:
    missing = []
    if set(finals) != set(wf):
        missing.append('finals/wf key 不一致: ' + str(sorted(set(finals) ^ set(wf))))
    for sid, mp4 in finals.items():
        if not os.path.exists(P('assets/h3_video', mp4)):
            missing.append('成片缺失 ' + mp4)
        if sid in wf and not os.path.exists(P('tools', wf[sid])):
            missing.append('工作流缺失 ' + wf[sid])
    for sid, info in shots_prev.items():
        if not os.path.exists(P('assets/previs', info['mp4'])):
            missing.append('预演缺失 ' + info['mp4'])
        if not os.path.isdir(P('assets/previs', info['frames'])):
            missing.append('帧目录缺失 ' + info['frames'])
    expected = {f'shot{i:02d}' for i in range(1, 28)}
    for sid in sorted(expected - set(finals)):
        missing.append('finals 未收录 ' + sid)
    print('CHECK (read-only)')
    print(f'  finals     : {len(finals)} 镜头  {min(finals)}..{max(finals)}')
    print(f'  wf         : {len(wf)} 镜头  {min(wf)}..{max(wf)}')
    print(f'  shots_prev : {len(shots_prev)} 镜头  {min(shots_prev)}..{max(shots_prev)}  (shot09 无帧目录，历史缺口)')
    for sid, mp4 in finals.items():
        mark = 'OK ' if os.path.exists(P('assets/h3_video', mp4)) else 'MISS'
        print(f'    {mark} {sid}  {mp4}  <- {wf.get(sid, "?")}')
    print('  缺失项: ' + (str(missing) if missing else '无'))
    sys.exit(1 if missing else 0)

# ---------- 01 剧本 ----------
d = out('01_剧本分镜')
cp('我们总要学会告别并在告别中成长-优化稿.md', d)
cp('告别与成长·分类资产清单.xlsx', d)

# ---------- 02 角色建模 ----------
chars = {
    'C01': dict(name='许宁·童年', design=['assets/ref/C01'], qc_prefix='C01'),
    'C05': dict(name='许宁·大学', design=['assets/ref/C05'], qc_prefix=None),
    'C08': dict(name='姥姥', design=['assets/ref/C08'], qc_prefix='C08'),
    'C09': dict(name='妈妈·青年', design=['assets/ref/C09'], qc_prefix='C09'),
    'C10': dict(name='妈妈·中年', design=['assets/ref/C10'], qc_prefix=None),
    'C12': dict(name='爸爸', design=['assets/ref/C12'], qc_prefix='C12'),
    'C14': dict(name='工友叔叔', design=['assets/ref/C14'], qc_prefix=None),
}
for cid, info in chars.items():
    d = out('02_角色建模', f'{cid}_{info["name"]}')
    for refdir in info['design']:
        if os.path.isdir(P(refdir)):
            for f in sorted(os.listdir(P(refdir))):
                if f.lower().endswith(('.png', '.jpg')):
                    cp(os.path.join(refdir, f), d)
    if info['qc_prefix']:
        for f in sorted(os.listdir(P('assets/qc'))):
            if f.startswith(info['qc_prefix'] + '_'):
                cp(os.path.join('assets/qc', f), d)

# ---------- 03 场景建模 ----------
envs = ['E01', 'E02', 'E03', 'E04', 'E05', 'E06', 'E07']
env_names = {'E01': '楼道口', 'E02': '病房', 'E03': '卧室镜前', 'E04': '火车站台',
             'E05': '南方街道', 'E06': '大巴车内', 'E07': '宿舍夜景'}
for eid in envs:
    d = out('03_场景建模', f'{eid}_{env_names[eid]}')
    refdir = P('assets/ref', eid)
    if os.path.isdir(refdir):
        for f in sorted(os.listdir(refdir)):
            if f.lower().endswith(('.png', '.jpg')):
                cp(os.path.join('assets/ref', eid, f), d)
    # qc 视图与探针图
    for f in sorted(os.listdir(P('assets/qc'))):
        fl = f.lower()
        if fl.startswith(eid.lower() + '_') or (eid == 'E01' and f.startswith('E01_check')) \
           or (eid == 'E03' and f.startswith('e03_')) or (eid == 'E04' and f.startswith('e04_')) \
           or (eid == 'E05' and f.startswith('e05_')):
            cp(os.path.join('assets/qc', f), d)

# ---------- 04 白模预演 ----------
for sid, info in shots_prev.items():
    d = out('04_白模预演', sid)
    fdir = P('assets/previs', info['frames'])
    # 已归档过代表帧就不再重抽：shot12-14 手工归档用的是 f1/64/128/191(192)，
    # 脚本的 nfs-2 会算出 f190，重抽只会制造冗余文件。
    has_frames = any(f.startswith('frame_') and f.endswith('.png') for f in os.listdir(d))
    if not has_frames and os.path.isdir(fdir):
        nfs = len(os.listdir(fdir))
        for n in [1, nfs // 3, 2 * nfs // 3, nfs - 2]:
            src = os.path.join(fdir, f'frame_{n:04d}.png')
            if os.path.exists(src):
                cp(src, d)
    cp(os.path.join('assets/previs', info['mp4']), d)
    # assets/previs/*_report.json 是渲染脚本输出的纯参数记录（如 shot14 仅 308B）；
    # 归档目录里同名文件可能是手写审查报告（shot14 为 1421B，含 timeline 与过审结论）。
    # 二者同名异源，绝不覆盖，否则会丢审查资料。
    rp = os.path.join('assets/previs', f'previs{sid[-2:]}_report.json')
    if os.path.exists(P(rp)):
        cp(rp, d, overwrite=False)

# ---------- 05 镜头成片 ----------
for sid, mp4 in finals.items():
    d = out('05_镜头成片', sid)
    mp4p = P('assets/h3_video', mp4)
    if os.path.exists(mp4p):
        contact_sheet(mp4p, os.path.join(d, f'{sid}_成片抽帧.jpg'))
    cp(os.path.join('tools', wf[sid]), d)
    qcjpg = P('assets/h3_video', f'qc_{sid}_h3.jpg')
    if os.path.exists(qcjpg):
        cp(os.path.join('assets/h3_video', f'qc_{sid}_h3.jpg'), d)

# ---------- 06 质检返修 ----------
d = out('06_质检返修')
for f in sorted(os.listdir(P('assets/h3_video'))):
    if f.startswith('qc_') and f.endswith('.jpg'):
        cp(os.path.join('assets/h3_video', f), d)
# 手机屏幕朝向对比：v3（屏对镜头）vs v4（背对镜头）
if os.path.exists(P('assets/h3_video/shot10_h3_v3.mp4')) and os.path.exists(P('assets/h3_video/shot10_h3_v4.mp4')):
    dd = out('06_质检返修', '案例1_手机屏幕朝向')
    contact_sheet(P('assets/h3_video/shot10_h3_v3.mp4'), os.path.join(dd, 'shot10_v3_错误_屏幕对镜头.jpg'))
    contact_sheet(P('assets/h3_video/shot10_h3_v4.mp4'), os.path.join(dd, 'shot10_v4_修正_背面对镜头.jpg'))

print('progress backfill done')
print(f'  索引覆盖 finals={len(finals)} wf={len(wf)} shots_prev={len(shots_prev)}')
for base, dirs, files in os.walk(P('progress')):
    lvl = base.replace(P('progress'), '').count(os.sep)
    if lvl <= 1:
        print('  ' * lvl + os.path.basename(base) + f'  ({len(files)} files)')
