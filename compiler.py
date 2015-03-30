#!/usr/bin/env python2.7

import os
import re
import sys
import importlib
import cStringIO
import tokenize

from common import *

def log(*xs):
    sys.stderr.write(' '.join([str(x) for x in xs]) + '\n')

# tokens:
SEMICOLON = 10
COMMA = 11
ASSIGN = 12
ARROW = 13
PAREN_OPEN  = 14
PAREN_CLOSE = 15
BRACKET_OPEN  = 16
BRACKET_CLOSE = 17
NEWLINE = 18

#COMMENT = 20

VARIABLE = 30
OFFSET_LABEL = 32
INTEGER = 33

STRING = 40


off_label = re.compile('^(:(?P<label>[a-z_][a-zA-Z0-9_-]*):)')

integer = re.compile('^(?P<num>0|-?([1-9][0-9]*))')
hex_integer = re.compile('^(?P<num>-?0x[0-9A-Fa-f]+)')

variable = re.compile(r'^(?P<var>[a-zA-Z_][a-zA-Z0-9_-]*(\.[a-zA-Z_][a-zA-Z0-9_-]*)*)')

plain_variable_full = re.compile(r'^(?P<var>[a-zA-Z_][a-zA-Z0-9_-]*)$')

def is_plain_variable(v):
    return plain_variable_full.match(v) is not None

def tokenize_offset_label(line):
    m = off_label.match(line)
    if not m:
        raise Exception("Offset label invalid: " + line)
    return (line[len(m.group(1)):], (OFFSET_LABEL, m.group('label')))

def tokenize_string(line, source):
    line = line[1:]
    s = ''

    # TODO: \u 32 bit hex
    backsmap = {'n': u'\n', 't': u'\t', 'r': u'\r', '0': u'\0'}

    while True:
        if not line:
            s += u'\n'
            line = source.readline()
            if not line:
                raise Exception("String not closed before EOF")

        c = line[0]
        line = line[1:]

        if c == '"':
            return (line, (STRING, s))

        if c == '\\':
            if not line:
                # slash at end of line means the line is suppressed
                line = source.readline()
                if not line:
                    raise Exception("String not closed before EOF")
                continue

            b = line[0]
            line = line[1:]

            if b in backsmap:
                s += backsmap[b]
            else:
                s += b
        else:
            s += c


def tokenize(source):
    tokens = []

    in_string = False

    while True:
        line = source.readline()
        if not line:
            break

        while True:
            line = line.lstrip(' \t')
            if not line:
                break

            if line[0] == '#':
                # leave a newline token
                line = '\n'

            elif line.startswith('\n'):
                tokens.append((NEWLINE, None))
                line = line[1:]

            elif line.startswith('{'):
                tokens.append((BRACKET_OPEN, None))
                line = line[1:]
            elif line.startswith('}'):
                tokens.append((BRACKET_CLOSE, None))
                line = line[1:]
            elif line.startswith('('):
                tokens.append((PAREN_OPEN, None))
                line = line[1:]
            elif line.startswith(')'):
                tokens.append((PAREN_CLOSE, None))
                line = line[1:]

            elif line.startswith(','):
                tokens.append((COMMA, None))
                line = line[1:]
            elif line.startswith(';'):
                tokens.append((SEMICOLON, None))
                line = line[1:]
            elif line.startswith('='):
                tokens.append((ASSIGN, None))
                line = line[1:]

            elif line.startswith('->'):
                tokens.append((ARROW, None))
                line = line[2:]

            elif line.startswith(':'):
                (line, tok) = tokenize_offset_label(line)
                tokens.append(tok)

            elif hex_integer.match(line):
                m = hex_integer.match(line)
                line = line[len(m.group(1)):]
                tokens.append((INTEGER, int(m.group('num'), 16)))

            elif integer.match(line):
                m = integer.match(line)
                line = line[len(m.group(1)):]
                tokens.append((INTEGER, int(m.group('num'))))

            elif variable.match(line):
                m = variable.match(line)
                line = line[len(m.group(1)):]
                tokens.append((VARIABLE, m.group('var')))

            elif line.startswith('"'):
                (line, tok) = tokenize_string(line, source)
                tokens.append(tok)

            else:
                raise Exception("Could not parse token: " + repr(line))

    return tokens

