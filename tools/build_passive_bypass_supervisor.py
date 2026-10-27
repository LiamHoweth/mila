#!/usr/bin/env python3
"""Generate the MiLa bench supervisor schematic and auditable pin-net tables.

This is an electrical bench reference. It does not emit a fabrication PCB or
claim independent command/plausibility supervision. Symbols are embedded,
numbered from manufacturer datasheets, and deliberately drawn as pin blocks.
"""
from __future__ import annotations

import csv
import json
import argparse
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware" / "passive_bypass_supervisor_rev_a"
NAME = "mila_passive_bypass_supervisor_rev_a"
NS = uuid.UUID("24787691-9d6f-4366-ae8a-a4d2872b27b8")


def uid(key: str) -> str:
    return str(uuid.uuid5(NS, key))


def q(value: str) -> str:
    return json.dumps(value)


@dataclass
class Part:
    ref: str
    value: str
    role: str
    footprint: str
    source: str
    pins: list[tuple[str, str, str, str | None]]
    x: float = 0
    y: float = 0
    board: bool = True
    bom: bool = True


def pin(number, name, net, kind="input"):
    return (str(number), name, kind, net)


parts: list[Part] = []


def add(ref, value, role, footprint, source, pins, x=0, y=0, **kwargs):
    p = Part(ref, value, role, footprint, source, pins, x, y, **kwargs)
    parts.append(p)
    return p


SC5 = "Package_TO_SOT_SMD:SOT-353_SC-70-5"
SC6 = "Package_TO_SOT_SMD:SOT-363_SC-70-6"
TS14 = "Package_SO:TSSOP-14_4.4x5mm_P0.65mm"
RFP = "Resistor_SMD:R_0603_1608Metric"
CFP = "Capacitor_SMD:C_0603_1608Metric"
SUP = "https://www.ti.com/lit/ds/symlink/tps3808-q1.pdf"
WD = "https://www.ti.com/lit/ds/symlink/tps3430-q1.pdf"
FF = "https://www.ti.com/lit/ds/symlink/sn74lvc74a-q1.pdf"
AND = "https://www.ti.com/lit/ds/symlink/sn74lvc1g08-q1.pdf"
BUF = "https://www.ti.com/lit/ds/symlink/sn74lvc1g17-q1.pdf"
INV = "https://www.ti.com/lit/ds/symlink/sn74lvc2g14-q1.pdf"
NOR = "https://www.ti.com/lit/ds/symlink/sn74lvc1g27.pdf"
DIODE = "https://www.diodes.com/datasheet/download/BAS70.pdf"

add("U1", "TPS3430WQDRCRQ1", "Independent window watchdog; fixed hardware settings",
    "Package_SON:VSON-10-1EP_3x3mm_P0.5mm_EP1.65x2.4mm", WD,
    [pin(1,"VDD1","V3V3","power_in"),pin(2,"CWD","WD_CWD"),pin(3,"SET0","GND"),
     pin(4,"CRST","WD_CRST"),pin(5,"GND","GND","power_in"),pin(6,"SET1","GND"),
     pin(7,"WDI","WDI"),pin(8,"WDO_N","HEALTH_N","open_collector"),
     pin(9,"NC",None,"no_connect"),pin(10,"VDD2","V3V3","power_in"),pin(11,"EP","GND","passive")], 180,60)
add("U2","TPS3808G33QDBVRQ1","3.3 V and ESP hardware reset supervisor", "Package_TO_SOT_SMD:SOT-23-6",SUP,
    [pin(1,"RESET_N","HEALTH_N","open_collector"),pin(2,"GND","GND","power_in"),
     pin(3,"MR_N","ESP_RESET_N"),pin(4,"CT","PG33_CT"),pin(5,"SENSE","V3V3"),pin(6,"VDD","V3V3","power_in")], 300,60)
add("U3","TPS3808G01QDBVRQ1","5 V adjustable monitor supplied by isolated diode-OR of both rails", "Package_TO_SOT_SMD:SOT-23-6",SUP,
    [pin(1,"RESET_N","HEALTH_N","open_collector"),pin(2,"GND","GND","power_in"),
     pin(3,"MR_N","V_PG5_SUP"),pin(4,"CT","PG5_CT"),pin(5,"SENSE","V5_SENSE"),pin(6,"VDD","V_PG5_SUP","power_in")], 420,60)
