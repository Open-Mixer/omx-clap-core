// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#ifndef OMX_CLAP_VOCABULARY_H
#define OMX_CLAP_VOCABULARY_H
/*
 * GENERATED: DO NOT EDIT BY HAND.
 * Produced by `omx-contract render --target c` from Open-Mixer/omx-clap's data/: the vocabulary
 * (docs/data-layout.md). A code is OMX_ and the code in upper snake case, and a reply code that carries a resp has it as that name and _RESP; a word is OMX_<ITEM>_<NAME>, each words
 * item with its _COUNT and an _INIT of its words in their order. A consumer writes and compares these, never a
 * literal of its own.
 */

/** @file
 * @brief The vocabulary of omx-clap: every code and every word as a string define, with its sentence
 * where it carries one. */

/* HOSTING_CLAP_CODES (contract.d/hosting/hosting.json) */
#define OMX_HOSTING_CLAP_EXTENSIONS_NOT_COVERED "hosting.clap.extensions-not-covered" ///< unknown: the plugin passed headless with OMX_CLAP_HOST_EXTENSIONS offered, and this host offers fewer of them, so that pass is not this host's; the record names the extensions it lacks
/** The source sentence (English) of OMX_HOSTING_CLAP_EXTENSIONS_NOT_COVERED. */
#define OMX_HOSTING_CLAP_EXTENSIONS_NOT_COVERED_TEXT_EN "Not every extension this plugin declares is covered by what was checked. Check the plugin against the extensions this host covers, or accept the gap."
#define OMX_HOSTING_CLAP_FORMAT_NOT_HOSTED "hosting.clap.format-not-hosted" ///< unsuitable: the host profile has no CLAP path (its clapExtensions is null), so no CLAP runs on it whatever was measured
/** The source sentence (English) of OMX_HOSTING_CLAP_FORMAT_NOT_HOSTED. */
#define OMX_HOSTING_CLAP_FORMAT_NOT_HOSTED_TEXT_EN "This host does not host the CLAP format. Use a host that does."
#define OMX_HOSTING_CLAP_HEADLESS_FAILED "hosting.clap.headless-failed" ///< unsuitable: init() or activate() failed with no window and only OMX_CLAP_HOST_EXTENSIONS offered (a plugin that requires the gui extension, or whose init returns false)
/** The source sentence (English) of OMX_HOSTING_CLAP_HEADLESS_FAILED. */
#define OMX_HOSTING_CLAP_HEADLESS_FAILED_TEXT_EN "The plugin failed while being checked headless, with no window. Fix what failed and check it again."
#define OMX_HOSTING_CLAP_LATENCY_MISMATCH "hosting.clap.latency-mismatch" ///< unsuitable: at one declared rate the latency the plugin declares is not the frame the qualifier's impulse arrives at (for an instrument, its note sounds before the declared latency); the record names the rate, declared and measured frames
/** The source sentence (English) of OMX_HOSTING_CLAP_LATENCY_MISMATCH. */
#define OMX_HOSTING_CLAP_LATENCY_MISMATCH_TEXT_EN "The plugin\342\200\231s reported latency does not match what was measured. Trust the measured figure, not the plugin\342\200\231s own report."
#define OMX_HOSTING_CLAP_NOTE_INPUT "hosting.clap.note-input" ///< the plugin declares a note input the configuration refuses
/** The source sentence (English) of OMX_HOSTING_CLAP_NOTE_INPUT. */
#define OMX_HOSTING_CLAP_NOTE_INPUT_TEXT_EN "This configuration refuses the note input the plugin declares. Run the plugin in a configuration that accepts its note input, or without notes."
#define OMX_HOSTING_CLAP_PROCESS_ERROR "hosting.clap.process-error" ///< unsuitable: process() returned CLAP_PROCESS_ERROR during the parameter or note sweep; the record counts the errors
/** The source sentence (English) of OMX_HOSTING_CLAP_PROCESS_ERROR. */
#define OMX_HOSTING_CLAP_PROCESS_ERROR_TEXT_EN "The plugin\342\200\231s processing call returned an error. Treat the plugin as faulty for this block."
#define OMX_HOSTING_CLAP_THREAD_VIOLATION "hosting.clap.thread-violation" ///< conditional: the strict thread-check caught a [main-thread] host call from the audio thread, or process() on another thread; the plugin runs isolated in a worker of its own
/** The source sentence (English) of OMX_HOSTING_CLAP_THREAD_VIOLATION. */
#define OMX_HOSTING_CLAP_THREAD_VIOLATION_TEXT_EN "The plugin called back from the wrong thread. Treat the plugin as not thread-safe."
#define OMX_HOSTING_CLAP_UNQUALIFIED "hosting.clap.unqualified" ///< unknown: no CLAP qualification is on record for the plugin (or its sweep made no process() call), so its topology, features and real-time safety are not judged
/** The source sentence (English) of OMX_HOSTING_CLAP_UNQUALIFIED. */
#define OMX_HOSTING_CLAP_UNQUALIFIED_TEXT_EN "This plugin has not been qualified for hosting. Qualify it before relying on it."

