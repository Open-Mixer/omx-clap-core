#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Pau Aliagas <linuxnow@gmail.com>
"""The replies this package declares, typed and named (omx-clap-core#49): OMX_CLAP_REPLIES of the omx-clap domain
(contract.d/omx-clap/omx-clap.json) types each reply whose verb omx-clap-host answers, in plugin-hostd-protocol's reply form
(plugin-hostd-protocol#19): resp 0 or resp count, then name:type for each field, each type one of the protocol table's
arg_types or one OMX_CLAP_REPLY_TYPES declares, once. And the code that writes each reply names the same fields: the
X(name, conversion) rows of its HOST_FIELDS_<VERB> in src/host_verbs.h, whose HOST_FIELDS_FMT is the builder's format.
The verbs are plugin-hostd-protocol's since ruling R5: the items VERB_ITEMS of its domain plugin-hostd-protocol (--verbs).

  tests/host-replies-check.py --table <plugin-hostd-protocol.json> --verbs <domain plugin-hostd-protocol.json> [--root <dir>] [--self-test]

Held, one failure line each:
  - every verb of VERB_ITEMS whose reply has a field (a <placeholder>) is typed in OMX_CLAP_REPLIES, or by the protocol
    (its table's reply_forms, or PROTOCOL_OWNED below until the table types it), or is PENDING; a verb typed here and by
    the protocol is a reply with two homes;
  - every key of OMX_CLAP_REPLIES is a verb of VERB_ITEMS, and its typed reply, each name:type written <name> and resp
    count written resp <count>, is word for word the verb's x-reply;
  - every type is an arg_type of the table or an own type; an own type the table also declares has two homes, an own
    type no reply names is dead, and an own type's pattern compiles and has its spelling (x-docs);
  - every reply OMX_CLAP_REPLIES types with fields has its HOST_FIELDS_<VERB>(X) in src/host_verbs.h, and every
    HOST_FIELDS_<VERB>(X) there is held to its reply's form, wherever that is typed: OMX_CLAP_REPLIES, or the protocol
    table's one reply_form of the verb (note_input, note_drops and note_out_drops are the table's, the coordinator's
    ruling on R5: the code reads their names and types from there, never from a copy here). Its names, in order, the
    form's, each conversion one the field's type is written with (TYPE_CONVERSIONS), and a source under src/ writes the
    reply with HOST_FIELDS_FMT(HOST_FIELDS_<VERB>); a HOST_FIELDS_ of a verb typed nowhere is a failure too.
--self-test breaks a copy of the inputs once per arm, each of which must fail. Exit 0 held; 1 a failure; 2 usage.
"""
import argparse
import copy
import glob
import json
import os
import re
import sys

DOMAIN = 'contract.d/omx-clap/omx-clap.json'
HEADER = 'src/host_verbs.h'
REPLIES = 'OMX_CLAP_REPLIES'
TYPES = 'OMX_CLAP_REPLY_TYPES'
# the verbs omx-clap-host answers by its own handlers, in plugin-hostd-protocol's domain plugin-hostd-protocol (ruling R5
# moved them there, word for word, from this tree's domain omx-clap)
VERB_ITEMS = ('PLUGIN_HOSTD_PROTOCOL_SHARED_VERBS', 'PLUGIN_HOSTD_PROTOCOL_CLAP_HOST_VERBS')
# the replies whose shape plugin-hostd-protocol declares, by verb title, and the file that holds it: the verbs of
# mod-host.h whose reply its host-dispatch writes from a struct it declares, and property_list, whose family the
# protocol's PHD_REPLY_ARGS types; their typed form is the protocol's to give
PROTOCOL_OWNED = {
    'remotePages': 'include/host-dispatch.h (host_plugin_info_t.remote_pages, the count the dispatcher answers)',
    'remotePageGet': 'include/host-dispatch.h (host_remote_page_t, the fields the dispatcher writes)',
    'paramInfo': 'include/host-dispatch.h (host_param_info_t, the fields the dispatcher writes)',
    'propertyList': 'include/plugin-hostd/protocol.h (PHD_REPLY_ARGS, which types property_info and property_get)',
}
# this package's replies not typed yet, each with what it needs
PENDING = {
    'audioPorts': 'an optional literal word (dry) and a repeated port record whose optional parts no arg_type spells',
}
# the conversions a builder writes a field of a type with: a type absent here is written as a word, %s
TYPE_CONVERSIONS = {'uint': {'%u'}, 'int': {'%d', '%i'}}
FIELD = re.compile(r'^([a-z][a-z0-9_]*):([a-z][a-z0-9-]*|[a-z][A-Za-z0-9]*)$')
DEFINE = re.compile(r'^[ \t]*#define[ \t]+HOST_FIELDS_([A-Z0-9_]+)\(X\)((?:[^\n]*\\\n)*[^\n]*)', re.M)
ROW = re.compile(r'X\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*"([^"]*)"\s*\)')


