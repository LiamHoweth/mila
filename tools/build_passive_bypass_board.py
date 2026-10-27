#!/usr/bin/env python3
"""Rebuild the MiLa isolated bench contact board (not a vehicle design).

Run with KiCad's bundled Python, which supplies pcbnew and wx.  This script
owns only hardware/passive_bypass_rev_a/ and does not edit historical PCBs.
"""
from pathlib import Path
import csv
import heapq
import json
import math
import re
import shutil
import subprocess
import uuid

import wx
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/passive_bypass_rev_a"
KICAD = Path("/Applications/KiCad/KiCad.app/Contents")
CLI = KICAD / "MacOS/kicad-cli"
LIB = KICAD / "SharedSupport"
NAME = "mila_passive_bypass_bench_rev_a"
NS = uuid.UUID("0be4cd13-b32e-4b31-b435-2cb1d417777a")


def uid(s):
    return str(uuid.uuid5(NS, s))


def q(s):
    return json.dumps(str(s))


def blocks(text, token):
    """Yield balanced expressions named token, ignoring quoted parentheses."""
    for m in re.finditer(r"\(" + re.escape(token) + r"\s", text):
        start = m.start()
        depth = 0
        quote = False
        escape = False
        for i in range(start, len(text)):
            c = text[i]
            if escape:
                escape = False
                continue
            if c == "\\" and quote:
                escape = True
                continue
            if c == '"':
                quote = not quote
                continue
            if not quote:
                depth += c == "("
                depth -= c == ")"
                if depth == 0:
                    yield text[start:i + 1]
                    break


def load_symbol(library, name):
    text = (LIB / "symbols" / (library + ".kicad_sym")).read_text()
    # A library's first symbol expression contains its nested graphic units;
    # balance-aware selection avoids matching a nested unit accidentally.
    found = next(b for b in blocks(text, "symbol")
                 if b.startswith("(symbol " + q(name) + "\n"))
    parent = re.search(r'\(extends "([^"]+)"\)', found)
    if parent:
        inherited = load_symbol(library, parent.group(1))
        units = [b for b in blocks(inherited, "symbol")
                 if re.match(r'\(symbol "[^"]+_[0-9]+_[0-9]+"', b)]
        found = re.sub(r'\(extends "[^"]+"\)', "", found)
        found = found[:-1] + "\n" + "\n".join(
            re.sub(r'\(symbol "[^\"]+_([0-9]+_[0-9]+)"',
                   lambda m: '(symbol ' + q(name + '_' + m.group(1)), b, count=1)
            for b in units) + "\n)"
    return found


PARTS = []


def part(ref, value, sym, fp, pins, pos, sch, angle=0, source=""):
    PARTS.append(dict(ref=ref, value=value, sym=sym, fp=fp, pins=pins,
                      pos=pos, sch=sch, angle=angle, source=source,
                      uuid=uid("symbol:" + ref)))


RELAY_SOURCE = "https://omronfs.omron.com/en_US/ecb/products/pdf/en-g6k.pdf"
N_SOURCE = "https://www.aosmd.com/res/data_sheets/AO3400A.pdf"
P_SOURCE = "https://www.aosmd.com/res/data_sheets/AO3401A.pdf"
SIGNALS = {
    "RLY1": {"2": "J4_13", "3": "J4_14", "4": "J5_10",
             "7": "J4_12", "6": "J4_15", "5": "J5_11"},
    "RLY2": {"2": "J4_11", "3": "J4_16", "4": "J6_8",
             "7": "J4_10", "6": "J4_17", "5": "J6_9"},
    "RLY3": {"2": "J4_9", "3": "J4_18", "4": "J4_8",
             "5": None, "6": None, "7": None},
    "RLY4": {"2": "J4_8", "3": "J4_19", "4": "J4_9",
             "5": None, "6": None, "7": None},
}