SEMICOLON = ';'
COMMA = ','
ASSIGN = '='
ARROW = '->'
PAREN_OPEN  = '('
PAREN_CLOSE = ')'
BRACKET_OPEN  = '{'
BRACKET_CLOSE = '}'
NEWLINE = '\n'

VARIABLE = 'var'
OFFSET_LABEL = ':off:'
INTEGER = 'int'

STRING = 'str'


def is_expression(ex):
    return ex['type'] in (E_INTEGER, E_STRING, E_LAMBDA,
                          E_VARREF, E_BIN_RAW, E_BIN_CONCAT,
                          E_APPLICATION, E_BLOCK)

# next token, or none if finished
def next_strict(tokens):
    if not tokens:
        return None
    return tokens.pop(0)

def find_next_normal(tokens):
    for t in tokens:
        if t[0] != NEWLINE:
            return t
    return None

# next token, ignoring any newlines
def next_normal(tokens):
    while True:
        t = next_strict(tokens)
        if not t:
            return None
        if t[0] != NEWLINE:
            return t


def parse_lambda(tokens):
    params = []

    t = next_strict(tokens)
    if t[0] != PAREN_OPEN:
        raise Exception("Expected lambda start")

    t = next_normal(tokens)

    if t[0] == PAREN_CLOSE:
        pass

    elif t[0] == VARIABLE:
        if not is_plain_variable(t[1]):
            raise Exception('Invalid parameter name: ' + str(t[1]))

        params.append(t[1])

        while True:
            t = next_normal(tokens)

            if t[0] == PAREN_CLOSE:
                break

            elif t[0] == COMMA:
                t = next_normal(tokens)

                if t[0] == VARIABLE and is_plain_variable(t[1]) and t[1] not in params:
                    params.append(t[1])
                else:
                    raise Exception('Unexpected token: ' + str(t))
            else:
                raise Exception('Unexpected token: ' + str(t))

    t = next_normal(tokens)

    if t[0] != ARROW:
        raise Exception('Unexpected token: ' + str(t))

    (tokens, body) = parse_expression(tokens)

    if not params:
        # ()->X == X
        return (tokens, body)

    return (tokens, e_lambda(params, body))

def parse_expression_varstart(tokens):
    var = next_strict(tokens)

    if var[0] != VARIABLE:
        raise Exception("Expected variable, got: " + str(t))

    if not tokens:
        return (tokens, e_varref(var[1]))

    t = find_next_normal(tokens)

    if t[0] == PAREN_OPEN:
        # consume the previous one
        t = next_normal(tokens)

        t = next_normal(tokens)

        if t[0] == PAREN_CLOSE:
            # X() == X
            return (tokens, e_varref(var[1]))

        else:
            # put the token back, it's not ours
            tokens.insert(0, t)

            (tokens, expression) = parse_expression(tokens)

            args = []
            args.append(expression)


            while True:
                t = next_normal(tokens)

                if t[0] == PAREN_CLOSE:
                    break

                elif t[0] == COMMA:
                    (tokens, expression) = parse_expression(tokens)
                    args.append(expression)

                else:
                    raise Exception('Unexpected token: ' + str(t))

        return (tokens, e_application(e_varref(var[1]), args))

    else:
        return (tokens, e_varref(var[1]))