add("D1","BAS70-05-7-F","Low-leakage supply OR keeps 5 V monitor alive when either rail disappears", "Package_TO_SOT_SMD:SOT-23",DIODE,
    [pin(1,"A1","V3V3","passive"),pin(2,"A2","V5_SUP","passive"),pin(3,"K1_K2","V_PG5_SUP","passive")], 780,60)


def schmitt(ref, role, a, y, x, yy):
    return add(ref,"SN74LVC1G17QDCKRQ1",role,SC5,BUF,
        [pin(1,"NC",None,"no_connect"),pin(2,"A",a),pin(3,"GND","GND","power_in"),
         pin(4,"Y",y,"output"),pin(5,"VCC","V3V3","power_in")],x,yy)


schmitt("U4","Clean open-drain fault edges before ordinary logic","HEALTH_N","HEALTH_OK",540,60)
schmitt("U5","Clean physical enable auxiliary-contact edges","DEADMAN_RAW","DEADMAN_OK",660,60)
add("U6","SN74LVC2G14IDCKRQ1","Invert WDI falling edges and debounce physical ARM",SC6,INV,
    [pin(1,"1A","WDI"),pin(2,"GND","GND","power_in"),pin(3,"2A","ARM_RC"),
     pin(4,"2Y","ARM_CLK","output"),pin(5,"VCC","V3V3","power_in"),pin(6,"1Y","HB_CLK","output")], 60,150)
add("U7","SN74LVC1G27DCKR","All three relay requests must be LOW at ARM edge; catalog bench part",SC6,NOR,
    [pin(1,"A","REQ_L"),pin(2,"GND","GND","power_in"),pin(3,"B","REQ_7"),
     pin(4,"Y","ZERO_REQ","output"),pin(5,"VCC","V3V3","power_in"),pin(6,"C","REQ_8")],180,150)


def and_gate(ref, role, a, b, y, x, yy):
    return add(ref,"SN74LVC1G08QDCKRQ1",role,SC5,AND,
        [pin(1,"A",a),pin(2,"B",b),pin(3,"GND","GND","power_in"),
         pin(4,"Y",y,"output"),pin(5,"VCC","V3V3","power_in")],x,yy)


and_gate("U8","Combine rail/watchdog health and firmware READY","HEALTH_OK","READY","HEALTH_READY",300,150)
and_gate("U9","Async clear source includes physical held enable","HEALTH_READY","DEADMAN_OK","QUALIFIED",420,150)


def flipflop(ref, role, clock1, data1, out1, clock2, data2, out2, x, yy, unused2=False):
    return add(ref,"SN74LVC74AQPWRG4Q1",role,TS14,FF,
       [pin(1,"1CLR_N","QUALIFIED"),pin(2,"1D",data1),pin(3,"1CLK",clock1),
        pin(4,"1PRE_N","V3V3"),pin(5,"1Q",out1,"output"),pin(6,"1Q_N",None,"output"),
        pin(7,"GND","GND","power_in"),pin(8,"2Q_N",None,"output"),pin(9,"2Q",out2,"output"),
        pin(10,"2PRE_N","V3V3"),pin(11,"2CLK",clock2),pin(12,"2D",data2),
        pin(13,"2CLR_N","GND" if unused2 else "QUALIFIED"),pin(14,"VCC","V3V3","power_in")],x,yy)


flipflop("U10","Two WDI falling edges after READY/enable; one full inter-edge cycle",
    "HB_CLK","V3V3","HB_ONE","HB_CLK","HB_ONE_SAFE","HB_GOOD",540,150)
flipflop("U11","Manual ARM edge latch; faults clear without automatic restart",
    "ARM_CLK","ARM_D","ARMED","GND","GND",None,660,150,unused2=True)
and_gate("U12","ARM edge accepted only after heartbeat cycle and zero requests","HB_GOOD","ZERO_REQ","ARM_D",60,240)
and_gate("U13","3.3 V lightly loaded permission driver; output is for carrier gate only","ARMED","QUALIFIED","PERMIT_DRIVER",180,240)
schmitt("U14","Buffered HB_ONE delay provides positive same-clock DFF hold margin","HB_STAGE_RC","HB_ONE_SAFE",780,240)