def snake(title):
    return re.sub(r'([A-Z])', r'_\1', title).upper()


def load(root, table_path, verbs_path):
    with open(os.path.join(root, DOMAIN)) as f:
        domain = json.load(f)
    with open(verbs_path) as f:
        verbs = json.load(f)
    with open(table_path) as f:
        table = json.load(f)
    with open(os.path.join(root, HEADER)) as f:
        header = f.read()
    sources = {}
    for path in sorted(glob.glob(os.path.join(root, 'src', '*.c'))):
        with open(path, encoding='utf-8', errors='replace') as f:
            sources[os.path.relpath(path, root)] = f.read()
    return {'domain': domain, 'verbs': verbs, 'table': table, 'header': header, 'sources': sources}


def parse(line):
    """(resp, [(name, type)]) of a typed reply, or a string saying what is wrong with it"""
    words = line.split(' ')
    if len(words) < 2 or words[0] != 'resp' or words[1] not in ('0', 'count'):
        return 'it is not resp 0 or resp count and its fields'
    fields = []
    for w in words[2:]:
        m = FIELD.match(w)
        if not m:
            return 'its word %r is not name:type' % w
        fields.append((m.group(1), m.group(2)))
    names = [n for n, _ in fields]
    if len(set(names)) != len(names):
        return 'a name is given twice'
    return words[1], fields


def spoken(resp, fields):
    """the typed reply as the verb's x-reply writes it"""
    return ' '.join(['resp', '0' if resp == '0' else '<count>'] + ['<%s>' % n for n, _ in fields])