/* HOSTING_COST_CODES (contract.d/hosting/hosting.json) */
#define OMX_HOSTING_COST_ABOVE_CEILING "hosting.cost.above-ceiling" ///< unsuitable: the plugin's P95 core fraction at the judged rate and quantum is above the host profile's per-instance ceiling
/** The source sentence (English) of OMX_HOSTING_COST_ABOVE_CEILING. */
#define OMX_HOSTING_COST_ABOVE_CEILING_TEXT_EN "The plugin\342\200\231s measured CPU cost is above the ceiling for this rate and quantum. Raise the ceiling, or use a plugin that costs less."
#define OMX_HOSTING_COST_FIELDS_MISSING "hosting.cost.fields-missing" ///< unknown: the cost record at the judged rate and quantum lacks a figure the comparison needs (refused before comparing, so an absent figure never passes); the record names them
/** The source sentence (English) of OMX_HOSTING_COST_FIELDS_MISSING. */
#define OMX_HOSTING_COST_FIELDS_MISSING_TEXT_EN "The cost measurement is missing fields it needs. Measure the plugin\342\200\231s cost again, completely."
#define OMX_HOSTING_COST_SPIKY_TAIL "hosting.cost.spiky-tail" ///< conditional: the P95 cost per sample is more than the policy's tail ratio above the median at the judged rate and quantum
/** The source sentence (English) of OMX_HOSTING_COST_SPIKY_TAIL. */
#define OMX_HOSTING_COST_SPIKY_TAIL_TEXT_EN "The plugin\342\200\231s CPU cost has a spiky tail: occasional blocks cost much more than the rest. Treat it as unreliable at this rate and quantum."
#define OMX_HOSTING_COST_UNMEASURED_AT_RATE_AND_QUANTUM "hosting.cost.unmeasured-at-rate-and-quantum" ///< unknown: no cost was measured at the rate and quantum being judged
/** The source sentence (English) of OMX_HOSTING_COST_UNMEASURED_AT_RATE_AND_QUANTUM. */
#define OMX_HOSTING_COST_UNMEASURED_AT_RATE_AND_QUANTUM_TEXT_EN "The plugin\342\200\231s CPU cost has not been measured at this rate and quantum. Measure it before relying on a ceiling."
#define OMX_HOSTING_COST_WITHIN_CEILING "hosting.cost.within-ceiling" ///< suitable: the P95 core fraction is within the host's per-instance ceiling and the tail is within the policy's ratio
/** The source sentence (English) of OMX_HOSTING_COST_WITHIN_CEILING. */
#define OMX_HOSTING_COST_WITHIN_CEILING_TEXT_EN "The plugin\342\200\231s measured CPU cost is within the ceiling for this rate and quantum."

/* HOSTING_FEATURES_CODES (contract.d/hosting/hosting.json) */
#define OMX_HOSTING_FEATURES_ATOM_IN_UNFED "hosting.features.atom-in-unfed" ///< a non-MIDI atom input no buffer here can feed
/** The source sentence (English) of OMX_HOSTING_FEATURES_ATOM_IN_UNFED. */
#define OMX_HOSTING_FEATURES_ATOM_IN_UNFED_TEXT_EN "This plugin declares a non-MIDI atom input that nothing here can feed. Run it where that input can be fed, or accept it stays empty."
#define OMX_HOSTING_FEATURES_HOST_NOT_PROVIDED "hosting.features.host-not-provided" ///< unsuitable: the plugin requires a feature the host refuses to provide on the audio thread (a disqualifying one, or one that pins the quantum where the quantum is not pinned); the record names them
/** The source sentence (English) of OMX_HOSTING_FEATURES_HOST_NOT_PROVIDED. */
#define OMX_HOSTING_FEATURES_HOST_NOT_PROVIDED_TEXT_EN "This plugin needs a host feature this host does not provide. Run it on a host that provides that feature."
#define OMX_HOSTING_FEATURES_MIDI_IN_FED_EMPTY "hosting.features.midi-in-fed-empty" ///< conditional: the plugin has a MIDI input, which an insert on a host that plays no notes never feeds; on the LV2 path an input the host cannot feed is refused at add
/** The source sentence (English) of OMX_HOSTING_FEATURES_MIDI_IN_FED_EMPTY. */
#define OMX_HOSTING_FEATURES_MIDI_IN_FED_EMPTY_TEXT_EN "This plugin\342\200\231s MIDI input is fed nothing. Connect a source of MIDI, or accept it runs with none."
#define OMX_HOSTING_FEATURES_MISSING "hosting.features.missing" ///< unsuitable: the plugin requires a feature the host does not provide; the LV2 adapter refuses it at add from its TTL, before its binary is opened
/** The source sentence (English) of OMX_HOSTING_FEATURES_MISSING. */
#define OMX_HOSTING_FEATURES_MISSING_TEXT_EN "This plugin is missing a feature it needs to run here. Provide that feature, or run it elsewhere."
#define OMX_HOSTING_FEATURES_PORTS_UNREADABLE "hosting.features.ports-unreadable" ///< the plugin declares ports its reader cannot read (a port node shared by several plugins of one bundle, a port with no symbol), so none reaches the host: the bundle's data is the fault, not the layout (omx-clap-core#255)
/** The source sentence (English) of OMX_HOSTING_FEATURES_PORTS_UNREADABLE. */
#define OMX_HOSTING_FEATURES_PORTS_UNREADABLE_TEXT_EN "This plugin declares ports its reader cannot read, so none of them reach the host. The fault is in the plugin\342\200\231s own bundle, not in this host."
#define OMX_HOSTING_FEATURES_ALL_PROVIDED "hosting.features.all-provided" ///< suitable: every feature the plugin requires is provided, and nothing in its descriptor is a caution
/** The source sentence (English) of OMX_HOSTING_FEATURES_ALL_PROVIDED. */
#define OMX_HOSTING_FEATURES_ALL_PROVIDED_TEXT_EN "This plugin has every feature it needs."
#define OMX_HOSTING_FEATURES_SCAN_PREDATES_FIELD "hosting.features.scan-predates-field" ///< unknown: the plugin's scan record has no feature list, because it was taken before the scan read one
/** The source sentence (English) of OMX_HOSTING_FEATURES_SCAN_PREDATES_FIELD. */
#define OMX_HOSTING_FEATURES_SCAN_PREDATES_FIELD_TEXT_EN "This plugin was scanned before this field existed, so it was never checked for it. Scan it again to check."