def define_parts():
    for i, x in enumerate((8, 21, 34, 47), 1):
        request = "REQ_GROUP" if i <= 2 else "REQ_K" + str(i + 4)
        pins = dict(SIGNALS["RLY" + str(i)])
        pins.update({"1": "COIL_5V", "8": "COIL_R" + str(i)})
        part("RLY" + str(i), "G6K-2P-Y DC5", "Relay:G6K-2",
             "MiLa_Bench:Relay_G6K_2P_Y_corrected", pins, (x, 21),
             (80 + (i - 1) * 125, 70), source=RELAY_SOURCE)
        part("Q" + str(i), "AO3400A", "Transistor_FET:AO3400A",
             "MiLa_Bench:SOT-23", {"1": "G_R" + str(i), "2": "GND",
                                   "3": "COIL_R" + str(i)},
             (x + 1, 14), (70 + (i - 1) * 125, 145), source=N_SOURCE)
        part("RG" + str(i), "330R", "Device:R", "MiLa_Bench:R_0805",
             {"1": request, "2": "G_R" + str(i)},
             (x - 1, 10), (45 + (i - 1) * 125, 145))
        part("RPD" + str(i), "10k", "Device:R", "MiLa_Bench:R_0805",
             {"1": "G_R" + str(i), "2": "GND"},
             (x + 4, 10), (95 + (i - 1) * 125, 145))
        part("D" + str(i), "1N4148W-E3-08", "Device:D", "MiLa_Bench:D_SOD123",
             {"1": "COIL_5V", "2": "COIL_R" + str(i)},
             (x + 4, 17), (95 + (i - 1) * 125, 175), angle=90,
             source="https://www.vishay.com/docs/86356/1n4148w.pdf")
    part("Q5", "AO3401A", "Transistor_FET:AO3401A", "MiLa_Bench:SOT-23",
         {"1": "P_GATE", "2": "5V_RAW", "3": "COIL_5V"},
         (20, 5), (195, 245), source=P_SOURCE)
    part("Q6", "AO3400A", "Transistor_FET:AO3400A", "MiLa_Bench:SOT-23",
         {"1": "G_PERMIT", "2": "GND", "3": "P_GATE"},
         (26, 5.5), (265, 245), source=N_SOURCE)
    part("RPG1", "10k", "Device:R", "MiLa_Bench:R_0805",
         {"1": "5V_RAW", "2": "P_GATE"}, (20, 8), (230, 215))
    part("RG6", "330R", "Device:R", "MiLa_Bench:R_0805",
         {"1": "COIL_PERMIT", "2": "G_PERMIT"}, (27, 2), (240, 280))
    part("RPD6", "82k", "Device:R", "MiLa_Bench:R_0805",
         {"1": "G_PERMIT", "2": "GND"}, (30.5, 7.5), (300, 270))
    part("JPWR1", "5V RAW AFTER EXTERNAL ENABLE", "Connector_Generic:Conn_01x02",
         "MiLa_Bench:PinHeader_1x02", {"1": "5V_RAW", "2": "GND"},
         (8, 5), (45, 240), angle=90)
    part("JCTRL1", "REQUESTS / PERMIT / 5V FEEDBACK",
         "Connector_Generic:Conn_01x06", "MiLa_Bench:PinHeader_1x06",
         {"1": "REQ_GROUP", "2": "REQ_K7", "3": "REQ_K8",
          "4": "COIL_PERMIT", "5": "GND", "6": "5V_RAW"},
         (35, 5), (90, 285), angle=90)
    part("J4B1", "J4 SIGNAL SUBSET",
         "Connector_Generic:Conn_02x06_Odd_Even", "MiLa_Bench:PinHeader_2x06",
         {"1": "J4_14", "2": "J4_13", "3": "J4_15", "4": "J4_12",
          "5": "J4_16", "6": "J4_11", "7": "J4_17", "8": "J4_10",
          "9": "J4_18", "10": "J4_9", "11": "J4_19", "12": "J4_8"},
         (18, 43), (395, 260), angle=90)
    part("JDAC1", "J5/J6 DAC SIGNALS", "Connector_Generic:Conn_01x04",
         "MiLa_Bench:PinHeader_1x04",
         {"1": "J5_10", "2": "J5_11", "3": "J6_8", "4": "J6_9"},
         (6, 35), (485, 260), angle=90)


def libraries():
    pretty = OUT / "MiLa_Bench.pretty"
    pretty.mkdir(parents=True, exist_ok=True)
    sources = {
        "Relay_G6K_2P_Y_corrected": "Relay_THT.pretty/Relay_DPDT_Omron_G6K-2P-Y.kicad_mod",
        "SOT-23": "Package_TO_SOT_SMD.pretty/SOT-23.kicad_mod",
        "R_0805": "Resistor_SMD.pretty/R_0805_2012Metric.kicad_mod",
        "D_SOD123": "Diode_SMD.pretty/D_SOD-123.kicad_mod",
        "PinHeader_1x02": "Connector_PinHeader_2.54mm.pretty/PinHeader_1x02_P2.54mm_Vertical.kicad_mod",
        "PinHeader_1x04": "Connector_PinHeader_2.54mm.pretty/PinHeader_1x04_P2.54mm_Vertical.kicad_mod",
        "PinHeader_1x06": "Connector_PinHeader_2.54mm.pretty/PinHeader_1x06_P2.54mm_Vertical.kicad_mod",
        "PinHeader_2x06": "Connector_PinHeader_2.54mm.pretty/PinHeader_2x06_P2.54mm_Vertical.kicad_mod",
    }
    for name, source in sources.items():
        text = (LIB / "footprints" / source).read_text()
        text = re.sub(r'^\(footprint "[^"]+"', '(footprint ' + q(name), text)
        if name == "Relay_G6K_2P_Y_corrected":
            # Manufacturer G6K-2P-Y drawing: y=0,3.2,5.4,7.6, x=0,5.08.
            # Installed KiCad 10 library incorrectly locates NC pins at y=3.0.
            for n in ("2", "7"):
                old = next(b for b in blocks(text, "pad") if b.startswith('(pad ' + q(n) + ' '))
                new = re.sub(r'\(at ([^ ]+) 3\)', r'(at \1 3.2)', old)
                assert new != old, "Library changed; recheck manufacturer footprint"
                text = text.replace(old, new)
        (pretty / (name + ".kicad_mod")).write_text(text)
    (OUT / "fp-lib-table").write_text(
        '(fp_lib_table (version 7) (lib (name "MiLa_Bench") (type "KiCad") '
        '(uri "${KIPRJMOD}/MiLa_Bench.pretty") (options "") '
        '(descr "Project-local bench footprints; corrected G6K NC row")))\n')
    symbols = {}
    local_definitions = []
    for spec in sorted({p["sym"] for p in PARTS}):
        lib, name = spec.split(":")
        definition = load_symbol(lib, name)
        symbols['MiLa_Bench:' + name] = definition
        local_definitions.append(definition)
    for p in PARTS:
        p['sym'] = 'MiLa_Bench:' + p['sym'].split(':')[1]
    (OUT/'MiLa_Bench.kicad_sym').write_text(
        '(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor")\n' +
        '\n'.join(local_definitions) + '\n)\n')
    (OUT/'sym-lib-table').write_text(
        '(sym_lib_table (version 7) (lib (name "MiLa_Bench") (type "KiCad") '
        '(uri "${KIPRJMOD}/MiLa_Bench.kicad_sym") (options "") '
        '(descr "Local resolved relay, FET, passive and connector symbols")))\n')
    return symbols