def problems(inp):
    out = []
    schemas = inp['domain']['components']['schemas']
    verbs = {}
    for name in VERB_ITEMS:
        item = inp['verbs']['components']['schemas'].get(name)
        if item is None or item.get('x-kind') != 'verbs':
            out.append('%s: no verbs item in plugin-hostd-protocol\'s domain plugin-hostd-protocol' % name)
            continue
        for v in item['oneOf']:
            verbs[v['title']] = v
    replies = schemas.get(REPLIES, {}).get('x-value', {})
    own = schemas.get(TYPES, {}).get('x-value', {})
    spellings = schemas.get(TYPES, {}).get('x-docs', {})
    arg_types = inp['table'].get('arg_types', {})
    protocol_typed = {c['verb'] for c in inp['table'].get('commands', []) if c.get('reply_forms')}
    # the table's form of each verb it types with one plain form (no repeat, no tail): (resp, [(name, type)])
    table_forms = {}
    for c in inp['table'].get('commands', []):
        rf = c.get('reply_forms') or []
        if len(rf) == 1 and not rf[0].get('repeat') and not rf[0].get('tail'):
            names, args = rf[0].get('names', []), rf[0].get('args', [])
            if len(names) != len(args):
                out.append('%s: the protocol table\'s reply_form names %d fields and types %d' % (c['verb'], len(names),
                                                                                                len(args)))
                continue
            table_forms[c['verb']] = (rf[0].get('resp'), list(zip(names, args)))

    # every reply with a field has one home
    for title, v in verbs.items():
        word, typed_here = v['const'], title in replies
        by_protocol = word in protocol_typed or title in PROTOCOL_OWNED
        if typed_here and by_protocol:
            where = 'the protocol table types it' if word in protocol_typed else PROTOCOL_OWNED[title]
            out.append('%s: typed in %s and by the protocol (%s): a reply has one home' % (word, REPLIES, where))
        elif typed_here and title in PENDING:
            out.append('%s: typed in %s and still PENDING: drop it from PENDING' % (word, REPLIES))
        elif '<' in v.get('x-reply', '') and not (typed_here or by_protocol or title in PENDING):
            out.append('%s: its reply %r is typed nowhere: declare it as %s.%s' % (word, v['x-reply'], REPLIES, title))

    # every typed reply is a verb's, and its words are the verb's x-reply
    forms = {}
    for title, line in replies.items():
        if title not in verbs:
            out.append('%s.%s: no verb omx-clap-host answers is titled %s' % (REPLIES, title, title))
            continue
        word = verbs[title]['const']
        form = parse(line)
        if isinstance(form, str):
            out.append('%s: %s.%s %r: %s' % (word, REPLIES, title, line, form))
            continue
        forms[title] = form
        if spoken(*form) != verbs[title].get('x-reply'):
            out.append('%s: %s.%s says %r, its x-reply %r: the words disagree with the form'
                       % (word, REPLIES, title, spoken(*form), verbs[title].get('x-reply')))
        for name, kind in form[1]:
            if kind not in arg_types and kind not in own:
                out.append('%s: the field %s has the type %s, which neither the protocol table\'s arg_types nor %s '
                           'declares' % (word, name, kind, TYPES))

    # every own type declared once, named, with its spelling
    used = {k for _, fields in forms.values() for _, k in fields}
    for kind, pattern in own.items():
        if kind in arg_types:
            out.append('%s.%s: the protocol table declares the type %s: a type has one home' % (TYPES, kind, kind))
        if kind not in used:
            out.append('%s.%s: no reply names the type %s' % (TYPES, kind, kind))
        if not spellings.get(kind):
            out.append('%s.%s: no spelling in its x-docs' % (TYPES, kind))
        try:
            re.compile(pattern)
        except re.error as e:
            out.append('%s.%s: its pattern %r does not compile: %s' % (TYPES, kind, pattern, e))

    # the code names the fields it writes, as the declaration types them: OMX_CLAP_REPLIES, or the protocol table
    rows = {}
    for m in DEFINE.finditer(inp['header']):
        rows[m.group(1)] = ROW.findall(m.group(2))
    titled = {snake(t): t for t in verbs}
    held = {}  # title -> (fields, where they are typed)
    for title, (_, fields) in forms.items():
        if fields:
            held[title] = (fields, '%s.%s' % (REPLIES, title))
    for title, v in verbs.items():
        form = table_forms.get(v['const'])
        if form and form[1] and title not in forms:
            if spoken(*form) != v.get('x-reply'):
                out.append('%s: the protocol table\'s reply_form says %r, its x-reply %r: the words disagree with the form'
                           % (v['const'], spoken(*form), v.get('x-reply')))
            if snake(title) in rows:
                held[title] = (form[1], 'the protocol table\'s reply_form')
    for macro in rows:
        title = titled.get(macro)
        if title not in held:
            out.append('%s: HOST_FIELDS_%s names the fields of a reply %s and the protocol table type none of'
                       % (HEADER, macro, REPLIES))
    for title, (fields, where) in held.items():
        word, macro = verbs[title]['const'], snake(title)
        if macro not in rows:
            out.append('%s: %s has no HOST_FIELDS_%s(X), the fields its reply is written with' % (word, HEADER, macro))
            continue
        code = rows[macro]
        for i in range(max(len(code), len(fields))):
            have = code[i][0] if i < len(code) else None
            want = fields[i][0] if i < len(fields) else None
            if have != want:
                out.append('%s: field %d is %s in HOST_FIELDS_%s of %s, %s in %s'
                           % (word, i + 1, have or 'missing', macro, HEADER, want or 'missing', where))
            elif code[i][1] not in TYPE_CONVERSIONS.get(fields[i][1], {'%s'}):
                out.append('%s: the field %s is written %s, which a %s is not written with (%s)'
                           % (word, have, code[i][1], fields[i][1],
                              ' or '.join(sorted(TYPE_CONVERSIONS.get(fields[i][1], {'%s'})))))
        use = re.compile(r'HOST_FIELDS_FMT\(\s*HOST_FIELDS_%s\s*\)' % macro)
        if not any(use.search(text) for text in inp['sources'].values()):
            out.append('%s: no source under src/ writes its reply with HOST_FIELDS_FMT(HOST_FIELDS_%s)' % (word, macro))
    return out