/* HOSTING_LATENCY_CODES (contract.d/hosting/hosting.json) */
#define OMX_HOSTING_LATENCY_NONCONFORMING "hosting.latency.nonconforming" ///< unknown: the measured latency does not scale with rate as a conforming plugin's does (its scaling class is nonconforming), so its figure is not used
/** The source sentence (English) of OMX_HOSTING_LATENCY_NONCONFORMING. */
#define OMX_HOSTING_LATENCY_NONCONFORMING_TEXT_EN "This plugin\342\200\231s reported latency does not conform to what a host can use. Don\342\200\231t trust its reported latency."
#define OMX_HOSTING_LATENCY_PARAMETER_DEPENDENT "hosting.latency.parameter-dependent" ///< conditional: the parameter sweep moved the plugin's latency; allowed where the host compensates, as it reads the live figure each cycle
/** The source sentence (English) of OMX_HOSTING_LATENCY_PARAMETER_DEPENDENT. */
#define OMX_HOSTING_LATENCY_PARAMETER_DEPENDENT_TEXT_EN "This plugin\342\200\231s latency changes with its parameters. Re-read its latency after a parameter change that could affect it."
#define OMX_HOSTING_LATENCY_RESOLVED "hosting.latency.resolved" ///< suitable: the plugin's latency is measured and fixed (for a CLAP, the declared figure is what was measured at every declared rate)
/** The source sentence (English) of OMX_HOSTING_LATENCY_RESOLVED. */
#define OMX_HOSTING_LATENCY_RESOLVED_TEXT_EN "This plugin\342\200\231s latency has been resolved to a fixed figure."
#define OMX_HOSTING_LATENCY_UNMEASURED "hosting.latency.unmeasured" ///< unknown: there is no latency figure, or the benchmark declared it unmeasurable; fails closed, never passed by default
/** The source sentence (English) of OMX_HOSTING_LATENCY_UNMEASURED. */
#define OMX_HOSTING_LATENCY_UNMEASURED_TEXT_EN "This plugin\342\200\231s latency has not been measured. Measure it before relying on it."

/* HOSTING_MEMORY_CODES (contract.d/hosting/hosting.json) */
#define OMX_HOSTING_MEMORY_ABOVE_CEILING "hosting.memory.above-ceiling" ///< the measured figure passes the host's budget for one instance or for all its plugins; the params name the figure, the ceiling, and whether the ceiling is provisional
/** The source sentence (English) of OMX_HOSTING_MEMORY_ABOVE_CEILING. */
#define OMX_HOSTING_MEMORY_ABOVE_CEILING_TEXT_EN "This plugin\342\200\231s measured memory is above the host\342\200\231s budget. Raise the budget, or use a plugin that uses less memory."
#define OMX_HOSTING_MEMORY_UNMEASURED "hosting.memory.unmeasured" ///< no figure at the host's rate and quantum, so the plugin is not known to fit; a missing figure never reads as fitting
/** The source sentence (English) of OMX_HOSTING_MEMORY_UNMEASURED. */
#define OMX_HOSTING_MEMORY_UNMEASURED_TEXT_EN "This plugin\342\200\231s memory has not been measured at the host\342\200\231s rate and quantum, so it is not known to fit. Measure it before trusting that it fits."
#define OMX_HOSTING_MEMORY_WITHIN_CEILING "hosting.memory.within-ceiling" ///< the measured figure fits a budget that was itself measured on that kind of host
/** The source sentence (English) of OMX_HOSTING_MEMORY_WITHIN_CEILING. */
#define OMX_HOSTING_MEMORY_WITHIN_CEILING_TEXT_EN "This plugin\342\200\231s measured memory fits a budget that was itself measured on this kind of host."
#define OMX_HOSTING_MEMORY_WITHIN_PROVISIONAL_CEILING "hosting.memory.within-provisional-ceiling" ///< the measured figure is under a budget not yet measured on that kind of host, so this says the figure and the ceiling, not that the plugin fits
/** The source sentence (English) of OMX_HOSTING_MEMORY_WITHIN_PROVISIONAL_CEILING. */
#define OMX_HOSTING_MEMORY_WITHIN_PROVISIONAL_CEILING_TEXT_EN "This plugin\342\200\231s measured memory is under a budget that has not yet been measured on this kind of host. This is not a guarantee that it fits, only that it is under that provisional budget."

/* HOSTING_OUTPUT_CODES (contract.d/hosting/hosting.json) */
#define OMX_HOSTING_OUTPUT_NON_FINITE "hosting.output.non-finite" ///< the plugin produced non-finite output
/** The source sentence (English) of OMX_HOSTING_OUTPUT_NON_FINITE. */
#define OMX_HOSTING_OUTPUT_NON_FINITE_TEXT_EN "This plugin produced non-finite output: infinities or NaNs. Treat its output as a fault."

