# coding: utf-8
from __future__ import unicode_literals

from scriptforge import CreateScriptService

import uno

import pathlib
import subprocess


def ssjson_ext_version():
    return "v0.1.3"


def decorate_parser(f):
    def _wrapper(*args, **keywords):
        if len(args) == 0:
            return None
        else:
            ssjson = args[0]
        if ssjson.is_fail():
            return None
        return f(*args, **keywords)
    return _wrapper


class SSJson(object):
    def __init__(self, load_data):
        if len(load_data) >= 2:
            self.header = load_data[0]
            self.data = load_data[1:]
            self.len_header = len(self.header)
            self.len_data = len(self.data)
            self.current_header = 0
            self.success = True
            self.fail_log = []
            self.parsed_header = ""
            self.parsed_data = ""
    @decorate_parser
    def next_header(self):
        self.current_header += 1

    @decorate_parser
    def get_header(self):
        result = self.header[self.current_header]
        return result
    @decorate_parser
    def get_data(self):
        l = []
        for i in range(self.len_data):
            l.append(self.data[i][self.current_header])
        return l
    def is_eof(self):
        return self.current_header >= self.len_header
    def is_success(self):
        return self.success
    def is_fail(self):
        return not self.success
    @decorate_parser
    def get_parsed_header(self):
        return self.parsed_header
    @decorate_parser
    def get_parsed_data(self):
        return self.parsed_data
    @decorate_parser
    def fail_parse(self, message = None):
        self.success = False
        self.parsed_header = None
        self.parsed_data = None
        if type(message) is str:
            self.fail_log.append(message)
        return None
    def add_fail_log(self, message):
        if is_fail():
            self.fail_log.append(message)
    def resume_parse(self):
        self.success = True
    @decorate_parser
    def success_parse(self, parsed_header = None, parsed_data = None):
        self.parsed_header = parsed_header
        self.parsed_data = parsed_data


def parse_ssjson(load_data):
    ssjson = SSJson(load_data)
    return run_parse_ssjson(ssjson)


@decorate_parser
def run_parse_ssjson(ssjson):
    many_till(ssjson, key_value, eof)
    data = ssjson.get_parsed_data()
    if data != None:
        transpose_data = list(zip(*data))
        s = to_object(ssjson, data)
        return s
    

# choice : SSJson -> [SSJson -> None] -> None
@decorate_parser
def choice(ssjson, parse_list):
    for p in parse_list:
        p(ssjson)
        if ssjson.is_success():
            return None
        else:
            ssjson.resume_parse()
    ssjson.fail_parse('fail all choice')


# many_till : SSJson -> (SSJson -> None) -> (SSJson -> None) -> None
@decorate_parser
def many_till(ssjson, parse, end):
    def loop():
        end(ssjson)
        if ssjson.is_success():
            return []
        else:
            ssjson.resume_parse()
            parse(ssjson)
            header = ssjson.get_parsed_header()
            data = ssjson.get_parsed_data()
            return [(header, data)] + loop()
    result  = loop()
    h = list_map(ssjson, lambda x: x[0], result)
    d = list_map(ssjson, lambda x: x[1], result)
    ssjson.success_parse(parsed_header = h, parsed_data = d)


@decorate_parser
def eof(ssjson):
    if ssjson.is_eof():
        ssjson.success_parse()
    else:
        ssjson.fail_parse("remain stream")


# satisfy: SSJson -> (String -> Bool) -> None
@decorate_parser
def satisfy(ssjson, p):
    header = ssjson.get_header()
    if p(header):
        data = ssjson.get_data()
        ssjson.next_header()
        ssjson.success_parse(parsed_header = header, parsed_data = data)
    else:
        ssjson.fail_parse("not satifsy")


# consume: SSJson -> String -> None
@decorate_parser
def consume(ssjson, s):
    satisfy(ssjson, lambda x: x == s)


# key_key: SSJson -> String -> None
@decorate_parser
def get_key(ssjson, s):
    satisfy(ssjson, lambda x: x.startswith(s))
    header = ssjson.get_parsed_header()
    if header != None:
        header = ssjson.get_parsed_header()[len(s):]
    data = ssjson.get_parsed_data()
    ssjson.success_parse(parsed_header = header, parsed_data = data)


# to_object: SSJson -> [[String]] -> [String]
@decorate_parser
def to_object(ssjson, s):
    def f(a):
        non_empty_str = list(filter(lambda x: x != "", a))
        if non_empty_str:
            return "{{ {:s} }}".format(", ".join(non_empty_str))
        else:
            return ""
    transpose_s = list(zip(*s))
    return list_map(ssjson, f, transpose_s)

