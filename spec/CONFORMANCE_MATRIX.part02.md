### Q55

Requirement: The exit with gtp = 0 deletes footplay.txt with the season files, so the player's edited names are gone and a new season draws new random names (kept: new random names...

Tests:
- test_files_program.py: test_a_season_that_ends_keeps_the_names_as_previous_and_starts_the_next_season
- test_files_store.py: test_the_season_end_keeps_the_names_as_previous_replaces_it_next_time_and_is_safe_to_repeat

### Q56

Requirement: The incompletion " bats it right back at <quarterback> " names defensive player L578 of the side ON OFFENSE (`Me.m370(wisoff, L578)`, pag 0x44cc09, read in the asm at...

Tests:
- test_pag_scrimmage.py: test_an_incompletion_bats_the_ball_back_with_the_offenses_own_defender_q56

### Q57

Requirement: After " is way to short" (the player's field goal from his own half) the play noise foot14 is not stopped: no PlayTackle comes before the possession change, so it loop...

Tests:
- test_pag_kicks.py: test_a_field_goal_from_the_own_half_is_way_too_short_and_the_clone_stops_the_play_noise_q57

### Q58

Requirement: The key echo sets the rate to vr + 5 but queues the character asynchronously and sets vr back at once, and SAPI renders it at the restored rate (TESTED, 8.1), so the e...

Tests:
- test_conformance_gaps.py: test_the_key_echo_purges_then_queues_the_character_in_the_last_voice_at_the_normal_rate_q58

### Q59

Requirement: F12 with only one SAPI voice: ChangeVoice returns at once without clk and without the F1 hand-back, so the interrupted wait receives F12 as an ordinary key (echoed as...

Tests:
- test_hotkeys.py: test_f12_with_one_voice_hands_f1_back_at_once_q59_not_reproduced

### Q60

Requirement: A fumbled run is not counted as a running play (the count is in the branch without a fumble, pag 0x44db46), while a fumbled pass keeps its attempt and its completion o...

Tests:
- test_pag_scrimmage.py: test_a_fumbled_run_is_not_a_running_play_and_its_tackle_sentence_is_never_spoken_q60
- test_conformance_review.py: test_a_fumbled_pass_keeps_its_attempt_and_its_completion_or_sack_q60

### Q61

Requirement: The kick-off starts the play noise foot14 (PlayNoise at 0x444c7d, after foot7) and nothing stops it before the player's run-out question (4.16: say5 and getkey2 at 0x4...

Tests:
- test_pag_kicks.py: test_the_run_out_question_keys_q17_and_the_touch_back
- test_conformance_review.py: test_the_play_noise_of_the_kick_off_still_loops_when_the_run_out_question_is_asked_and_the_touch_back_stops_it_q61

### Q62

Requirement: The return flag L30c (no pause before the tackle of a kick-off return) is set at every return (0x446bb6) and reset only where a play ends in the field of play (0x45073...

Tests:
- test_pag_kicks.py: test_a_return_flag_left_by_a_touchdown_return_skips_the_pause_of_the_next_play_in_the_field
- test_pag_kicks.py: test_a_long_return_for_a_touchdown_counts_down_from_100_and_leaves_the_return_flag_set


## GAME_SPEC 17.2, what must stay exact

### X1

Requirement: Every spoken text with its spelling, its spaces (Str$ leading and doubled spaces included, G-S3), its punctuation and its pieces as sections 3 to 5 build it; which spe...

Tests:
- test_program_texts.py: test_every_text_of_form_load_is_a_string_of_the_original_except_the_clones_own
- test_prompt_texts.py: test_every_short_text_is_a_string_of_the_original
- test_season_texts.py: test_every_text_of_the_season_engine_is_a_string_of_the_original
- test_phrases.py: test_every_text_of_the_play_engine_is_a_string_of_the_original
- test_standings.py: test_the_texts_are_strings_of_the_original
- test_speakers.py: test_the_replay_texts_are_strings_of_the_original
- test_pag_golden.py: test_the_classic_game_gives_the_golden_transcript

### X2

Requirement: Every key in every state, including "any other key", F1 to F4 and the F1 hand-back after a global key menu (4, 8.1, 8.2; D-018), except the keypad digits and the typed...

Tests:
- test_keys.py: test_a_key_and_the_character_it_typed_are_pumped_together_and_g2_stays_the_originals, test_key_char_is_the_originals_lcase_chr_of_the_code, test_take_typed_waits_for_the_character_that_follows_its_key, test_take_typed_never_eats_the_next_key, test_read_key_skips_modifiers_and_keeps_every_key_typed_ahead, test_keys_typed_during_a_synchronous_line_only_the_last_survives_with_its_code, test_dy_waits_its_seconds_pumps_keys_and_is_not_ended_by_one, test_getkey_waits_for_a_key_and_stops_speech and 3 more
- test_hotkeys.py: test_alt_and_f10_are_the_escape_code_with_no_character_and_run_no_menu, test_a_key_that_is_not_global_runs_no_menu, test_a_global_key_during_a_pause_runs_its_menu_and_the_next_wait_clears_the_f1, test_a_global_key_at_the_games_wait_with_ambient_sounds_ends_it_as_f1, test_a_global_key_typed_during_a_waited_line_runs_at_the_next_pump_and_that_wait_ends_as_f1, test_f5_speaks_the_key_list_waits_for_its_end_and_hands_f1_back, test_the_key_list_is_the_original_text, test_a_key_during_the_key_list_stops_it_and_still_hands_f1_back and 20 more
- test_pag_flow.py: test_any_other_key_is_echoed_and_the_menu_starts_again_at_item_1
- test_program_menu.py: test_any_other_key_is_echoed_and_the_choice_starts_at_one_again
- test_window.py: test_the_title_is_the_owners_title_format, test_posted_key_messages_arrive_as_virtual_key_codes, test_keys_that_type_are_followed_by_their_character_and_others_by_none, test_shift_down_in_the_keyboard_state_makes_the_posted_keys_type_their_shifted_characters, test_a_window_without_a_character_handler_still_gets_every_key, test_typed_characters_reach_the_key_input_in_order_with_their_keys, test_alt_f4_closes_the_window_and_never_reaches_the_game, test_alt_and_f10_release_are_swallowed_and_other_releases_are_harmless and 2 more

### X3

Requirement: Every random draw with its range, its redraw rule and its history length, in the order of the code (5, 6; D-013); the outcome table, the field goal draws, punts, kick-...

Tests:
- test_rnd.py: test_rnd_is_int_of_rnd_times_n_plus_one_and_below_is_without_the_plus_one, test_the_edges_of_the_range_never_leave_it, test_random_is_the_rnd_the_sound_procedures_call_and_it_checks_its_source, test_the_default_source_is_a_real_generator, test_a_seeded_source_repeats_the_same_numbers, test_every_bucket_of_the_main_draws_is_hit_about_equally_often, test_redraw_takes_the_first_acceptable_value_in_the_order_drawn, test_redraw_is_bounded_then_takes_the_scanned_candidate_and_logs_once and 1 more
- test_pag_numbers.py: test_below_single_is_varint_of_varmul_of_a_single_by_an_integer, test_a_single_rounding_does_change_some_draws_so_the_type_matters, test_the_fpu_draws_are_int_of_the_exact_product_for_every_24_bit_rnd, test_the_percent_tests_compare_a_single_as_fstp_dword_stores_it, test_int_of_l64_over_2_is_exact_in_the_library
- test_setup.py: test_the_draws_go_in_the_originals_order_own_team_then_the_opponent_then_periods_then_warnings
- test_playtables.py: test_the_twelve_runs_have_the_yards_and_sounds_of_the_spec_table, test_the_eighteen_passes_have_the_yards_sack_and_completion_of_the_spec_table, test_every_pair_has_one_entry_and_the_run_directions_are_the_original_draws, test_the_kick_numbers_are_the_original_ones, test_the_field_goal_chances_of_the_spec_follow_from_five_draws_of_70, test_neutral_modifiers_change_nothing
- test_schedule.py: test_a_scripted_schedule_follows_the_lifted_procedure_draw_by_draw
- test_pag_golden.py: test_the_classic_game_gives_the_golden_transcript
- test_conformance_review.py: test_each_phrase_history_has_the_length_of_the_spec_and_no_phrase_comes_back_inside_it
- test_conformance_review.py: test_the_hand_off_and_drop_back_histories_keep_the_last_16_values

### X4

Requirement: Every sound: file, volume, pan, frequency, loop, slot, wait and key behavior and its place among the spoken lines (10, WAV_EVENT_MAP; D-023 except its two slips).

Tests:
- test_game_sounds.py: test_start_crowds_loops_both_beds_at_minus_1200_at_their_own_rate, test_wavol_is_added_to_every_level, test_set_crwd1_raises_crowd_1_for_a_game_without_restarting_it, test_stop_crowds_stops_both_beds, test_c2uf_from_the_base_is_13_steps_in_1_3_seconds, test_c2dh_from_full_is_7_steps_to_minus_600_in_0_7_seconds, test_c2df_goes_down_to_the_base, test_c2uh_never_ramps_and_takes_no_time and 32 more
- test_audio_render.py: test_pan_gains_attenuate_only_the_far_channel_by_pan_over_100_db, test_pan_table_gains_are_the_documented_decibel_steps, test_usable_frequency_range_is_directsounds, test_real_lengths_at_the_pitch_extremes_match_the_spec, test_level_gain_is_hundredths_of_a_decibel, test_pitch_changes_by_the_frequency_ratio, test_length_scales_inversely_with_frequency, test_the_rendered_length_is_exactly_the_computed_length_at_any_pitch and 8 more
- test_audio_library.py: test_the_shipped_files_are_the_originals_byte_for_byte
- test_pag_golden.py: test_the_classic_game_gives_the_golden_transcript
- test_conformance_gaps.py: test_the_confirmed_roles_play_the_confirmed_files_through_the_games_sound_procedures

### X5

Requirement: The pauses dy and rady with their formulas and places (7; G-S2; S5.2: every site is in `work/pause_table_s43.txt`, and the sequences of 3 to 5 give their order on each...

Tests:
- test_pause_lengths.py: test_the_pauses_of_a_snap_count_follow_the_speech_rate, test_the_shortest_snap_count_is_only_the_crowd_pause, test_the_longest_snap_count_is_6_seconds_at_rate_one_and_1_36_at_rate_five
- test_pag_games.py: test_every_pause_of_a_game_is_a_site_of_the_pause_table_and_every_site_is_reached
- test_speakers.py: test_rady_waits_the_drawn_thirtieth_over_vr_times_25_with_vr_at_least_1
- test_speakers.py: test_dy_waits_the_seconds_and_pumps_keys_without_ending_early, test_rady_waits_the_drawn_thirtieth_over_vr_times_25_with_vr_at_least_1

### X6

Requirement: The value order of the original's files as far as the game keeps them (12; D-024 item 4).

Tests:
- test_files_savedgame.py: test_the_values_are_in_the_originals_order_and_the_name_is_a_long_then_codes
- test_files_season_files.py: test_footbal2_is_16_records_integers_for_the_division_games_and_singles_for_the_rest
- test_files_season_files.py: test_footbal3_is_64_integers_wins_then_losses_division_by_division

### X7

Requirement: The quirks kept in 17.5.

Tests:
- test_conformance.py: test_the_quirk_classes_of_17_5_and_the_quirk_rows_are_the_same_set
- test_conformance.py: test_the_map_covers_every_requirement_and_names_nothing_else


## GAP_REGISTER, the entries that close in S8.1

### G-S1

Requirement: Asynchronous, synchronous and purged speech.

Tests:
- test_sapi_roles.py: test_a_synchronous_line_waits_for_everything_queued_before_it
- test_sapi_roles.py: test_a_voice_change_never_cuts_the_text_before_it
- test_speakers.py: test_stopspeech_purges_the_queue

### G-S3

Requirement: Str$ and doubled spaces.

Tests:
- test_vbnum.py: test_str_puts_a_space_before_a_number_that_is_not_negative_and_a_minus_before_a_negative_one
- test_vbnum.py: test_the_doubled_space_of_the_originals_sentences_comes_from_str
- test_season_texts.py: test_the_joining_texts_keep_their_spaces
- test_season_frame.py: test_the_score_sentence_for_each_case_with_the_doubled_spaces_str_makes
- test_program_menu.py: test_the_numbers_of_todays_game_are_str_numbers_with_a_space_in_front

### G-S5

Requirement: The key echo rate.

Tests:
- test_conformance_gaps.py: test_the_key_echo_purges_then_queues_the_character_in_the_last_voice_at_the_normal_rate_q58

### G-K1

Requirement: Keys typed while the program is busy.

Tests:
- test_keys.py: test_keys_typed_during_a_synchronous_line_only_the_last_survives_with_its_code
- test_keys.py: test_take_typed_never_eats_the_next_key
- test_game_sounds.py: test_keys_during_a_ramp_are_kept_and_do_not_shorten_it

### G-K4

Requirement: Closing the window.

Tests:
- test_window.py: test_alt_f4_closes_the_window_and_never_reaches_the_game
- test_app_startup.py: test_closing_the_window_while_the_game_talks_ends_the_program_within_two_seconds
- test_program_exit.py: test_closing_the_window_in_the_menu_ends_the_game_with_no_exit_sequence

### G-A1

Requirement: Sound slots.

Tests:
- test_audio_engine.py: test_the_seven_original_slots_and_the_extra_channel
- test_audio_engine.py: test_a_new_sound_in_a_slot_stops_that_slots_sound
- test_game_sounds.py: test_play_of_foot2_uses_the_one_shot_slot_beside_the_crowd_bed

### G-A2

Requirement: The play noise loop.

Tests:
- test_conformance_gaps.py: test_the_safety_net_stops_the_play_noise_at_a_key_wait_and_counts_it_and_otherwise_does_nothing
- test_game_sounds.py: test_stop_play_noise_stops_only_the_noise
- test_pag_kicks.py: test_a_field_goal_from_the_own_half_is_way_too_short_and_the_clone_stops_the_play_noise_q57
- test_pag_games.py: test_every_game_ends_with_a_winner_and_the_engine_never_needed_a_safety_net

### G-A5

Requirement: Crowd beds after a game (new in S4.4).

Tests:
- test_program_game.py: test_the_crowd_beds_restart_when_the_week_loop_begins_again_g_a5
- test_program_game.py: test_the_beds_are_not_started_again_when_no_game_stopped_them

### G-F2

Requirement: After a game.

Tests:
- test_program_game.py: test_after_the_game_the_season_engine_gets_its_score_then_the_standings_follow
- test_program_game.py: test_silent_standings_after_week_16_wait_for_no_key_q53_not_reproduced

### G-F3

Requirement: End of a season.

Tests:
- test_program_game.py: test_a_season_that_ends_in_pog_deletes_its_files_says_so_and_starts_a_new_one
- test_files_program.py: test_a_season_that_ends_keeps_the_names_as_previous_and_starts_the_next_season

### G-F4

Requirement: footplay.txt at the end of a season.

Tests:
- test_files_program.py: test_a_season_that_ends_keeps_the_names_as_previous_and_starts_the_next_season
- test_files_store.py: test_the_season_end_keeps_the_names_as_previous_replaces_it_next_time_and_is_safe_to_repeat

### G-F6

Requirement: Exit paths.

Tests:
- test_program_exit.py: test_the_exit_plays_foot0_says_the_thank_you_then_beeps_twice_and_says_the_closing_sentence
- test_program_exit.py: test_exit_beeps_use_the_sound_chain_and_say_nothing_when_there_is_no_sound_layer

### G-D1

Requirement: Redraw loops.

Tests:
- test_rnd.py: test_redraw_is_bounded_then_takes_the_scanned_candidate_and_logs_once
- test_schedule.py: test_a_source_stuck_on_one_number_still_gives_a_valid_schedule_through_the_bounds
- test_names.py: test_the_redraw_is_bounded_when_the_source_is_stuck_on_a_blank_slot
- test_season_week.py: test_a_source_that_never_gives_a_free_team_still_ends_through_the_bounded_redraws
- test_playoffs.py: test_a_computer_game_ends_on_a_stuck_source_through_the_bounded_redraws

### G-D2

Requirement: Random numbers.

Tests:
- test_rnd.py: test_rnd_is_int_of_rnd_times_n_plus_one_and_below_is_without_the_plus_one, test_the_edges_of_the_range_never_leave_it, test_random_is_the_rnd_the_sound_procedures_call_and_it_checks_its_source, test_the_default_source_is_a_real_generator, test_a_seeded_source_repeats_the_same_numbers, test_every_bucket_of_the_main_draws_is_hit_about_equally_often, test_redraw_takes_the_first_acceptable_value_in_the_order_drawn, test_redraw_is_bounded_then_takes_the_scanned_candidate_and_logs_once and 1 more
- test_season_frame.py: test_the_game_and_the_sounds_draw_from_the_same_generator

### G-C1

Requirement: Invariants.

Tests:
- test_pag_games.py: test_every_game_ends_with_a_winner_and_the_engine_never_needed_a_safety_net
- test_pag_games.py: test_the_ball_down_and_distance_are_valid_at_every_next_play
- test_season_games.py: test_a_season_of_a_random_team_ends_in_the_season_over_state_with_a_consistent_bracket
- test_season_games.py: test_every_team_can_be_the_player_and_the_engine_never_raises_a_state_error
- test_conformance_gaps.py: test_the_10000_game_and_season_property_runs_of_s81_found_no_failure


## The 26 sounds the owner confirmed by ear

### OBS-foot8

Requirement: foot8.wav, confirmed by the owner by ear as: ambient sound one

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_game_sounds.py: test_ambient_sound_choice_draws

### OBS-foot9

Requirement: foot9.wav, confirmed by the owner by ear as: ambient sound two

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_game_sounds.py: test_ambient_sound_choice_draws

### OBS-foot10

Requirement: foot10.wav, confirmed by the owner by ear as: ambient sound three

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_game_sounds.py: test_ambient_sound_choice_draws

### OBS-foot0

Requirement: foot0.wav, confirmed by the owner by ear as: intro music

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_game_sounds.py: test_intro_plays_foot0_once_waited_then_loops_it_at_the_same_level

### OBS-foot14

Requirement: foot14.wav, confirmed by the owner by ear as: play noise

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_conformance_gaps.py: test_the_confirmed_roles_play_the_confirmed_files_through_the_games_sound_procedures

### OBS-foot12

Requirement: foot12.wav, confirmed by the owner by ear as: ball contact

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_conformance_gaps.py: test_whole_games_play_the_kick_the_ball_contact_the_bleep_and_the_celebrations_the_owner_named

### OBS-foot4

Requirement: foot4.wav, confirmed by the owner by ear as: pile up hit

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_conformance_gaps.py: test_the_confirmed_roles_play_the_confirmed_files_through_the_games_sound_procedures

### OBS-foot5

Requirement: foot5.wav, confirmed by the owner by ear as: two tackler hit

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_conformance_gaps.py: test_the_confirmed_roles_play_the_confirmed_files_through_the_games_sound_procedures

### OBS-foot6

Requirement: foot6.wav, confirmed by the owner by ear as: single tackle hit

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_conformance_gaps.py: test_the_confirmed_roles_play_the_confirmed_files_through_the_games_sound_procedures

### OBS-foot11

Requirement: foot11.wav, confirmed by the owner by ear as: referee whistle

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_conformance_gaps.py: test_the_confirmed_roles_play_the_confirmed_files_through_the_games_sound_procedures

### OBS-foot25

Requirement: foot25.wav, confirmed by the owner by ear as: Super Bowl win music

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_superbowl.py: test_the_player_wins_the_sentence_a_run_foot25_and_a_second_run

### OBS-foot3

Requirement: foot3.wav, confirmed by the owner by ear as: the snap

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_conformance_gaps.py: test_the_confirmed_roles_play_the_confirmed_files_through_the_games_sound_procedures

### OBS-foot7

Requirement: foot7.wav, confirmed by the owner by ear as: kick

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_conformance_gaps.py: test_whole_games_play_the_kick_the_ball_contact_the_bleep_and_the_celebrations_the_owner_named

### OBS-foot13

Requirement: foot13.wav, confirmed by the owner by ear as: censor bleep

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_conformance_gaps.py: test_whole_games_play_the_kick_the_ball_contact_the_bleep_and_the_celebrations_the_owner_named

### OBS-foot1

Requirement: foot1.wav, confirmed by the owner by ear as: crowd, first layer

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_game_sounds.py: test_start_crowds_loops_both_beds_at_minus_1200_at_their_own_rate

### OBS-foot2

Requirement: foot2.wav, confirmed by the owner by ear as: crowd, second layer

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_game_sounds.py: test_start_crowds_loops_both_beds_at_minus_1200_at_their_own_rate

### OBS-foot15

Requirement: foot15.wav, confirmed by the owner by ear as: celebration sound one

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_game_sounds.py: test_celebration_sound_draws_the_file_and_a_nonzero_pitch_step

### OBS-foot16

Requirement: foot16.wav, confirmed by the owner by ear as: celebration sound two

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_game_sounds.py: test_celebration_sound_draws_the_file_and_a_nonzero_pitch_step

### OBS-foot17

Requirement: foot17.wav, confirmed by the owner by ear as: celebration sound three

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_game_sounds.py: test_celebration_sound_draws_the_file_and_a_nonzero_pitch_step

### OBS-foot18

Requirement: foot18.wav, confirmed by the owner by ear as: celebration sound four

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_game_sounds.py: test_celebration_sound_draws_the_file_and_a_nonzero_pitch_step

### OBS-foot19

Requirement: foot19.wav, confirmed by the owner by ear as: celebration sound five

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_game_sounds.py: test_celebration_sound_draws_the_file_and_a_nonzero_pitch_step

### OBS-foot20

Requirement: foot20.wav, confirmed by the owner by ear as: celebration sound six

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_game_sounds.py: test_celebration_sound_draws_the_file_and_a_nonzero_pitch_step

### OBS-foot21

Requirement: foot21.wav, confirmed by the owner by ear as: celebration sound seven

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_game_sounds.py: test_celebration_sound_draws_the_file_and_a_nonzero_pitch_step

### OBS-foot22

Requirement: foot22.wav, confirmed by the owner by ear as: celebration sound eight

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_game_sounds.py: test_celebration_sound_draws_the_file_and_a_nonzero_pitch_step

### OBS-foot23

Requirement: foot23.wav, confirmed by the owner by ear as: celebration sound nine

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_game_sounds.py: test_celebration_sound_draws_the_file_and_a_nonzero_pitch_step

### OBS-foot24

Requirement: foot24.wav, confirmed by the owner by ear as: celebration sound ten

Tests:
- test_conformance_gaps.py: test_every_sound_the_owner_confirmed_has_the_clones_event_name_for_its_file
- test_game_sounds.py: test_celebration_sound_draws_the_file_and_a_nonzero_pitch_step


## NFL_EXTRA_FEATURES 3, the cross-cutting requirements C1 to C10 (nfl4 only, rule 0.13)

### C1

Requirement: Switches. Under "Rules" in the F9 menu: one on/off per feature NX1 to NX4 and NX7, the playbook choice (NX5), and "Franchise" as a game mode chosen when a new season s...

Tests:
- test_nx_settings.py: test_the_defaults_are_the_nfl_rules_with_timeouts_on, test_the_rules_line_is_read, test_a_bad_rules_or_switch_line_is_a_problem_and_keeps_the_default, test_the_file_is_written_with_both_lines_and_reads_back_the_same, test_the_program_rules_follow_the_setting, test_the_menu_opens_on_rules_classic_and_escape_leaves, test_enter_switches_to_the_nfl_rules_saves_and_says_it_applies_from_the_next_game, test_a_switch_says_used_with_the_nfl_rules_while_rules_is_classic and 7 more
- test_sx9_switches.py: test_every_combination_of_the_switches_in_a_quick_game
- test_nx_save.py: test_save_game_in_nfl_mode_writes_the_record_and_loading_it_restores_the_whole_record

### C2

Requirement: The clock. The original has no clock: a quarter is a number of counted plays and F4 invents a time (GAME_SPEC 5.3, 5.6). Timeouts, the two-minute warning, challenge li...

Tests:
- test_nx_clock.py: test_the_rules_table_holds_the_2026_rulebook_numbers, test_every_runoff_range_fits_the_play_clock_and_every_range_is_ordered, test_period_lengths, test_warning_periods, test_the_late_windows_where_out_of_bounds_stops_the_clock_until_the_snap, test_the_tempo_of_the_offense, test_each_kind_of_play_draws_its_live_time_once_from_its_range, test_a_try_and_a_touch_back_take_no_time_and_draw_nothing and 20 more
- test_nx_engine.py: test_f4_in_a_play_menu_speaks_the_real_time_and_draws_nothing
- test_nx_games.py: test_every_period_ends_when_the_clock_reaches_zero_and_the_clock_is_never_negative

### C3

Requirement: Neutral equals classic. Where a feature changes probabilities (ratings, playbooks, penalties' frequency), the neutral setting (all ratings average, playbook Classic, p...

Tests:
- test_fr_neutral.py: test_n1_every_row_is_the_originals_with_every_rating_70_for_every_pair_of_slots, test_n1_a_roster_with_no_ratings_is_read_as_the_playbooks_object_reads_it, test_n2_a_game_of_70s_through_the_franchise_seams_equals_the_same_game_without_ratings, test_n2_the_franchise_game_has_the_leagues_players_and_no_drawn_name, test_n3_a_season_with_every_strength_equal_is_the_classic_season, test_n3_a_season_in_a_league_with_a_spread_differs_from_the_classic_one_and_stays_a_season
- test_nx_playbook_mods.py: test_unarmed_modifiers_and_a_zero_mod_return_every_row_unchanged_like_neutral
- test_nx_playbook_games.py: test_a_classic_side_calls_nothing_and_a_game_of_classic_books_draws_nothing_extra
- test_pag_golden.py: test_the_classic_game_gives_the_golden_transcript
- test_sx9_switches.py: test_with_rules_classic_a_season_says_nothing_of_the_extras_or_the_franchise

### C4

Requirement: Random draws. All new draws use the one `GameRandom` with its bounded redraws (G-D1); each new draw is documented like the original's (range, order, redraw rule) in th...

Tests:
- test_nx_clock.py: test_a_stopped_clock_has_no_runoff_and_draws_nothing
- test_nx_qb.py: test_classic_has_no_quarterback_runs_and_its_hooks_draw_nothing
- test_nx_penalties.py: test_no_draw_at_all_with_penalties_off
- test_nx_onside.py: test_the_computer_never_declares_and_draws_nothing_otherwise
- test_nx_playbook_games.py: test_a_classic_side_calls_nothing_and_a_game_of_classic_books_draws_nothing_extra
- test_pag_games.py: test_the_hooks_are_called_in_classic_and_change_nothing

### C5

Requirement: Speech texts. New spoken sentences are listed with an ID and exact spelling in `spec\STRINGS_NX.md` (written by SX.1; a generator, never typed by hand, D-017). Pools o...

Tests:
- test_nx_remarks.py: test_the_timeout_pool_is_the_five_lines_of_strings_nx_with_their_exact_spaces, test_the_file_of_the_defaults_lists_every_default_line, test_remark_ids, test_a_line_is_changed_switched_off_added_or_kept_when_it_is_bad, test_an_unknown_placeholder_is_counted_and_spoken_as_written, test_ids_that_are_not_remarks_twice_or_empty_are_problems, test_the_example_of_the_players_guide_works_as_written, test_every_line_off_means_silence and 9 more
- test_nx_fouls.py: test_every_foul_has_its_spoken_name_in_strings_nx_and_p25_shares_holding
- test_fr_news_list.py: test_the_fifteen_pools_are_the_lines_of_strings_nx_with_their_exact_spaces, test_every_default_line_uses_only_the_placeholders_of_its_pool, test_the_file_of_the_defaults_lists_every_default_line, test_news_ids, test_a_line_is_changed_switched_off_added_or_kept_when_it_is_bad, test_the_banter_names_are_not_allowed_in_the_news_and_the_default_or_nothing_is_used, test_an_unknown_placeholder_of_the_pool_is_counted_and_spoken_as_written, test_ids_that_are_not_news_twice_or_empty_are_problems and 15 more

### C6

Requirement: Help. F5, F6 and F7 (special keys, game instructions, football terminology and hints) are the original's strings. In N. F. L. rules mode each gets one added, separate...

Tests:
- test_nx_engine.py: test_f5_f6_f7_add_their_lines_after_the_original_text_during_an_nfl_game
- test_nx_engine.py: test_the_help_of_a_classic_program_has_no_feature_lines_only_the_keys
- test_nx_penalties.py: test_the_help_of_f5_f6_and_f7_names_the_penalties_when_they_are_on
- test_nx_qb.py: test_the_help_of_f5_f6_and_f7_names_the_quarterback_runs_when_they_are_on

### C7

Requirement: Statistics. The quarter statistics (4.19) keep their sentences. In N. F. L. rules mode, added lines (spoken after the original ones): penalties and penalty yards of ea...

Tests:
- test_nx_engine.py: test_the_statistics_add_the_timeouts_used
- test_nx_penalties.py: test_the_statistics_add_the_penalties_and_their_yards
- test_nx_onside_fouls.py: test_the_statistics_add_the_onside_kicks_tried_and_recovered
- test_nx_qb.py: test_the_statistics_add_the_quarterback_runs_and_their_yards
- test_nx_review_computer.py: test_the_quarter_statistics_say_the_challenges_won_and_lost_of_each_side

### C8

Requirement: Tests (CLAUDE.md 1: run before saying it works). Each feature has: rule tests against `nfl_rules_<year>` (the numbers), scripted-random flow tests with the exact spoke...

Tests:
- test_nx_games.py: test_the_sample_falls_in_the_calibration_bands
- test_nx_penalty_games.py: test_the_sample_falls_near_the_nfl_rates
- test_nx_onside_fouls.py: test_whole_simulated_games_keep_every_onside_property
- test_nx_qb_games.py: test_the_games_have_quarterback_runs_of_every_kind
- test_nx_review_games.py: test_the_games_have_booth_reviews_and_coach_challenges_reversed_and_confirmed
- test_nx_playbook_games.py: test_a_whole_game_through_the_two_level_menus
- test_nx_enforcement.py: test_random_fouls_and_plays_always_give_a_valid_result

### C9

Requirement: Accessibility. Every decision point speaks what is being asked, the choices, and the current answer; Up and Down or Tab change it, a letter key sets it, Enter takes it...

Tests:
- test_nx_review_flows.py: test_the_keys_at_the_question_are_up_down_y_n_enter_and_f1_and_any_other_key_asks_again_with_the_answer_kept
- test_nx_penalties.py: test_f1_says_the_flag_again_and_the_keypad_one_is_not_the_letter_a
- test_nx_onside.py: test_f1_asks_again_f3_says_the_score_and_the_keypad_one_is_not_y
- test_nx_penalties.py: test_the_prompt_starts_at_decline_when_the_play_was_better_and_a_d_and_a_keys_set_the_answer
- test_sx9_speech_stress.py: test_nvda_closing_in_the_middle_of_the_roster_goes_on_with_sapi_and_every_player_is_said, test_a_franchise_year_with_the_sapi_voice_failing_and_no_screen_reader_reaches_the_next_season, test_nvda_closing_at_the_draft_with_slow_speech_the_offseason_goes_on_with_sapi

### C10

Requirement: Robustness. A damaged or missing extras file is repaired from the defaults with a spoken notice (playbook 7.10); the extras never end the program; Save Game works at e...

Tests:
- test_nx_pending_save.py: test_s_at_the_prompt_puts_the_declined_board_keeps_the_choice_and_saves, test_a_loaded_game_asks_the_choice_first_and_accepting_enforces_the_penalty, test_declining_after_the_load_leaves_the_play_as_it_stood, test_s_again_after_the_load_keeps_it_again, test_a_save_that_cannot_be_written_asks_the_choice_again, test_a_classic_program_that_says_no_plays_the_declined_board, test_s_where_the_choice_cannot_be_kept_says_so_and_the_prompt_goes_on, test_can_save_only_a_new_down_for_the_team_with_the_ball and 7 more
- test_nx_save.py: test_a_fuzz_of_damaged_records_raises_only_value_error
- test_nx_penalty_list.py: test_a_fuzz_of_damaged_penalties_files_never_raises_and_always_leaves_a_usable_table
- test_nx_remarks.py: test_a_fuzz_of_damaged_remarks_files_never_raises_and_always_leaves_a_usable_pool
- test_nx_playbook_list.py: test_a_fuzz_of_damaged_files_never_raises_and_always_leaves_a_usable_table
- test_sx9_saved_states.py: test_a_record_with_every_field_away_from_its_start_goes_through_the_file_and_into_a_game, test_every_field_with_a_value_of_the_wrong_kind_refuses_the_record, test_whole_games_saved_at_every_wait_read_back_whole_and_a_loaded_game_plays_to_its_end
- test_sx9_league_damage.py: test_the_franchise_wrote_a_file_at_every_stage_of_the_year, test_every_damage_of_league_sav_at_every_stage_opens_the_copy_and_says_so_once, test_a_missing_league_sav_at_every_stage_opens_the_copy, test_both_files_damaged_at_every_stage_set_the_franchise_aside, test_a_restart_from_a_damaged_file_at_every_offseason_stage_reaches_the_next_season_whole, test_the_first_file_of_a_new_franchise_damaged_with_no_copy_sets_the_franchise_aside


## NFL_EXTRA_FEATURES 6 to 12, the features N1 to N7 (nfl4 only, rule 0.13)

### N1.1

Requirement: The state has the timeouts left of each team for each half and period. They are spoken at the start of each half and on F1 in N. F. L. rules mode ("you have two timeou...

Tests:
- test_nx_timeouts.py: test_a_new_half_renews_the_timeouts_a_new_quarter_of_the_same_half_does_not
- test_nx_engine.py: test_the_timeouts_are_said_once_at_the_first_kickoff_of_a_half_and_of_an_overtime_period
- test_nx_engine.py: test_f1_adds_the_clock_and_the_timeouts_after_the_original_sentences

### N1.2

Requirement: The player calls a timeout from the offense menu or the defense menu (an added item and the letter key T) and at no other time; a timeout the player has none of is ref...

Tests:
- test_nx_engine.py: test_t_calls_the_time_out_at_once_and_the_menu_starts_again
- test_nx_engine.py: test_a_timeout_with_none_left_is_refused_never_granted
- test_nx_engine.py: test_a_second_timeout_in_the_same_dead_ball_period_is_refused_and_the_menu_stays
- test_nx_tkey.py: test_the_time_out_item_still_works_by_its_number_and_enter

### N1.3

Requirement: The computer uses timeouts by rules from published practice (the league's article is no longer reachable; NFL_RULES_RESEARCH Part 2 section 5 and the play-by-play coun...

Tests:
- test_nx_timeouts.py: test_rule_1_none_left_means_no_timeout
- test_nx_timeouts.py: test_rule_3_the_fourth_quarter_trailing_or_tied
- test_nx_timeouts.py: test_a_trailing_computer_defense_uses_its_timeouts_to_get_the_ball_back
- test_nx_timeouts.py: test_timeouts_off_means_no_computer_timeout_and_no_draw_for_one

### N1.4

Requirement: The sounds and sentences: the whistle wav and the original's bleep for the stop, an announcer sentence ("Time out called by the <team>, <n> left"), a customizable rema...

Tests:
- test_nx_remarks.py: test_the_timeout_pool_is_the_five_lines_of_strings_nx_with_their_exact_spaces
- test_nx_engine.py: test_the_last_timeout_says_none_are_left_and_a_remark_may_follow

### N1.5

Requirement: The clock effects of C2: the clock stops and restarts correctly; F4 speaks the real time.

Tests:
- test_nx_clock.py: test_the_rules_table_holds_the_2026_rulebook_numbers
- test_nx_clock.py: test_a_timeout_never_lets_the_period_run_out_and_draws_nothing_when_the_clock_is_stopped
- test_nx_engine.py: test_f4_in_a_play_menu_speaks_the_real_time_and_draws_nothing

### N2.1

Requirement: The ruling model. The simulation has no video, so some plays get an initial "ruling on the field" that is wrong with a small, tunable probability by category (a comple...

Tests:
- test_nx_review_rules.py: test_the_rates_are_design_6_1_per_thousand_with_the_close_rates_of_the_calibration
- test_nx_review_rules.py: test_the_aspects_of_a_play_are_in_the_order_of_the_priority_of_design_6_1
- test_nx_review_plays.py: test_a_wrong_ruling_is_clear_and_obvious_with_85_percent

### N2.2

Requirement: The player hears the ruling, a short color remark from the announcer that hints at how close it looked (in the manner of Ghip's remarks; customizable pool), and has th...

Tests:
- test_nx_review_plays.py: test_the_hint_chance_is_70_after_a_wrong_ruling_and_50_after_a_close_one
- test_nx_review_flows.py: test_the_keys_at_the_question_are_up_down_y_n_enter_and_f1_and_any_other_key_asks_again_with_the_answer_kept
- test_nx_review_refusals.py: test_the_letter_c_says_why_there_is_no_challenge

### N2.3

Requirement: The review: the announcer says the referee is going under the hood (a pause drawn in the original's manner with dy), then "the ruling on the field is confirmed" or "re...

Tests:
- test_nx_review_flows.py: test_a_challenge_that_wins_gives_the_first_down_and_costs_nothing
- test_nx_review_flows.py: test_a_challenge_that_loses_costs_a_time_out_and_the_item_then_says_there_is_nothing_to_challenge
- test_nx_review_rules.py: test_the_ten_rulings_the_player_hears_and_the_sentences_around_them

### N2.4

Requirement: Booth reviews (scoring plays, turnovers, the last two minutes, overtime): spoken as "the replay official has stopped the game to review"; no cost; the same reversal lo...

Tests:
- test_nx_review_computer.py: test_a_booth_review_of_a_close_ruling_has_a_14_percent_chance
- test_nx_review_refusals.py: test_a_score_a_turnover_or_a_failed_fourth_down_is_the_replay_officials_and_the_letter_c_says_so

### N2.5

Requirement: The computer coach challenges by a rule of thumb (design 6.4: a call against it, the hint it heard, a challenge and a timeout in hand; calibrated to the NFL's 0.24 to...

Tests:
- test_nx_review_computer.py: test_the_computer_throws_the_flag_after_a_strong_hint_and_the_review_reverses_the_ruling, test_the_computer_throws_the_flag_after_a_strong_hint_with_chance_80_percent
- test_nx_review_games.py: test_never_more_than_three_challenges_a_team_and_a_third_only_after_a_success

### N2.7

Requirement: After a reversal a head coach may change an accept or decline choice made on that play (15-7-3 Item 3); the player is asked again (NX7).

Tests:
- test_nx_review_penalties.py: test_the_player_declines_a_flag_the_review_changes_the_ruling_and_the_flag_is_offered_again_and_accepted

### N2.6

Requirement: A challenge never reaches the original's F2 "instant replay" (the replay of the speech lines of the last play stays as it is and is named in the menus only as instant...

Tests:
- test_nx_review_fixes.py: test_the_sentences_of_a_review_are_spoken_and_logged_but_not_kept_for_the_instant_replay

### N3.1

Requirement: New offense plays, each a named play with an outcome row against the six defense calls (data, H8): QB Sneak (short yardage, high success, tiny fumble chance, the right...

Tests:
- test_nx_qb_plays.py: test_a_sneak_speaks_its_sentences_and_counts_as_a_running_play_and_on_its_own_line
- test_nx_qb.py: test_the_rows_are_the_designs_table_of_7_1
- test_nx_qb.py: test_the_scramble_has_one_row_for_every_defense_call

### N3.2

Requirement: The slide: when a keeper gains a first down or is near the sideline or the goal line, a slide may be chosen by the quarterback (an automatic rule for the computer; for...

Tests:
- test_nx_qb_plays.py: test_a_gain_of_8_or_more_may_end_in_a_slide_that_cuts_the_gain_and_stays_in_bounds
- test_nx_qb_plays.py: test_the_slide_cuts_0_to_2_yards_and_a_cut_of_0_still_slides
- test_nx_qb_penalties.py: test_a_late_hit_on_the_slider_is_unnecessary_roughness_15_yards_and_a_first_down

### N3.3

Requirement: Statistics: the keeper counts as a running play and its yards as running yards, plus its own line in the added statistics (C7); a fumble counts as a fumble lost when l...

Tests:
- test_nx_qb_games.py: test_the_statistics_equal_the_events_less_the_runs_a_penalty_erased
- test_nx_qb_plays.py: test_a_fumble_on_a_draw_is_a_fumble_lost_and_not_a_running_play
- test_nx_qb.py: test_the_statistics_add_the_quarterback_runs_and_their_yards

### N3.4

Requirement: Sentences in the manner of 5.9 ("<quarterback> keeps the ball and runs around the right end", "the quarterback sneak is good for a first down"), a new phrase family wi...

Tests:
- test_nx_qb_plays.py: test_a_keeper_says_a_line_of_pool_qb_then_the_run_with_a_direction_and_the_tackle
- test_nx_qb_plays.py: test_pool_qb_never_repeats_one_of_the_last_three_lines

### N3.5

Requirement: The computer chooses keepers (short-yardage sneaks, late-game scrambles when trailing, rarely otherwise) by rules in its design file; the defense calls against a keepe...

Tests:
- test_nx_qb_plays.py: test_the_computer_sneaks_on_third_or_fourth_and_one_or_two_with_chance_1_in_2
- test_nx_qb_plays.py: test_the_computers_defense_matches_a_repeated_quarterback_run

### N4.1

Requirement: At a kick-off or safety kick of the player's team in N. F. L. rules mode, a yes-or-no question in the style of 4.16: "<coach> do you wish to try an onside kick" with t...

Tests:
- test_nx_onside.py: test_the_question_is_due_by_the_rule_of_design_8_2
- test_nx_onside.py: test_the_player_says_yes_with_y_and_enter_and_the_kick_follows
- test_nx_onside.py: test_the_always_setting_asks_at_every_kick_off
- test_nx_onside_default.py: test_a_new_player_is_asked_at_every_kick
- test_nx_onside_default.py: test_a_file_from_before_the_change_with_sensible_moves_once
- test_nx_onside_default.py: test_the_players_team_is_asked_at_every_kick_off
- test_nx_onside_default.py: test_the_players_team_is_asked_at_a_safety_kick_too
- test_nx_onside_default.py: test_the_computer_is_never_asked
- test_sx10d_kicks.py: test_the_digit_four_declares_the_onside_kick_and_d_describes_the_short_kick
- test_sx10d_kicks.py: test_the_computer_kicks_onside_by_its_rule_late_and_behind

### N4.2

Requirement: The kick: a short kick sentence sequence in the manner of 5.10 (the setup, the kick, the scramble for the ball), with the original's kick sounds, and one outcome draw...

Tests:
- test_nx_onside.py: test_the_distance_runs_from_8_to_14_yards
- test_nx_onside.py: test_a_recovery_needs_a_draw_below_the_eight_percent_chance
- test_nx_onside.py: test_the_kicking_team_recovers_it