/* HOSTING_OVERRIDE_CODES (contract.d/hosting/hosting.json) */
#define OMX_HOSTING_OVERRIDE_CURATOR_ISOLATED "hosting.override.curator-isolated" ///< unsuitable: the curator's override holds the plugin isolated, whatever its measurements say
/** The source sentence (English) of OMX_HOSTING_OVERRIDE_CURATOR_ISOLATED. */
#define OMX_HOSTING_OVERRIDE_CURATOR_ISOLATED_TEXT_EN "The curator\342\200\231s override is isolated from this run. Apply the override where the curator\342\200\231s run can see it."

/* HOSTING_PATCH_CODES (contract.d/hosting/hosting.json) */
#define OMX_HOSTING_PATCH_BUSY "hosting.patch.busy" ///< a patch write found the previous one not yet taken by the plugin's thread; the host retries it for a while before answering this
/** The source sentence (English) of OMX_HOSTING_PATCH_BUSY. */
#define OMX_HOSTING_PATCH_BUSY_TEXT_EN "The plugin\342\200\231s patch is busy right now. Try again once it\342\200\231s free."
#define OMX_HOSTING_PATCH_NOT_WRITABLE "hosting.patch.not-writable" ///< the plugin lists no such writable property, or the adapter did not create it: a patch write is refused
/** The source sentence (English) of OMX_HOSTING_PATCH_NOT_WRITABLE. */
#define OMX_HOSTING_PATCH_NOT_WRITABLE_TEXT_EN "This plugin\342\200\231s patch cannot be written. Treat it as read-only."
#define OMX_HOSTING_PATCH_TOO_LARGE "hosting.patch.too-large" ///< the value of a patch write is longer than the property's max_bytes
/** The source sentence (English) of OMX_HOSTING_PATCH_TOO_LARGE. */
#define OMX_HOSTING_PATCH_TOO_LARGE_TEXT_EN "This patch is too large for the plugin to accept. Use a smaller patch."

/* HOSTING_PRESET_CODES (contract.d/hosting/hosting.json) */
#define OMX_HOSTING_PRESET_NOT_FOUND "hosting.preset.not-found" ///< the bundle holds no preset of that name for this plugin
/** The source sentence (English) of OMX_HOSTING_PRESET_NOT_FOUND. */
#define OMX_HOSTING_PRESET_NOT_FOUND_TEXT_EN "This preset could not be found. Check its name and location and try again."

/* HOSTING_PROVENANCE_CODES (contract.d/hosting/hosting.json) */
#define OMX_HOSTING_PROVENANCE_HOST_DIFFERS "hosting.provenance.host-differs" ///< unknown: the figures were measured on a host other than the one the console runs on, so no verdict is carried over from them
/** The source sentence (English) of OMX_HOSTING_PROVENANCE_HOST_DIFFERS. */
#define OMX_HOSTING_PROVENANCE_HOST_DIFFERS_TEXT_EN "The host that measured this plugin differs from the one running it now. Measure it again on this host, or accept the difference."
#define OMX_HOSTING_PROVENANCE_SWEEP_CONTROL_DID_NOT_FIRE "hosting.provenance.sweep-control-did-not-fire" ///< unknown: the sweep's positive control did not fire, so nothing the sweep measured counts
/** The source sentence (English) of OMX_HOSTING_PROVENANCE_SWEEP_CONTROL_DID_NOT_FIRE. */
#define OMX_HOSTING_PROVENANCE_SWEEP_CONTROL_DID_NOT_FIRE_TEXT_EN "The sweep\342\200\231s control plugin did not fire during the measurement. Check the control plugin and measure again."

/* HOSTING_REALISED_CODES (contract.d/hosting/hosting.json) */
#define OMX_HOSTING_DISABLED "hosting.disabled" ///< the console's in-process switch is off: an LV2 runs isolated, and a third-party CLAP, which has no other path, is refused
/** The source sentence (English) of OMX_HOSTING_DISABLED. */
#define OMX_HOSTING_DISABLED_TEXT_EN "This plugin is disabled. Enable it before using it."
#define OMX_HOSTING_LINKED "hosting.linked" ///< the plugin is one of the engine's statically linked CLAPs and runs in-process on the node that carries the CLAP bank
/** The source sentence (English) of OMX_HOSTING_LINKED. */
#define OMX_HOSTING_LINKED_TEXT_EN "This plugin is realised linked into the host\342\200\231s own process."
#define OMX_HOSTING_NO_REALISATION "hosting.no-realisation" ///< the plugin earned a path that has no body here: no LV2 adapter or CLAP bank to run it, or a port class the stage cannot bind
/** The source sentence (English) of OMX_HOSTING_NO_REALISATION. */
#define OMX_HOSTING_NO_REALISATION_TEXT_EN "This plugin has no realisation: nothing runs it. Give it a way to run before using it."
#define OMX_HOSTING_REALISED_IN_PROCESS "hosting.realised.in-process" ///< the plugin runs in-process: it earned it and the console's switch allows it
/** The source sentence (English) of OMX_HOSTING_REALISED_IN_PROCESS. */
#define OMX_HOSTING_REALISED_IN_PROCESS_TEXT_EN "This plugin is realised in its own process, isolated from the host\342\200\231s."
#define OMX_HOSTING_UNJUDGED "hosting.unjudged" ///< the plugin has no verdict on record for this build (a linked CLAP without a row measured on the pinned build): it is refused at load
/** The source sentence (English) of OMX_HOSTING_UNJUDGED. */
#define OMX_HOSTING_UNJUDGED_TEXT_EN "This plugin has not been judged yet. Judge it before trusting any verdict about it."