def make_schematic(symbols):
    root_uuid = uid("root-sheet")
    libtext = "\n".join(re.sub(r'^\(symbol "[^"]+"', '(symbol ' + q(k), v)
                         for k, v in symbols.items())
    lines = [f'(kicad_sch (version 20250114) (generator "eeschema") '
             f'(uuid {q(root_uuid)}) (paper "A2")',
             '(title_block (title "MiLa passive bypass: isolated BENCH ONLY") '
             '(date "2026-10-07") (rev "A") '
             '(comment 1 "Contacts: simulator 0-5 V, <=1 mA only; no vehicle") '
             '(comment 2 "External watchdog/supervisor and physical series enable required"))',
             '(lib_symbols\n' + libtext + '\n)']
    for p in PARTS:
        x, y = (round(round(v/1.27)*1.27, 5) for v in p["sch"])
        # Schematic orientation stays zero for intelligible standard symbols.
        props = []
        for key, value, dy, hide in (
                ("Reference", p["ref"], -12, False),
                ("Value", p["value"], -9, False),
                ("Footprint", p["fp"], 0, True),
                ("Datasheet", p["source"], 0, True)):
            tx,ty,justify=x,y+dy,''
            if key in ('Reference','Value'):
                if p['ref'].startswith('RLY'):
                    tx,ty=x+22,y+(-2 if key=='Reference' else 2)
                    justify='(justify left)'
                elif p['ref'].startswith('Q'):
                    tx,ty=x+5.08,y+(-1.905 if key=='Reference' else 1.27)
                    justify='(justify left)'
                elif p['ref'].startswith('R'):
                    tx,ty=x+3.81,y+(-1.27 if key=='Reference' else 1.27)
                    justify='(justify left)'
                elif p['ref'].startswith('D'):
                    tx,ty=x,y+(-5.08 if key=='Reference' else -2.54)
                elif p['ref'].startswith('J'):
                    tx,ty=x,y+(-15.24 if key=='Reference' else -12.7)
            props.append(f'(property {q(key)} {q(value)} (at {tx:g} {ty:g} 0) '
                         f'(effects (font (size 1.3 1.3)) {justify} '
                         f'{"(hide yes)" if hide else ""}))')
        pins = list(blocks(symbols[p["sym"]], "pin"))
        instance_pins = []
        for pin in pins:
            n = re.search(r'\(number "([^"]+)"', pin).group(1)
            px, py, a = map(float, re.search(r'\(at ([^ ]+) ([^ ]+) ([^)]+)\)', pin).groups())
            # Symbol coordinates use +y up; sheet coordinates use +y down.
            sx, sy = x + px, y - py
            instance_pins.append(f'(pin {q(n)} (uuid {q(uid(p["ref"] + ":pin:" + n))}))')
            net = p["pins"][n]
            if net is None:
                lines.append(f'(no_connect (at {sx:g} {sy:g}) '
                             f'(uuid {q(uid(p["ref"]+":nc:"+n))}))')
                continue
            # Continue outward opposite the pin's inward orientation.
            rad = math.radians(a)
            ex = round(sx - 3.81 * math.cos(rad), 5)
            ey = round(sy + 3.81 * math.sin(rad), 5)
            lines.append(f'(wire (pts (xy {sx:g} {sy:g}) (xy {ex:g} {ey:g})) '
                         f'(stroke (width 0) (type default)) '
                         f'(uuid {q(uid(p["ref"]+":wire:"+n))}))')
            label_angle = int(a) % 360
            lines.append(f'(global_label {q(net)} (shape bidirectional) (at {ex:g} {ey:g} {label_angle}) '
                         f'(effects (font (size 1.1 1.1)) (justify left bottom)) '
                         f'(uuid {q(uid(p["ref"]+":label:"+n))}))')
        lines.append(f'(symbol (lib_id {q(p["sym"])}) (at {x} {y} 0) (unit 1) '
                     f'(in_bom yes) (on_board yes) (dnp no) (uuid {q(p["uuid"])})\n' +
                     '\n'.join(props + instance_pins) +
                     f'\n(instances (project {q(NAME)} (path {q("/"+root_uuid)} '
                     f'(reference {q(p["ref"])}) (unit 1)))))')
    notes = [
        (35, 25, "BENCH ONLY: no Nissan harness, ECU, pedal, brake, or steering connection."),
        (35, 32, "Four NONLATCHING relays: RLY1 K3/K4; RLY2 K5/K6; RLY3 K7; RLY4 K8."),
        (35, 195, "COIL_5V is switched only; no external supply or energy storage may feed this net."),
        (35, 202, "Flyback diodes lengthen release: dropout/bounce/skew must be measured."),
        (35, 320, "JPWR1: regulated 4.75-5.25 V, 150 mA current limit, physical series enable upstream."),
        (35, 327, "JCTRL1 inputs active HIGH: >=2.60 V at header; LOW <=0.4 V; default disconnected OFF."),
        (35, 334, "COIL_PERMIT comes from external independent supervisor. This board has no watchdog."),
        (35, 341, "All contact nets are isolated from logic GND. Source simulator provides its own references."),
        (35, 348, "G6K pins1(+)/8(-) coil; poleA3 COM/2 NC/4 NO; poleB6 COM/7 NC/5 NO."),
        (35, 355, "K7/K8 remain independent. Mixed states are testable here and are not declared vehicle-safe."),
        (35, 362, "Passive NC bypass depends on healthy contacts and connector continuity; no stuck-contact claim."),
    ]
    for i, (x, y, text) in enumerate(notes):
        lines.append(f'(text {q(text)} (at {x} {y} 0) '
                     '(effects (font (size 1.4 1.4)) (justify left bottom)) '
                     f'(uuid {q(uid("note:"+str(i)))}))')
    lines.append('(embedded_fonts no))')
    (OUT / (NAME + ".kicad_sch")).write_text('\n'.join(lines))


