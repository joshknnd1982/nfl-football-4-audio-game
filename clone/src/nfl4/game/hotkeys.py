"""The seven global keys and their menus: F5, F6, F7, F8, F11, F12 and Ctrl. This is inspired by Jim Kitchen.

GAME_SPEC 4.1 to 4.8 and 8.1 (CODE (lifted) Form_KeyDown p_42e5e0, speckeys p_420860, readins p_420040, SayHints
p_420b50, ctog p_4216b0, adjvol p_421960, adjrate p_423530, ChangeVoice p_4239c0; read in full in S7.4a). The original
calls these menus from Form_KeyDown, which runs inside whatever DoEvents loop was waiting (B-P13), so each is a small modal
menu nested in the interrupted wait. Here `HotKeys.dispatch` is KeyInput's key_handler: it runs inside KeyInput.pump()
with the same tests in the same order (each reads g again after the menu before). Every menu ends as the original's do:
clk and g = "112" (F1), so the interrupted wait ends as if F1 had been pressed and repeats its prompt (D-018). A global
key pressed inside a menu nests a second menu, as in the original.

What the clone does differently, each decided before: F12 is the voice picker of playbook 7.4.2 per role instead of the
original's yes or no walk through every voice (G-S8), and with fewer than two voices it hands F1 back like every other
menu (Q59 not reproduced, D-034); F11 sets the crowd levels from their base values (D-023: no double counting of the
entry sound volume); F7 ends the blitz text with "play." (D-014); the rate stays in -10 to 10 (D-022 item 3); every menu
speaks with the speaker whose voice it sets, with that speaker's own volume (D-022 item 5); the files footbal0.dat and
football.vol are settings.txt (Options.save, G-F8). H12 (nfl4 only, NFL_EXTRAS_DESIGN 3): F5, F6 and F7 speak the
lines of `Rules.extra_help(key)` after the original text; ClassicRules gives none.
"""
from __future__ import annotations

import logging

from ..speech.roles import F11_NAMES, ROLES, VOLUME_ORDER
from . import extra_texts as words
from . import help_texts as H
from . import prompt_texts as T

log = logging.getLogger("nfl4.game")

KEY_F1 = "112"
KEY_F5, KEY_F6, KEY_F7, KEY_F8, KEY_F11, KEY_F12, KEY_CTRL = "116", "117", "118", "119", "122", "123", "17"
KEY_ENTER, KEY_ESCAPE, KEY_UP, KEY_DOWN = "13", "27", "38", "40"
VOLUME_STEP = 5                 # F11 part 1: a voice's volume in steps of 5 (0 to 100)
SOUND_STEP = 100                # F11 part 2: wavol in steps of 100 hundredths of a decibel (0 to -5000)
SOUND_FLOOR = -5000
READINS_PAUSE = 0.3             # readins' dy(0.3) between its two parts


