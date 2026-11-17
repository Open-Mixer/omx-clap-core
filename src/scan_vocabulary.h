// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
#ifndef SCAN_VOCABULARY_H
#define SCAN_VOCABULARY_H
/*
 * GENERATED: DO NOT EDIT BY HAND.
 * Produced by `omx-contract render --target c` from Open-Mixer/scan's data/: the vocabulary
 * (docs/data-layout.md). A code is OMX_ and the code in upper snake case, and a reply code that carries a resp has it as that name and _RESP; a word is OMX_<ITEM>_<NAME>, each words
 * item with its _COUNT and an _INIT of its words in their order. A consumer writes and compares these, never a
 * literal of its own.
 */

/** @file
 * @brief The vocabulary of scan: every code and every word as a string define, with its sentence
 * where it carries one. */

/* SCAN_DOCUMENTS (scan/scan.json) */
#define OMX_SCAN_DOCUMENTS_CLAP_SCAN_DOCUMENT "CLAP_SCAN_DOCUMENT" ///< The JSON document of omx-clap-scan, one entry per file with its plugins, parameters and ports. Owned by omx-clap-core, which writes it; its shape is omx-clap-core's reference.
/** The source sentence (English) of OMX_SCAN_DOCUMENTS_CLAP_SCAN_DOCUMENT. */
#define OMX_SCAN_DOCUMENTS_CLAP_SCAN_DOCUMENT_TEXT_EN "The JSON document omx-clap-scan writes, one entry per file with its plugins, its parameters and its ports."
#define OMX_SCAN_DOCUMENTS_FIELD_DUMP "FIELD_DUMP" ///< The field dump of omx-clap-scan --fields: the line `# omx-clap-scan --fields 1`, the format's version, then one `<scope> TAB <field> TAB <value>` record per field a plugin states. Its scopes are SCAN_FIELD_SCOPES.
/** The source sentence (English) of OMX_SCAN_DOCUMENTS_FIELD_DUMP. */
#define OMX_SCAN_DOCUMENTS_FIELD_DUMP_TEXT_EN "The field dump omx-clap-scan --fields writes: a version line, then one scope, field and value record per field a plugin states."
/** The number of words of SCAN_DOCUMENTS. */
#define OMX_SCAN_DOCUMENTS_COUNT 2u
/** The words of SCAN_DOCUMENTS in their declared order, as a C initializer list. */
#define OMX_SCAN_DOCUMENTS_INIT { "CLAP_SCAN_DOCUMENT", "FIELD_DUMP" }
/** Expands `X(code, "word", NAME)` once per word of SCAN_DOCUMENTS, in order, the code being its place in the order. The documents a plugin scan writes, named here and owned elsewhere: the contract names them so the writers and readers cite one word, and keeps no shape of its own for them. */
#define OMX_SCAN_DOCUMENTS(X) \
    X(0u, "CLAP_SCAN_DOCUMENT", CLAP_SCAN_DOCUMENT) X(1u, "FIELD_DUMP", FIELD_DUMP)

