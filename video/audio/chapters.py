"""Write build/chapters.txt (ffmetadata) from build/timeline.json."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMES = {
    "cold_open": "Cold open", "title": "Title", "roster": "Choose your fighter", "boot_chain": "Part 1: What even is a computer",
    "install_net": "Part 2: The install (any%)", "first_boot": "First boot", "objection": "Objection! (Gentoo, LFS, NixOS)",
    "principles": "Part 3: The five principles", "pacman": "Part 4: pacman and partial upgrades", "aur": "Part 5: The AUR",
    "wiki": "Part 6: The Wiki (a special interest)", "gaming": "Part 7: But can it game?", "winupdate": "Meanwhile, on Windows",
    "rice": "Part 8: The rice", "family": "Intermission: the family group chat", "finale": "Finale",
    "tut_intro": "TUTORIAL: before you start", "tut_usb": "Tutorial 1-4: USB + boot", "tut_live": "Tutorial 5-8: live system",
    "tut_disk": "Tutorial 9-12: partition, format, mount", "tut_install": "Tutorial 13-14: pacstrap + fstab",
    "tut_config": "Tutorial 15-19: configure", "tut_boot": "Tutorial 20-21: bootloader + network", "tut_reboot": "Tutorial 22-23: reboot + first steps",
    "credits": "Credits", "post_credits": "Post-credits",
}
tl = json.load(open(os.path.join(ROOT, "build", "timeline.json")))
segs = [(m["start"], NAMES[m["id"]]) for m in tl["music"] if m["id"] in NAMES]
out = [";FFMETADATA1", "title=I Use Arch, By The Way", "artist=Claude Opus 5.5"]
for i, (st, name) in enumerate(segs):
    end = segs[i + 1][0] if i + 1 < len(segs) else tl["total"]
    out += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(st * 1000)}", f"END={int(end * 1000)}", f"title={name}"]
open(os.path.join(ROOT, "build", "chapters.txt"), "w").write("\n".join(out) + "\n")
for st, name in segs: print(f"{int(st // 60):02d}:{int(st % 60):02d} {name}")
