
E_INTEGER = 'INT'
E_STRING  = 'STR'
E_LAMBDA  = 'LAM'
E_VARREF  = 'VAR'

E_APPLICATION = 'APP'

E_OFFSET_LABEL = 'OFF'

E_OFFSET_REF = 'OFFREF'

E_BIN_RAW = 'RAW'
E_BIN_CONCAT = 'BINCAT'

E_BLOCK = 'BLK'

E_BUILTIN_FUNC = 'BUILTIN'

E_NEEDS_WORK = 'NEEDS_WORK'


def getbin(sx):
    if sx['type'] == E_BIN_RAW:
        return sx

    if sx['type'] == E_BIN_CONCAT:
        out = []
        for x in sx['data']:
            b = getbin(x)
            if b['type'] != E_BIN_RAW:
                raise Exception("Expected bin: " + str(b))
            out.append(b)
        sumlen = 0
        joined = []
        if out:
            sumlen = reduce(lambda x, y: x + y, [x['len'] for x in out])
            joined = reduce(lambda x, y: x + y, [x['data'] for x in out])
        return e_bin_raw(sumlen, joined)

    if sx['type'] == E_OFFSET_LABEL:
        return e_bin_raw(0, [])

    raise Exception("Tried to get binary from " + str(sx))


# final: whether this is in its final form
# len:   the length of binary content, or None if n/a / unknown

def e_needs_work(length=None):
    return {'len': length, 'final': False, 'type':E_NEEDS_WORK, 'data': None}

def e_integer(n):
    return {'len': None, 'final': True, 'type':E_INTEGER, 'data':n}

def e_string(n):
    return {'len': None, 'final': True, 'type':E_STRING, 'data':n}

def e_varref(x):
    return {'len': None, 'final': False, 'type':E_VARREF, 'data': x}

def e_offset_label(x):
    return {'len': 0, 'final': True, 'type':E_OFFSET_LABEL, 'data': x}

def e_offset_ref(x):
    return {'len': None, 'final': False, 'type':E_OFFSET_REF, 'data': x}

def get_bin_concat_len(lst):
    lens = [x['len'] for x in lst]
    if not any([l is None for l in lens]):
        return sum(lens)
    return None

def e_bin_concat(lst, labels=None):
    if not labels:
        labels = {}
    return {'len': get_bin_concat_len(lst), 'final': all([x['final'] for x in lst]),
            'type':E_BIN_CONCAT, 'data': lst}

# x is a list of integers
def e_bin_raw(bitlen, x):
    return {'len':bitlen, 'final': True, 'type':E_BIN_RAW, 'data': x}

def e_block(assignments, value, labels=None):
    if not labels:
        labels = {}
    return {'len': value['len'], 'final': value['final'], 'type':E_BLOCK,
            'data': {'vars':assignments, 'val':value, 'labels':labels}}

def e_application(f, args):
    if f['type'] != E_VARREF:
        raise Exception("Application can only be performed on named functions")
    return {'len': None, 'final': False, 'type':E_APPLICATION, 'data': {'f': f, 'args': args}}

def e_lambda(params, body, env=None):
    return {'len': None, 'final': True, 'type':E_LAMBDA, 'data': {'params':params, 'body':body, 'env':env}}

def e_builtin_func(paramsnum, f):
    return {'len': None, 'final': True, 'type':E_BUILTIN_FUNC,
            'data': {'paramsnum': paramsnum, 'func': f}}