def self_test(inp):
    def domain(fn):
        def arm(i):
            fn(i['domain']['components']['schemas'])
        return arm

    def protocol(fn):
        def arm(i):
            fn(i['verbs']['components']['schemas'])
        return arm

    def table(verb, fn):
        def arm(i):
            hit = [c for c in i['table']['commands'] if c['verb'] == verb and c.get('reply_forms')]
            assert hit, verb
            fn(hit[0])
        return arm

    def header(old, new):
        def arm(i):
            assert old in i['header'], old
            i['header'] = i['header'].replace(old, new, 1)
        return arm

    def sources(old, new):
        def arm(i):
            hit = [p for p, t in i['sources'].items() if old in t]
            assert hit, old
            i['sources'][hit[0]] = i['sources'][hit[0]].replace(old, new)
        return arm

    def typed(s, title, line):
        s[REPLIES]['x-value'][title] = line

    arms = [  # what, the change, a word of the failure it must raise
        ('a reply undeclared (note_drops, its reply_forms dropped from the table)',
         table('note_drops', lambda c: c.pop('reply_forms')), 'note_drops: its reply'),
        ('a reply undeclared (idle_hold)', domain(lambda s: s[REPLIES]['x-value'].pop('idleHold')),
         'idle_hold: its reply'),
        ('a reply the protocol table types typed here again (note_drops)',
         domain(lambda s: typed(s, 'noteDrops', 'resp 0 notes:uint releases:uint sysex:uint unmappable:uint')),
         'note_drops: typed in OMX_CLAP_REPLIES and by the protocol'),
        ('a field renamed in the table (note_out_drops)',
         table('note_out_drops', lambda c: c['reply_forms'][0]['names'].__setitem__(0, 'drops')),
         'field 1 is dropped in HOST_FIELDS_NOTE_OUT_DROPS of src/host_verbs.h, drops in the protocol table'),
        ('a type changed in the table (note_drops notes as word)',
         table('note_drops', lambda c: c['reply_forms'][0]['args'].__setitem__(0, 'word')),
         'the field notes is written %u, which a word is not written with'),
        ('a field renamed in the code (notes)', header('X(notes,', 'X(note_count,'),
         'field 1 is note_count in HOST_FIELDS_NOTE_DROPS'),
        ('a field dropped from the code (code of idle_hold)', header(' X(code, "%s")', ''),
         'field 5 is missing in HOST_FIELDS_IDLE_HOLD'),
        ('a conversion the type is not written with (port as %u)', header('X(port, "%s")', 'X(port, "%u")'),
         'the field port is written %u'),
        ('a reply written without its fields (note_out_drops)',
         sources('HOST_FIELDS_FMT(HOST_FIELDS_NOTE_OUT_DROPS)', '"resp 0 %u %u %u"'),
         'HOST_FIELDS_FMT(HOST_FIELDS_NOTE_OUT_DROPS)'),
        ('the words disagree with the form (x-reply renamed)',
         protocol(lambda s: s['PLUGIN_HOSTD_PROTOCOL_CLAP_HOST_VERBS']['oneOf'][3].update(
             {'x-reply': 'resp 0 <notes> <releases> <sysex> <lost>'})),
         'the words disagree with the form'),
        ('a type declared nowhere',
         domain(lambda s: typed(s, 'idleHold', 'resp 0 target:jack-port held:hold aggregate:microseconds active:uint '
                                               'code:word')),
         'the type jack-port, which neither'),
        ('an own type the protocol declares',
         domain(lambda s: (s[TYPES]['x-value'].update({'uint': '[0-9]+'}),
                           s[TYPES]['x-docs'].update({'uint': 'a count'}))),
         'the protocol table declares the type uint'),
        ('an own type no reply names', domain(lambda s: (s[TYPES]['x-value'].update({'spare': '[a-z]+'}),
                                                          s[TYPES]['x-docs'].update({'spare': 'a spare word'}))),
         'no reply names the type spare'),
        ('an own type with no spelling', domain(lambda s: s[TYPES]['x-docs'].pop('hold')), 'hold: no spelling'),
        ('a reply the protocol owns typed here (param_info)',
         domain(lambda s: typed(s, 'paramInfo', 'resp 0 unit:word scale:word min:number max:number default:number '
                                                'step:number stable_symbol:word')),
         'param_info: typed in OMX_CLAP_REPLIES and by the protocol'),
        ('a reply the protocol table types typed here (property_get)',
         domain(lambda s: typed(s, 'propertyGet', 'resp 0 value:quoted-escaped')),
         'property_get: typed in OMX_CLAP_REPLIES and by the protocol'),
        ('a pending reply typed (audio_ports)', domain(lambda s: typed(s, 'audioPorts', 'resp 0 port:word')),
         'still PENDING'),
        ('a key that is no verb', domain(lambda s: typed(s, 'noteDropz', 'resp 0 notes:uint')),
         'no verb omx-clap-host answers is titled noteDropz'),
        ('a typed reply that is not resp 0 or resp count', domain(lambda s: typed(s, 'idleHold', 'resp 1 target:hold')),
         'it is not resp 0 or resp count'),
        ('fields of a reply typed nowhere in the code',
         header('#define HOST_FIELDS_NOTE_INPUT(X)', '#define HOST_FIELDS_ALL_NOTES_OFF(X) X(channel, "%u")\n'
                                                     '#define HOST_FIELDS_NOTE_INPUT(X)'),
         'HOST_FIELDS_ALL_NOTES_OFF names the fields'),
    ]
    missed = 0
    for what, apply, expect in arms:
        broken = copy.deepcopy(inp)
        apply(broken)
        hit = [p for p in problems(broken) if expect in p]
        if not hit:
            print('host-replies-check --self-test: %s was not refused for its own reason (%s)' % (what, expect),
                  file=sys.stderr)
            missed += 1
        else:
            print('ok   sabotage: %s: %s' % (what, hit[0]))
    if missed:
        return 1
    print('host-replies-check --self-test: %d sabotage arms, each refused' % len(arms))
    return 0