@decorate_parser
def ignore(ssjson):
    consume(ssjson, "IGNORE")
    data = ssjson.get_parsed_data()
    ssjson.success_parse(parsed_data=list_map(ssjson, lambda x: "", data))


@decorate_parser
def start_object(ssjson):
    def f(x):
        def g(y):
            consume(y, x)
        return g
    start = map(f, ["START_OBJECT", "{"])
    choice(ssjson, start)


@decorate_parser
def end_object(ssjson):
    def f(x):
        def g(y):
            consume(y, x)
        return g
    end = map(f, ["END_OBJECT", "}"])
    choice(ssjson, end)


@decorate_parser
def start_array(ssjson):
    def f(x):
        def g(y):
            consume(y, x)
        return g
    start = map(f, ["START_ARRAY", "["])
    choice(ssjson, start)


@decorate_parser
def end_array(ssjson):
    def f(x):
        def g(y):
            consume(y, x)
        return g
    end = map(f, ["END_ARRAY", "]"])
    choice(ssjson, end)


@decorate_parser
def key_start_object(ssjson):
    def f(x):
        def g(y):
            get_key(y, x)
        return g
    start = map(f, ["START_OBJECT_", "{_"])
    choice(ssjson, start)


@decorate_parser
def key_start_array(ssjson):
    def f(x):
        def g(y):
            get_key(y, x)
        return g
    start = map(f, ["START_ARRAY_", "[_"])
    choice(ssjson, start)


# object: SSJson -> None
@decorate_parser
def p_object(ssjson):
    start_object(ssjson)
    many_till(ssjson, key_value, end_object)
    data = ssjson.get_parsed_data()
    s = to_object(ssjson, data)
    ssjson.success_parse(parsed_data = s)


@decorate_parser
def object_with_key(ssjson):
    key_start_object(ssjson)
    key = ssjson.get_parsed_header()
    many_till(ssjson, key_value, end_object)
    data = ssjson.get_parsed_data()
    s = to_object(ssjson, data)
    ssjson.success_parse(parsed_header = key, parsed_data = s)


# to_array: SSJson -> [[String]] -> [String]
@decorate_parser
def to_array(ssjson, s):
    def f(a):
        non_empty_str = list(filter(lambda x: x != "", a))
        if non_empty_str == ['"EMPTY"']:
            return "[]"
        elif non_empty_str == []:
            return ""
        else:
            return "[ {:s} ]".format(", ".join(non_empty_str))
    transpose_s = list(zip(*s))
    return list_map(ssjson, f, transpose_s)


@decorate_parser
def array(ssjson):
    start_array(ssjson)
    many_till(ssjson, value, end_array)
    data = ssjson.get_parsed_data()
    s = to_array(ssjson, data)
    ssjson.success_parse(parsed_data = s)


@decorate_parser
def array_with_key(ssjson):
    key_start_array(ssjson)
    key = ssjson.get_parsed_header()
    many_till(ssjson, value, end_array)
    data = ssjson.get_parsed_data()
    s = to_array(ssjson, data)
    ssjson.success_parse(parsed_header = key, parsed_data = s)


@decorate_parser
def value(ssjson):
    choice(ssjson, [ignore, p_object, array, value_singleton])


@decorate_parser
def value_singleton(ssjson):
    choice(ssjson, [value_raw, value_str, value_value])


@decorate_parser
def value_raw(ssjson):
    consume(ssjson, "RAW")


@decorate_parser
def value_str(ssjson):
    def f(x):
        if x == "":
            return ""
        else:
            return f'"{x}"'
    consume(ssjson, "STR")
    data = ssjson.get_parsed_data()
    ssjson.success_parse(parsed_data=list_map(ssjson, f, data))


@decorate_parser
def value_value(ssjson):
    def is_number(s):
        try:
            float(s)
        except ValueError:
            return False
        except TypeError:
            return False
        else:
            return True
    def f(x):
        if is_number(x) or (x == ''):
           return x
        elif x == 't':
            return 'true'
        elif x == 'f':
            return 'false'
        else:
            return f'"{x}"'
    consume(ssjson, "VALUE")
    data = ssjson.get_parsed_data()
    ssjson.success_parse(parsed_data=list_map(ssjson, f, data))


@decorate_parser
def key_value(ssjson):
    choice(ssjson, [ignore, object_with_key, array_with_key, key_value_singleton])
    key = ssjson.get_parsed_header()
    data = ssjson.get_parsed_data()
    def f(x):
        if x:
            return f'"{key}": {x}'
        else:
            return ''
    v = list_map(ssjson, f, data)
    ssjson.success_parse(parsed_header = key, parsed_data = v)


@decorate_parser
def key_value_singleton(ssjson):
    choice(ssjson, [key_value_raw, key_value_str, key_value_default])


@decorate_parser
def key_value_raw(ssjson):
    get_key(ssjson, "RAW_")