# This can contain all sorts of things
def parse_block(tokens):
    has_label = False
    assignments = []
    parts = []

    t = next_strict(tokens)
    if t[0] != BRACKET_OPEN:
        raise Exception("Expected block start")

    t = next_normal(tokens)

    while True:
        if t[0] == BRACKET_CLOSE:
            break

        if t[0] == SEMICOLON:
            # XXX: could maybe be stricter about this
            pass

        elif t[0] == OFFSET_LABEL:
            has_label = True
            parts.append(e_offset_label(t[1]))

        else:
            if ((t[0] == VARIABLE) and is_plain_variable(t[1]) and
                     tokens and (tokens[0][0] == ASSIGN)):
                # the ASSIGN we just saw
                t2 = next_strict(tokens)
                # the expression, starting on the same line.
                (tokens, t3) = parse_expression_strict(tokens)

                if t[1] in assignments:
                    raise Exception('Duplicate variable assignment: ' + str(t))

                assignments.append((t[1], t3 ))

            else:
                tokens.insert(0, t)
                (tokens, thing) = parse_expression_strict(tokens)
                parts.append(thing)

            t = next_strict(tokens)
            if t[0] not in (SEMICOLON, NEWLINE, BRACKET_CLOSE):
                raise Exception("statement not terminated, got: " + str(t))
            tokens.insert(0, t)

        t = next_normal(tokens)

    if len(parts) > 1:
        # unless we have a single string, take any string tokens to be
        # comments. A bit cheeky but highly convenient.
        parts = [p for p in parts if p['type'] != E_STRING]

    if len(parts) == 1 and is_expression(parts[0]):
        value = parts[0]
    else:
        value = e_bin_concat(parts)

    if not assignments and not has_label:
        # {X} == X
        return (tokens, value)

    return (tokens, e_block(assignments, value))


def parse_expression_strict(tokens):
    if not tokens:
        raise Exception("No tokens")

    t = tokens[0]

    if t[0] == PAREN_OPEN:
        return parse_lambda(tokens)

    elif t[0] == BRACKET_OPEN:
        return parse_block(tokens)

    elif t[0] == VARIABLE:
        return parse_expression_varstart(tokens)

    elif t[0] == INTEGER:
        return (tokens[1:], e_integer(t[1]))

    elif t[0] == STRING:
        tokens = tokens[1:]
        rvs = u''
        while t and t[0] == STRING:
            rvs += t[1]
            tn = find_next_normal(tokens)
            if not tn or tn[0] != STRING:
                break
            t = next_normal(tokens)
        return (tokens, e_string(rvs))

    else:
        raise Exception("Unexpected token " + str(t))

def parse_expression(tokens):
    # we can wipe out any leading newlines
    t = next_normal(tokens)
    tokens.insert(0, t)
    return parse_expression_strict(tokens)

def ast(tokens):
    # Because we put brackets around the input, we know we're just
    # about to read an expression.
    (tokens, expression) = parse_expression_strict(tokens)

    # We also know there's nothing after the block, so if that parsed
    # correctly we're good to go.
    assert not tokens

    return expression


def special_Import(env, offset, fx):
    if fx['type'] != E_STRING:
        raise Exception("Import takes String as argument")
    f = fx['data']

    # FIXME: toctou
    if os.path.exists(f + '.psm'):
        source = open(f + '.psm', 'r').read()
        return build_expression('{'+source+'}', offset)
    elif os.path.exists(f + '.py'):
        mod = importlib.import_module(f)
        return mod.build()

    raise Exception("Unknown module: " + fx[1])

# Philosophically the outer program looks like WithPosition(0,
# "{"+source+"}"), so closer bound WithPosition takes precedent.
def special_WithPosition(env, offset, ix, bx):
    if not ix['final']:
        return e_needs_work(bx['len'])
    if ix['type'] != E_INTEGER:
        raise Exception("WithPosition takes Integer as first")

    return eval_transparent(bx, env, ix['data'])


def set_offset(vs, n, l):
    changed = False
    seen = False
    out = []
    for (k, v) in vs:
        if n == k:
            seen = True
            if v != l:
                changed = True
                out.append((n, l))
            else:
                out.append((k, v))
        else:
            out.append((k, v))

    if not seen:
        changed = True
        out.insert(0, (n, l))

    return (changed, out)

def env_lookup(v, env):
    for scope in env:
        if v in scope:
            return scope[v]
    raise Exception("Undefined env variable " + v)

def block_lookup(v, block):
    if block['type'] != E_BLOCK:
        if not block['final']:
            return e_needs_work(block['len'])
        raise Exception("Attempt to lookup " + v + " on non block: " + str(block))
    for (k, x) in block['data']['vars']:
        if v == k:
            return x
    if v in block['data']['labels']:
        return block['data']['labels'][v]

    raise Exception("Undefined block variable " + v)

