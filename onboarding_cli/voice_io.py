from __future__ import annotations

import os
import subprocess
import tempfile
from typing import Tuple


class VoiceIO:
    def __init__(
        self,
        language: str = "en-US",
        tts_rate: int = 180,
        input_device: str = "default",
        use_pyaudio: bool = False,
    ) -> None:
        self._language = language
        self._tts_rate = tts_rate
        self._input_device = input_device
        self._use_pyaudio = use_pyaudio

    def listen_once(self) -> Tuple[str | None, str | None]:
        try:
            import speech_recognition as sr  # type: ignore[import-not-found]
        except Exception:
            return None, (
                "Voice input dependency missing: install `SpeechRecognition` and "
                "`PyAudio` (or system portaudio bindings)."
            )

        recognizer = sr.Recognizer()
        if not self._use_pyaudio:
            return self._listen_with_arecord(sr, recognizer)

        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.4)
                audio = recognizer.listen(source, timeout=8, phrase_time_limit=25)
        except Exception:
            # Fallback path without PyAudio: record via arecord and transcribe.
            return self._listen_with_arecord(sr, recognizer)

        try:
            text = recognizer.recognize_google(audio, language=self._language)
            return text.strip(), None
        except sr.UnknownValueError:
            return None, "Could not understand audio. Try again."
        except Exception as exc:
            return None, f"Speech recognition error: {exc}"

    def _listen_with_arecord(self, sr_module: object, recognizer: object) -> Tuple[str | None, str | None]:
        errors: list[str] = []
        for device in self._candidate_input_devices():
            wav_path = ""
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    wav_path = tmp.name
                cmd = [
                    "arecord",
                    "-q",
                    "-D",
                    device,
                    "-f",
                    "S16_LE",
                    "-r",
                    "16000",
                    "-c",
                    "1",
                    "-d",
                    "7",
                    wav_path,
                ]
                result = subprocess.run(
                    cmd,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=12,
                )
                if result.returncode != 0:
                    errors.append(
                        f"{device} (exit {result.returncode}): "
                        f"{self._compact_detail(result.stderr, result.stdout)}"
                    )
                    continue

                with sr_module.AudioFile(wav_path) as source:
                    audio = recognizer.record(source)
                text = recognizer.recognize_google(audio, language=self._language)
                return text.strip(), None
            except Exception as exc:
                errors.append(f"{device}: {exc}")
            finally:
                if wav_path:
                    try:
                        os.remove(wav_path)
                    except Exception:
                        pass

        joined = "; ".join(errors[:3]) if errors else "no compatible ALSA capture device found"
        return None, (
            "Microphone error: Could not use PyAudio or arecord fallback. "
            f"Tried devices: {', '.join(self._candidate_input_devices())}. "
            f"Details: {joined}. "
            "Tip: if device is busy, set VOICE_INPUT_DEVICE=pipewire (or a dsnoop/sysdefault alias) and close apps using mic."
        )

    def _candidate_input_devices(self) -> list[str]:
        candidates = [
            self._input_device,
            "pipewire",
            "pulse",
            "default",
            "sysdefault",
            "plughw:0,0",
            "hw:0,0",
            "plughw:1,0",
            "hw:1,0",
        ]
        candidates.extend(self._list_alsa_pcm_names())
        seen: set[str] = set()
        ordered: list[str] = []
        for item in candidates:
            normalized = item.strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                ordered.append(normalized)
        return ordered

    def _list_alsa_pcm_names(self) -> list[str]:
        try:
            result = subprocess.run(
                ["arecord", "-L"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except Exception:
            return []
        if result.returncode != 0:
            return []

        names: list[str] = []
        for raw in result.stdout.splitlines():
            if not raw.strip():
                continue
            if raw.startswith(" ") or raw.startswith("\t"):
                continue
            name = raw.strip()
            if name and name not in {"null"}:
                names.append(name)
        # keep list short to avoid very long retry loops
        return names[:12]

    @staticmethod
    def _compact_detail(stderr: str, stdout: str) -> str:
        text = " ".join((stderr or "").split())
        if text:
            return text[:180]
        text = " ".join((stdout or "").split())
        if text:
            return text[:180]
        return "record failed"

    def speak(self, text: str) -> None:
        content = text.strip()
        if not content:
            return
        if self._speak_pyttsx3(content):
            return
        self._speak_spd_say(content)

    def _speak_pyttsx3(self, text: str) -> bool:
        try:
            import pyttsx3  # type: ignore[import-not-found]
        except Exception:
            return False

        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", self._tts_rate)
            engine.say(text)
            engine.runAndWait()
            return True
        except Exception:
            return False

    def _speak_spd_say(self, text: str) -> None:
        try:
            subprocess.run(["spd-say", text], check=False, timeout=20)
        except Exception:
            return
