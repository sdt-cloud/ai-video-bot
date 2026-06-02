import os
import asyncio
import json
import re
import edge_tts
from subtitle_enhancer import subtitle_enhancer

# Edge-TTS ticks to seconds conversion factor (10 million ticks per second)
TICKS_TO_SECONDS = 1e-7

def clean_word(word: str) -> str:
    """Cleans punctuation and whitespace from a word for match comparison."""
    return re.sub(r'[^\w\s]', '', word).lower().strip()

async def generate_voice_and_timestamps_edge(text: str, voice: str, rate: str, audio_path: str) -> list[dict]:
    """
    Saves TTS audio and extracts millisecond-accurate word boundaries from Edge-TTS.
    Returns a list of dicts: [{'text': 'word', 'start': 0.12, 'end': 0.45, 'duration': 0.33}]
    """
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    word_boundaries = []
    
    # Open the file for writing binary chunks
    with open(audio_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                # offset and duration are in 100ns units (ticks)
                start_time = chunk["offset"] * TICKS_TO_SECONDS
                duration = chunk["duration"] * TICKS_TO_SECONDS
                word_boundaries.append({
                    "text": chunk["text"],
                    "start": round(start_time, 3),
                    "end": round(start_time + duration, 3),
                    "duration": round(duration, 3)
                })
                
    return word_boundaries

def generate_heuristic_timestamps(text: str, duration: float, start_offset: float = 0.0) -> list[dict]:
    """
    Fallback heuristic aligner (for ElevenLabs or API failures).
    Distributes the duration among words using character length weighting.
    """
    words = text.split()
    total_words = len(words)
    if total_words == 0:
        return []
        
    total_chars = sum(len(w) for w in words)
    if total_chars == 0:
        return []
        
    # Adjust for natural pauses on punctuation
    PAUSE_PUNCTUATION = {
        ",": 0.15,
        ".": 0.35,
        "!": 0.40,
        "?": 0.35,
        "...": 0.50,
        "…": 0.50
    }
    
    pauses = []
    for w in words:
        pause_val = 0.0
        for p, p_dur in PAUSE_PUNCTUATION.items():
            if w.endswith(p):
                pause_val = p_dur
                break
        pauses.append(pause_val)
        
    total_pause = sum(pauses)
    active_duration = max(0.1, duration - total_pause)
    time_per_char = active_duration / total_chars
    
    boundaries = []
    current_time = start_offset
    
    for i, w in enumerate(words):
        char_dur = len(w) * time_per_char
        pause_dur = pauses[i]
        
        boundaries.append({
            "index": i,
            "text": w,
            "start": round(current_time, 3),
            "end": round(current_time + char_dur, 3),
            "duration": round(char_dur, 3)
        })
        
        current_time += char_dur + pause_dur
        
    return boundaries

def slice_global_timestamps(all_boundaries: list[dict], narrations: list[str], slide_durations: list[float]) -> list[list[dict]]:
    """
    Slices global word boundaries into scene-specific relative timings.
    Matches words by sequential count to guarantee alignment.
    """
    sliced_timings = []
    boundary_idx = 0
    total_boundaries = len(all_boundaries)
    
    for i, narration in enumerate(narrations):
        slide_dur = slide_durations[i]
        scene_words = narration.split()
        scene_word_count = len(scene_words)
        
        scene_boundaries = []
        
        # Take matching sequential boundaries
        for _ in range(scene_word_count):
            if boundary_idx < total_boundaries:
                scene_boundaries.append(all_boundaries[boundary_idx])
                boundary_idx += 1
            else:
                break
                
        # Make timestamps relative to the start of the scene narration
        if scene_boundaries:
            start_offset = scene_boundaries[0]["start"]
            relative_boundaries = []
            
            for word_idx, b in enumerate(scene_boundaries):
                rel_start = max(0.0, b["start"] - start_offset)
                rel_end = max(rel_start + 0.05, b["end"] - start_offset)
                relative_boundaries.append({
                    "index": word_idx,
                    "text": b["text"],
                    "start": round(rel_start, 3),
                    "end": round(rel_end, 3),
                    "duration": round(rel_end - rel_start, 3)
                })
                
            # Cap final boundary at slide duration
            for rb in relative_boundaries:
                if rb["end"] > slide_dur:
                    rb["end"] = slide_dur
                    rb["duration"] = max(0.05, rb["end"] - rb["start"])
                    
            sliced_timings.append(relative_boundaries)
        else:
            # Fallback to heuristic if no boundaries matched
            sliced_timings.append(generate_heuristic_timestamps(narration, slide_dur))
            
    return sliced_timings
