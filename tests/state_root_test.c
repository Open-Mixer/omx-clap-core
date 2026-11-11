/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * This file is part of omx-clap-host.
 *
 * Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
 */

/*
 * state_root_test: src/state_root.h on its own. mkdir_p makes a nested root at the mode given and leaves an existing
 * component as it is; pid_dead reads a live pid as alive and an exited one as dead once it is reaped; a name shaped
 * lv2-<pid>-<n> or lv2-<pid>-<n>.saved gives up its pid, anything else none; prune_dead removes a dead pid's directory
 * and its .saved copy, recursively, and leaves a live pid's and a malformed name alone; enter makes the root at 0700,
 * brings a looser existing one to 0700, prunes it, and moves the process into it.
 */

#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <unistd.h>

#include "state_root.h"

// every path built below is a short, fixed fixture name under a PATH_MAX-sized root: never near PATH_MAX in practice,
// but gcc cannot see that through state_root_mkdir_p's `const char *` and flags a truncation it cannot rule out
#pragma GCC diagnostic ignored "-Wformat-truncation"

static int failures;

#define CHECK(cond, ...)                                                                                              \
    do {                                                                                                              \
        if (!(cond)) {                                                                                                \
            printf("FAIL " __VA_ARGS__);                                                                              \
            printf("\n");                                                                                             \
            failures++;                                                                                               \
        }                                                                                                             \
    } while (0)

static mode_t mode_of(const char *path)
{
    struct stat st;

    if (stat(path, &st) != 0)
        return (mode_t)-1;
    return st.st_mode & 07777;
}

static int is_dir(const char *path)
{
    struct stat st;

    return stat(path, &st) == 0 && S_ISDIR(st.st_mode);
}

/* a pid no process answers to any more, without reusing one still live: a forked child, exited and reaped */
static long dead_pid(void)
{
    pid_t p = fork();

    if (p == 0)
        _exit(0);
    waitpid(p, NULL, 0);
    return (long)p;
}

static void test_mkdir_p(const char *base)
{
    char nested[PATH_MAX], existing[PATH_MAX];

    snprintf(nested, sizeof(nested), "%s/a/b/c", base);
    CHECK(state_root_mkdir_p(nested, 0700) == 0, "mkdir_p refused a makeable nested path");
    CHECK(is_dir(nested), "mkdir_p did not make %s", nested);
    CHECK(mode_of(nested) == 0700, "mkdir_p made %s at %o, not 0700", nested, (unsigned)mode_of(nested));

    snprintf(existing, sizeof(existing), "%s/a", base);
    CHECK(state_root_mkdir_p(nested, 0700) == 0, "mkdir_p refused a path already made");
    CHECK(mode_of(existing) == 0700, "mkdir_p's second call changed the mode of an existing component");

    // a regular file in the way of a directory component: refused, not clobbered
    {
        char blocked[PATH_MAX], under[PATH_MAX];
        FILE *f;

        snprintf(blocked, sizeof(blocked), "%s/blocked", base);
        f = fopen(blocked, "w");
        CHECK(f != NULL, "could not make the file %s to block mkdir_p with", blocked);
        if (f)
            fclose(f);
        snprintf(under, sizeof(under), "%s/blocked/under", base);
        CHECK(state_root_mkdir_p(under, 0700) != 0, "mkdir_p walked through a file as if it were a directory");
    }
}

static void test_pid_dead(void)
{
    long dead = dead_pid();

    CHECK(!state_root_pid_dead((long)getpid()), "this live process read as dead");
    CHECK(state_root_pid_dead(dead), "an exited, reaped pid (%ld) read as alive", dead);
    CHECK(!state_root_pid_dead(0), "pid 0 read as a dead candidate");
    CHECK(!state_root_pid_dead(-1), "a negative pid read as a dead candidate");
}

static void test_dead_candidate_pid(void)
{
    CHECK(state_root_dead_candidate_pid("lv2-1234-5") == 1234, "lv2-1234-5 did not give up pid 1234");
    CHECK(state_root_dead_candidate_pid("lv2-1234-5.saved") == 1234, "lv2-1234-5.saved did not give up pid 1234");
    CHECK(state_root_dead_candidate_pid("notlv2-1234-5") == 0, "a name with no lv2- prefix gave up a pid");
    CHECK(state_root_dead_candidate_pid("lv2-abc-5") == 0, "a non-numeric pid field gave up a pid");
    CHECK(state_root_dead_candidate_pid("lv2-1234") == 0, "a name with no serial past the pid gave up a pid");
    CHECK(state_root_dead_candidate_pid("lv2-") == 0, "lv2- alone gave up a pid");
}

static void touch(const char *path)
{
    FILE *f = fopen(path, "w");

    if (f)
        fclose(f);
}

