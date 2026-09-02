# scripts/test_phase6.py
import os
import sys

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from fastapi.testclient import TestClient
from backend.app.database.database import SessionLocal
from backend.app.models.movie import Movie
from backend.app.services.agents.agent_orchestrator import agent_orchestrator
from backend.app.services.agents.persona_agent import PersonaProfilerAgent
from backend.app.services.agents.scout_agent import CandidateScoutAgent
from backend.app.services.agents.critic_agent import FilmCriticAgent
from backend.app.services.agents.arbiter_agent import ConsensusArbiterAgent
from backend.app.services.agents.strategist_agent import ViewingStrategistAgent
from backend.app.main import app

def run_phase6_tests():
    print("=" * 80)
    print("MOVIEREC PHASE 6: AUTONOMOUS MULTI-AGENT RECOMMENDATION & DEBATE NETWORK")
    print("=" * 80)

    db = SessionLocal()
    try:
        # 1. Test Agent Network Initialization & Roster Discovery
        print("\n[TEST 1] Testing Agent Network Roster & Descriptors...")
        roster = agent_orchestrator.get_roster()
        assert len(roster) == 5, f"Expected 5 specialized agents, got {len(roster)}"
        agent_names = [a["name"] for a in roster]
        roster_str = ", ".join([f"{a['avatar']} {a['name']} ({a['role']})" for a in roster])
        print(f"✅ Roster Verified (5 Agents Active): {roster_str}")
        assert "Aura" in agent_names, "Persona agent Aura missing!"
        assert "Argus" in agent_names, "Scout agent Argus missing!"
        assert "Kael" in agent_names, "Critic agent Kael missing!"
        assert "Solon" in agent_names, "Arbiter agent Solon missing!"
        assert "Vesper" in agent_names, "Strategist agent Vesper missing!"

        # 2. Test Persona Profiler Agent (Aura)
        print("\n[TEST 2] Testing Persona Profiler Agent ('Aura')...")
        persona_agent = PersonaProfilerAgent()
        p_query = "Mind-bending psychological sci-fi with time paradoxes and existential dread"
        persona, p_msg = persona_agent.analyze_profile(p_query, archetype_name="The Mind-Bending Sci-Fi Architect")
        
        assert persona.archetype == "The Mind-Bending Sci-Fi Architect"
        assert len(persona.target_moods) > 0
        assert persona.complexity_level == "Cerebral & High-Concept"
        print(f"✅ Persona Formulated: Archetype={persona.archetype}, Pacing={persona.pacing_preference}, Complexity={persona.complexity_level}")
        print(f"   Target Moods: {persona.target_moods}")
        print(f"   Agent Message: {p_msg.content}")

        # 3. Test Candidate Scout Agent (Argus)
        print("\n[TEST 3] Testing Candidate Scout Agent ('Argus')...")
        scout_agent = CandidateScoutAgent()
        candidates, s_msg = scout_agent.scout_candidates(p_query, persona, db, pool_size=6)
        
        assert len(candidates) > 0, "Candidate scout returned 0 candidates!"
        top_cand = candidates[0]
        print(f"✅ Scout Retrieved {len(candidates)} Candidates across Vector & Graph.")
        print(f"   Top Candidate: \"{top_cand['movie'].title}\" (Scout Score: {top_cand['scout_score']}%)")
        print(f"   Discovery Source: {top_cand['discovery_source']}")
        print(f"   Scout Pitch: {top_cand['scout_pitch']}")

        # 4. Test Film Critic & Fact-Checker Agent (Kael)
        print("\n[TEST 4] Testing Film Critic & Fact-Checker Agent ('Kael')...")
        critic_agent = FilmCriticAgent()
        critiqued, c_msg = critic_agent.review_candidate_pool(candidates, persona, debate_rigor="Fierce & Ruthless")
        
        assert len(critiqued) == len(candidates)
        top_critiqued = critiqued[0]
        rubric = top_critiqued["critic_rubric"]
        print(f"✅ Critic Evaluation Complete for \"{top_critiqued['movie'].title}\":")
        print(f"   Overall Critic Score: {rubric.overall_critic_score}/100")
        print(f"   Rubric: Narrative={rubric.narrative_depth}%, Visuals={rubric.visual_craft}%, Pacing={rubric.pacing_tension}%, Resonance={rubric.emotional_resonance}%")
        print(f"   Pros: {rubric.pros}")
        print(f"   Caveats: {rubric.caveats}")

        # 5. Test Consensus Arbiter Agent (Solon)
        print("\n[TEST 5] Testing Consensus Arbiter Agent ('Solon')...")
        arbiter_agent = ConsensusArbiterAgent()
        arbitrated, a_msg = arbiter_agent.arbitrate_candidates(critiqued, limit=4)
        
        assert len(arbitrated) > 0
        top_arb = arbitrated[0]
        print(f"✅ Arbiter Deliberation Reconciled {len(arbitrated)} Consensus Picks:")
        print(f"   Top Consensus Pick: \"{top_arb['movie'].title}\"")
        print(f"   Consensus Score: {top_arb['consensus_score']}% ({top_arb['agreement_level']})")
        print(f"   Synthesis: {top_arb['arbiter_synthesis']}")

        # 6. Test Viewing Strategist Agent (Vesper)
        print("\n[TEST 6] Testing Viewing Strategist Agent ('Vesper')...")
        strategist_agent = ViewingStrategistAgent()
        enhanced, v_msg = strategist_agent.enhance_candidates(arbitrated, db)
        
        assert len(enhanced) == len(arbitrated)
        top_enhanced = enhanced[0]
        dossier = top_enhanced["viewing_dossier"]
        print(f"✅ Viewing Dossier Prepared for \"{top_enhanced['movie'].title}\":")
        print(f"   Optimal Setting: {dossier.optimal_setting}")
        print(f"   Target Vibe: {dossier.target_vibe}")
        print(f"   Atmosphere Pairing: {dossier.snack_atmosphere_pairing}")
        if dossier.double_feature:
            print(f"   Double Feature Pairing: \"{dossier.double_feature.title}\" ({dossier.double_feature.year}) -> {dossier.double_feature.pairing_rationale}")

        # 7. Test End-to-End Deliberation Pipeline via Orchestrator
        print("\n[TEST 7] Testing End-to-End Multi-Agent Deliberation Pipeline...")
        test_prompt = "Atmospheric crime thriller with complex characters and dark gritty tone"
        delib_result = agent_orchestrator.deliberate(
            query=test_prompt,
            db=db,
            archetype="The Dark Noir & Crime Strategist",
            debate_rigor="Balanced & Analytical",
            limit=4
        )

        assert delib_result.total_rounds == 5, f"Expected 5 rounds, got {delib_result.total_rounds}"
        assert len(delib_result.recommendations) > 0, "Expected recommendations"
        print(f"✅ End-to-End Deliberation Completed in {delib_result.telemetry['timings_ms']['total_pipeline_ms']}ms!")
        print(f"   Executive Summary: {delib_result.executive_summary}")
        print("\n   Deliberation Log Messages:")
        for msg in delib_result.deliberation_log:
            print(f"   [{msg.round_index}] {msg.agent_avatar} {msg.agent_name} ({msg.agent_role}): {msg.content[:95]}...")

        # 8. Test Single-Movie Quick Debate Showdown
        print("\n[TEST 8] Testing Single-Movie Quick Debate Showdown...")
        inception = db.query(Movie).filter(Movie.title.ilike("%Inception%")).first()
        if inception:
            quick_result = agent_orchestrator.quick_debate(
                db=db,
                movie_id=inception.id,
                user_context="Looking for mind-bending films with high stakes",
                debate_rigor="Balanced & Analytical"
            )
            assert quick_result is not None, "Quick debate returned None!"
            print(f"✅ Quick Debate for \"{quick_result.movie.title}\":")
            print(f"   Scout Pitch: {quick_result.scout_pitch}")
            print(f"   Critic Review: {quick_result.critic_review}")
            print(f"   Consensus: {quick_result.consensus_score}% ({quick_result.agreement_level})")
            print(f"   Verdict: {quick_result.consensus_verdict}")

        # 9. Test FastAPI Endpoints via TestClient
        print("\n[TEST 9] Testing FastAPI Phase 6 Agent Endpoints via TestClient...")
        client = TestClient(app)

        # 9a. GET /api/agents/roster
        res = client.get("/api/agents/roster")
        assert res.status_code == 200, f"GET /api/agents/roster failed: {res.text}"
        roster_data = res.json()
        assert roster_data["total_agents"] == 5
        print(f"✅ GET /api/agents/roster -> 200 OK ({roster_data['total_agents']} agents active)")

        # 9b. GET /api/agents/personas
        res = client.get("/api/agents/personas")
        assert res.status_code == 200, f"GET /api/agents/personas failed: {res.text}"
        personas_data = res.json()
        assert len(personas_data["personas"]) >= 5
        print(f"✅ GET /api/agents/personas -> 200 OK ({len(personas_data['personas'])} persona archetypes available)")

        # 9c. GET /api/agents/stats
        res = client.get("/api/agents/stats")
        assert res.status_code == 200, f"GET /api/agents/stats failed: {res.text}"
        stats_data = res.json()
        assert stats_data["phase"] == 6
        print(f"✅ GET /api/agents/stats -> 200 OK (Phase {stats_data['phase']})")

        # 9d. POST /api/agents/deliberate
        req_body = {
            "query": "Interstellar journey to save humanity through wormholes",
            "archetype": "The Mind-Bending Sci-Fi Architect",
            "debate_rigor": "Balanced & Analytical",
            "limit": 4
        }
        res = client.post("/api/agents/deliberate", json=req_body)
        assert res.status_code == 200, f"POST /api/agents/deliberate failed: {res.text}"
        delib_api_data = res.json()
        assert len(delib_api_data["recommendations"]) > 0
        print(f"✅ POST /api/agents/deliberate -> 200 OK ({len(delib_api_data['recommendations'])} recommendations with 5-agent deliberation log)")

        # 9e. POST /api/agents/quick-debate
        if inception:
            res = client.post("/api/agents/quick-debate", json={"movie_id": inception.id})
            assert res.status_code == 200, f"POST /api/agents/quick-debate failed: {res.text}"
            quick_api_data = res.json()
            assert quick_api_data["consensus_score"] > 0
            print(f"✅ POST /api/agents/quick-debate -> 200 OK (Showdown for \"{quick_api_data['movie']['title']}\" -> {quick_api_data['consensus_score']}%)")

        print("\n" + "=" * 80)
        print("🎉 ALL PHASE 6 MULTI-AGENT NETWORK TESTS PASSED PERFECTLY!")
        print("=" * 80)

    finally:
        db.close()

if __name__ == "__main__":
    run_phase6_tests()