def mm(v):
    return pcbnew.FromMM(v)


def point(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def pos_mm(obj):
    p = obj.GetPosition()
    return pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)


class Router:
    """Conservative two-layer Manhattan router for this small bench board.

    KiCad DRC, rather than this routing approximation, is the acceptance gate.
    Obstacles include all copper pads and previously routed foreign nets.
    """
    STEP = 0.2
    WIDTH = 0.25
    VIA_BLOCK_RADIUS = 0.78

    def __init__(self, board, pads, width=60, height=50, step=None,
                 mounts=None, track_width=None, search_limit=None, goal_tiebreak=False,
                 heuristic_weight=1.0):
        self.board = board
        self.pads = pads
        self.search_limit = search_limit
        self.goal_tiebreak = goal_tiebreak
        self.heuristic_weight = heuristic_weight
        if step is not None:
            self.STEP = step
        if track_width is not None:
            self.WIDTH = track_width
        self.nx = int(round(width/self.STEP))+1
        self.ny = int(round(height/self.STEP))+1
        self.edge_cells=max(4,int(math.ceil(0.7/self.STEP)))
        self.occupied = [dict(), dict()]
        self.edges = set()
        self.via_points = []
        for pad in pads:
            net = pad.GetNetname() or '__unused_' + pad.m_Uuid.AsString()
            x, y = pos_mm(pad)
            size = pad.GetSize()
            sx, sy = pcbnew.ToMM(size.x), pcbnew.ToMM(size.y)
            angle = int(round(pad.GetOrientationDegrees())) % 180
            if angle == 90:
                sx, sy = sy, sx
            margin = 0.34
            layers = [0, 1] if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else [0]
            for layer in layers:
                self.rect(layer, net, x - sx/2 - margin, y - sy/2 - margin,
                          x + sx/2 + margin, y + sy/2 + margin)
        # Mechanical M3 holes; keep copper away from hole edges.
        for x, y in (mounts if mounts is not None else
                     ((3, 3), (57, 3), (3, 47), (57, 47))):
            for layer in (0, 1):
                self.disk(layer, "__mount", x, y, 2.2)

    def grid(self, xy):
        return tuple(int(round(v / self.STEP)) for v in xy)

    def xy(self, cell):
        return cell[0] * self.STEP, cell[1] * self.STEP

    def rect(self, layer, net, x1, y1, x2, y2):
        for gx in range(max(0, int(math.floor(x1/self.STEP))), min(self.nx, int(math.ceil(x2/self.STEP))+1)):
            for gy in range(max(0, int(math.floor(y1/self.STEP))), min(self.ny, int(math.ceil(y2/self.STEP))+1)):
                self.occupied[layer].setdefault((gx, gy), set()).add(net)

    def disk(self, layer, net, x, y, radius):
        gx, gy = self.grid((x, y))
        d = int(math.ceil(radius/self.STEP))
        for dx in range(-d, d+1):
            for dy in range(-d, d+1):
                if (dx*self.STEP)**2 + (dy*self.STEP)**2 <= radius**2:
                    self.occupied[layer].setdefault((gx+dx, gy+dy), set()).add(net)

    def free(self, gx, gy, layer, net):
        if not (self.edge_cells <= gx < self.nx - self.edge_cells and
                self.edge_cells <= gy < self.ny - self.edge_cells):
            return False
        return self.occupied[layer].get((gx, gy), set()) <= {net}

    def via_free(self, gx, gy, net):
        x,y = self.xy((gx,gy))
        for vx,vy,vnet in self.via_points:
            distance = math.dist((x,y),(vx,vy))
            if distance < 0.01 and net == vnet:
                return True
            if distance < 0.7:
                return False
        reach=int(round(0.4/self.STEP))
        for layer in (0, 1):
            for dx in range(-reach, reach+1):
                for dy in range(-reach, reach+1):
                    if not self.free(gx+dx, gy+dy, layer, net):
                        return False
        return True

    def route(self, a, b, net):
        ga, gb = self.grid(pos_mm(a)), self.grid(pos_mm(b))
        def pad_layers(pad):
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:return (0, 1)
            return (0,) if pad.GetLayerSet().Contains(pcbnew.F_Cu) else (1,)
        al, bl = pad_layers(a), pad_layers(b)
        starts = [(ga[0], ga[1], layer) for layer in al]
        goals = {(gb[0], gb[1], layer) for layer in bl}
        queue = []
        dist = {}
        previous = {}
        serial = 0
        for state in starts:
            dist[state] = 0
            h = abs(ga[0]-gb[0])+abs(ga[1]-gb[1])
            heapq.heappush(queue, (h, h if self.goal_tiebreak else 0, serial, state))
            serial += 1
        finish = None
        expansions = 0
        while queue:
            expansions += 1
            if self.search_limit is not None and expansions > self.search_limit:
                return False
            _, _, _, u = heapq.heappop(queue)
            if u in goals:
                finish = u
                break
            gx, gy, layer = u
            neighbors = [(gx+1,gy,layer,1), (gx-1,gy,layer,1),
                         (gx,gy+1,layer,1), (gx,gy-1,layer,1)]
            if self.via_free(gx, gy, net):
                neighbors.append((gx,gy,1-layer,18))
            for vx, vy, vl, cost in neighbors:
                v = (vx, vy, vl)
                if not self.free(vx,vy,vl,net):
                    continue
                nd = dist[u]+cost
                if nd >= dist.get(v, float('inf')):
                    continue
                dist[v] = nd
                previous[v] = u
                h = abs(vx-gb[0])+abs(vy-gb[1])+(0 if vl in bl else 18)
                heapq.heappush(queue, (nd+h*self.heuristic_weight,
                                     h if self.goal_tiebreak else 0, serial, v))
                serial += 1
        if finish is None:
            return False
        path = [finish]
        while path[-1] in previous:
            path.append(previous[path[-1]])
        path.reverse()
        # Segment simplification: preserve bends and layer transitions.
        simplified = [path[0]]
        last_direction = None
        for i in range(1,len(path)):
            direction = tuple(path[i][j]-path[i-1][j] for j in range(3))
            if direction != last_direction and i > 1:
                simplified.append(path[i-1])
            last_direction = direction
        simplified.append(path[-1])
        tracks = [(pos_mm(a), self.xy(path[0]), path[0][2])]
        for u, v in zip(simplified, simplified[1:]):
            if u[2] != v[2]:
                location = self.xy(u)
                if any(math.dist(location,(x,y)) < 0.01 and n == net
                       for x,y,n in self.via_points):
                    continue
                via = pcbnew.PCB_VIA(self.board)
                via.SetPosition(point(*self.xy(u)))
                via.SetWidth(mm(0.7))
                via.SetDrill(mm(0.3))
                via.SetViaType(pcbnew.VIATYPE_THROUGH)
                via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                via.SetNetCode(a.GetNetCode())
                self.board.Add(via)
                self.via_points.append((*location,net))
                for layer in (0,1):
                    self.disk(layer,net,*self.xy(u),self.VIA_BLOCK_RADIUS)
            else:
                tracks.append((self.xy(u),self.xy(v),u[2]))
        tracks.append((self.xy(path[-1]),pos_mm(b),path[-1][2]))
        for start,end,layer in tracks:
            if math.dist(start,end) < 0.0001:
                continue
            edge = (tuple(start),tuple(end),layer,net)
            if edge in self.edges:
                continue
            self.edges.add(edge)
            track = pcbnew.PCB_TRACK(self.board)
            track.SetStart(point(*start))
            track.SetEnd(point(*end))
            track.SetWidth(mm(self.WIDTH))
            track.SetLayer(pcbnew.F_Cu if layer == 0 else pcbnew.B_Cu)
            track.SetNetCode(a.GetNetCode())
            self.board.Add(track)
        # Block foreign routing conservatively around every route grid cell.
        for gx,gy,layer in path:
            self.disk(layer,net,gx*self.STEP,gy*self.STEP,0.49)
        return True


