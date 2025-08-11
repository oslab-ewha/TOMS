#!/usr/bin/env python3
import re
from pathlib import Path

# ---------- 기본 유틸 ----------

def iter_sections(lines):
    """yield (name, start_idx, end_idx_exclusive). 섹션 헤더줄('*name') 포함."""
    n = len(lines); i = 0
    while i < n:
        m = re.match(r'^\s*\*([A-Za-z0-9_]+)\s*$', lines[i])
        if m:
            name = m.group(1).lower()
            j = i + 1
            while j < n and not re.match(r'^\s*\*[A-Za-z0-9_]+\s*$', lines[j]):
                j += 1
            yield (name, i, j)
            i = j
        else:
            i += 1

def rewrite_by_sections(lines, transformers):
    """transformers: dict[name -> fn(block_lines) -> new_block_lines]"""
    out = []
    pos = 0
    for name, s, e in iter_sections(lines):
        while pos < s:
            out.append(lines[pos]); pos += 1
        block = lines[s:e]
        fn = transformers.get(name)
        out.extend(fn(block) if fn else block)
        pos = e
    while pos < len(lines):
        out.append(lines[pos]); pos += 1
    return out

def keep_newline(s):
    return s if s.endswith("\n") else s + "\n"

# ---------- 섹션 변환기 ----------

def xf_mem(algorithm: str):
    """Offloading/DVS/Baseline 에서는 첫 활성 라인만(주로 dram) 남기고 나머지는 주석."""
    algo = algorithm.lower()
    def _xf(block):
        if algo not in ("offloading", "dvs", "baseline"):
            return block
        out = [block[0]]  # *mem
        seen_active = False
        for ln in block[1:]:
            st = ln.strip()
            if not st or st.startswith("#"):
                out.append(ln); continue
            if not seen_active:
                seen_active = True
                out.append(ln)
            else:
                out.append("# " + ln if not ln.lstrip().startswith("#") else ln)
        return out
    return _xf

def xf_tee(tee_enabled: bool):
    def _xf(block):
        return [block[0], f"{1 if tee_enabled else 0}\n"]
    return _xf

def xf_offratio(offloading_enabled: bool):
    """offloading 끄면 0만 활성, 나머지 전부 주석. 0이 없으면 추가."""
    def _xf(block):
        if offloading_enabled:
            return block
        out = [block[0]]
        found_zero = False
        for ln in block[1:]:
            st = ln.strip()
            if not st or st.startswith("#"):
                out.append(ln); continue
            try:
                val = float(st.split()[0])
            except Exception:
                out.append("# " + ln if not ln.lstrip().startswith("#") else ln)
                continue
            if val == 0 and not found_zero:
                out.append("0\n"); found_zero = True
            else:
                out.append("# " + ln if not ln.lstrip().startswith("#") else ln)
        if not found_zero:
            out.append("0\n")
        return out
    return _xf

def xf_cpufreq(dvfs_enabled: bool):
    """DVFS 끄면 첫 유효 라인만 활성(표준값으로 강제), 나머지는 주석. 주석 헤더 보존."""
    def _xf(block):
        if dvfs_enabled:
            return block
        out = []
        i = 0
        # 주석 헤더 보존
        while i < len(block) and block[i].strip().startswith("#"):
            out.append(block[i]); i += 1
        # *cpufreq
        if i < len(block) and block[i].strip().lower().startswith("*cpufreq"):
            out.append(block[i]); i += 1
        else:
            return ["# wcet_scale power_active power_idle\n", "*cpufreq\n", "1    100    1\n"]
        kept = False
        while i < len(block):
            ln = block[i]; i += 1
            st = ln.strip()
            if not st:
                out.append(ln); continue
            if st.startswith("#"):
                out.append(ln); continue
            if not kept:
                out.append("1    100    1\n"); kept = True
            else:
                out.append("# " + ln if not ln.lstrip().startswith("#") else ln)
        if not kept:
            out.append("1    100    1\n")
        return out
    return _xf

def xf_task(offloading_enabled: bool):
    """offloading 끄면 마지막 필드(오프로딩 플래그) 전부 0 강제."""
    def _xf(block):
        if offloading_enabled:
            return block
        out = [block[0]]
        for ln in block[1:]:
            st = ln.strip()
            if not st or st.startswith("#"):
                out.append(ln); continue
            parts = re.split(r"\s+", st)
            if len(parts) >= 8 and re.match(r"^\d+$", parts[0]):
                parts[-1] = "0"
                out.append("\t".join(parts) + "\n")
            else:
                out.append(ln)
        return out
    return _xf

# ---------- 공개 함수: conf 생성 ----------

def create_conf(base_conf: Path, out_conf: Path, algorithm: str,
                tee_enabled: bool, offloading_enabled: bool, dvfs_enabled: bool):
    """
    base_conf를 읽어서 알고리즘 정책에 따라 섹션별로 안전하게 수정/주석 처리 후 out_conf에 씀.
    *end 없이도 동작.
    """
    lines = base_conf.read_text().splitlines(True)
    transformers = {
        "mem": xf_mem(algorithm),
        "tee": xf_tee(tee_enabled),
        "offloadingratio": xf_offratio(offloading_enabled),
        "cpufreq": xf_cpufreq(dvfs_enabled),
        "task": xf_task(offloading_enabled),
    }
    new_lines = rewrite_by_sections(lines, transformers)
    out_conf.write_text("".join(new_lines))

# ---------- 사용 예시 ----------
if __name__ == "__main__":
    BASE = Path("simulators/candy_cycle.conf")
    out_dir = Path("simulators/tmp"); out_dir.mkdir(exist_ok=True)
    scenarios = [
        ("CO-DMO-CT", True,  True,  True ),
        ("CO-DMO",    False, True,  True ),
        ("Offloading",False, True,  False),
        ("DVS",       False, False, True ),
        ("Baseline",  False, False, False),
    ]
    for name, tee, offl, dvfs in scenarios:
        create_conf(BASE, out_dir / f"{name.lower()}.conf", name, tee, offl, dvfs)
    print(f"generated: {out_dir.resolve()}")
