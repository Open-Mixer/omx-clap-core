/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com> */
/* The installed tree is the one the loader reads (omx-contract docs/consumer-move.md, step 6 and the recipe's test 7): `make install-contract`
 * into a scratch directory, then omx_domain_open_at() opens the scan domain there, finds the meter scope and a catalog sentence of it.
 * usage: domain_installed_test <installed contract directory> */
#include <omxcontract/omx_domain.h>

#include <stdio.h>
#include <string.h>

int main(int argc, char **argv)
{
    omx_domain *d = NULL;
    omx_domain_error err;
    omx_domain_word_info w;
    const char *text;
    int bad = 0;

    if (argc != 2)
    {
        fprintf(stderr, "usage: domain_installed_test <installed contract directory>\n");
        return 2;
    }
    if (omx_domain_open_at(argv[1], "scan", &d, &err) != 0)
    {
        fprintf(stderr, "domain_installed_test: the installed scan domain does not open at %s: %s: %s\n", argv[1], err.code, err.message);
        return 1;
    }
    if (omx_domain_word(d, "SCAN_FIELD_SCOPES", "meter", &w) != 0 || w.code != 13)
    {
        fprintf(stderr, "domain_installed_test: the installed domain has no meter word at code 13\n");
        bad = 1;
    }
    text = omx_domain_text(d, "SCAN_FIELD_SCOPES.meter", "ca");
    if (!text || strstr(text, "mesurador") == NULL)
    {
        fprintf(stderr, "domain_installed_test: the installed catalogs hold no Catalan sentence for the meter scope (%s)\n", text ? text : "NULL");
        bad = 1;
    }
    omx_domain_close(d);
    if (!bad)
        puts("domain_installed_test: the installed scan domain opens, with its meter word and its Catalan sentence");
    return bad;
}