def board_text(board, text, x, y, size=0.85):
    item = pcbnew.PCB_TEXT(board)
    item.SetText(text)
    item.SetPosition(point(x,y))
    item.SetTextSize(point(size,size))
    item.SetTextThickness(mm(0.12))
    item.SetLayer(pcbnew.F_SilkS)
    board.Add(item)


def make_board():
    board = pcbnew.BOARD()
    board.SetFileName(str(OUT / (NAME + ".kicad_pcb")))
    board.GetDesignSettings().SetBoardThickness(mm(1.6))
    board.GetDesignSettings().m_MinClearance = mm(0.2)
    board.GetDesignSettings().m_CopperEdgeClearance = mm(0.5)
    nets = {}
    names = {n for p in PARTS for n in p["pins"].values() if n}
    names.update('unconnected-('+p['ref']+'-Pad'+pin+')'
                 for p in PARTS for pin,net in p['pins'].items() if net is None)
    for name in sorted(names):
        info = pcbnew.NETINFO_ITEM(board,name)
        board.Add(info)
        nets[name] = info
    all_pads = []
    footprint_map = {}
    for p in PARTS:
        lib, name = p["fp"].split(":")
        fp = pcbnew.FootprintLoad(str(OUT / (lib + ".pretty")),name)
        fp.SetReference(p["ref"])
        fp.SetValue(p["value"])
        fp.GetField(pcbnew.FIELD_T_DATASHEET).SetText(p["source"])
        fp.SetFPIDAsString(p["fp"])
        fp.SetPath(pcbnew.KIID_PATH('/'+uid('root-sheet')+'/'+p['uuid']))
        fp.SetUuid(pcbnew.KIID(p["uuid"]))
        fp.SetPosition(point(*p["pos"]))
        fp.SetOrientationDegrees(p["angle"])
        board.Add(fp)
        fp.Value().SetVisible(False)
        fp.Reference().SetTextSize(point(0.85,0.85))
        fp.Reference().SetTextThickness(mm(0.12))
        fp.Reference().SetTextAngle(pcbnew.EDA_ANGLE(0,pcbnew.DEGREES_T))
        fp.Reference().SetPosition(point(p["pos"][0],p["pos"][1]-2.2))
        for pad in fp.Pads():
            net = p["pins"][pad.GetNumber()]
            if net:
                pad.SetNet(nets[net])
            else:
                pad.SetNet(nets['unconnected-('+p['ref']+'-Pad'+pad.GetNumber()+')'])
            all_pads.append(pad)
        footprint_map[p["ref"]] = fp
    # Clear relay identifiers of the top-coil hole row; identify functional groups.
    for i in range(1,5):
        fp = footprint_map['RLY'+str(i)]
        fp.Reference().SetPosition(point(PARTS[(i-1)*5]['pos'][0]+2.54,31))
    footprint_map['J4B1'].Reference().SetPosition(point(25,45.4))
    footprint_map['JDAC1'].Reference().SetPosition(point(9.8,37.2))
    footprint_map['JPWR1'].Reference().SetPosition(point(9.2,2.5))
    footprint_map['JCTRL1'].Reference().SetPosition(point(40.1,2.5))
    for i,x in enumerate((8,21,34,47),1):
        footprint_map['D'+str(i)].Reference().SetPosition(point(x+7.2,17))
    for ref,xy in {'Q5':(20,2.2),'Q6':(23,6.3),'RPG1':(15.6,7.4),
                   'RG6':(31,2),'RPD6':(30.5,5.1),'RG2':(16.4,10),
                   'RG3':(31,11.7)}.items():
        footprint_map[ref].Reference().SetPosition(point(*xy))
    for start,end in (((0,0),(60,0)),((60,0),(60,50)),((60,50),(0,50)),((0,50),(0,0))):
        line = pcbnew.PCB_SHAPE(board)
        line.SetShape(pcbnew.SHAPE_T_SEGMENT)
        line.SetStart(point(*start))
        line.SetEnd(point(*end))
        line.SetWidth(mm(0.05))
        line.SetLayer(pcbnew.Edge_Cuts)
        board.Add(line)
    # Project-local simple NPTH mounting holes, no ground annulus.
    for i,(x,y) in enumerate(((3,3),(57,3),(3,47),(57,47)),1):
        fp = pcbnew.FOOTPRINT(board)
        fp.SetReference('H'+str(i))
        fp.SetValue('MountingHole_3.2mm')
        fp.SetPosition(point(x,y))
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        fp.SetExcludedFromBOM(True)
        fp.SetExcludedFromPosFiles(True)
        fp.SetBoardOnly(True)
        pad = pcbnew.PAD(fp)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetSize(point(3.2,3.2))
        pad.SetDrillSize(point(3.2,3.2))
        # Copy the cached static mask before mutation; mutating AllCuMask()
        # directly makes serialization lose soldermask openings on THT pads.
        layers = pcbnew.LSET(pcbnew.LSET.AllCuMask())
        layers.AddLayer(pcbnew.F_Mask)
        layers.AddLayer(pcbnew.B_Mask)
        pad.SetLayerSet(layers)
        pad.SetPosition(point(x,y))
        fp.Add(pad)
        board.Add(fp)
        drawing=pcbnew.PCB_SHAPE(board)
        drawing.SetShape(pcbnew.SHAPE_T_CIRCLE)
        drawing.SetStart(point(x,y))
        drawing.SetEnd(point(x+1.6,y))
        drawing.SetWidth(mm(0.12))
        drawing.SetLayer(pcbnew.Dwgs_User)
        board.Add(drawing)
    board_text(board,'BENCH ONLY / NO VEHICLE',31,48,1.0)
    board_text(board,'CONTACTS 0-5V <=1mA',30,34,0.85)
    board_text(board,'MiLa PASSIVE BYPASS Rev A',30,38,0.85)
    # Dense analog/signal routing first, followed by local gates, then supply buses.
    bynet = {}
    for pad in all_pads:
        if pad.GetNetname():
            bynet.setdefault(pad.GetNetname(),[]).append(pad)
    order = sorted(bynet, key=lambda n:(-2 if n == 'GND' else -1 if n in ('J4_18','J4_19') else
                                       0 if n.startswith(('J4_','J5_','J6_')) else
                                       2 if n == 'COIL_5V' else 1,
                                       -len(bynet[n]),n))
    router = Router(board,all_pads)
    failed = []
    for net in order:
        pads = bynet[net]
        connected = [pads[0]]
        remaining = pads[1:]
        while remaining:
            candidates = sorted((math.dist(pos_mm(a),pos_mm(b)),i,a,b)
                                for i,b in enumerate(remaining) for a in connected)
            success = False
            for _,i,a,b in candidates:
                if router.route(a,b,net):
                    connected.append(b)
                    remaining.pop(i)
                    success = True
                    break
            if not success:
                failed.append(net)
                break
        print('Routed',net,'pads',len(pads),'OK' if net not in failed else 'FAILED',flush=True)
    pcbnew.SaveBoard(str(OUT / (NAME + '.kicad_pcb')),board)
    (OUT / 'routing_summary.json').write_text(json.dumps({
        'failed_nets':failed,'net_count':len(bynet),'tracks':len(list(board.GetTracks())),
        'board_mm':[60,50],'route_track_mm':router.WIDTH,'copper_layers':2},indent=2)+'\n')
    if failed:
        print('Routing incomplete: '+', '.join(failed),flush=True)


