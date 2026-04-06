from __future__ import annotations

from raygame.model.defs import Condition, EndingDef


ENDING_DEFS: dict[str, EndingDef] = {
    "collapse": EndingDef(
        id="collapse",
        title="倒在冷库",
        body="冷气顺着伤口往里钻。你没能把人带出去，真相和名字一起冻在了白雾里。",
        priority=100,
        conditions=(Condition("flag_set", "run_failed"),),
    ),
    "too_late": EndingDef(
        id="too_late",
        title="迟来一步",
        body="你还是到了屠宰场，只是乌鸦已经比你先一步走完了最后几分钟。她留下的，只有证据和一间太冷的房间。",
        priority=90,
        conditions=(Condition("flag_set", "crow_dead"),),
    ),
    "truth_and_cost": EndingDef(
        id="truth_and_cost",
        title="真相与代价",
        body="你把乌鸦带了出来，也把账本和真相一起带了出来。只是回头看时，你已经被这趟路掏空了大半条命。",
        priority=80,
        conditions=(
            Condition("flag_set", "crow_rescued"),
            Condition("has_item", "ledger"),
            Condition("flag_set", "crow_talked"),
            Condition("resource_at_most", "health:2"),
        ),
    ),
    "deal": EndingDef(
        id="deal",
        title="交易",
        body="乌鸦活下来了，账本也没流出去。头目退了一步，城市却把你的名字记得更牢了。",
        priority=70,
        conditions=(Condition("flag_set", "boss_ledger"), Condition("flag_set", "crow_rescued")),
    ),
    "silent_justice": EndingDef(
        id="silent_justice",
        title="沉默的正义",
        body="你把人带出了冷库，却没来得及把所有问题都问完。头目还在，账本也未必还在，但乌鸦至少活着。",
        priority=60,
        conditions=(Condition("flag_set", "crow_rescued"),),
    ),
}