def eval_varref(ex, env, offset):
    if var['type'] != E_VARREF:
        raise Exception("Error this is not a var: " + str(var))
    return lookup(ex, env)

def eval_varref(var, env, offset):
    if var['type'] != E_VARREF:
        raise Exception("Attempt to lookup non var: " + str(var))
    v = var['data']
    bits = v.split('.')
    ex = env_lookup(bits[0], env)

    for b in bits[1:]:
        if not ex['final']:
            rv = e_varref(var['data'])
            rv['final'] = ex['final']
            rv['len'] = ex['len']
            return rv

        ex = block_lookup(b, ex)

    if not ex['final']:
        rv = e_varref(var['data'])
        rv['final'] = ex['final']
        rv['len'] = ex['len']
        return rv

    return ex

def eval_application_builtin(ex, env, offset):
    func = eval_varref(ex['data']['f'], env, offset)
    if func['type'] != E_BUILTIN_FUNC:
        raise Exception("Error this is not a builtin: " + str(ex['data']['f']))
    params_num = func['data']['paramsnum']
    args_num = len(ex['data']['args'])
    if params_num != args_num:
        raise Exception("Tried to apply " + str(args_num) +
                        " arg(s) to " + ex['data']['f']['data'] + " but that takes " + str(params_num))

    if func['data']['func'] == special_WithPosition:
        args = []
        for v in ex['data']['args']:
            args.append(eval_transparent(v, env, None))
        while args[0]['type'] == E_BLOCK:
            args[0] = args[0]['data']['val']
        rv = func['data']['func'](*([env, offset]+args))

    else:
        args = []
        for v in ex['data']['args']:
            arg = eval_transparent(v, env, offset)
            # none of the builtins take blocks... atm.
            while arg['type'] == E_BLOCK:
                arg = arg['data']['val']
            args.append(arg)

        if func['data']['func'] == special_Import:
            rv = func['data']['func'](*([env, offset]+args))
        else:
            rv = func['data']['func'](*args)

    if not rv['final']:
        # return a copy of the original thing.
        reex = e_application(ex['data']['f'], ex['data']['args'])
        reex['final'] = False
        reex['len'] = rv['len']
        return reex

    return rv

def eval_application_lambda(ex, env, offset):
    func = eval_varref(ex['data']['f'], env, offset)
    if func['type'] != E_LAMBDA:
        raise Exception("Error this is not a lambda: " + str(ex['data']['f']))
    params = func['data']['params']
    params_num = len(func['data']['params'])
    args_num = len(ex['data']['args'])
    if params_num != args_num:
        raise Exception("Tried to apply " + str(args_num) +
                        " arg(s) to " + ex['data']['f']['data'] + " but that takes " + str(params_num))
    strictvs = {}
    for k, v in zip(params, ex['data']['args']):
        strictvs[k] = eval_transparent(v, env, offset)

    # Note the use of the lambdas env as a base
    funcenv = [strictvs] + func['data']['env']
    rv = eval_transparent(func['data']['body'], funcenv, offset)

    if not rv['final']:
        # return a copy of the original thing.
        reex = e_application(ex['data']['f'], ex['data']['args'])
        reex['final'] = False
        reex['len'] = rv['len']
        return reex

    return rv

def eval_application(ex, env, offset):
    func = eval_varref(ex['data']['f'], env, offset)
    if func['type'] == E_BUILTIN_FUNC:
        return eval_application_builtin(ex, env, offset)
    if func['type'] == E_LAMBDA:
        return eval_application_lambda(ex, env, offset)
    raise Exception(str(ex['data']['f']) + " was not a lambda")


def eval_bin_concat(ex, env, offset):
    rv = e_bin_concat(ex['data'][:])
    pos = offset

    out = []
    for x in rv['data']:
        v = eval_transparent(x, env, pos)
        if v['final'] and v['type'] not in (E_BLOCK, E_BIN_CONCAT, E_BIN_RAW,
                                            E_OFFSET_LABEL):
            raise Exception("bin concat has non bin at top level " +  str(v))
        if pos is not None and v['len'] is not None:
            pos += v['len']
        else:
            pos = None
        out.append(v)

    # fill in our new knowledge
    rv['data']  = out
    rv['final'] = all([v['final'] for v in rv['data']])
    lens = [v['len'] for v in rv['data']]
    rv['len']   = sum(lens) if None not in lens else None

    # could do label stripping once the block has that info?
    if all([x['type'] == E_BIN_RAW for x in rv['data']]):
        rv = getbin(rv)

    return rv