/* HOSTING_RESOURCE_HINTS_CODES (contract.d/hosting/hosting.json) */
#define OMX_HOSTING_RESOURCE_HINTS_OUT_OF_RANGE "hosting.resource-hints.out-of-range" ///< a figure below zero, or past what its hint's member holds
/** The source sentence (English) of OMX_HOSTING_RESOURCE_HINTS_OUT_OF_RANGE. */
#define OMX_HOSTING_RESOURCE_HINTS_OUT_OF_RANGE_TEXT_EN "This plugin declared a resource hint figure below zero, or past what that hint can hold. None of its hints are trusted; every one reads as unknown."
#define OMX_HOSTING_RESOURCE_HINTS_UNKNOWN_HINT "hosting.resource-hints.unknown-hint" ///< the declared mask sets a bit RESOURCE_HINTS has no hint for
/** The source sentence (English) of OMX_HOSTING_RESOURCE_HINTS_UNKNOWN_HINT. */
#define OMX_HOSTING_RESOURCE_HINTS_UNKNOWN_HINT_TEXT_EN "This plugin\342\200\231s declared hints set a bit that names no known hint. None of its hints are trusted; every one reads as unknown."
#define OMX_HOSTING_RESOURCE_HINTS_WRONG_UNIT "hosting.resource-hints.wrong-unit" ///< a figure not in its hint's unit: a flag that is not a boolean, a count, a time or a size that is not an integer
/** The source sentence (English) of OMX_HOSTING_RESOURCE_HINTS_WRONG_UNIT. */
#define OMX_HOSTING_RESOURCE_HINTS_WRONG_UNIT_TEXT_EN "This plugin declared a resource hint figure in the wrong unit: a flag that is not a boolean, or a count, time or size that is not a whole number. None of its hints are trusted; every one reads as unknown."

/* HOSTING_RT_SAFETY_CODES (contract.d/hosting/hosting.json) */
#define OMX_HOSTING_RT_SAFETY_CLEAN_UNDER_SWEEP "hosting.rt-safety.clean-under-sweep" ///< suitable: the interposer counted no allocation, lock or system call on the audio thread over the armed blocks with every parameter swept
/** The source sentence (English) of OMX_HOSTING_RT_SAFETY_CLEAN_UNDER_SWEEP. */
#define OMX_HOSTING_RT_SAFETY_CLEAN_UNDER_SWEEP_TEXT_EN "The plugin showed no real-time safety violation under the sweep. It passed clean."
#define OMX_HOSTING_RT_SAFETY_NOT_REPRODUCIBLE "hosting.rt-safety.not-reproducible" ///< unknown: the interposer's counts varied between runs of the same plugin
/** The source sentence (English) of OMX_HOSTING_RT_SAFETY_NOT_REPRODUCIBLE. */
#define OMX_HOSTING_RT_SAFETY_NOT_REPRODUCIBLE_TEXT_EN "The real-time safety measurement could not be reproduced. Measure it again before trusting it."
#define OMX_HOSTING_RT_SAFETY_CLEAN_UNDER_NOTES "hosting.rt-safety.clean-under-notes" ///< suitable: played under the interposer, the plugin made no allocation, lock or system call
/** The source sentence (English) of OMX_HOSTING_RT_SAFETY_CLEAN_UNDER_NOTES. */
#define OMX_HOSTING_RT_SAFETY_CLEAN_UNDER_NOTES_TEXT_EN "The plugin showed no real-time safety violation while playing notes. It passed clean."
#define OMX_HOSTING_RT_SAFETY_NOTES_UNMEASURED "hosting.rt-safety.notes-unmeasured" ///< unknown: the plugin takes notes and was not played under the interposer; the parameter sweep alone says nothing about a voice
/** The source sentence (English) of OMX_HOSTING_RT_SAFETY_NOTES_UNMEASURED. */
#define OMX_HOSTING_RT_SAFETY_NOTES_UNMEASURED_TEXT_EN "The plugin\342\200\231s real-time safety while playing notes has not been measured. Measure it before relying on it."
#define OMX_HOSTING_RT_SAFETY_VIOLATIONS_UNDER_NOTES "hosting.rt-safety.violations-under-notes" ///< conditional: played under the interposer, the plugin allocated, locked or made a system call; it runs in a worker of its own
/** The source sentence (English) of OMX_HOSTING_RT_SAFETY_VIOLATIONS_UNDER_NOTES. */
#define OMX_HOSTING_RT_SAFETY_VIOLATIONS_UNDER_NOTES_TEXT_EN "The plugin violated real-time safety while playing notes. Treat it as not real-time safe with notes."
#define OMX_HOSTING_RT_SAFETY_OWN_THREADS "hosting.rt-safety.own-threads" ///< conditional: the plugin started threads of its own at instantiate (counted from /proc/self/task); a worker thread is not RT-unsafe, so the plugin still shares a worker (D20)
/** The source sentence (English) of OMX_HOSTING_RT_SAFETY_OWN_THREADS. */
#define OMX_HOSTING_RT_SAFETY_OWN_THREADS_TEXT_EN "The plugin starts threads of its own beside its audio. It is real-time safe, and it can share a worker; its threads share the cores with the audio."
#define OMX_HOSTING_RT_SAFETY_UNMEASURED "hosting.rt-safety.unmeasured" ///< unknown: no interposer count was taken with every parameter swept (or the plugin has none to sweep), so the audio thread was never traced
/** The source sentence (English) of OMX_HOSTING_RT_SAFETY_UNMEASURED. */
#define OMX_HOSTING_RT_SAFETY_UNMEASURED_TEXT_EN "The plugin\342\200\231s real-time safety has not been measured. Measure it before relying on it."
#define OMX_HOSTING_RT_SAFETY_VIOLATIONS_IN_RUN "hosting.rt-safety.violations-in-run" ///< conditional: the interposer counted allocations, locks or system calls on the audio thread over the armed blocks; the plugin runs in a worker of its own, never grouped with RT-safe plugins
/** The source sentence (English) of OMX_HOSTING_RT_SAFETY_VIOLATIONS_IN_RUN. */
#define OMX_HOSTING_RT_SAFETY_VIOLATIONS_IN_RUN_TEXT_EN "The plugin violated real-time safety during the run. Treat it as not real-time safe."

