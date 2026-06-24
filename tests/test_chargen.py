"""Tests for the OSRIC character-creation state machine."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chargen import CharacterCreator, ORDER


def decide(p, *, method="4d6", ancestry=None, cls=None, classes=None, align=None,
           name="Test", scores=None, rerolls=0, _state=None):
    """A scripted decider. _state carries a mutable reroll counter."""
    step = p.get("step")
    opts = p.get("options") or []
    if step == "ability_method":
        return {"method": method}
    if step == "input_scores":
        return {"scores": scores or {a: 12 for a in ORDER}}
    if step == "assign_scores":
        if _state is not None and _state["rerolls"] < rerolls:
            _state["rerolls"] += 1
            return {"reroll": True}
        # Assign highest-to-lowest into STR, DEX, ... so a requested martial
        # class reliably meets its Strength minimum.
        return {"assignment": sorted(p["rolled"], reverse=True)}
    if step == "choose_ancestry":
        return {"ancestry": ancestry or opts[0]}
    if step == "choose_class":
        if classes:
            return {"classes": list(classes)}
        return {"class": cls if (cls in opts) else opts[0]}
    if step == "choose_alignment":
        return {"alignment": align or opts[0]}
    if step == "name_character":
        return {"name": name}
    return {}


def run(seed, allow_overrides=False, **kw):
    state = {"rerolls": 0}
    cc = CharacterCreator(name="Recruit AAAA", seed=seed,
                          allow_overrides=allow_overrides)
    choices = []
    while not cc.complete:
        p = cc.pending()
        if p is None:
            break
        d = decide(p, _state=state, **kw)
        choices.append(d)
        cc.choose(d)
    return cc.result(), choices


def _snap(c):
    return (c.name, c.race, c.char_class, c.alignment, dict(c.scores),
            c.str_pct, c.hp_max, c.ac_descending, c.ac_ascending, c.gold)


def test_full_build_is_valid():
    c, _ = run(101, ancestry="Human", cls="Fighter", align="LG", name="Niorvia")
    assert c.name == "Niorvia"
    assert c.race == "Human" and c.char_class == "Fighter"
    assert c.alignment == "LG"
    assert all(3 <= c.scores[a] <= 19 for a in ORDER)
    assert c.hp_max >= 1
    assert c.ac_descending + 0 == 20 - c.ac_ascending     # the two AC scales agree
    assert c.gold > 0


def test_determinism():
    a, ca = run(2024, ancestry="Elf", cls="Fighter", align="CG")
    b, cb = run(2024, ancestry="Elf", cls="Fighter", align="CG")
    assert _snap(a) == _snap(b) and ca == cb
    d, _ = run(999, ancestry="Elf", cls="Fighter", align="CG")
    assert _snap(d) != _snap(a)                            # different seed differs


def test_reroll_preserves_determinism():
    a, _ = run(555, rerolls=3, ancestry="Human", cls="Thief", align="N")
    b, _ = run(555, rerolls=3, ancestry="Human", cls="Thief", align="N")
    assert _snap(a) == _snap(b)
    none, _ = run(555, rerolls=0, ancestry="Human", cls="Thief", align="N")
    assert _snap(none) != _snap(a)                         # rerolls advance the RNG


def test_input_mode():
    godly = {"str": 18, "dex": 17, "con": 16, "int": 15, "wis": 14, "cha": 13}
    c, _ = run(7, method="input", scores=godly, ancestry="Human",
               cls="Fighter", align="LN")
    # Human has no adjustments, so scores survive as entered (STR may gain a pct).
    assert c.scores["dex"] == 17 and c.scores["con"] == 16
    assert c.scores["str"] in (18, 19)


def test_exceptional_strength():
    # A warrior with an 18 STR rolls exceptional Strength.
    c, _ = run(3, method="input",
               scores={"str": 18, "dex": 12, "con": 12, "int": 12, "wis": 12, "cha": 12},
               ancestry="Human", cls="Fighter", align="LG")
    assert (c.str_pct >= 1) or (c.scores["str"] == 19)
    # A non-warrior never gets exceptional Strength.
    m, _ = run(3, method="input",
               scores={"str": 18, "dex": 12, "con": 12, "int": 12, "wis": 12, "cha": 12},
               ancestry="Human", cls="Thief", align="N")
    assert m.str_pct == 0 and m.scores["str"] == 18


def test_override_toggle():
    # Halflings can't normally be Magic-Users; overrides allow it.
    c, _ = run(42, allow_overrides=True, method="input",
               scores={"str": 9, "dex": 12, "con": 12, "int": 12, "wis": 12, "cha": 12},
               ancestry="Halfling", cls="Magic-User", align="N")
    assert c.race == "Halfling" and c.char_class == "Magic-User"


def test_multiclass_any_combo_under_overrides():
    # Greyhawk "weird" mode: any race, any combination of any classes, no gate.
    c, _ = run(77, allow_overrides=True, method="input",
               scores={a: 15 for a in ORDER},
               ancestry="Human",
               classes=["Fighter", "Magic-User", "Thief", "Cleric"],
               align="N", name="Quadfecta")
    assert c.classes_list == ["Fighter", "Magic-User", "Thief", "Cleric"]
    assert c.char_class == "Fighter"           # primary drives tables
    assert c.hp_max >= 1 and c.gold > 0
    repo_d = c.to_repo_dict()
    assert [x["class"] for x in repo_d["classes"]] == \
        ["Fighter", "Magic-User", "Thief", "Cleric"]


def test_multiclass_dedupes_and_is_deterministic():
    a, _ = run(88, allow_overrides=True, ancestry="Elf",
               classes=["Fighter", "Fighter", "Magic-User"], align="CG")
    b, _ = run(88, allow_overrides=True, ancestry="Elf",
               classes=["Fighter", "Fighter", "Magic-User"], align="CG")
    assert a.classes_list == ["Fighter", "Magic-User"]      # deduped, order kept
    assert _snap(a)[6:] == _snap(b)[6:]                     # hp/ac/gold reproducible


def test_single_class_path_unchanged():
    c, _ = run(101, ancestry="Human", cls="Fighter", align="LG", name="Niorvia")
    assert c.classes_list == ["Fighter"] and c.char_class == "Fighter"


def test_name_defaults_to_handle():
    c, _ = run(1, ancestry="Human", cls="Fighter", align="LG", name="")
    assert c.name == "Recruit AAAA"                        # blank keeps the handle


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All chargen tests passed.")
