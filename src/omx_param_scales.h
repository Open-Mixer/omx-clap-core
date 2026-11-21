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

#ifndef OMX_PARAM_SCALES_CODES_H
#define OMX_PARAM_SCALES_CODES_H
/*
 * GENERATED: DO NOT EDIT BY HAND.
 * Rendered from OMX_CLAP_SCALE_CODES of the omx-clap-scale domain: the scale codes of org.openmixer.param-contract/1.
 * A plugin includes this header for the codes its get() reports; the key of each code is a standard scale id of omx-contract's PARAM_SCALES.
 */

/** @file
 * @brief The scale codes of the parameter contract extension, one OMX_CLAP_SCALE_ define per standard scale id. */

/** how a parameter's plain value is laid out along its position: the code is this extension's, the word a PARAM_SCALES id */
#define OMX_CLAP_SCALE_LINEAR 0u ///< the value is linear in position
#define OMX_CLAP_SCALE_LOG 1u ///< geometric in position, both bounds positive
#define OMX_CLAP_SCALE_STEPPED 2u ///< the whole numbers from min to max, CLAP_PARAM_IS_STEPPED, step 1

/** every field of the sheet as X(value, "field"), in its declared order, for a table a consumer builds at run time */
#define OMX_CLAP_PARAM_SCALES(X) \
    X(0u, "linear") X(1u, "log") X(2u, "stepped")

#endif /* OMX_PARAM_SCALES_CODES_H */
