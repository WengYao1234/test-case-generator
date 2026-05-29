#!/usr/bin/env python3
"""多平台安装脚本：把 test-case-generator 技能接入目标 Agent。

把本技能软链接（失败回退为复制）到目标 Agent 的 skills 目录，并初始化项目级
经验库（从 experience-seed/ 播种）。平台差异的唯一权威来源是
references/platform-profiles.md。

用法:
    python tools/install.py                         # 自动探测平台
    python tools/install.py --agent cursor          # 指定平台
    python tools/install.py --agent qwen --root ~/custom/skills
    python tools/install.py --agent claude --copy   # 强制复制而非软链接
    python tools/install.py --list                  # 列出支持的平台
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

SKILL_NAME = "test-case-generator"

# 平台档案（与 references/platform-profiles.md 第 1 节保持一致）。
# root_candidates: 全局技能根目录候选（按顺序探测，第一个存在的父目录优先）。
PLATFORMS: dict[str, dict] = {
    "qwen": {
        "label": "Qwen Code",
        "root_candidates": ["~/.qwen/skills"],
        "trigger": '在 Qwen Code 中输入强意图关键词（如"生成测试用例"）激活。',
    },
    "cursor": {
        "label": "Cursor",
        "root_candidates": ["~/.cursor/skills", "~/.cursor/skills-cursor"],
        "trigger": "在 Cursor 中输入强意图关键词激活（技能随 SKILL.md 自动发现）。",
    },
    "claude": {
        "label": "Claude Code",
        "root_candidates": ["~/.claude/skills"],
        "trigger": "在 Claude Code 中输入强意图关键词激活。",
    },
}


def skill_source_dir() -> Path:
    """返回技能根目录（本脚本位于 tools/ 下，父目录即技能根）。"""
    return Path(__file__).resolve().parent.parent


def resolve_root(agent: str, override: str | None) -> Path:
    """确定目标平台的 skills 根目录。"""
    if override:
        return Path(override).expanduser().resolve()
    candidates = PLATFORMS[agent]["root_candidates"]
    # 优先选父目录已存在的候选（说明该 Agent 已安装）。
    for cand in candidates:
        p = Path(cand).expanduser()
        if p.exists() or p.parent.exists():
            return p.resolve()
    # 都不存在则用第一个候选（后续会创建）。
    return Path(candidates[0]).expanduser().resolve()


def detect_agent() -> str | None:
    """根据各 Agent 主目录是否存在自动探测平台。"""
    found = []
    for agent, info in PLATFORMS.items():
        for cand in info["root_candidates"]:
            if Path(cand).expanduser().parent.exists():
                found.append(agent)
                break
    if len(found) == 1:
        return found[0]
    return None  # 0 个或多个，需用户显式指定


def link_skill(src: Path, dest: Path, force_copy: bool) -> str:
    """把技能放到 dest。优先软链接，失败/指定 --copy 则复制。返回采用的方式。"""
    if dest.exists() or dest.is_symlink():
        if dest.is_symlink() and dest.resolve() == src:
            return "already-linked"
        raise FileExistsError(f"目标已存在：{dest}（请先移除或改用其他 --root）")

    dest.parent.mkdir(parents=True, exist_ok=True)

    if not force_copy:
        try:
            dest.symlink_to(src, target_is_directory=True)
            return "symlink"
        except (OSError, NotImplementedError):
            # Windows 无权限 / 不支持符号链接 → 回退复制
            pass

    shutil.copytree(src, dest, ignore=shutil.ignore_patterns(
        ".git", "artifacts", "output", "experience", "__pycache__", "*.pyc"
    ))
    return "copy"


def seed_experience(skill_dir: Path) -> bool:
    """从 experience-seed/ 播种项目级 experience/（已存在则跳过）。

    skill_dir 传入安装后的技能目录：软链接时解析回源目录，复制时为副本目录。
    """
    seed = skill_dir / "experience-seed"
    exp = skill_dir / "experience"
    if not seed.is_dir():
        return False
    if exp.exists() and any(exp.iterdir()):
        return False
    exp.mkdir(exist_ok=True)
    for f in seed.glob("*.md"):
        shutil.copy2(f, exp / f.name)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="多平台安装 test-case-generator 技能")
    parser.add_argument("--agent", choices=list(PLATFORMS), help="目标平台；省略则自动探测")
    parser.add_argument("--root", help="自定义 skills 根目录，覆盖平台默认")
    parser.add_argument("--copy", action="store_true", help="强制复制而非软链接")
    parser.add_argument("--list", action="store_true", help="列出支持的平台后退出")
    args = parser.parse_args()

    if args.list:
        print("支持的平台：")
        for agent, info in PLATFORMS.items():
            print(f"  {agent:8} {info['label']:14} root: {', '.join(info['root_candidates'])}")
        return 0

    agent = args.agent or detect_agent()
    if not agent:
        print("无法自动确定平台（探测到 0 个或多个 Agent）。", file=sys.stderr)
        print("请用 --agent 指定，例如：python tools/install.py --agent cursor", file=sys.stderr)
        print("可用：" + ", ".join(PLATFORMS), file=sys.stderr)
        return 2

    src = skill_source_dir()
    root = resolve_root(agent, args.root)
    dest = root / SKILL_NAME

    print(f"平台：{PLATFORMS[agent]['label']}")
    print(f"技能源：{src}")
    print(f"安装到：{dest}")

    try:
        mode = link_skill(src, dest, args.copy)
    except FileExistsError as e:
        print(f"跳过安装：{e}", file=sys.stderr)
        return 1

    mode_label = {
        "symlink": "已创建软链接",
        "copy": "已复制（软链接不可用，回退复制）",
        "already-linked": "已存在且指向本技能，跳过",
    }[mode]
    print(f"接入方式：{mode_label}")

    seeded = seed_experience(dest.resolve())
    print(f"经验库：{'已从 experience-seed/ 播种 experience/' if seeded else 'experience/ 已存在或无种子，跳过'}")

    print()
    print("安装完成。触发方式：")
    print(f"  {PLATFORMS[agent]['trigger']}")
    print("产物目录：output/（HTML 报告）、artifacts/（中间产物）、experience/（项目级经验库）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