@decorate_parser
def key_value_str(ssjson):
    def f(x):
        if not x == '':
            return f'"{x}"'
    get_key(ssjson, "STR_")
    key = ssjson.get_parsed_header()
    data = ssjson.get_parsed_data()
    ssjson.success_parse(parsed_header=key, parsed_data=list_map(ssjson, f, data))


@decorate_parser
def key_value_default(ssjson):
    def is_number(s):
        try:
            float(s)
        except ValueError:
            return False
        except TypeError:
            return False
        else:
            return True
    def f(x):
        if is_number(x) or (x == ''):
           return x
        elif x == 't':
            return 'true'
        elif x == 'f':
            return 'false'
        else:
            return f'"{x}"'
    get_key(ssjson, "")
    key = ssjson.get_parsed_header()
    data = ssjson.get_parsed_data()
    ssjson.success_parse(parsed_header=key, parsed_data=list_map(ssjson, f, data))


@decorate_parser
def list_map(ssjson, f, data):
    if data == None:
        return None
    else:
        return list(map(f, data))

class CellCoord:
    doc = CreateScriptService("Calc")
    def __init__(self, r, c, s):
        self.coord_r = r
        self.coord_c = c
        self.sheet = s
    def set_coord_row(self, r):
        self.coord_r = r
    def set_coord_column(self, c):
        self.coord_c = c
    def get_coord_row(self):
        return self.coord_r
    def get_coord_column(self):
        return self.coord_c
    def move_right(self):
        self.coord_c += 1
    def move_down(self):
        self.coord_r += 1
    def get_cell_value(self):
        return self.doc.GetValue(self.doc.A1Style(self.coord_r, self.coord_c, sheetname=self.sheet))
    def set_cell_value(self, v):
        self.doc.SetValue(self.doc.A1Style(self.coord_r, self.coord_c, sheetname=self.sheet), v)

class Option():
    def __init__(self, doc):
        self.output_dir = pathlib.Path(doc.GetValue('_Option.B3'))
        self.json_formatter_path = pathlib.Path(doc.GetValue('_Option.C3'))
        self.ssjson_version = doc.GetValue('_Option.D3')

def last_input_json_column(s):
    # "C3"
    cc = CellCoord(3, 3, s)
    if cc.get_cell_value() != "START_JSON":
        raise Exception
    while True:
        cc.move_right()
        v = cc.get_cell_value()
        if v == "END_JSON":
            end_c = cc.coord_c
            break
    return end_c

def last_input_type_row(s):
    # "D3"
    cc = CellCoord(3, 4, s)
    while True:
        cc.move_down()
        v = cc.get_cell_value()
        if v == "":
            end_r = cc.coord_r - 1
            break
    return end_r

def make_cdda_mod():
    log_init()
    doc = CreateScriptService("Calc")
    bas = CreateScriptService("Basic")
    option = Option(doc)
    if option.ssjson_version != ssjson_ext_version():
        bas.MsgBox('expected version {}. but extension version is {}'.format(option.ssjson_version, ssjson_ext_version()))
        return None
    sheets = filter(lambda x: not x.startswith('_'), doc.Sheets)
    inputs = []
    for s in sheets:
        log("load sheet: " + s)
        filename = doc.GetValue(s + ".B4")
        if not filename == '':
            start = "D3"
            end_r = last_input_type_row(s)
            end_c = last_input_json_column(s)
            input_range = doc.A1Style(3, 4, end_r, end_c, s)
            input_data = doc.GetValue(input_range)
            objs = parse_ssjson(input_data)
            inputs.append((option.output_dir/filename, objs))
        else:
            log("skip load: not input OUTPUT_PATH")
    outputs = {}
    for (f, objs) in inputs:
        if f in outputs.keys():
            outputs[f] = outputs[f] + objs
        else:
            outputs[f] = objs
    for p, objs in outputs.items():
        log("output to " + str(p))
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.is_file():
            p.unlink()
        with p.open(mode='w') as f:
            json = '[ {} ]'.format(", ".join(objs))
            if option.json_formatter_path.is_file():
                cmd = [option.json_formatter_path]
                result = subprocess.run(cmd, input=json, text=True, capture_output=True)
                f.write(result.stdout)
            else:
                f.write(json)
    bas.MsgBox("end script")

global g_cc_log

def log(s):
    g_cc_log.set_cell_value(s)
    g_cc_log.move_down()

def log_init():
    global g_cc_log
    g_cc_log = CellCoord(1, 1, "_Log")
    g_cc_log.doc.ClearAll('$_Log.A:A')


import unohelper
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation( \
    None,"org.openoffice.script.DummyImplementationForPythonScripts", \
    ("org.openoffice.script.DummyServiceForPythonScripts",),)