def header(ref, role, nets, x, yy):
    return add(ref,f"BENCH_1x{len(nets):02d}",role,
        f"Connector_PinHeader_2.54mm:PinHeader_1x{len(nets):02d}_P2.54mm_Vertical","",
        [pin(i+1,n,n,"passive") for i,n in enumerate(nets)],x,yy)


header("J1","ESP interface: shared 3.3 V rail, no GPIO mapping assumed",["GND","V3V3","ESP_RESET_HEADER","WDI_HEADER","READY_HEADER","REQ_L","REQ_7","REQ_8"],60,60)
header("J2","Protected regulated bench 5 V upstream rail",["V5_SUP","GND"],300,240)
header("J3","External held enable: pole A 1-2 physically cuts coil feed; pole B 3-4 reports enable",["V5_SUP","V5_COIL_SWITCHED","V3V3","DEADMAN_HEADER"],420,240)
header("J4","Physical normally-open ARM pushbutton shorts 1-2 only",["ARM_SW","GND"],540,240)
header("J5","Relay board interface; physical coil feed and returned carrier 5 V continuity sense",["GND","V5_COIL_SWITCHED","COIL_PERMIT","REQ_L","REQ_7","REQ_8","CARRIER_5V_FEEDBACK"],660,240)
header("J6","3.3 V test/status points only",["GND","HEALTH_OK","QUALIFIED","HB_GOOD","ARMED","ZERO_REQ"],780,150)


def passive(ref,value,role,a,b):
    add(ref,value,role,RFP if ref.startswith("R") else CFP,"",
        [pin(1,"1",a,"passive"),pin(2,"2",b,"passive")])


for ref,val,role,a,b in [
    ("R1","10k 1%","Watchdog fixed window setting","V3V3","WD_CWD"),
    ("R2","10k 1%","Watchdog fixed reset setting","V3V3","WD_CRST"),
    ("R3","100k 1%","300 ms nominal PG33 reset release","V3V3","PG33_CT"),
    ("R4","100k 1%","300 ms nominal PG5 reset release","V_PG5_SUP","PG5_CT"),
    ("R5","10k 1%","Shared open-drain health pull-up","V3V3","HEALTH_N"),
    ("R6","100k 1%","ARM default released; 100 ms nominal release RC","V3V3","ARM_RC"),
    ("R7","1k 1%","ARM press current/RC limit","ARM_RC","ARM_SW"),
    ("R8","10k 1%","Disconnected enable defaults LOW","DEADMAN_RAW","GND"),
    ("R9","10k 1%","READY defaults LOW","READY","GND"),
    ("R10","10k 1%","WDI defaults LOW","WDI","GND"),
    ("R11","10k 1%","Relay request default LOW","REQ_L","GND"),
    ("R12","10k 1%","Relay request default LOW","REQ_7","GND"),
    ("R13","10k 1%","Relay request default LOW","REQ_8","GND"),
    ("R14","100 1%","Short local WDI wire series damping","WDI_HEADER","WDI"),
    ("R15","100 1%","Short local READY wire series damping","READY_HEADER","READY"),
    ("R16","1k 1%","ESP hardware reset input current limit","ESP_RESET_HEADER","ESP_RESET_N"),
    ("R17","100 1%","Physical enable sense series damping","DEADMAN_HEADER","DEADMAN_RAW"),
    ("R18","1k 1%","Permit initial MOS gate-current limit and series damping","PERMIT_DRIVER","COIL_PERMIT"),
    ("R19","82k 1%","Light permission load; parallel carrier 82k provides passive LOW","COIL_PERMIT","GND"),
    ("R20","10k 1%","Permit-gate ARMED input passive LOW","ARMED","GND"),
    ("R21","10k 1%","Permit-gate QUALIFIED input passive LOW","QUALIFIED","GND"),
    ("R22","100k 0.1%","Returned carrier 5 V divider upper resistor; ~4.655 V threshold","CARRIER_5V_FEEDBACK","V5_SENSE"),
    ("R23","9.53k 0.1%","5 V monitor divider lower resistor","V5_SENSE","GND"),
    ("R24","1k 1%","Heartbeat stage hold-time margin delay","HB_ONE","HB_STAGE_RC"),
]: passive(ref,val,role,a,b)