class HotKeys:
    def __init__(self, game):
        self.g = game
        # the clone's added global keys, after the original's (S7.4b: F9, GAP_REGISTER G-K2); code text -> menu
        self.added: dict[str, object] = {}
        self.runs: list[str] = []      # every menu started, in order (the tests read it)

    def install(self) -> None:
        self.g.keys.key_handler = self.dispatch

    # ----- Form_KeyDown -----

    def dispatch(self, code: str) -> None:
        """0x42e6f0 to 0x42e811: F12, F11, F8, F7, F6, F5, Ctrl, each test reading g after the menu before (the calls at
        0x42e6f5 ChangeVoice, 0x42e730 adjvol, 0x42e75d ctog, 0x42e78a SayHints, 0x42e7b7 readins, 0x42e7e4 speckeys,
        0x42e811 adjrate)."""
        keys = self.g.keys
        for key, menu in ((KEY_F12, self.change_voice), (KEY_F11, self.adjvol), (KEY_F8, self.ctog),
                          (KEY_F7, self.say_hints), (KEY_F6, self.readins), (KEY_F5, self.speckeys),
                          (KEY_CTRL, self.adjrate)):
            if keys.code_text == key:
                self.runs.append(key)
                menu()
        menu = self.added.get(keys.code_text)
        if menu is not None:
            self.runs.append(keys.code_text)
            menu()

    # ----- the frame every menu shares -----

    @property
    def keys(self):
        return self.g.keys

    @property
    def options(self):
        return self.g.options

    def _hand_back(self) -> None:
        """clk, then g = "112": the interrupted wait repeats its prompt (D-018)."""
        self.keys.clk()
        self.keys.code_text = KEY_F1

    def _extra_help(self, key: str) -> None:
        """H12: the added help of the N. F. L. rules mode after the original text (Classic: none). During a game the rules
        that game was started with (a change of the Rules setting applies from the next game, SX.2), else the program's."""
        engine = self.g.play_engine
        rules = engine.rules if engine is not None else self.g.rules
        for line in rules.extra_help(key):
            self.g.say5(line)
        for line in self.g.franchise_help(key):               # nfl4 only (SX.8e): the Franchise's lines, while it is in use
            self.g.say5(line)

    def _wait_speech(self) -> None:
        self.keys.wait_speech(self.g.speech)

    # ----- F5, speckeys (4.2) -----

    def speckeys(self) -> None:
        g, keys = self.g, self.keys
        keys.clk()                                       # 0x4208a6
        g.stopspeech()                                   # 0x4208c5
        g.say5(H.SPECIAL_KEYS)                           # 0x4209da
        self._extra_help(KEY_F5)
        self._wait_speech()                              # 0x420a00 to 0x420aa4
        if keys.code_text != "":
            g.stopspeech()                               # 0x420ac3
        self._hand_back()                                # 0x420ade, 0x420afd

    # ----- F6, readins (4.3) -----

    def readins(self) -> None:
        g, keys = self.g, self.keys
        while True:                                      # L_42009b
            keys.clk()                                   # 0x4200a1
            g.stopspeech()                               # 0x4200c6
            g.say5(H.GAME_INSTRUCTIONS)                  # 0x42016f
            self._wait_speech()                          # L_42018e
            if keys.code_text == "":
                g.dy(READINS_PAUSE, 0x42028d)
            else:
                g.stopspeech()                           # 0x4202bd
                if keys.code_text == KEY_F1:
                    continue                             # 0x4202f0: part 1 again
                if keys.code_text == KEY_ESCAPE:
                    break                                # 0x42030a: the end
                keys.clk()                               # 0x420316
            g.say5(H.FOOTBALL_INSTRUCTIONS)              # L_420335, 0x420691
            self._extra_help(KEY_F6)
            self._wait_speech()                          # L_4206b0
            if keys.code_text == "":
                break
            g.stopspeech()                               # 0x420796
            if keys.code_text != KEY_F1:                 # 0x4207c9
                break
        self._hand_back()                                # L_4207cf: 0x4207d5, 0x4207f9

    # ----- F7, SayHints (4.4) -----

    def say_hints(self) -> None:
        g, keys = self.g, self.keys
        keys.clk()                                       # 0x420b99
        g.stopspeech()                                   # 0x420bb8
        g.say5(H.TERMINOLOGY + H.TERMINOLOGY_CLONE_END)  # 0x421532 (D-014: "play." at the end)
        self._extra_help(KEY_F7)
        self._wait_speech()                              # L_421558
        if keys.code_text != "":
            g.stopspeech()                               # 0x42161b
        self._hand_back()                                # 0x421636, 0x421655

    # ----- F8, ctog (4.5) -----

    def ctog(self) -> None:
        g, keys, options = self.g, self.keys, self.options
        keys.clk()                                       # 0x42170b
        g.stopspeech()                                   # 0x42172a
        if options.comtog == 0:                          # 0x421764: 0 or Empty
            options.set_comtog(1)
            g.say(T.COMMENTS_OFF)                        # 0x421795
        else:
            options.set_comtog(0)
            g.say(T.COMMENTS_ON)                         # 0x4217cc
        options.save()                                   # 0x421808 to 0x4218c2: football.vol
        self._hand_back()                                # 0x4218cb, 0x4218ef

    # ----- Ctrl, adjrate (4.8) -----

    def adjrate(self) -> None:
        g, keys, options = self.g, self.keys, self.options
        g.stopspeech()                                   # 0x42357c
        while True:                                      # L_4235a4
            keys.clk()                                   # 0x4235af
            g.speech.set_rate(options.vr)                # 0x4235f9: Voice.Rate = vr
            g.voice_speak(T.RATE_PROMPT, wait=False)     # 0x423658
            g.voice_speak(str(options.vr), wait=False)   # 0x4236b1: the number, CStr(vr)
            while True:                                  # L_4236c9
                keys.code_text = ""                      # 0x4236eb
                keys.wait_key()                          # L_4236f1
                if keys.code_text == KEY_UP:             # vr + 1 (0x423737) and Voice.Rate (0x4237bf)
                    options.set_vr(options.vr + 1)       # kept in -10 to 10 (D-022 item 3)
                elif keys.code_text == KEY_DOWN:         # vr - 1 (0x42377e) and Voice.Rate (0x4237bf)
                    options.set_vr(options.vr - 1)
                elif keys.code_text == KEY_ENTER:
                    keys.clk()                           # 0x4238ae
                    keys.code_text = KEY_F1              # 0x4238d1
                    options.save()                       # 0x4238ee to 0x423963: footbal0.dat
                    return
                else:
                    break                                # 0x4238a5: the instruction again
                g.stopspeech()                           # L_423784: Rate = vr (set_vr), 0x42381c: purge
                g.voice_speak(str(options.vr), wait=False)   # 0x42387b

    # ----- F11, adjvol (4.6) -----

    def adjvol(self) -> None:
        g, keys, options = self.g, self.keys, self.options
        g.stopspeech()                                   # 0x421a26
        for role in VOLUME_ORDER:                        # For L88 = 1 To 5 (0x421aef)
            # 0x421b00 clk; the voice load 0x421b7a, Rate 0x422298 and Volume 0x422330 are the speaker's own voice,
            # rate and volume, which the clone applies at every text of that speaker (D-022 item 5)
            keys.clk()
            prompt = T.VOLUME_PROMPT_START + F11_NAMES[role] + T.VOLUME_PROMPT_MIDDLE + T.VOLUME_PROMPT_END
            while True:                                  # L_4223c2
                g.say6(prompt, role=role)                # 0x4223c9
                while True:                              # L_4223e1
                    keys.clk()                           # 0x4223e4
                    keys.getkey(g.speech)                # 0x4223ff
                    if keys.code_text == KEY_UP:
                        volume = options.volume(role) + VOLUME_STEP
                        if volume < 100:                 # 0x42250b
                            options.set_volume(role, volume)         # Voice.Volume 0x42269c
                            g.say6(T.VOLUME_HIGHER, role=role)       # 0x4228b4
                        else:
                            options.set_volume(role, 100)            # Voice.Volume 0x4225d0
                            g.say6(T.VOLUME_MAXIMUM, role=role)      # 0x422611
                    elif keys.code_text == KEY_DOWN:
                        volume = options.volume(role) - VOLUME_STEP
                        if volume > 0:                   # 0x4227ae
                            options.set_volume(role, volume)         # Voice.Volume 0x42293f
                            g.say6(T.VOLUME_LOWER, role=role)        # 0x422980
                        else:
                            options.set_volume(role, 0)              # Voice.Volume 0x422873
                            g.say6(T.VOLUME_MINIMUM, role=role)      # 0x4228b4
                    else:
                        break
                if keys.code_text == KEY_ENTER:          # 0x4229b6: the next voice
                    break
                if keys.code_text != KEY_F1:             # 0x4229c5
                    g.saykey()                           # 0x4229ce
        self._sound_volume()

    def _sound_volume(self) -> None:
        """adjvol's part 2 (0x422a0f to 0x423443): the sound volume with the crowd beds and foot0 as the demo."""
        g, keys, options = self.g, self.keys, self.options
        sounds = g.sounds
        keys.clk()                                       # 0x422a0f; the announcer's voice 0x422a89, 0x422c31, 0x422ca7
        entry = options.wavol
        crowd2_base = None
        if sounds is not None:
            crowd2_base = sounds.crowd2_level() - entry  # L78 without the entry wavol it holds (D-023)
            sounds.set_crowd_levels(-100 + entry)        # 0x422d68: crowd 1 to -100 + wavol
            sounds.c2uf()                                # 0x422d85: crowd 2 up to full
        keys.clk()                                       # 0x422e3c
        prompt = T.SOUND_PROMPT_START + T.SOUND_PROMPT_MIDDLE + T.SOUND_PROMPT_END
        while True:                                      # L_422e94
            keys.clk()                                   # 0x422e97
            g.say2(prompt)                               # 0x422eb6
            while True:                                  # L_422ece
                keys.getkey(g.speech)                    # 0x422ed7
                if keys.code_text == KEY_UP:
                    level = options.wavol + SOUND_STEP
                    if level < 0:                        # 0x422f6c
                        options.set_wavol(level)
                        g.say2(T.VOLUME_HIGHER)          # 0x423070
                    else:
                        options.set_wavol(0)
                        g.say2(T.VOLUME_MAXIMUM)         # 0x422fab
                elif keys.code_text == KEY_DOWN:
                    level = options.wavol - SOUND_STEP
                    if level >= SOUND_FLOOR:             # 0x423031: exactly -5000 says " volume lower "
                        options.set_wavol(level)
                        g.say2(T.VOLUME_LOWER)           # 0x423097
                    else:
                        options.set_wavol(SOUND_FLOOR)
                        g.say2(T.VOLUME_MINIMUM)         # 0x423070
                else:
                    break
                if sounds is not None:                   # L_4230af: the beds at the new level (D-023), the demo
                    sounds.set_crowd_levels(-100 + options.wavol, 0 + options.wavol)   # 0x4230f2, 0x423151
                    sounds.play2(T.DEMO_SOUND)           # 0x423186: a key stops it and is lost
                keys.clk()                               # 0x4231ad
            if keys.code_text == KEY_ENTER:              # 0x4231d2
                break
            if keys.code_text != KEY_F1:                 # 0x4231e1
                g.saykey()                               # 0x4231ea
        if sounds is not None:                           # L_42320b
            sounds.set_crowd_levels(sounds.crwd1 + options.wavol, crowd2_base + options.wavol)   # 0x42324b, 0x4232a2
            sounds.make_hike()                           # 0x423310: the hike at -1600 + wavol
        options.save()                                   # 0x423341 to 0x42342a: football.vol
        keys.code_text = KEY_F1                          # 0x423438 (no clk here)

    # ----- F12, ChangeVoice (4.7; the clone's voice picker, G-S8) -----

    def change_voice(self) -> None:
        """F12: for each speaker in the original's order (announcer, own quarterback, opponent quarterback, own punter,
        opponent punter) the engine and voice picker of playbook 7.4.2; Escape keeps that speaker's voice. Then clk,
        g = "112", the settings saved (footbal0.dat) and GetSexOf (0x4287a9 to 0x428e38). With fewer than two voices
        there is nothing to choose: the original returned at once (0x423a30, Q59); the clone hands F1 back."""
        g, options = self.g, self.options
        from .voice_choice import choose_role_voice, voices_or_none
        voices = voices_or_none(options.voice_catalog)
        if voices is None or len(voices) < 2:
            log.info("F12: %s voices listed, nothing to choose", 0 if voices is None else len(voices))
            self._hand_back()
            return
        g.stopspeech()                                   # 0x423a56
        for role in ROLES:
            chosen = choose_role_voice(g.speech, self.keys, voices, role, options.voice(role),
                                       letter_mode=lambda: options.settings.speech.list_letters, clock=g.clock)
            if chosen is None:
                continue                                 # Escape: this speaker keeps its voice
            options.set_voice(role, None if chosen.index == 0 else chosen.voice_id)
            g.speech.stop()
            g.speech.say(words.voice_chosen(chosen.name) + " " + words.VOICE_SAMPLE, g.keys.quit, role=role)
        # the announcer again (0x428323, Rate 0x42860f, Volume 0x428709: every speaker's own at every text), clk
        # 0x42875c, g = "112" 0x4287a9
        self._hand_back()
        options.save()                                   # 0x4287c9 to 0x42892e: footbal0.dat
        g.get_sex_of()                                   # 0x428e38