/* HOSTING_STABILITY_CODES (contract.d/hosting/hosting.json) */
#define OMX_HOSTING_STABILITY_CYCLES_BELOW_FLOOR "hosting.stability.cycles-below-floor" ///< unknown: the plugin was instantiated fewer times than the policy's cycle floor
/** The source sentence (English) of OMX_HOSTING_STABILITY_CYCLES_BELOW_FLOOR. */
#define OMX_HOSTING_STABILITY_CYCLES_BELOW_FLOOR_TEXT_EN "The plugin was soaked for fewer cycles than the floor needs. Soak it for enough cycles before trusting the result."
#define OMX_HOSTING_STABILITY_CRASH_UNATTRIBUTED "hosting.stability.crash-unattributed" ///< unknown: a crash was recorded that no signature attributes to the plugin
/** The source sentence (English) of OMX_HOSTING_STABILITY_CRASH_UNATTRIBUTED. */
#define OMX_HOSTING_STABILITY_CRASH_UNATTRIBUTED_TEXT_EN "Something crashed during the run, but not a plugin that could be identified. Narrow down which plugin crashed before trusting any of them."
#define OMX_HOSTING_STABILITY_CRASHED_ATTRIBUTED_PLUGIN "hosting.stability.crashed-attributed-plugin" ///< unsuitable: a recorded crash is attributed to the plugin's own binary
/** The source sentence (English) of OMX_HOSTING_STABILITY_CRASHED_ATTRIBUTED_PLUGIN. */
#define OMX_HOSTING_STABILITY_CRASHED_ATTRIBUTED_PLUGIN_TEXT_EN "This plugin crashed during the run. Don\342\200\231t host it until it\342\200\231s fixed."
#define OMX_HOSTING_STABILITY_CALLEE_SAVED_CLOBBERED "hosting.stability.callee-saved-clobbered" ///< the plugin returned from a call with a callee-saved register changed (0.26.2): the host's guard put it back, but not the other members' state in the same process, so the plugin runs only in a worker of its own
/** The source sentence (English) of OMX_HOSTING_STABILITY_CALLEE_SAVED_CLOBBERED. */
#define OMX_HOSTING_STABILITY_CALLEE_SAVED_CLOBBERED_TEXT_EN "This plugin returned from a call having changed a register it should have preserved. The host put the register back, but other plugins sharing its process were not protected, so it now runs only in a worker of its own."
#define OMX_HOSTING_STABILITY_CRASHED_LIVE_ON_THIS_RIG "hosting.stability.crashed-live-on-this-rig" ///< the plugin crashed live on this rig
/** The source sentence (English) of OMX_HOSTING_STABILITY_CRASHED_LIVE_ON_THIS_RIG. */
#define OMX_HOSTING_STABILITY_CRASHED_LIVE_ON_THIS_RIG_TEXT_EN "This plugin crashed live on this rig. Don\342\200\231t host it on this rig until it\342\200\231s fixed."
#define OMX_HOSTING_STABILITY_LINKS_GUI_TOOLKIT "hosting.stability.links-gui-toolkit" ///< conditional: the plugin links a GUI toolkit, a caution only where it shares a process
/** The source sentence (English) of OMX_HOSTING_STABILITY_LINKS_GUI_TOOLKIT. */
#define OMX_HOSTING_STABILITY_LINKS_GUI_TOOLKIT_TEXT_EN "This plugin links a GUI toolkit, which this host does not run headless. Run it where a GUI toolkit is safe, or use a plugin without one."
#define OMX_HOSTING_STABILITY_SOAK_FAILED_AT_RATE "hosting.stability.soak-failed-at-rate" ///< unsuitable: the soak failed at the very rate being judged (a supervisor timeout aside, which is the harness's)
/** The source sentence (English) of OMX_HOSTING_STABILITY_SOAK_FAILED_AT_RATE. */
#define OMX_HOSTING_STABILITY_SOAK_FAILED_AT_RATE_TEXT_EN "The plugin failed its soak test at this sample rate. Don\342\200\231t trust it at this rate until it\342\200\231s fixed."
#define OMX_HOSTING_STABILITY_SOAKED "hosting.stability.soaked" ///< suitable: the plugin cleared the cycle floor and the soak, with no crash and no caution
/** The source sentence (English) of OMX_HOSTING_STABILITY_SOAKED. */
#define OMX_HOSTING_STABILITY_SOAKED_TEXT_EN "The plugin completed its soak test. It held up over the run."
#define OMX_HOSTING_STABILITY_SPAWNS_THREADS "hosting.stability.spawns-threads" ///< conditional: the plugin spawns threads, a caution only where it shares a process
/** The source sentence (English) of OMX_HOSTING_STABILITY_SPAWNS_THREADS. */
#define OMX_HOSTING_STABILITY_SPAWNS_THREADS_TEXT_EN "This plugin spawns its own threads. Watch it for behaviour a host does not control."
#define OMX_HOSTING_STABILITY_UNMEASURED "hosting.stability.unmeasured" ///< unknown: no lifecycle measurement is on record
/** The source sentence (English) of OMX_HOSTING_STABILITY_UNMEASURED. */
#define OMX_HOSTING_STABILITY_UNMEASURED_TEXT_EN "This plugin\342\200\231s stability has not been measured. Measure it before relying on it."
#define OMX_HOSTING_STABILITY_UNSOAKED "hosting.stability.unsoaked" ///< unknown: the soak ran for less than the policy's time, did not sweep the parameters, or failed at some rate
/** The source sentence (English) of OMX_HOSTING_STABILITY_UNSOAKED. */
#define OMX_HOSTING_STABILITY_UNSOAKED_TEXT_EN "This plugin has not been soaked. Soak it before trusting it over a long run."