def manifests():
    with (OUT / 'bom.csv').open('w',newline='') as f:
        w=csv.writer(f)
        w.writerow(['reference','quantity','value','footprint','manufacturer_datasheet','scope','tolerance'])
        for p in PARTS:
            w.writerow([p['ref'],1,p['value'],p['fp'],p['source'],'isolated bench only',
                        '1%' if p['fp']=='MiLa_Bench:R_0805' else ''])
    with (OUT / 'pin_net_map.csv').open('w',newline='') as f:
        w=csv.writer(f)
        w.writerow(['reference','pin','net','original_terminal_or_role'])
        for p in PARTS:
            for pin,net in sorted(p['pins'].items(),key=lambda it:int(it[0])):
                role = (net.replace('_','-') if net and net.startswith(('J4_','J5_','J6_'))
                        else 'intentionally unused contact' if net is None else net)
                w.writerow([p['ref'],pin,net or '',role])
    (OUT / (NAME+'.kicad_pro')).write_text(json.dumps({
        'meta':{'filename':NAME+'.kicad_pro','version':1},
        'board':{'design_settings':{'rules':{
            'min_clearance':0.2,'min_track_width':0.25,'min_via_diameter':0.7,
            'min_through_hole_diameter':0.3,'min_hole_clearance':0.25,
            'min_copper_edge_clearance':0.5,'min_silk_clearance':0.1,
            'min_silk_text_height':0.8,'min_silk_text_thickness':0.1}}},
        'net_settings':{'classes':[{'name':'Default','clearance':0.2,
            'track_width':0.25,'via_diameter':0.7,'via_drill':0.3}], 'version':4}
    },indent=2)+'\n')