# We keep re-evaluating blocks while we learn new information about
# the labels, from top to bottom. If we ever stop making progress on a
# label without determining its value then it's game over. XXX: could
# change this to potentially allow progress to be made anywhere in the
# block or even the whole program, but this should be sufficient for
# now.
#
# For now I'll just use a naive ordering of assignments, but in future
# it should allow for re-ordering to find dependencies.
def eval_block(ex, env, offset):

    rv = e_block(ex['data']['vars'][:],
                 ex['data']['val'].copy(),
                 ex['data']['labels'].copy())

    if offset is None:
        # there isn't much point working on the block until we're in a
        # position to fill in our labels offsets, one by one
        return rv

    # If we have binary content, our goal is to determine the values
    # for the labels within that content from, one-by-one.
    labels_context = {}
    vars_context = {}
    env = [vars_context] + [labels_context] + env

    if rv['data']['val']['type'] == E_BIN_CONCAT:
        # start with placeholder vars for label values
        for a in rv['data']['val']['data']:
            if a['type'] == E_OFFSET_LABEL:
                if a['data'] in labels_context:
                    raise Exception("duplicate definition of label " + a['data'])
                labels_context[a['data']] = e_offset_ref(a['data'])

    known_labels = []
    while True:
        known_labels_prev = known_labels
        known_labels = []

        # evaluate variables as best we can, given the placeholder labels
        outvars = []
        for (k, v) in rv['data']['vars']:
            vars_context[k] = eval_transparent(v, env, offset)
            outvars.append((k, vars_context[k]))
        # fill in our new knowledge
        rv['data']['vars'] = outvars

        # evaluate the block value as best we can
        block_value = eval_transparent(rv['data']['val'], env, offset)

        # fill in our new knowledge
        rv['data']['val'] = block_value
        rv['final'] = block_value['final'] and all([v['final'] for (k, v) in outvars])
        rv['len']   = block_value['len']

        if rv['data']['val']['type'] == E_BIN_CONCAT:
            sum_len = offset

            # if we learned any label values, feed it in and go again
            for part in block_value['data']:
                if part['len'] is None:
                    break

                if part['type'] == E_OFFSET_LABEL:
                    labels_context[part['data']] = e_integer(sum_len)
                    known_labels.append(part['data'])

                sum_len += part['len']
            else:
                # we've calculated all the labels
                if len(known_labels) == len(known_labels_prev):
                    break

            continue

        # if we made it here then it looks like we have everything
        break

    # It's actually fine to not fully evaluate a block even when our
    # own offset is known, because we may still depend on other
    # variables that are non-final and waiting on our own length to
    # become final.
    if rv['len'] is None:
        raise Exception("Our length is still unknown: "+str(rv))

    # set any offsets so others can use them
    for k in labels_context:
        rv['data']['labels'][k] = labels_context[k]

    return rv

def eval_transparent(ex, environment, offset):
    if ex['type'] == E_BLOCK:
        return eval_block(ex, environment, offset)
    if ex['type'] == E_APPLICATION:
        return eval_application(ex, environment, offset)
    if ex['type'] == E_VARREF:
        rv = eval_varref(ex, environment, offset)
        if rv['type'] == E_BUILTIN_FUNC and rv['data']['paramsnum'] == 0:
            return eval_application(e_application(ex, []), environment, offset)
        return rv
    if ex['type'] == E_BIN_CONCAT:
        return eval_bin_concat(ex, environment, offset)
    if ex['type'] == E_LAMBDA:
        ex['data']['env'] = environment
        return ex

    if ex['type'] == E_OFFSET_REF:
        x = eval_varref(e_varref(ex['data']), environment, offset)
        return x
        return ex

    if ex['type'] == E_STRING:
        return ex
    if ex['type'] == E_INTEGER:
        return ex
    if ex['type'] == E_BIN_RAW:
        return ex
    if ex['type'] == E_OFFSET_LABEL:
        return ex
    if ex['type'] == E_BUILTIN_FUNC:
        return ex

    raise Exception("Unrecognized expression: " + str(ex))