/* HOSTING_STATE_CODES (contract.d/hosting/hosting.json) */
#define OMX_HOSTING_STATE_NOT_A_COPY "hosting.state.not-a-copy" ///< not a save's copy directory of the root
/** The source sentence (English) of OMX_HOSTING_STATE_NOT_A_COPY. */
#define OMX_HOSTING_STATE_NOT_A_COPY_TEXT_EN "This path is not a save\342\200\231s copy directory of the state root. Use the copy directory a save actually made."
#define OMX_HOSTING_STATE_PATH_ON_AUDIO "hosting.state.path-on-audio" ///< makePath: called on the audio role
/** The source sentence (English) of OMX_HOSTING_STATE_PATH_ON_AUDIO. */
#define OMX_HOSTING_STATE_PATH_ON_AUDIO_TEXT_EN "This path was requested from the audio role, where it cannot be made. Request it from outside the audio role."
#define OMX_HOSTING_STATE_PATH_OUTSIDE "hosting.state.path-outside" ///< makePath: empty, absolute, or a `..` component
/** The source sentence (English) of OMX_HOSTING_STATE_PATH_OUTSIDE. */
#define OMX_HOSTING_STATE_PATH_OUTSIDE_TEXT_EN "This path is empty, absolute, or steps outside with a `..` component. Use a path relative to the state root, with no `..`."
#define OMX_HOSTING_STATE_PATH_SYMLINK "hosting.state.path-symlink" ///< makePath: a component is a symbolic link
/** The source sentence (English) of OMX_HOSTING_STATE_PATH_SYMLINK. */
#define OMX_HOSTING_STATE_PATH_SYMLINK_TEXT_EN "A component of this path is a symbolic link, which is not allowed here. Use a path with no symbolic links."
#define OMX_HOSTING_STATE_PATH_TOO_LONG "hosting.state.path-too-long" ///< makePath: PATH_MAX or more, or a long component
/** The source sentence (English) of OMX_HOSTING_STATE_PATH_TOO_LONG. */
#define OMX_HOSTING_STATE_PATH_TOO_LONG_TEXT_EN "This path, or one of its components, is too long. Use a shorter path."
#define OMX_HOSTING_STATE_PATH_UNMAKEABLE "hosting.state.path-unmakeable" ///< makePath: a directory could not be made
/** The source sentence (English) of OMX_HOSTING_STATE_PATH_UNMAKEABLE. */
#define OMX_HOSTING_STATE_PATH_UNMAKEABLE_TEXT_EN "The directory for this path could not be made. Check that the state root is writable and try again."
#define OMX_HOSTING_STATE_UNREADABLE "hosting.state.unreadable" ///< the plugin does not declare the state feature, has no state interface, or its restore failed
/** The source sentence (English) of OMX_HOSTING_STATE_UNREADABLE. */
#define OMX_HOSTING_STATE_UNREADABLE_TEXT_EN "This plugin\342\200\231s saved state could not be read. Treat it as lost, or restore it from a working copy."