/* SCAN_FIELD_SCOPES (scan/scan.json) */
#define OMX_SCAN_FIELD_SCOPES_PLUGIN "plugin" ///< the plugin as a whole
/** The source sentence (English) of OMX_SCAN_FIELD_SCOPES_PLUGIN. */
#define OMX_SCAN_FIELD_SCOPES_PLUGIN_TEXT_EN "The plugin as a whole."
#define OMX_SCAN_FIELD_SCOPES_PARAM "param" ///< a CLAP parameter, indexed in get_info order
/** The source sentence (English) of OMX_SCAN_FIELD_SCOPES_PARAM. */
#define OMX_SCAN_FIELD_SCOPES_PARAM_TEXT_EN "A CLAP parameter, indexed in get_info order."
#define OMX_SCAN_FIELD_SCOPES_AUDIO_IN "audio_in" ///< an audio input port, indexed
/** The source sentence (English) of OMX_SCAN_FIELD_SCOPES_AUDIO_IN. */
#define OMX_SCAN_FIELD_SCOPES_AUDIO_IN_TEXT_EN "An audio input port, indexed."
#define OMX_SCAN_FIELD_SCOPES_AUDIO_OUT "audio_out" ///< an audio output port, indexed
/** The source sentence (English) of OMX_SCAN_FIELD_SCOPES_AUDIO_OUT. */
#define OMX_SCAN_FIELD_SCOPES_AUDIO_OUT_TEXT_EN "An audio output port, indexed."
#define OMX_SCAN_FIELD_SCOPES_NOTE_IN "note_in" ///< a note input port, indexed
/** The source sentence (English) of OMX_SCAN_FIELD_SCOPES_NOTE_IN. */
#define OMX_SCAN_FIELD_SCOPES_NOTE_IN_TEXT_EN "A note input port, indexed."
#define OMX_SCAN_FIELD_SCOPES_NOTE_OUT "note_out" ///< a note output port, indexed
/** The source sentence (English) of OMX_SCAN_FIELD_SCOPES_NOTE_OUT. */
#define OMX_SCAN_FIELD_SCOPES_NOTE_OUT_TEXT_EN "A note output port, indexed."
#define OMX_SCAN_FIELD_SCOPES_PORT "port" ///< an LV2 port, indexed by lv2:index
/** The source sentence (English) of OMX_SCAN_FIELD_SCOPES_PORT. */
#define OMX_SCAN_FIELD_SCOPES_PORT_TEXT_EN "An LV2 port, indexed by its lv2:index."
#define OMX_SCAN_FIELD_SCOPES_PANEL "panel" ///< the panel description of a plugin that serves org.openmixer.panel-description/1: its family and fingerprint
/** The source sentence (English) of OMX_SCAN_FIELD_SCOPES_PANEL. */
#define OMX_SCAN_FIELD_SCOPES_PANEL_TEXT_EN "The panel description of a plugin that serves org.openmixer.panel-description/1: its family and its fingerprint."
#define OMX_SCAN_FIELD_SCOPES_SECTION "section" ///< a section of the panel description, indexed
/** The source sentence (English) of OMX_SCAN_FIELD_SCOPES_SECTION. */
#define OMX_SCAN_FIELD_SCOPES_SECTION_TEXT_EN "A section of the panel description, indexed."
#define OMX_SCAN_FIELD_SCOPES_CONTROL "control" ///< a control of the panel description, indexed
/** The source sentence (English) of OMX_SCAN_FIELD_SCOPES_CONTROL. */
#define OMX_SCAN_FIELD_SCOPES_CONTROL_TEXT_EN "A control of the panel description, indexed."
#define OMX_SCAN_FIELD_SCOPES_ROLE "role" ///< a role of the panel description, indexed
/** The source sentence (English) of OMX_SCAN_FIELD_SCOPES_ROLE. */
#define OMX_SCAN_FIELD_SCOPES_ROLE_TEXT_EN "A role of the panel description, indexed."
#define OMX_SCAN_FIELD_SCOPES_DISPLAY "display" ///< a display of the panel description, indexed
/** The source sentence (English) of OMX_SCAN_FIELD_SCOPES_DISPLAY. */
#define OMX_SCAN_FIELD_SCOPES_DISPLAY_TEXT_EN "A display of the panel description, indexed."
#define OMX_SCAN_FIELD_SCOPES_PLACEMENT_DEFAULT "placement_default" ///< a per-placement come-up value of the panel description, indexed
/** The source sentence (English) of OMX_SCAN_FIELD_SCOPES_PLACEMENT_DEFAULT. */
#define OMX_SCAN_FIELD_SCOPES_PLACEMENT_DEFAULT_TEXT_EN "A per-placement come-up value of the panel description, indexed."
/** The number of words of SCAN_FIELD_SCOPES. */
#define OMX_SCAN_FIELD_SCOPES_COUNT 13u
/** The words of SCAN_FIELD_SCOPES in their declared order, as a C initializer list. */
#define OMX_SCAN_FIELD_SCOPES_INIT { "plugin", "param", "audio_in", "audio_out", "note_in", "note_out", "port", "panel", "section", "control", "role", "display", "placement_default" }
/** Expands `X(code, "word", NAME)` once per word of SCAN_FIELD_SCOPES, in order, the code being its place in the order. The scopes of a field dump record, as written before the first TAB; an indexed scope is followed by `:<index>`. Named here, owned by their writers: omx-clap-core's scan (docs/scan.md there) and plugin-hostd's field dump (docs/formats.md there) keep the code that writes them. */
#define OMX_SCAN_FIELD_SCOPES(X) \
    X(0u, "plugin", PLUGIN) X(1u, "param", PARAM) X(2u, "audio_in", AUDIO_IN) X(3u, "audio_out", AUDIO_OUT) \
    X(4u, "note_in", NOTE_IN) X(5u, "note_out", NOTE_OUT) X(6u, "port", PORT) X(7u, "panel", PANEL) \
    X(8u, "section", SECTION) X(9u, "control", CONTROL) X(10u, "role", ROLE) X(11u, "display", DISPLAY) \
    X(12u, "placement_default", PLACEMENT_DEFAULT)

#endif /* SCAN_VOCABULARY_H */