def build_expression(source, offset):
    tokens = tokenize(cStringIO.StringIO(source))
    builtins = {'Import': e_builtin_func(1, special_Import),
                'WithPosition': e_builtin_func(2, special_WithPosition)}
    return eval_transparent(ast(tokens), [builtins], offset)

################ PRINTING

def indent(i, inline):
    if not inline:
        return i*' '
    return ''

def nl(inline):
    if not inline:
        return '\n'
    return ''

def meta(ex):
    return '['+str(ex['len'])+':'+str(ex['final'])+':'+ex['type']+']'

def print_nicely_block(i, ex, inline):
    x = indent(i, inline) + meta(ex)+'{'+nl(inline)
    i += 4
    for (k, v) in ex['data']['vars']:
        x +=(indent(i, False)+k+' = ')
        x+=print_nicely(i, v, True)+nl(inline)
    x+=print_nicely(i, ex['data']['val'], False)+nl(inline)
    i -= 4
    x+= (i*' ') + '}'
    return x

def print_nicely_hex(i, ex, inline):
    x = indent(i, inline) + meta(ex)+'['+'\n'
    for ci in range(0, len(ex['data']), 16):
        hx = [hex(a)[2:].rjust(2,'0') for a in ex['data'][ci:ci+16]]
        x += ' '.join(hx)+'\n'
    return x+']'+nl(inline)

def print_nicely(i, ex, inline):
    if ex['type'] == E_BLOCK:
        return print_nicely_block(i, ex, False)+nl(inline)

    if ex['type'] == E_BIN_RAW:
        return print_nicely_hex(i, ex, inline)+nl(inline)

    elif ex['type'] == E_STRING:
        return indent(i, inline) + repr(ex['data'])+nl(inline)

    elif ex['type'] == E_VARREF:
        return indent(i, inline) + str(ex['data'])+nl(inline)

    elif ex['type'] == E_OFFSET_REF:
        return indent(i, inline) + str(ex['data'])+nl(inline)

    elif ex['type'] == E_OFFSET_LABEL:
        return indent(i, inline) + ':'+str(ex['data'])+':'+nl(inline)

    elif ex['type'] == E_INTEGER:
        return indent(i, inline) + str(ex['data'])+nl(inline)

    elif ex['type'] == E_BUILTIN_FUNC:
        return indent(i, inline) + '<'+ex['data']['func'].__name__+'>'+nl(inline)

    elif ex['type'] == E_LAMBDA:
        return (indent(i, inline) + '(' + ', '.join(ex['data']['params']) + ') ->'+
                print_nicely(i+4, ex['data']['body'], False))+nl(inline)

    elif ex['type'] == E_APPLICATION:
        return (indent(i, inline) +
                meta(ex)+print_nicely(i, ex['data']['f'], True)+
                '(' + (',\n'+indent(i, False)).join([print_nicely(i+4, arg, True) for arg in ex['data']['args']]) +
               ')')+nl(inline)

    elif ex['type'] == E_BIN_CONCAT:
        x = meta(ex)+'{'+nl(False)
        for part in ex['data']:
            x+=print_nicely(i, part, False)
        return x+'}'+nl(inline)
    else:
        raise Exception('unknown type to print: ' + str(ex))

def print_env(env):
    return '['+', '.join(['['+', '.join([k for k in c])+']' for c in env])+']'

############## GO

def block_binary_only(x):
    if not x['final']:
        raise Exception("tried to extract binary from non-final block: " +str(x))
    while x['type'] == E_BLOCK:
        x = x['data']['val']
    parts = []
    if x['type'] == E_BIN_CONCAT:
        for p in x['data']:
            parts.append(block_binary_only(p))
        x['data'] = parts
    return getbin(x)

if '__main__' == __name__:
    x = build_expression('WithPosition(0, {'+sys.stdin.read()+'})', None)

    x = block_binary_only(x)
    for b in x['data']:
        sys.stdout.write(chr(b))