/* HOSTING_TOPOLOGY_CODES (contract.d/hosting/hosting.json) */
#define OMX_HOSTING_TOPOLOGY_AMBISONIC_CONFIG "hosting.topology.ambisonic-config" ///< an ambisonic port refuses the carrier's ordering or normalisation
/** The source sentence (English) of OMX_HOSTING_TOPOLOGY_AMBISONIC_CONFIG. */
#define OMX_HOSTING_TOPOLOGY_AMBISONIC_CONFIG_TEXT_EN "This plugin\342\200\231s ambisonic port refuses the carrier\342\200\231s channel ordering or normalisation. Use a carrier whose ordering and normalisation this port accepts."
#define OMX_HOSTING_TOPOLOGY_CHANNEL_MAP_UNKNOWN "hosting.topology.channel-map-unknown" ///< a surround port names a channel id the host does not know, or refuses the carrier's channel mask
/** The source sentence (English) of OMX_HOSTING_TOPOLOGY_CHANNEL_MAP_UNKNOWN. */
#define OMX_HOSTING_TOPOLOGY_CHANNEL_MAP_UNKNOWN_TEXT_EN "This plugin\342\200\231s surround port names a channel this host does not know, or refuses the carrier\342\200\231s channel mask. Use a carrier whose channels this host recognises."
#define OMX_HOSTING_TOPOLOGY_INSTRUMENT "hosting.topology.instrument" ///< suitable: on a host that plays notes, the plugin has no audio input, a note or MIDI input and an audio output (one or two channels for a CLAP)
/** The source sentence (English) of OMX_HOSTING_TOPOLOGY_INSTRUMENT. */
#define OMX_HOSTING_TOPOLOGY_INSTRUMENT_TEXT_EN "This plugin is hosted as an instrument: it has no audio input of its own."
#define OMX_HOSTING_TOPOLOGY_MATCHED "hosting.topology.matched" ///< suitable: the plugin's main audio ports are mono to mono or stereo to stereo, with no sidechain input
/** The source sentence (English) of OMX_HOSTING_TOPOLOGY_MATCHED. */
#define OMX_HOSTING_TOPOLOGY_MATCHED_TEXT_EN "This plugin\342\200\231s ports match the topology it is hosted on."
#define OMX_HOSTING_TOPOLOGY_NO_AUDIO_INPUT "hosting.topology.no-audio-input" ///< the plugin has no audio input
/** The source sentence (English) of OMX_HOSTING_TOPOLOGY_NO_AUDIO_INPUT. */
#define OMX_HOSTING_TOPOLOGY_NO_AUDIO_INPUT_TEXT_EN "This plugin has no audio input."
#define OMX_HOSTING_TOPOLOGY_NO_AUDIO_OUTPUT "hosting.topology.no-audio-output" ///< the host has nothing of the plugin to carry: a CLAP plugin with an audio input or an auxiliary port and no main output, an LV2 plugin with no port at all (any other plugin with no audio output is hosted as a pass-through tool)
/** The source sentence (English) of OMX_HOSTING_TOPOLOGY_NO_AUDIO_OUTPUT. */
#define OMX_HOSTING_TOPOLOGY_NO_AUDIO_OUTPUT_TEXT_EN "This plugin has nothing for the host to carry on its output: it declares an audio input or auxiliary port but no main output. Use a plugin with a main audio output, or run it as a pass-through tool."
#define OMX_HOSTING_TOPOLOGY_PORT_TOO_WIDE "hosting.topology.port-too-wide" ///< a port of more channels than the limit, or an ambisonic port whose channels are not (order+1)²
/** The source sentence (English) of OMX_HOSTING_TOPOLOGY_PORT_TOO_WIDE. */
#define OMX_HOSTING_TOPOLOGY_PORT_TOO_WIDE_TEXT_EN "This plugin\342\200\231s port has more channels than the limit, or its ambisonic channel count is not valid for its order. Use a plugin whose ports stay within the channel limit."
#define OMX_HOSTING_TOPOLOGY_PORT_WITHOUT_CHANNELS "hosting.topology.port-without-channels" ///< a port of zero channels
/** The source sentence (English) of OMX_HOSTING_TOPOLOGY_PORT_WITHOUT_CHANNELS. */
#define OMX_HOSTING_TOPOLOGY_PORT_WITHOUT_CHANNELS_TEXT_EN "This plugin declares a port with zero channels. Fix the plugin\342\200\231s port declaration before hosting it."
#define OMX_HOSTING_TOPOLOGY_TOO_MANY_PORTS "hosting.topology.too-many-ports" ///< more than the limit of auxiliary ports on one side, or more than one main port on a side
/** The source sentence (English) of OMX_HOSTING_TOPOLOGY_TOO_MANY_PORTS. */
#define OMX_HOSTING_TOPOLOGY_TOO_MANY_PORTS_TEXT_EN "This plugin declares more auxiliary ports than the limit on one side, or more than one main port on a side. Use a plugin within the port limits."
#define OMX_HOSTING_TOPOLOGY_WIDER_THAN_STRIP "hosting.topology.wider-than-strip" ///< a main port is wider than the lane the caller runs the plugin on
/** The source sentence (English) of OMX_HOSTING_TOPOLOGY_WIDER_THAN_STRIP. */
#define OMX_HOSTING_TOPOLOGY_WIDER_THAN_STRIP_TEXT_EN "This plugin\342\200\231s main port is wider than the strip it runs on. Run it on a strip wide enough for its main port."

/* HOSTING_WORKER_CODES (contract.d/hosting/hosting.json) */
#define OMX_HOSTING_WORKER_NONCONFORMING "hosting.worker.nonconforming" ///< unsuitable: the plugin's worker interface was refused while its latency was measured, so it is not hostable
/** The source sentence (English) of OMX_HOSTING_WORKER_NONCONFORMING. */
#define OMX_HOSTING_WORKER_NONCONFORMING_TEXT_EN "This plugin\342\200\231s worker does not conform to what a worker must do. Don\342\200\231t rely on its worker."

#endif /* OMX_CLAP_VOCABULARY_H */