def validate_export():
    validation = OUT/'validation'
    preview = OUT/'previews'
    manufacturing = OUT/'manufacturing_bench_only'
    for directory in (validation,preview,manufacturing):
        directory.mkdir(exist_ok=True)
    sch = str(OUT/(NAME+'.kicad_sch'))
    pcb = str(OUT/(NAME+'.kicad_pcb'))
    jobs = [
        ['sch','erc','--format','json','--severity-all','--exit-code-violations','-o',str(validation/'erc.json'),sch],
        ['pcb','drc','--schematic-parity','--format','json','--severity-all','--exit-code-violations','-o',str(validation/'drc.json'),pcb],
        ['sch','export','netlist','--format','kicadxml','-o',str(OUT/'passive_bypass.net'),sch],
        ['sch','export','svg','-o',str(preview) + '/',sch],
        ['sch','export','pdf','-o',str(preview/'schematic.pdf'),sch],
        ['pcb','export','svg','--layers','F.Cu,F.Silkscreen,User.Drawings,Edge.Cuts','--fit-page-to-board','--exclude-drawing-sheet','--mode-single','-o',str(preview/'board_top.svg'),pcb],
        ['pcb','export','svg','--layers','B.Cu,Edge.Cuts','--fit-page-to-board','--exclude-drawing-sheet','--mode-single','-o',str(preview/'board_bottom.svg'),pcb],
        ['pcb','export','svg','--layers','F.Fab,F.Silkscreen,User.Drawings,Edge.Cuts','--sketch-pads-on-fab-layers','--fit-page-to-board','--exclude-drawing-sheet','--mode-single','-o',str(preview/'board_assembly.svg'),pcb],
    ]
    results=[]
    for args in jobs:
        r=subprocess.run([str(CLI)]+args,text=True,capture_output=True)
        results.append({'command':args,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        print(args[:3],r.returncode,r.stdout.strip(),r.stderr.strip(),flush=True)
    # Manufacturing exports are generated only following successful rules/parity checks.
    if all(r['exit_code']==0 for r in results[:3]):
        extra = [
            ['pcb','export','gerbers','-o',str(manufacturing)+'/',pcb],
            ['pcb','export','drill','--excellon-separate-th','--generate-map','--map-format','svg','--generate-report','--report-path',str(manufacturing/'drill_report.txt'),'-o',str(manufacturing)+'/',pcb],
            ['pcb','export','pos','--format','csv','--units','mm','--side','both','-o',str(manufacturing/'positions.csv'),pcb],
        ]
        for args in extra:
            r=subprocess.run([str(CLI)]+args,text=True,capture_output=True)
            results.append({'command':args,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
            print(args[:3],r.returncode,r.stdout.strip(),r.stderr.strip(),flush=True)
        previous_combined_drill=manufacturing/(NAME+'.drl')
        if previous_combined_drill.exists() and results[-2]['exit_code']==0:
            previous_combined_drill.unlink()
    (validation/'commands.json').write_text(json.dumps(results,indent=2)+'\n')
    return all(r['exit_code']==0 for r in results)


def readme():
    (OUT/'README.md').write_text('''# MiLa passive bypass bench board — revision A

This is an isolated, current-limited simulator contact board. **No vehicle use.**
It preserves the three existing control domains and six passive NC paths using
four nonlatching Omron G6K-2P-Y DC5 relays. RLY3/RLY4 each use one pole; their
second poles are explicitly unconnected. K7/K8 independence is preserved.

## Electrical envelope and interfaces

- JPWR1 pin 1: regulated 4.75–5.25 V after an external physical series-enable
  switch. JPWR1 pin 2: logic/coil GND. Set the supply current limit to 150 mA.
- JCTRL1: 1 REQ_GROUP, 2 REQ_K7, 3 REQ_K8, 4 COIL_PERMIT, 5 GND,
  6 CARRIER_5V_FEEDBACK (direct connection to 5V_RAW). Digital inputs 1–4
  are active high and nominal 3.3 V, including COIL_PERMIT from the supervisor.
  Feedback pin 6 carries up to 5.25 V to the external
  resistor-divider monitor only; never connect it to an ESP GPIO or supply it.
  HIGH must be at least 2.60 V at the board header, LOW at most 0.4 V.
  All N-FET gates have 330-ohm series resistance. Q1–Q4 off bias is 10 kohm;
  Q6 permit-gate off bias RPD6 is 82 kohm, matched to the external supervisor's
  low-load LVC output guarantee. P-FET gate-to-source bias RPG1 stays 10 kohm.
  All carrier resistors require 1% tolerance, including RPD6; the gate-voltage
  bounds must not be extended to unspecified resistor substitutions.
- J4B1 is a 12-pin bench subset of original J4; JDAC1 is a 4-pin bench subset of
  original J5/J6. **Neither connector shares the original physical pinout.**
  Use `pin_net_map.csv`; names preserve canonical original connector terminals.
  Headers are unshrouded and unkeyed: mark pin 1, check the fixture orientation
  against the assembly drawing, and add cable strain relief before testing.
- Each contact signal is limited to 0–5 V and 1 mA on the simulator. Contacts
  do not connect to board GND. Provide source/load references externally.
- External independent supervisor supplies COIL_PERMIT. This board does not
  implement watchdog, freshness, boot/brownout qualification, DAC validation,
  dual-channel plausibility, or a vehicle safety case.
- No energy storage or external source may feed COIL_5V. The P-FET body diode
  does not provide reverse-current blocking. Its source is 5V_RAW and drain is
  COIL_5V; reversing it defeats the power cutoff.

## Operation

COIL_PERMIT low or disconnected turns off the common high-side coil feed.
With COIL_PERMIT high, REQ_GROUP energizes RLY1/RLY2, REQ_K7 RLY3, and REQ_K8
RLY4. Healthy unpowered contacts connect 3–2 and 6–7; energized contacts connect
3–4 and 6–5. Relay supply removal eventually restores NC after mechanical
release and bounce. This is not instantaneous or immune to welded contacts.

The supervisor senses JCTRL1 pin 6 through its divider. Complete loss of this
control header or JPWR1 power drops carrier feedback and clears its ARM latch;
reconnection requires a new valid heartbeat qualification and manual ARM edge.
This does not detect every individual broken conductor or intermittent fault.

Flyback diode cathodes connect to COIL_5V, anodes to their coil drains. These
diodes protect drivers but lengthen release. Measure release/bounce/skew on
the actual assembled board, including high-side cutoff with a low-side stuck
on. K7/K8 mixed states remain reachable and are not declared vehicle-safe.

## Manufacturer pinout and local footprint correction

G6K-2P-Y DC5 coil 1(+), 8(-); pole A COM 3/NC 2/NO 4; pole B COM 6/NC 7/NO 5.
The manufacturer bottom-view drawing gives hole rows 0, 3.2, 5.4, 7.6 mm and
opposing row spacing 5.08 mm. The installed KiCad 10 G6K-2P-Y footprint has
NC pads 2/7 at 3.0 mm; the project-local footprint corrects them to 3.2 mm.
Hole diameter 0.85 mm and pad diameter 1.7 mm. Inspect a 1:1 print and real
relay before ordering. All FETs use SOT-23 pins 1 gate, 2 source, 3 drain.

Manufacturer sources:

- [Omron G6K](https://omronfs.omron.com/en_US/ecb/products/pdf/en-g6k.pdf),
  manufacturer THT G6K-2P-Y drawing and terminal arrangement.
- [AO3400A](https://www.aosmd.com/res/data_sheets/AO3400A.pdf)
- [AO3401A](https://www.aosmd.com/res/data_sheets/AO3401A.pdf)
- [Vishay 1N4148W-E3-08](https://www.vishay.com/docs/86356/1n4148w.pdf)

## CAD and verification

The 60×50 mm, two-layer, 1.6-mm board uses 0.25-mm traces, 0.20-mm clearance,
0.70/0.30-mm vias, and four 3.2-mm unplated mounting holes. Mechanical contacts
are separated from logic by the relay insulation; no semiconductor is placed
in an NC/COM/NO signal path. Bench headers are 2.54-mm friction-fit prototypes,
not an automotive connector solution. The PCB is reviewed against the same
component/pin manifest that creates the editable schematic and BOM.

Rebuild with KiCad's bundled Python:

```sh
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9 tools/build_passive_bypass_board.py
```

Review `validation/erc.json`, `validation/drc.json` including schematic parity,
`passive_bypass.net`, and `validation/commands.json`. Bench manufacturing files
under `manufacturing_bench_only/` are exported only if ERC/DRC/netlist commands
pass. Electrical CAD checks do not establish relay behavior or vehicle safety.
Original PCB1/PCB2 files and libraries are preserved.

## Required assembled-board acceptance

1. Without any supply, map all six NC connections and confirm all NO paths
   open, contact-to-logic isolation, no misplaced/mirrored relay pins.
2. With simulator sources/load current limited, check all eight combinations
   of REQ_GROUP/REQ_K7/REQ_K8 under valid permit against the canonical table.
3. Drop each request, permit, series-enable, power, and logic source separately;
   capture contact disconnect/NC restoration, bounce, skew, and coil current.
4. Hold each low-side driver on and remove high-side permit; then force Q5 on
   and verify request removal still releases each coil. Neither single cutoff
   failure is declared fail-safe against a concurrent other-driver fault.
5. Sweep 4.75–5.25 V with maximum four-coil load. Check thermal rise and verify
   the external supervisor withdraws permit before coil behavior is ambiguous.
6. Inspect soldering/polarities; perform 100%-net continuity before sources are
   attached. Do not connect a vehicle when these bench tests pass.
''')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    app=wx.App(False)
    define_parts()
    symbols=libraries()
    manifests()
    make_schematic(symbols)
    make_board()
    readme()
    ok=validate_export()
    print('CAD validation PASS' if ok else 'CAD validation FAILED; see JSON reports',flush=True)
    return 0 if ok else 1


if __name__=='__main__':
    raise SystemExit(main())
