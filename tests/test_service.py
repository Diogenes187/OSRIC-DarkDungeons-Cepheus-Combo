"""End-to-end test of the persistent, replayable chargen service.

Drives a build to completion through a simulated server restart (the repo is
closed and reopened from the same file mid-build) and checks the character is
saved correctly and the session row is cleaned up.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state.repo import Repo
import service


def decide(pending):
    step = pending.get("step")
    opts = pending.get("options") or []
    if step == "ability_method":
        return {"method": "4d6"}
    if step == "assign_scores":
        return {"assignment": sorted(pending["rolled"], reverse=True)}
    if step == "input_scores":
        return {"scores": {a: 12 for a in pending["abilities"]}}
    if step == "choose_ancestry":
        return {"ancestry": "Human" if "Human" in opts else opts[0]}
    if step == "choose_class":
        return {"class": "Fighter" if "Fighter" in opts else opts[0]}
    if step == "choose_alignment":
        return {"alignment": opts[0]}
    if step == "name_character":
        return {"name": "Faelith"}
    return {}


def test_persistent_build_survives_restart():
    path = tempfile.mktemp(suffix=".db")
    repo = Repo.open(path)
    cid = repo.create_campaign("Greyhawk Test")

    started = service.chargen_start(repo, cid)
    sid = started["session_id"]
    pending = started["pending"]
    assert pending["step"] == "ability_method"

    chid = None
    steps = 0
    while True:
        res = service.chargen_choose(repo, cid, sid, decide(pending))
        assert res is not None
        pending = res["pending"]
        steps += 1
        if steps == 2:                          # simulate a restart mid-build
            repo.close()
            repo = Repo.open(path)
        if res.get("character_id"):
            chid = res["character_id"]
            break
        assert steps < 20                       # safety

    # The character was saved with the chosen name, and the session is gone.
    ch = repo.get_character(chid)
    assert ch is not None and ch["name"] == "Faelith"
    assert ch["race"] == "Human" and "Fighter" in ch["classes_json"]
    assert repo.get_chargen_session(cid, sid) is None
    # An event was recorded on the chronicle spine.
    evs = repo.recent_events(cid)
    assert any(e["kind"] == "character" for e in evs)
    repo.close()
    os.remove(path)


def test_unknown_session_returns_none():
    repo = Repo.memory()
    cid = repo.create_campaign("X")
    assert service.chargen_choose(repo, cid, "nope", {}) is None
    assert service.chargen_get(repo, cid, "nope") is None
    repo.close()


if __name__ == "__main__":
    test_persistent_build_survives_restart()
    test_unknown_session_returns_none()
    print("All chargen-service tests passed.")
