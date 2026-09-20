# backend/app/services/neuro_studio.py
import re
import uuid
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from backend.app.models.movie import Movie
from backend.app.schemas.studio import (
    DubbingVoice,
    DubbingManifest,
    ActMonologue,
    WordTimingMarker,
    ReCutVibe,
    ReCutShot,
    ReCutTreatment,
)

class NeuroStudioService:
    def __init__(self):
        self._voices: List[DubbingVoice] = self._init_voices()
        self._vibes: List[ReCutVibe] = self._init_vibes()

    def _init_voices(self) -> List[DubbingVoice]:
        return [
            # English
            DubbingVoice(
                voice_id="en_titan",
                name="Titan Vance",
                language_code="en",
                language_name="English (US)",
                gender="male",
                archetype="Epic Hollywood Baritone",
                description="Resonant, deep cinematic blockbuster narrator with monumental presence.",
                speech_rate=0.92,
                speech_pitch=0.85,
                sample_phrase="In a world where memories can be reconstructed, one secret remains buried in the deep."
            ),
            DubbingVoice(
                voice_id="en_selene",
                name="Selene Cross",
                language_code="en",
                language_name="English (UK)",
                gender="female",
                archetype="Noir Detective & Intimate Auteur",
                description="Sultry, enigmatic, breathless pacing ideal for psychological thrillers and neo-noir.",
                speech_rate=0.98,
                speech_pitch=1.05,
                sample_phrase="The rain washed away the evidence, but the shadow on 4th Avenue was already waiting."
            ),
            DubbingVoice(
                voice_id="en_nexus",
                name="Aria Nexus",
                language_code="en",
                language_name="English (US)",
                gender="female",
                archetype="Cybernetic Synthetic Intelligence",
                description="Precise, crystal-clear, eerie electronic cadence with subtle vocoder inflection.",
                speech_rate=1.05,
                speech_pitch=1.12,
                sample_phrase="System breach confirmed. Neural synchronization threshold exceeded by 400 percent."
            ),
            # Spanish
            DubbingVoice(
                voice_id="es_mateo",
                name="Mateo Calderón",
                language_code="es",
                language_name="Spanish (Castilian/LatAm)",
                gender="male",
                archetype="Gothic Passion & Dramatic Gravity",
                description="Warm, impassioned baritone carrying intense emotional weight and cinematic flair.",
                speech_rate=0.96,
                speech_pitch=0.90,
                sample_phrase="Cuando el destino llama en el silencio de la noche, no hay marcha atrás."
            ),
            DubbingVoice(
                voice_id="es_valeria",
                name="Valeria Soler",
                language_code="es",
                language_name="Spanish (Latin America)",
                gender="female",
                archetype="Magnetic Thriller Narrator",
                description="Crisp, dynamic storytelling voice with suspenseful cadence and melodic tone.",
                speech_rate=1.02,
                speech_pitch=1.08,
                sample_phrase="Cada secreto tiene su precio, y hoy ha llegado la hora de pagar."
            ),
            # French
            DubbingVoice(
                voice_id="fr_antoine",
                name="Antoine De La Tour",
                language_code="fr",
                language_name="French",
                gender="male",
                archetype="Auteur Poetic Philosopher",
                description="Velvety, reflective tone reminiscent of French New Wave cinema and art-house narratives.",
                speech_rate=0.94,
                speech_pitch=0.92,
                sample_phrase="Dans le reflet d'un songe oublié, la vérité n'est plus qu'une illusion poétique."
            ),
            DubbingVoice(
                voice_id="fr_claire",
                name="Claire Vaneau",
                language_code="fr",
                language_name="French",
                gender="female",
                archetype="Cerebral Elegance",
                description="Sophisticated, intimate, nuanced inflection capturing psychological tension.",
                speech_rate=1.0,
                speech_pitch=1.04,
                sample_phrase="Le compte à rebours est lancé. Nul ne pourra échapper à la mémoire."
            ),
            # Japanese
            DubbingVoice(
                voice_id="ja_ryu",
                name="Ryunosuke Kuroda (黒田 竜之介)",
                language_code="ja",
                language_name="Japanese",
                gender="male",
                archetype="High-Octane Shonen & Cyber-Samurai",
                description="Commanding, fierce, razor-sharp theatrical delivery with high dramatic tension.",
                speech_rate=1.08,
                speech_pitch=0.88,
                sample_phrase="運命を切り裂け！目覚めた力は、もう誰にも止められない。"
            ),
            DubbingVoice(
                voice_id="ja_ayame",
                name="Ayame Fujiwara (藤原 あやめ)",
                language_code="ja",
                language_name="Japanese",
                gender="female",
                archetype="Ethereal Anime Oracle",
                description="Dreamy, crystalline, mysterious cadence perfect for sci-fi and supernatural drama.",
                speech_rate=0.98,
                speech_pitch=1.18,
                sample_phrase="失われた記憶の彼方で、時空を超えた約束が再び動き出す。"
            ),
            # German
            DubbingVoice(
                voice_id="de_klaus",
                name="Klaus Von Stern",
                language_code="de",
                language_name="German",
                gender="male",
                archetype="Industrial Dystopian Authority",
                description="Deep, monolithic, disciplined timber built for sci-fi epics and cold-war thrillers.",
                speech_rate=0.95,
                speech_pitch=0.82,
                sample_phrase="Die Grenze zwischen Mensch und Maschine ist endgültig gefallen."
            ),
            # Hindi
            DubbingVoice(
                voice_id="hi_vikram",
                name="Vikram Rathore (विक्रम राठौड़)",
                language_code="hi",
                language_name="Hindi",
                gender="male",
                archetype="Epic Bollywood & Action Maestro",
                description="Powerful, thunderous, emotionally gripping voice loaded with theatrical grandeur.",
                speech_rate=0.98,
                speech_pitch=0.89,
                sample_phrase="जब तक तूफान से नहीं टकराओगे, तब तक समंदर का खौफ खत्म नहीं होगा।"
            ),
            DubbingVoice(
                voice_id="hi_ananya",
                name="Ananya Sen (अनन्या सेन)",
                language_code="hi",
                language_name="Hindi",
                gender="female",
                archetype="Melodic Cinematic Storyteller",
                description="Expressive, evocative, warm and poetic narrative voice for dramatic journeys.",
                speech_rate=1.0,
                speech_pitch=1.06,
                sample_phrase="यह सिर्फ एक कहानी नहीं, रूह को छू लेने वाला एक अंतहीन सफर है।"
            )
        ]

    def _init_vibes(self) -> List[ReCutVibe]:
        return [
            ReCutVibe(
                vibe_id="cyberpunk",
                name="Cyberpunk Synthwave Dystopia",
                tagline="Neon drenched rain, analog Moog sub-bass, and digital alienation.",
                icon="fa-microchip",
                primary_color="#00E5FF",
                lut_css_filter="contrast(135%) saturate(175%) hue-rotate(185deg) brightness(95%)",
                lut_description="Cyan/Magenta dual-split tone with hyper-crushed shadows and electric neon glow.",
                soundtrack_tempo_bpm=128,
                soundtrack_key="D Minor",
                soundtrack_instruments=["Moog Sub 37", "LinnDrum 808", "Distorted Arpeggiators", "Tape Echo Shimmer"],
                narrative_pacing="Pulsing hypnotic rhythm with aggressive smash-cuts on the drum transients."
            ),
            ReCutVibe(
                vibe_id="wes_anderson",
                name="Pastel Whimsical Symmetrical",
                tagline="Obsessive center-framing, quirky xylophones, and nostalgic warm yellow palettes.",
                icon="fa-palette",
                primary_color="#F4A261",
                lut_css_filter="sepia(45%) saturate(145%) brightness(108%) contrast(92%)",
                lut_description="Warm vintage kodachrome sepia, subdued contrast, and glowing golden hour tint.",
                soundtrack_tempo_bpm=104,
                soundtrack_key="C Major / A Minor",
                soundtrack_instruments=["Glockenspiel", "Pizzicato Chamber Strings", "Harpsichord", "Vintage Snare"],
                narrative_pacing="Deliberate 90-degree whip-pans, snap zooms, and deadpan freeze-frame vignettes."
            ),
            ReCutVibe(
                vibe_id="neo_noir",
                name="90s Grungy Neo-Noir",
                tagline="Smoke-filled blinds, melancholic brass, rainslicked pavement, and moral gray zones.",
                icon="fa-user-secret",
                primary_color="#A8DADC",
                lut_css_filter="grayscale(85%) contrast(165%) brightness(88%) sepia(20%)",
                lut_description="Monochromatic high-contrast silver halide with deep obsidian blacks and sepia tint.",
                soundtrack_tempo_bpm=74,
                soundtrack_key="F Minor",
                soundtrack_instruments=["Muted Tenor Saxophone", "Brush Snare", "Upright Double Bass", "Rain Foley"],
                narrative_pacing="Slow-burn atmospheric dread interspersed with abrupt violent revelation cuts."
            ),
            ReCutVibe(
                vibe_id="techno_thriller",
                name="High-Tension Psychological Thriller",
                tagline="Sub-bass drone risers, Shepard tone frequency illusions, and clinical claustrophobia.",
                icon="fa-brain",
                primary_color="#E63946",
                lut_css_filter="contrast(150%) saturate(80%) brightness(90%) hue-rotate(330deg)",
                lut_description="Desaturated clinical teal-green grade with aggressive crimson alert flashes.",
                soundtrack_tempo_bpm=140,
                soundtrack_key="Bb Minor",
                soundtrack_instruments=["Waterphone", "Shepard Tone Synthesizer", "Orchestral Stabs", "Staccato Violas"],
                narrative_pacing="Staccato micro-edits accelerating into an overwhelming sensory sensory crescendo."
            ),
            ReCutVibe(
                vibe_id="retro_slasher",
                name="80s VHS Grindhouse Slasher",
                tagline="Analog tape tracking artifacts, heavy film grain, screaming synthesizers, and midnight terror.",
                icon="fa-skull",
                primary_color="#9D0208",
                lut_css_filter="contrast(140%) saturate(160%) sepia(30%) hue-rotate(345deg)",
                lut_description="Bleeding crimson saturation, analog VHS tape warmth, and heavy crushed blacks.",
                soundtrack_tempo_bpm=120,
                soundtrack_key="E Minor",
                soundtrack_instruments=["Roland Jupiter-8", "Detuned FM Bells", "Analog Noise Sweeps", "Heartbeat Kick"],
                narrative_pacing="Predatory POV gliding tracking shots punctuated by sudden jump-shock transitions."
            ),
            ReCutVibe(
                vibe_id="french_wave",
                name="Intimate French New Wave",
                tagline="Existential jump-cuts, acoustic upright piano, Parisian melancholy, and romantic poetry.",
                icon="fa-film",
                primary_color="#E9C46A",
                lut_css_filter="grayscale(40%) contrast(110%) brightness(102%) sepia(25%)",
                lut_description="Soft 35mm celluloid glow, pastel champagne highlights, and subtle vintage vignette.",
                soundtrack_tempo_bpm=86,
                soundtrack_key="G Major",
                soundtrack_instruments=["Unprepared Upright Piano", "Melancholic Accordion", "Soft Cello", "Café Ambience"],
                narrative_pacing="Poetic discontinuous jump-cuts following wandering glances and philosophical musings."
            )
        ]

    def get_available_voices(self) -> List[DubbingVoice]:
        return self._voices

    def get_voice_by_id(self, voice_id: str) -> Optional[DubbingVoice]:
        for v in self._voices:
            if v.voice_id == voice_id:
                return v
        return None

    def get_preset_vibes(self) -> List[ReCutVibe]:
        return self._vibes

    def get_vibe_by_id(self, vibe_id: str) -> ReCutVibe:
        for v in self._vibes:
            if v.vibe_id == vibe_id:
                return v
        return self._vibes[0]

    def generate_trailer_recut(
        self,
        movie_id: int,
        vibe_id: str,
        custom_prompt: Optional[str] = None,
        intensity: float = 1.0,
        db: Optional[Session] = None
    ) -> ReCutTreatment:
        movie = None
        if db:
            movie = db.query(Movie).filter(Movie.id == movie_id).first()

        title = movie.title if movie else "Untitled Masterpiece"
        overview = movie.overview if movie else "An enigmatic cinematic journey through uncharted depths."
        genre = movie.genres[0].name if (movie and movie.genres) else "Drama"
        director = movie.directors[0].name if (movie and movie.directors) else "Visionary Director"
        year = movie.release_date[:4] if (movie and movie.release_date) else "2024"

        vibe = self.get_vibe_by_id(vibe_id)

        # Concept formulation
        remix_genre = f"{vibe.name.split(' ')[0]} {genre}"
        
        prompt_influence = f" Custom Treatment Guidance: '{custom_prompt}'." if custom_prompt else ""
        concept_logline = (
            f"What if {title} was conceived not as a {genre.lower()}, but as a {vibe.name.lower()}? "
            f"Set against a reimagined sonic landscape of {', '.join(vibe.soundtrack_instruments[:2])}, "
            f"this cut re-contextualizes {title} as an exploration of psychological friction and sensory excess.{prompt_influence}"
        )

        directorial_vision = (
            f"Re-imagined through the lens of {vibe.name}: Applying a custom color grade of '{vibe.lut_description}' "
            f"with {vibe.soundtrack_tempo_bpm} BPM acoustic sync. Every cut aligns with the rhythm of {vibe.narrative_pacing}"
        )

        # Generate 4-Act Shot Breakdown
        shots = [
            ReCutShot(
                shot_number=1,
                act="Act I: Inciting Ambience",
                start_sec=0.0,
                end_sec=14.0,
                visual_description=f"Wide establishing tableau of {title}'s iconic setting, heavily graded with {vibe.primary_color} volumetric lighting.",
                camera_movement="Slow forward creeping push-in, low horizon line.",
                color_grade_treatment=f"Crushed blacks, glowing {vibe.primary_color} ambient bleed.",
                audio_soundscape=f"Subtle drone in {vibe.soundtrack_key} fading into quiet {vibe.soundtrack_instruments[0]}.",
                transition_type="Fade from Black with analog scanline flash",
                narrator_voiceover=f"We thought we knew the story of {title}. But memory has a way of rewriting itself."
            ),
            ReCutShot(
                shot_number=2,
                act="Act II: Rising Distortion",
                start_sec=14.0,
                end_sec=35.0,
                visual_description=f"Rapid character profiles: intense close-up reaction shots juxtaposed with structural tension.",
                camera_movement="Steadicam circular orbit around protagonist.",
                color_grade_treatment=f"{vibe.lut_description} with sharp edge-contrast enhancements.",
                audio_soundscape=f"BPM ramps to {vibe.soundtrack_tempo_bpm}. Introduction of {vibe.soundtrack_instruments[1]}.",
                transition_type="Kinetic Match Cut on character eye-line",
                narrator_voiceover=f"When the boundaries began to fracture, there was no turning back from the inevitable."
            ),
            ReCutShot(
                shot_number=3,
                act="Act III: Sensory Crescendo",
                start_sec=35.0,
                end_sec=65.0,
                visual_description=f"High-velocity montage of the central conflict, action beats, and psychological revelations.",
                camera_movement="Dynamic whip-pans and stutter-frame handheld velocity.",
                color_grade_treatment="Maximum saturation flare with strobe highlights on impact frames.",
                audio_soundscape=f"Full acoustic crescendo: {', '.join(vibe.soundtrack_instruments)} driving at peak intensity.",
                transition_type="Hard Smash Cut on musical transients",
                narrator_voiceover=f"Every secret has its echo. And this time, silence is no longer an option."
            ),
            ReCutShot(
                shot_number=4,
                act="Act IV: The Lingering Stinger",
                start_sec=65.0,
                end_sec=82.0,
                visual_description=f"Cryptic final frame of {title}: solitary silhouette or unresolved prop holding in stillness.",
                camera_movement="Locked-off static frame slowly breathing backwards.",
                color_grade_treatment="Desaturating to deep obsidian shadow with single neon rimlight.",
                audio_soundscape=f"Sudden audio drop-out leaving only a single sustained note from {vibe.soundtrack_instruments[0]}.",
                transition_type="Snap to Title Card with chromatic aberration glitch",
                narrator_voiceover=f"{title}. Experience the alternate dimension."
            )
        ]

        full_monologue = " ".join([s.narrator_voiceover for s in shots])

        soundscape_cues = [
            f"Opening Ambience: 30-second low frequency drone in {vibe.soundtrack_key}",
            f"Transient Beat: Percussive strike at 00:14 aligning with character turn",
            f"Cadence Ramp: Continuous BPM acceleration from 80 to {vibe.soundtrack_tempo_bpm} BPM",
            f"Drop & Stinger: Complete acoustic cutoff at 01:05 followed by sub-bass impact"
        ]

        tagline_options = {
            "cyberpunk": f"In the neon abyss of {year}, consciousness is the ultimate heist.",
            "wes_anderson": f"A thoroughly curated and slightly eccentric retelling of {title}.",
            "neo_noir": f"The rain never stops in {title}. Neither do the regrets.",
            "techno_thriller": f"Your perception is the primary vulnerability.",
            "retro_slasher": f"In {year}, the nightmare found a new frequency.",
            "french_wave": f"To look into {title} is to glimpse the poetry of what might have been."
        }
        suggested_tagline = tagline_options.get(vibe_id, f"The reimagined vision of {title}.")

        return ReCutTreatment(
            treatment_id=f"recut_{vibe_id}_{uuid.uuid4().hex[:8]}",
            movie_id=movie_id,
            movie_title=title,
            original_genre=genre,
            vibe=vibe,
            remix_genre=remix_genre,
            concept_logline=concept_logline,
            directorial_vision=directorial_vision,
            lut_filter_css=vibe.lut_css_filter,
            soundtrack_profile={
                "tempo_bpm": vibe.soundtrack_tempo_bpm,
                "key": vibe.soundtrack_key,
                "instrumentation": vibe.soundtrack_instruments,
                "mixing_profile": f"Spatialized 7.1 with heavy compression on {vibe.soundtrack_instruments[0]}"
            },
            acts_timeline=shots,
            voiceover_monologue=full_monologue,
            soundscape_cues=soundscape_cues,
            suggested_tagline=suggested_tagline
        )

    def generate_multilingual_dub(
        self,
        movie_id: int,
        language: str = "en",
        voice_id: Optional[str] = None,
        script_style: str = "epic",
        custom_monologue: Optional[str] = None,
        db: Optional[Session] = None
    ) -> DubbingManifest:
        movie = None
        if db:
            movie = db.query(Movie).filter(Movie.id == movie_id).first()

        title = movie.title if movie else "Cinematic Odyssey"
        overview = movie.overview if movie else "A profound tale of mystery, discovery, and human passion."
        genre = movie.genres[0].name if (movie and movie.genres) else "Drama"

        # Resolve voice
        matched_voice = None
        if voice_id:
            matched_voice = self.get_voice_by_id(voice_id)
        if not matched_voice:
            # Pick first matching language voice
            for v in self._voices:
                if v.language_code == language:
                    matched_voice = v
                    break
        if not matched_voice:
            matched_voice = self._voices[0]

        # Monologue text per language
        scripts_by_lang = {
            "en": {
                "title": title,
                "acts": [
                    ("Act I: Origin", "00:00", "Narrator", f"Some stories do not merely unfold; they echo through the corridors of time."),
                    ("Act II: The Descent", "00:15", "Narrator", f"In {title}, the line separating reality from illusion begins to dissolve."),
                    ("Act III: The Reckoning", "00:35", "Narrator", f"Every choice demands a sacrifice, and the darkest secrets refuse to stay buried."),
                    ("Act IV: The Legacy", "00:55", "Narrator", f"Witness the revelation. Nothing will ever be the same again.")
                ]
            },
            "es": {
                "title": title,
                "acts": [
                    ("Acto I: El Origen", "00:00", "Narrador", f"Hay historias que no solo se cuentan; resuenan en los confines del tiempo."),
                    ("Acto II: El Descenso", "00:15", "Narrador", f"En {title}, la delgada línea entre la verdad y la ilusión se desvanece por completo."),
                    ("Acto III: El Juicio", "00:35", "Narrador", f"Cada decisión tiene su precio, y los secretos más oscuros siempre encuentran la luz."),
                    ("Acto IV: El Legado", "00:55", "Narrador", f"Descubre la revelación definitiva. El destino está a punto de cambiar para siempre.")
                ]
            },
            "fr": {
                "title": title,
                "acts": [
                    ("Acte I: L'Origine", "00:00", "Narrateur", f"Certaines histoires ne s'effacent jamais; elles résonnent à travers les âges."),
                    ("Acte II: La Faille", "00:15", "Narrateur", f"Dans {title}, la frontière entre le rêve et la réalité se dissout doucement."),
                    ("Acte III: L'Affrontement", "00:35", "Narrateur", f"Chaque choix exige un sacrifice, et le passé refuse d'être oublié."),
                    ("Acte IV: L'Éveil", "00:55", "Narrateur", f"Vivez l'expérience inoubliable. Le silence n'a plus sa place.")
                ]
            },
            "ja": {
                "title": f"『{title}』",
                "acts": [
                    ("幕一: 胎動", "00:00", "語り手", f"時を超えて響き渡る、決して消えることのない記憶の物語がある。"),
                    ("幕二: 迷宮", "00:15", "語り手", f"『{title}』において、現実と幻想の境界線は音を立てて崩れ去る。"),
                    ("幕三: 激突", "00:35", "語り手", f"すべての選択には代償が伴い、深淵の真実は沈黙を拒絶する。"),
                    ("幕四: 覚醒", "00:55", "語り手", f"その結末を刮目せよ。世界はもう二度と同じ姿には戻らない。")
                ]
            },
            "de": {
                "title": title,
                "acts": [
                    ("Akt I: Der Ursprung", "00:00", "Erzähler", f"Manche Geschichten vergehen nie; sie hallen durch die Korridore der Ewigkeit."),
                    ("Akt II: Der Riss", "00:15", "Erzähler", f"In {title} beginnt die Grenze zwischen Realität und Illusion zu zerfallen."),
                    ("Akt III: Die Konfrontation", "00:35", "Erzähler", f"Jede Entscheidung fordert ein Opfer, und das Dunkel lässt sich nicht verbergen."),
                    ("Akt IV: Das Vermächtnis", "00:55", "Erzähler", f"Erlebe die unaufhaltsame Wahrheit. Nichts wird jemals wieder so sein.")
                ]
            },
            "hi": {
                "title": title,
                "acts": [
                    ("अंक १: शुरुआत", "00:00", "सूत्रधार", f"कुछ कहानियां वक्त के साथ नहीं मिटतीं, वे सदियों तक गूंजती रहती हैं।"),
                    ("अंक २: रहस्य का जाल", "00:15", "सूत्रधार", f"{title} में हकीकत और भरम के बीच का फासला धीरे-धीरे मिटने लगता है।"),
                    ("अंक ३: अंतिम जंग", "00:35", "सूत्रधार", f"हर फैसले की एक भारी कीमत होती है, और छिपे हुए राज कभी खामोश नहीं रहते।"),
                    ("अंक ४: दास्तान-ए-इंसाफ", "00:55", "सूत्रधार", f"इस बेमिसाल दास्तान के गवाह बनिए। अब कुछ भी पहले जैसा नहीं रहेगा।")
                ]
            }
        }

        lang_data = scripts_by_lang.get(language, scripts_by_lang["en"])
        
        act_monologues: List[ActMonologue] = []
        for idx, (act_name, tc, spk, txt) in enumerate(lang_data["acts"]):
            act_monologues.append(ActMonologue(
                act_index=idx + 1,
                act_name=act_name,
                timecode=tc,
                speaker=spk,
                text=txt
            ))

        full_script = " ".join([a.text for a in act_monologues])
        if custom_monologue:
            full_script = custom_monologue

        # Word timing markers computation for real-time karaoke HUD
        if matched_voice.language_code == "ja":
            raw_chunks = re.findall(r'[^、。！？\s]+[、。！？]?', full_script)
            words = []
            for chunk in raw_chunks:
                clean = chunk
                while len(clean) > 4:
                    words.append(clean[:3])
                    clean = clean[3:]
                if clean:
                    words.append(clean)
        else:
            words = re.findall(r'\S+', full_script)
        
        word_markers: List[WordTimingMarker] = []
        current_time_ms = 400  # Initial breath buffer
        
        for w in words:
            # Word duration based on character length and voice speed modifier
            duration = int((200 + len(w) * 28) / (matched_voice.speech_rate or 1.0))
            word_markers.append(WordTimingMarker(
                word=w,
                start_ms=current_time_ms,
                end_ms=current_time_ms + duration
            ))
            # Pause slightly after punctuation
            pause = 280 if any(punct in w for punct in ['.', '!', '?', '।', '。']) else 60
            current_time_ms += duration + pause

        total_duration_sec = round(current_time_ms / 1000.0, 2)

        acoustic_recommendation = (
            f"Mixed with {matched_voice.archetype} delivery at {matched_voice.speech_rate}x pacing. "
            f"Recommend -3dB background soundtrack ducking during vocal word intervals."
        )

        return DubbingManifest(
            movie_id=movie_id,
            movie_title=title,
            language_code=matched_voice.language_code,
            language_name=matched_voice.language_name,
            voice=matched_voice,
            full_script=full_script,
            localized_title=lang_data.get("title", title),
            acts=act_monologues,
            word_markers=word_markers,
            total_estimated_duration_sec=total_duration_sec,
            acoustic_recommendation=acoustic_recommendation
        )

    def export_treatment_markdown(self, treatment: ReCutTreatment, dubbing: Optional[DubbingManifest] = None) -> str:
        lines = [
            f"# 🎬 Neuro-Cinematic Director's Cut: {treatment.movie_title}",
            f"**Remix Style:** {treatment.vibe.name} | **Vibe ID:** `{treatment.vibe.vibe_id}`",
            f"**Concept Logline:** *\"{treatment.suggested_tagline}\"*",
            "",
            "---",
            "",
            "## 👁️ Directorial Vision & Philosophy",
            treatment.concept_logline,
            "",
            f"**Color Grading LUT (CSS Preset):** `{treatment.lut_filter_css}`",
            f"**Visual Grade Notes:** {treatment.vibe.lut_description}",
            "",
            "## 🎵 Acoustic & Soundtrack Composition Blueprint",
            f"- **Tempo:** {treatment.soundtrack_profile.get('tempo_bpm', 120)} BPM",
            f"- **Key:** {treatment.soundtrack_profile.get('key', 'D Minor')}",
            f"- **Instrumentation:** {', '.join(treatment.soundtrack_profile.get('instrumentation', []))}",
            f"- **Audio Pacing:** {treatment.vibe.narrative_pacing}",
            "",
            "### Sound Design Cues:",
            "\n".join([f"- 🎧 {cue}" for cue in treatment.soundscape_cues]),
            "",
            "## 🎞️ Act-by-Act Shot Sequence & Editing Blueprint",
        ]

        for s in treatment.acts_timeline:
            lines.extend([
                f"### Shot {s.shot_number}: {s.act} [{s.start_sec:.1f}s - {s.end_sec:.1f}s]",
                f"- **Visuals:** {s.visual_description}",
                f"- **Camera:** {s.camera_movement}",
                f"- **Transition:** `{s.transition_type}`",
                f"- **Audio:** {s.audio_soundscape}",
                f"- **Voiceover Monologue:** *\"{s.narrator_voiceover}\"*",
                ""
            ])

        if dubbing:
            lines.extend([
                "---",
                "",
                f"## 🎙️ LinguaCine Multilingual Voiceover Manifest ({dubbing.language_name})",
                f"- **Voice Persona:** {dubbing.voice.name} ({dubbing.voice.archetype})",
                f"- **Pacing / Pitch:** {dubbing.voice.speech_rate}x speed / {dubbing.voice.speech_pitch} pitch",
                f"- **Estimated Duration:** {dubbing.total_estimated_duration_sec:.1f} seconds",
                f"- **Audio Mixing:** {dubbing.acoustic_recommendation}",
                "",
                "### Full Voiceover Monologue:",
                f"> {dubbing.full_script}",
                ""
            ])

        lines.append("\n*Generated by MovieRec Neuro-Cinematic AI Studio (Phase 9)*\n")
        return "\n".join(lines)

neuro_studio = NeuroStudioService()