static void test_prune_dead(const char *base)
{
    char root[PATH_MAX], live_dir[PATH_MAX], dead_dir[PATH_MAX], dead_saved[PATH_MAX], dead_saved_file[PATH_MAX],
         malformed[PATH_MAX];
    long live = (long)getpid(), dead = dead_pid();

    snprintf(root, sizeof(root), "%s/prune", base);
    CHECK(state_root_mkdir_p(root, 0700) == 0, "could not make %s to prune-test in", root);

    snprintf(live_dir, sizeof(live_dir), "%s/lv2-%ld-1", root, live);
    snprintf(dead_dir, sizeof(dead_dir), "%s/lv2-%ld-2", root, dead);
    snprintf(dead_saved, sizeof(dead_saved), "%s/lv2-%ld-2.saved", root, dead);
    snprintf(dead_saved_file, sizeof(dead_saved_file), "%s/kept.preset", dead_saved);
    snprintf(malformed, sizeof(malformed), "%s/lv2-not-a-pid-9", root);

    CHECK(state_root_mkdir_p(live_dir, 0700) == 0, "could not make the live-pid fixture directory");
    CHECK(state_root_mkdir_p(dead_saved, 0700) == 0, "could not make the dead-pid .saved fixture directory");
    CHECK(state_root_mkdir_p(dead_dir, 0700) == 0, "could not make the dead-pid fixture directory");
    CHECK(state_root_mkdir_p(malformed, 0700) == 0, "could not make the malformed-name fixture directory");
    touch(dead_saved_file);

    state_root_prune_dead(root);

    CHECK(is_dir(live_dir), "prune_dead removed a live pid's directory");
    CHECK(!is_dir(dead_dir), "prune_dead left a dead pid's directory");
    CHECK(!is_dir(dead_saved), "prune_dead left a dead pid's .saved directory");
    CHECK(is_dir(malformed), "prune_dead removed a directory whose name is not a pid at all");
}

static void test_enter(const char *base)
{
    char root[PATH_MAX], loose[PATH_MAX], cwd_before[PATH_MAX], dead_dir[PATH_MAX];
    int saved_fd = open(".", O_RDONLY);
    long dead = dead_pid();

    CHECK(saved_fd >= 0, "could not keep the test's own cwd open to restore it");
    CHECK(getcwd(cwd_before, sizeof(cwd_before)) != NULL, "getcwd failed before state_root_enter");

    // a root not yet there: made at 0700 and entered
    snprintf(root, sizeof(root), "%s/enter/state", base);
    CHECK(state_root_enter(root) == 0, "state_root_enter refused a makeable new root");
    CHECK(mode_of(root) == 0700, "state_root_enter made the root at %o, not 0700", (unsigned)mode_of(root));
    {
        char cwd_after[PATH_MAX], real_root[PATH_MAX];

        CHECK(getcwd(cwd_after, sizeof(cwd_after)) != NULL, "getcwd failed after state_root_enter");
        CHECK(realpath(root, real_root) != NULL, "realpath of the entered root failed");
        CHECK(strcmp(cwd_after, real_root) == 0, "state_root_enter left the cwd at %s, not the root %s", cwd_after, real_root);
    }
    if (saved_fd >= 0)
    {
        CHECK(fchdir(saved_fd) == 0, "could not restore the test's own cwd");
        close(saved_fd);
    }

    // an existing root at a looser mode, with a dead pid's leftovers in it: brought to 0700 and pruned, in one call
    snprintf(loose, sizeof(loose), "%s/loose", base);
    CHECK(state_root_mkdir_p(loose, 0755) == 0, "could not make the loose-mode fixture root");
    CHECK(mode_of(loose) == 0755, "the loose-mode fixture was not made at 0755 to begin with");
    snprintf(dead_dir, sizeof(dead_dir), "%s/lv2-%ld-1", loose, dead);
    CHECK(state_root_mkdir_p(dead_dir, 0700) == 0, "could not make the dead-pid fixture under the loose root");
    saved_fd = open(".", O_RDONLY);
    CHECK(state_root_enter(loose) == 0, "state_root_enter refused an existing, looser root");
    CHECK(mode_of(loose) == 0700, "state_root_enter left an existing root at %o, not 0700", (unsigned)mode_of(loose));
    CHECK(!is_dir(dead_dir), "state_root_enter did not prune a dead pid's leftovers in an existing root");
    if (saved_fd >= 0)
    {
        fchdir(saved_fd);
        close(saved_fd);
    }
    (void)cwd_before;
}

int main(void)
{
    char rel[] = "build/state-root-test.XXXXXX";
    char base[PATH_MAX];

    if (!mkdtemp(rel))
    {
        perror("mkdtemp");
        return 1;
    }
    // absolute, so a path built from it still resolves once a test below moves the process's own cwd into it
    if (!realpath(rel, base))
    {
        perror("realpath");
        return 1;
    }
    test_mkdir_p(base);
    test_pid_dead();
    test_dead_candidate_pid();
    test_prune_dead(base);
    test_enter(base);

    if (failures)
    {
        printf("%d check(s) failed\n", failures);
        return 1;
    }
    printf("ok   state root: made at 0700, a dead instance's leftovers pruned, the host's cwd moved into it\n");
    return 0;
}
