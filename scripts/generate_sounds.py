#!/usr/bin/env python3
"""
Sound generation utility for Vocalinux.

This script generates the notification sounds used by Vocalinux for:
- Start recording (ascending pitch glide)
- Stop recording (descending pitch glide)
- Error notification (lower descending glide)

The sounds use smooth pitch glides with pure sine waves and soft envelopes
to create pleasant, headphone-friendly audio feedback.

Usage:
    python scripts/generate_sounds.py

The generated sounds will be placed in resources/sounds/

Design Philosophy:
- Pure sine waves (no harsh harmonics)
- Smoothstep interpolation for pitch transitions
- Soft attack/decay envelopes
- Lower frequencies (F4-A4 range) for warmth
- Consistent glide aesthetic across all sounds
"""

import math
import os
import struct
import wave


def generate_glide_tone(
    filename: str,
    freq_start: float,
    freq_end: float,
    duration: float = 0.6,
    amplitude: float = 0.16,
    sample_rate: int = 44100,
) -> None:
    """
    Generate a smooth pitch glide tone.

    Args:
        filename: Output WAV file path
        freq_start: Starting frequency in Hz
        freq_end: Ending frequency in Hz
        duration: Duration in seconds
        amplitude: Volume (0.0 to 1.0)
        sample_rate: Audio sample rate
    """
    num_samples = int(sample_rate * duration)
    samples = []

    for i in range(num_samples):
        t = i / sample_rate
        progress = i / num_samples

        # Ultra-soft envelope: sine-squared with exponential decay
        envelope = (math.sin(math.pi * progress) ** 2) * math.exp(-0.5 * progress)

        # Smooth pitch glide using smoothstep interpolation
        # This creates buttery smooth transitions with no abrupt changes
        glide = progress ** 2 * (3 - 2 * progress)
        freq_current = freq_start + (freq_end - freq_start) * glide

        # Generate pure sine wave
        phase = 2 * math.pi * freq_current * t
        sample = amplitude * envelope * math.sin(phase)
        samples.append(sample)

    # Convert to 16-bit PCM
    wav_samples = [int(sample * 32767) for sample in samples]

    # Write WAV file
    with wave.open(filename, "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(struct.pack("<" + "h" * len(wav_samples), *wav_samples))

    print(f"Generated: {filename}")


def main():
    """Generate all Vocalinux notification sounds."""
    # Determine output directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    sounds_dir = os.path.join(repo_root, "resources", "sounds")

    os.makedirs(sounds_dir, exist_ok=True)
    print(f"Generating sounds in: {sounds_dir}\n")

    # START: Ascending F4→A4 (positive, uplifting)
    print("Generating start_recording.wav (ascending F4→A4)...")
    generate_glide_tone(
        os.path.join(sounds_dir, "start_recording.wav"),
        freq_start=349.23,  # F4
        freq_end=440.00,    # A4
        duration=0.6,
        amplitude=0.16,
    )

    # STOP: Descending A4→F4 (resolution, completion)
    print("Generating stop_recording.wav (descending A4→F4)...")
    generate_glide_tone(
        os.path.join(sounds_dir, "stop_recording.wav"),
        freq_start=440.00,  # A4
        freq_end=349.23,    # F4
        duration=0.6,
        amplitude=0.16,
    )

    # ERROR: Lower descending E4→C4 (sad, concerning but gentle)
    print("Generating error.wav (descending E4→C4)...")
    generate_glide_tone(
        os.path.join(sounds_dir, "error.wav"),
        freq_start=329.63,  # E4
        freq_end=261.63,    # C4
        duration=0.7,
        amplitude=0.14,  # Slightly quieter
    )

    print("\n✓ All sounds generated successfully!")
    print("\nSound characteristics:")
    print("- Pure sine waves (headphone-friendly)")
    print("- Smoothstep pitch interpolation (no jumps)")
    print("- Soft envelopes (sine-squared with decay)")
    print("- Lower frequencies (F4-A4 range, warm and pleasant)")
    print("- Consistent glide aesthetic")


if __name__ == "__main__":
    main()