for i in range(1,14):
    rail = "V_PG5_SUP" if i == 3 else "V3V3"
    passive(f"C{i}","100nF X7R 10V",f"Place at U{i} supply pin(s)",rail,"GND")
passive("C14","1uF X7R 10V","ARM debounce capacitor; verify contact bounce on bench","ARM_RC","GND")
passive("C15","1uF X7R 10V","Local 3.3 V decoupling; no hold-up promise","V3V3","GND")
passive("C16","1uF X7R 10V","Upstream 5 V local decoupling; not downstream of enable switch","V5_SUP","GND")
passive("C17","1nF C0G 10V","5 V SENSE divider noise filter; ~8.7 us nominal RC","V5_SENSE","GND")
passive("C18","100pF C0G 5% 10V","Heartbeat stage delay; ~100 ns nominal RC before Schmitt buffer","HB_STAGE_RC","GND")
passive("C19","100nF X7R 10V","Place at U14 supply pin","V3V3","GND")

for i,p in enumerate([p for p in parts if p.ref[0] in "RC"]):
    p.x=50 + (i%10)*77
    p.y=320 + (i//10)*47

for i,n in enumerate(("V3V3","V5_SUP","GND","V_PG5_SUP")):
    add(f"#PWR{i+1}","EXTERNAL_SUPPLY_FLAG",f"Bench externally driven {n}","","",
        [pin(1,"PWR",n,"power_out")],60+i*120,550,board=False,bom=False)


def layout(p: Part):
    left=[]; right=[]
    for entry in p.pins:
        (right if entry[2] in ("output","open_collector") else left).append(entry)
    w = 5.08 if len(p.pins)==2 else 20.32
    step=2.54
    h=max(5.08,(max(len(left),len(right))-1)*step/2+3.81)
    positions=[]
    for entries,x,angle in ((left,-w-2.54,0),(right,w+2.54,180)):
        for i,entry in enumerate(entries):
            yy=(len(entries)-1)*step/2-i*step
            positions.append((entry,x,yy,angle))
    return w,h,positions


def embedded(p: Part) -> str:
    w,h,positions=layout(p)
    symbol_name=f"MiLaBench:{p.ref.replace('#','')}_BLOCK"
    body=[f'(symbol {q(symbol_name)} (pin_names (offset 0.8)) (exclude_from_sim no) (in_bom {"yes" if p.bom else "no"}) (on_board {"yes" if p.board else "no"})',
      '(property "Reference" "U" (at 0 0 0) (effects (font (size 1.27 1.27))))',
      f'(property "Value" {q(p.value)} (at 0 0 0) (effects (font (size 1.27 1.27))))',
      f'(symbol {q(p.ref.replace("#","")+"_BLOCK_0_1")} (rectangle (start {-w} {h}) (end {w} {-h}) (stroke (width 0.254) (type default)) (fill (type background))))',
      f'(symbol {q(p.ref.replace("#","")+"_BLOCK_1_1")}']
    for (number,name,kind,net),x,y,angle in positions:
        body.append(f'(pin {kind} line (at {x} {y} {angle}) (length 2.54) (name {q(name)} (effects (font (size 1.0 1.0)))) (number {q(number)} (effects (font (size 1.0 1.0)))))')
    body += [')',')']
    return '\n'.join(body)


def placement(p: Part):
    w,h,positions=layout(p)
    rootid=uid("root")
    pid=uid(p.ref)
    libid=f"MiLaBench:{p.ref.replace('#','')}_BLOCK"
    lines=[f'(symbol (lib_id {q(libid)}) (at {p.x} {p.y} 0) (unit 1) (in_bom {"yes" if p.bom else "no"}) (on_board {"yes" if p.board else "no"}) (dnp no) (uuid {q(pid)})',
      f'(property "Reference" {q(p.ref)} (at {p.x} {p.y-h-7.62} 0) (effects (font (size 1.27 1.27))))',
      f'(property "Value" {q(p.value)} (at {p.x} {p.y-h-5.08} 0) (effects (font (size 1.0 1.0))))',
      f'(property "Footprint" {q(p.footprint)} (at {p.x} {p.y} 0) (effects (font (size 1.27 1.27)) hide))',
      f'(property "Datasheet" {q(p.source)} (at {p.x} {p.y} 0) (effects (font (size 1.27 1.27)) hide))',
      f'(property "Description" {q(p.role)} (at {p.x} {p.y} 0) (effects (font (size 1.27 1.27)) hide))']
    for (number,*_),*unused in positions:
        lines.append(f'(pin {q(number)} (uuid {q(uid(p.ref+"pin"+number))}))')
    lines.append(f'(instances (project {q(NAME)} (path {q("/"+rootid)} (reference {q(p.ref)}) (unit 1)))) )')
    for (number,name,kind,net),x,y,angle in positions:
        ax=round(p.x+x,4); ay=round(p.y-y,4)
        if net is None:
            lines.append(f'(no_connect (at {ax} {ay}) (uuid {q(uid(p.ref+"nc"+number))}))')
            continue
        ex=round(ax+(-3.81 if x<0 else 3.81),4)
        lines.append(f'(wire (pts (xy {ax} {ay}) (xy {ex} {ay})) (stroke (width 0) (type default)) (uuid {q(uid(p.ref+"wire"+number))}))')
        rot=0 if x>0 else 180
        lines.append(f'(label {q(net)} (at {ex} {ay} {rot}) (effects (font (size 1.0 1.0)) (justify left bottom)) (uuid {q(uid(p.ref+"label"+number))}))')
    return '\n'.join(lines)


def write_csv(path:Path,fieldnames,rows):
    with path.open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fieldnames); writer.writeheader(); writer.writerows(rows)


