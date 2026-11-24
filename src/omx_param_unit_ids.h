/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * This file is part of omx-clap.
 *
 * omx-clap is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * omx-clap is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with omx-clap.  If not, see <http://www.gnu.org/licenses/>.
 *
 * Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
 */

#ifndef OMX_CLAP_PARAM_UNIT_IDS_H
#define OMX_CLAP_PARAM_UNIT_IDS_H
/*
 * GENERATED: DO NOT EDIT BY HAND.
 * Rendered from OMX_PARAM_CONTRACT_UNIT_IDS of contract.d/omx-param-contract: the standard unit id of each unit code of org.openmixer.param-contract/1.
 * A reader includes this header beside omx_param_units.h: the first column is the code define rendered there, the third the PARAM_UNITS const the code stands for.
 */

/** @file
 * @brief The standard unit id of each code of the parameter contract extension, one X(code, token, id) row per token. */

/** each unit code's token and the standard unit id it stands for, the const of a word of omx-contract's PARAM_UNITS */
#define OMX_PARAM_UNIT_IDS(X) \
    X(OMX_CLAP_UNIT_NONE, "none", "none") \
    X(OMX_CLAP_UNIT_S, "s", "s") \
    X(OMX_CLAP_UNIT_MS, "ms", "ms") \
    X(OMX_CLAP_UNIT_MIN, "min", "min") \
    X(OMX_CLAP_UNIT_BAR, "bar", "bar") \
    X(OMX_CLAP_UNIT_BEAT, "beat", "beat") \
    X(OMX_CLAP_UNIT_FRAME, "frame", "frames") \
    X(OMX_CLAP_UNIT_M, "m", "m") \
    X(OMX_CLAP_UNIT_CM, "cm", "cm") \
    X(OMX_CLAP_UNIT_MM, "mm", "mm") \
    X(OMX_CLAP_UNIT_KM, "km", "km") \
    X(OMX_CLAP_UNIT_INCH, "inch", "inch") \
    X(OMX_CLAP_UNIT_MILE, "mile", "mile") \
    X(OMX_CLAP_UNIT_DB, "db", "dB") \
    X(OMX_CLAP_UNIT_PC, "pc", "percent") \
    X(OMX_CLAP_UNIT_COEF, "coef", "coef") \
    X(OMX_CLAP_UNIT_HZ, "hz", "Hz") \
    X(OMX_CLAP_UNIT_KHZ, "khz", "kHz") \
    X(OMX_CLAP_UNIT_MHZ, "mhz", "MHz") \
    X(OMX_CLAP_UNIT_BPM, "bpm", "bpm") \
    X(OMX_CLAP_UNIT_OCT, "oct", "oct") \
    X(OMX_CLAP_UNIT_CENT, "cent", "cents") \
    X(OMX_CLAP_UNIT_SEMITONE12_TET, "semitone12TET", "st") \
    X(OMX_CLAP_UNIT_DEGREE, "degree", "deg") \
    X(OMX_CLAP_UNIT_MIDI_NOTE, "midiNote", "midiNote") \
    X(OMX_CLAP_UNIT_DBFS, "dbfs", "dBFS") \
    X(OMX_CLAP_UNIT_DBU, "dbu", "dBu") \
    X(OMX_CLAP_UNIT_RATIO, "ratio", "ratio") \
    X(OMX_CLAP_UNIT_LUFS, "lufs", "LUFS") \
    X(OMX_CLAP_UNIT_DB_PER_OCT, "dbPerOct", "dBPerOct") \
    X(OMX_CLAP_UNIT_DB_PER_S, "dbPerS", "dBPerS") \
    X(OMX_CLAP_UNIT_DBTP, "dbtp", "dBTP") \
    X(OMX_CLAP_UNIT_LU, "lu", "LU")

#endif /* OMX_CLAP_PARAM_UNIT_IDS_H */