def main():
    ap = argparse.ArgumentParser(
        usage='host-replies-check.py --table <plugin-hostd-protocol.json> --verbs <domain plugin-hostd-protocol.json> '
              '[--root <dir>] [--self-test]')
    ap.add_argument('--table', required=True)
    ap.add_argument('--verbs', required=True)
    ap.add_argument('--root', default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument('--self-test', action='store_true')
    args = ap.parse_args()
    if not os.path.isfile(args.table):
        print('host-replies-check: no protocol table at %r (plugin-hostd-protocol.pc\'s table)' % args.table,
              file=sys.stderr)
        return 2
    if not os.path.isfile(args.verbs):
        print('host-replies-check: no domain plugin-hostd-protocol at %r (the verbs omx-clap-host answers, ruling R5)'
              % args.verbs, file=sys.stderr)
        return 2
    inp = load(args.root, args.table, args.verbs)
    found = problems(inp)
    for p in found:
        print('host-replies-check: %s' % p, file=sys.stderr)
    if found:
        return 1
    typed = inp['domain']['components']['schemas'][REPLIES]['x-value']
    print('host-replies-check: %d replies typed in %s (%s), each written by the fields it declares; %s the protocol\'s '
          'to type; %s pending' % (len(typed), REPLIES, ', '.join(sorted(typed)), ', '.join(sorted(PROTOCOL_OWNED)),
                                    ', '.join(sorted(PENDING))))
    return self_test(inp) if args.self_test else 0


if __name__ == '__main__':
    sys.exit(main())
