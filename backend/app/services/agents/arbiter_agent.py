# backend/app/services/agents/arbiter_agent.py
from typing import Dict, Any, List, Optional, Tuple
from backend.app.services.agents.base_agent import BaseAgent
from backend.app.schemas.agents import AgentMessage

class ConsensusArbiterAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="arbiter_agent_solon",
            name="Solon",
            role="Consensus Arbiter & Debate Moderator",
            avatar="⚖️",
            accent_color="#10b981",
            description="Moderates agent cross-examination, balances scout enthusiasm against critic scrutiny, computes mathematical consensus, and formulates final consensus verdicts."
        )

    def arbitrate_candidates(
        self,
        critiqued_candidates: List[Dict[str, Any]],
        limit: int = 5
    ) -> Tuple[List[Dict[str, Any]], AgentMessage]:
        """Arbitrates the debate between Scout and Critic, ranking candidates by consensus index."""
        consensus_candidates = []

        for c in critiqued_candidates:
            scout_score = c.get("scout_score", 75.0)
            critic_score = c.get("critic_score", 75.0)
            movie = c["movie"]

            # Mathematical Consensus Index
            consensus_score = round((scout_score * 0.48) + (critic_score * 0.52), 1)

            # Measure agreement delta
            delta = abs(scout_score - critic_score)
            if delta <= 4.0:
                agreement_level = "Unanimous Consensus"
                synthesis_tone = "Full alignment achieved between discovery scout and film critic."
            elif delta <= 10.0:
                agreement_level = "Strong Agreement"
                synthesis_tone = "Solid convergence on narrative merit and thematic resonance."
            elif delta <= 18.0:
                agreement_level = "Nuanced Compromise"
                synthesis_tone = "Scout enthusiasm balanced with critic caveats regarding pacing and length."
            else:
                agreement_level = "Polarized Debate"
                synthesis_tone = "Dynamic debate between high thematic relevance and demanding narrative demands."

            # Construct Arbiter's Synthesis
            rubric = c["critic_rubric"]
            arbiter_synthesis = (
                f"Consensus Verdict ({consensus_score}% - {agreement_level}): "
                f"\"{movie.title}\" satisfies the user's prompt through {c['discovery_source']}. "
                f"{synthesis_tone} Recommending with an overall critic benchmark of {critic_score}/100."
            )

            c_copy = dict(c)
            c_copy["consensus_score"] = consensus_score
            c_copy["agreement_level"] = agreement_level
            c_copy["arbiter_synthesis"] = arbiter_synthesis
            consensus_candidates.append(c_copy)

        # Sort by consensus score descending
        consensus_candidates.sort(key=lambda x: x["consensus_score"], reverse=True)
        top_consensus = consensus_candidates[:limit]

        # Build Arbiter Message
        top_names = [f"\"{c['movie'].title}\" ({c['consensus_score']}%)" for c in top_consensus[:3]]
        arbiter_msg_content = (
            f"⚖️ **Consensus Verdict Finalized**: Reconciled Scout and Critic debate scores. "
            f"Top consensus recommendations established: {', '.join(top_names)}. "
            f"Discrepancies resolved with weighted Bayesian priors. Forwarding to Viewing Strategist."
        )

        agent_msg = self.create_message(
            round_index=4,
            message_type="consensus_verdict",
            content=arbiter_msg_content,
            confidence=0.98
        )

        return top_consensus, agent_msg
