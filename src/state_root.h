/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * This file is part of omx-clap-host.
 *
 * omx-clap-host is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * omx-clap-host is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with omx-clap-host.  If not, see <http://www.gnu.org/licenses/>.
 *
 * Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
 */

/** @file
 * @brief The state root a host enters at start: made private, pruned of a dead instance's leftovers, and the
 * process's cwd moved into it. */

/*
 * state_root.h: a process-wide directory, <state root>/lv2-<pid>-<n> an LV2 instance's own (lv2_instance.c) and
 * whatever else a hosted plugin writes relative to the host's cwd (clap-protoplug). state_root_enter is the one entry
 * point: it makes the root at 0700 if it is not there yet, brings an existing one that is looser to 0700 as well,
 * removes every lv2-<pid>-<n> directory and lv2-<pid>-<n>.saved copy whose pid no longer answers (a crash or a kill-9
 * leaves them; the next host on the same root, any pid, prunes them before any instance of its own is named), and
 * chdir()s the process into it. The pieces are static inline, each small enough to call on its own from a test with no
 * link beyond libc.
 */

#ifndef OMX_STATE_ROOT_H
#define OMX_STATE_ROOT_H

#include <dirent.h>
#include <errno.h>
#include <ftw.h>
#include <limits.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

/* `path`, and every directory component above it, made with `mode` where it does not exist yet; an existing component
 * that is a directory already is kept as it is, its mode untouched. 0, or -1 for a component that cannot be made or is
 * not a directory */
static inline int state_root_mkdir_p(const char *path, mode_t mode)
{
    char tmp[PATH_MAX];
    size_t n = strlen(path), i;

    if (n == 0 || n >= sizeof(tmp))
        return -1;
    memcpy(tmp, path, n + 1);
    for (i = 1; i <= n; i++)
    {
        struct stat st;

        if (tmp[i] != '/' && tmp[i] != '\0')
            continue;
        tmp[i] = '\0';
        if (mkdir(tmp, mode) != 0 && (errno != EEXIST || stat(tmp, &st) != 0 || !S_ISDIR(st.st_mode)))
            return -1;
        tmp[i] = path[i];
    }
    return 0;
}

/* true for a pid no process answers to any more: kill(pid, 0) says so with ESRCH; any other errno (EPERM: a live pid
 * owned by someone else, say) is read as alive, so a root shared with another user's host prunes only what it is sure
 * of */
static inline int state_root_pid_dead(long pid)
{
    return pid > 0 && kill((pid_t)pid, 0) != 0 && errno == ESRCH;
}

/* `name`'s pid, for an entry shaped lv2-<pid>-<n> or lv2-<pid>-<n>.saved (lv2_instance.c's naming); 0 for anything
 * else, so a 0 pid (never a real one) never matches */
static inline long state_root_dead_candidate_pid(const char *name)
{
    char *end;
    long pid;

    if (strncmp(name, "lv2-", 4) != 0)
        return 0;
    pid = strtol(name + 4, &end, 10);
    return pid > 0 && *end == '-' ? pid : 0;
}

static inline int state_root_remove_one(const char *path, const struct stat *st, int flag, struct FTW *ftw)
{
    (void)st; (void)flag; (void)ftw;
    return remove(path);
}

/* every lv2-<pid>-<n> directory and lv2-<pid>-<n>.saved copy directly under `root` whose pid answers no more */
static inline void state_root_prune_dead(const char *root)
{
    DIR *d = opendir(root);
    struct dirent *e;

    if (!d)
        return;
    while ((e = readdir(d)) != NULL)
    {
        char path[PATH_MAX];

        if (!state_root_pid_dead(state_root_dead_candidate_pid(e->d_name)))
            continue;
        if (snprintf(path, sizeof(path), "%s/%s", root, e->d_name) < (int)sizeof(path))
            nftw(path, state_root_remove_one, 16, FTW_DEPTH | FTW_PHYS);
    }
    closedir(d);
}

/* the state root made at 0700 (private: a plugin's saved state is the operator's alone), a dead instance's leftovers
 * pruned, and the process's cwd moved into it. 0, or -1 for a root that cannot be made, chmod'd or entered: the caller
 * keeps its start cwd and offers no state root in that case */
static inline int state_root_enter(const char *root)
{
    if (state_root_mkdir_p(root, 0700) != 0)
        return -1;
    chmod(root, 0700);         /* a root an earlier, less strict version made is brought to 0700 as well */
    state_root_prune_dead(root);
    return chdir(root);
}

#endif /* OMX_STATE_ROOT_H */