def verify_netlist(path: Path):
    """Compare actual KiCad exported connectivity against all specified pins."""
    expected = {(p.ref, n): net for p in parts if not p.ref.startswith("#")
                for n, name, kind, net in p.pins if net is not None}
    actual = {(node.attrib["ref"], node.attrib["pin"]): net.attrib["name"].lstrip("/")
              for net in ET.parse(path).findall("./nets/net") for node in net.findall("node")}
    actual = {key: value for key, value in actual.items() if not key[0].startswith("#")}
    unused = {(p.ref, n) for p in parts if not p.ref.startswith("#")
              for n, name, kind, net in p.pins if net is None}
    wrong_nc = {key: actual.get(key) for key in unused
                if not actual.get(key, "").startswith("unconnected-")}
    if wrong_nc:
        raise SystemExit(f"Intentionally unused pins are unexpectedly connected: {wrong_nc!r}")
    actual = {key: value for key, value in actual.items() if key not in unused}
    missing = {key: value for key, value in expected.items() if actual.get(key) != value}
    extra = {key: value for key, value in actual.items() if expected.get(key) != value}
    if missing or extra:
        raise SystemExit(f"Pin-net verification failed: mismatch={missing!r}; unexpected={extra!r}")
    print(f"PASS: {len(expected)} populated component pin nets match KiCad export; {len(unused)} NC pins checked")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-netlist", type=Path, help="Verify an actual KiCad XML netlist instead of regenerating")
    args = parser.parse_args()
    if args.verify_netlist:
        verify_netlist(args.verify_netlist)
        return
    OUT.mkdir(parents=True,exist_ok=True)
    for p in parts:
        p.x=round(p.x/1.27)*1.27
        p.y=round(p.y/1.27)*1.27
    schematic=[f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {q(uid("root"))}) (paper "A1")',
      '(title_block (title "MiLa passive bypass external supervisor - bench Rev A") (date "2026-10-07") (rev "A BENCH ONLY") (company "MiLa") (comment 1 "Isolated bench reference; physical acceptance pending; no vehicle authorization,") (comment 2 "no independent analog plausibility validator"))',
      '(lib_symbols',*[embedded(p) for p in parts],')']
    for p in parts: schematic.append(placement(p))
    for i,(y,text) in enumerate([(15,"BENCH ONLY: regulated 5.0 V + shared ESP 3.3 V; keep disconnected from vehicle."),
        (20,"Hardware: window watchdog + both rail supervisors + physical held enable + READY -> asynchronous latch clear."),
        (25,"Two post-READY WDI falling edges -> HB_GOOD; fresh physical ARM rising edge with requests all LOW -> ARMED."),
        (30,"3.3 V COIL_PERMIT is only for relay gate input. External enable pole J3(1-2) physically interrupts coil power."),
        (35,"J5 pin 7 returns carrier post-enable/pre-cutoff 5 V: R22 monitors actual feed; never connect this 5 V wire to ESP."),
        (95,"A. POWER AND WATCHDOG: rail monitors remain independent of the ESP application."),
        (200,"B. QUALIFICATION AND ARM: asynchronous fault clear; two heartbeat stages; fresh physical ARM edge."),
        (280,"J3: external held DPST-NO enable, no jumper in deployed setup. J4: separate normally-open ARM button."),
        (285,"Output is not a semantic command/plausibility monitor. Driver/relay/ECU timing requires measured bench validation."),
        (290,"C. OUTPUT AND INTERFACES: 3.3 V permission is for the carrier MOSFET gate only; carrier feedback is 5 V."),
        (295,"D. PASSIVES: connected by named nets; place each U's 100 nF physically at its supply pins."),
        (535,"E. SUPPLY FLAGS: rails are externally driven or passively fed; flags are not physical components.")]):
        schematic.append(f'(text {q(text)} (at 20 {y} 0) (effects (font (size 1.27 1.27)) (justify left)) (uuid {q(uid("note"+str(i)))}))')
    schematic.append('(embedded_fonts no) )')
    (OUT/f"{NAME}.kicad_sch").write_text('\n'.join(schematic)+"\n")
    library='(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor")\n'+ '\n'.join(
        embedded(p).replace(q(f"MiLaBench:{p.ref.replace('#','')}_BLOCK"),q(f"{p.ref.replace('#','')}_BLOCK"),1) for p in parts)+'\n)\n'
    (OUT/"MiLaBench.kicad_sym").write_text(library)
    (OUT/"sym-lib-table").write_text('(sym_lib_table (version 7) (lib (name "MiLaBench") (type "KiCad") (uri "${KIPRJMOD}/MiLaBench.kicad_sym") (options "") (descr "Bench supervisor pin blocks from manufacturer data")))\n')
    project_path = OUT/f"{NAME}.kicad_pro"
    project = json.loads(project_path.read_text()) if project_path.exists() else {}
    project["meta"] = {"filename":f"{NAME}.kicad_pro","version":3}
    design = project.setdefault("board", {}).setdefault("design_settings", {})
    design.setdefault("meta", {})["version"] = 2
    design["drc_exclusions"] = []
    design.setdefault("rules", {}).update({
        "min_clearance":0.2, "min_track_width":0.25, "min_via_diameter":0.7,
        "min_through_hole_diameter":0.3, "min_hole_clearance":0.25,
        "min_hole_to_hole":0.25, "min_copper_edge_clearance":0.5,
        "min_silk_clearance":0.1, "min_text_height":0.8, "min_text_thickness":0.1})
    net_settings = project.setdefault("net_settings", {})
    net_settings.setdefault("meta", {})["version"] = 5
    classes = net_settings.setdefault("classes", [])
    default = next((cls for cls in classes if cls.get("name") == "Default"), None)
    if default is None:
        default = {"name":"Default"}
        classes.append(default)
    default.update({"clearance":0.2,"track_width":0.25,"via_diameter":0.7,"via_drill":0.3})
    project_path.write_text(json.dumps(project,indent=2)+"\n")
    write_csv(OUT/"pin_net.csv",["reference","value","pin","pin_name","electrical_type","net"],
        [{"reference":p.ref,"value":p.value,"pin":num,"pin_name":n,"electrical_type":kind,"net":net or "NC"}
         for p in parts for num,n,kind,net in p.pins])
    write_csv(OUT/"bom.csv",["reference","value","footprint","role","manufacturer_datasheet"],
        [{"reference":p.ref,"value":p.value,"footprint":p.footprint,"role":p.role,"manufacturer_datasheet":p.source} for p in parts if p.bom])
    (OUT/"circuit.json").write_text(json.dumps([p.__dict__ for p in parts],indent=2)+"\n")
    print(f"Wrote {len(parts)} symbols and {sum(len(p.pins) for p in parts)} pin records to {OUT}")


if __name__ == "__main__":
    main()
