"""Tests for the self-play training gym: the engine-as-judge reward loop."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import selfplay_gym as gym


def test_grader_passes_clean_and_fails_fabrication():
    # required tool called, no error -> pass
    good = gym.grade({"attack"}, [{"name": "attack"}],
                     [{"hit": True, "damage": 5}], "He strikes for 5.")
    assert good["passed"] and good["reward"] == 1.0
    # no tool call but prose claims an outcome -> fail, and the invented number flagged
    bad = gym.grade({"attack"}, [], [], "You strike for 7 damage and it dies.")
    assert not bad["passed"] and "7" in bad["invented_numbers"]
    # tool errored -> fail
    err = gym.grade({"attack"}, [{"name": "attack"}], [{"error": "no active combat"}], "")
    assert not err["passed"] and err["errors"] == ["no active combat"]


def test_reference_policy_passes_every_scenario():
    rep = gym.run(policy=gym.reference_policy, rounds=1)
    assert rep["pass_rate"] == 1.0, [t for t in rep["transcript"] if not t["passed"]]
    # every scenario type was exercised
    assert {t["scenario"] for t in rep["transcript"]} == {s.name for s in gym.SCENARIOS}


def test_lazy_policy_fails_every_scenario():
    rep = gym.run(policy=gym.lazy_policy, rounds=1)
    assert rep["passed"] == 0
    assert all("did not call required tool" in " ".join(t["reasons"])
               for t in rep["transcript"])


def test_run_writes_only_passing_turns(tmp_path=None):
    import tempfile, json
    path = os.path.join(tempfile.mkdtemp(), "corpus.jsonl")
    gym.run(policy=gym.reference_policy, rounds=2, out_path=path)
    lines = [json.loads(l) for l in open(path, encoding="utf-8")]
    assert len(lines) == 2 * len(gym.SCENARIOS)         # all passed, all written
    for ex in lines:
        assert ex["messages"][0]["role"] == "system"
        assert ex["messages"][-1]["tool_calls"]          # the gold calls are recorded


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All gym tests passed.")
