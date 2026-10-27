#!/usr/bin/env python3
"""Route the separate MiLa bench supervisor from its owner's schematic XML.

Ownership: PCB, project-local footprint copies, pcb_validation/, manufacture/.
The circuit owner supplies circuit.json, schematic, netlist.xml and project.
This script does not edit those sources. No vehicle or manufacturing order.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

import wx
import pcbnew

import build_passive_bypass_board as common

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/passive_bypass_supervisor_rev_a'
NAME='mila_passive_bypass_supervisor_rev_a'
WIDTH,HEIGHT=80,60
MOUNTS=((3,3),(77,3),(3,57),(77,57))
ACCEPTED_LAYOUT=OUT/'pcb_validation/accepted_layout.json'

class FinePitchRouter(common.Router):
    VIA_BLOCK_RADIUS = 0.69  # 0.35 via + 0.125 track radius + 0.20 clearance + margin
    """Avoid rounding obstacle boxes outward twice around fine-pitch pins.

    The common router already expands copper by clearance plus track radius.
    Only grid-cell centers inside that expanded box are occupied here; using
    floor on the minimum additionally consumed a valid TSSOP pin exit row.
    Native KiCad DRC remains the final geometry check.
    """
    def rect(self, layer, net, x1, y1, x2, y2):
        for gx in range(max(0, int(math.ceil(x1/self.STEP))),
                        min(self.nx, int(math.floor(x2/self.STEP))+1)):
            for gy in range(max(0, int(math.ceil(y1/self.STEP))),
                            min(self.ny, int(math.floor(y2/self.STEP))+1)):
                self.occupied[layer].setdefault((gx, gy), set()).add(net)

    def route(self, a, b, net):
        # A blocked destination cannot be reached by the A* walk. Detect that
        # immediately rather than expanding the whole board for each pair.
        gx, gy = self.grid(common.pos_mm(b))
        layers = (0, 1) if b.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else (
            (0,) if b.GetLayerSet().Contains(pcbnew.F_Cu) else (1,))
        if not any(self.free(gx, gy, layer, net) for layer in layers):
            return False
        def exits(pad):
            x,y=self.grid(common.pos_mm(pad))
            ls=(0,1) if pad.GetAttribute()==pcbnew.PAD_ATTRIB_PTH else (
                (0,) if pad.GetLayerSet().Contains(pcbnew.F_Cu) else (1,))
            return sum(self.free(x+dx,y+dy,layer,net) for layer in ls
                       for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)))
        # Start inside the narrower pin escape. A trapped destination is then
        # rejected by a small search, instead of flooding all free board space.
        if exits(b)<exits(a):a,b=b,a
        return super().route(a, b, net)

    def via_free(self, gx, gy, net):
        x,y=self.xy((gx,gy))
        for vx,vy,vnet in self.via_points:
            distance=math.dist((x,y),(vx,vy))
            if distance<0.01 and net==vnet:return True
            if distance<0.9:return False
        # Obstacles already include a 0.125 mm track radius. A via requires
        # an extra 0.225 mm radius, rather than the coarse router's 0.4 mm box.
        for layer in (0,1):
            for dx in range(-3,4):
                for dy in range(-3,4):
                    if math.hypot(dx*self.STEP,dy*self.STEP)>0.23:continue
                    if not self.free(gx+dx,gy+dy,layer,net):return False
        return True

# Positions are footprint origins, not pin1; orientations use KiCad degrees.
PLACEMENT={
    'U1':(15,20,0),'U2':(15,30,0),'U3':(65,20,0),'D1':(60,16,0),
    'U4':(28,20,0),'U5':(52,20,0),'U6':(44,30,0),'U7':(30,34,0),
    'U8':(36,20,0),'U9':(44,20,0),'U10':(35,44,0),'U11':(52,44,0),
    'U12':(43,40,0),'U13':(65,44,0),'U14':(27.5,42,0),
    'J1':(10,5,90),'J2':(72,8,0),'J3':(72,22,0),
    'J4':(72,38,0),'J5':(50,54,90),'J6':(48,5,90),
    'R1':(10,18,0),'R2':(10,22,0),'R3':(11.3,29,0),'R4':(62,24.5,0),
    'R5':(22,17,0),'R6':(47,34.5,0),'R7':(50,38,0),'R8':(51,24,0),
    'R9':(32,14,0),'R10':(36,30,0),'R11':(29,12,0),'R12':(32,12,0),
    'R13':(35,12,0),'R14':(17.5,9,0),'R15':(22,9,0),'R16':(13,9,0),
    'R17':(65,28,0),'R18':(63,49,0),'R19':(60,49,0),'R20':(58,46.5,0),
    'R21':(50,34,0),'R22':(64.5,12,0),'R23':(68,12,0),'R24':(25,39,0),
    'C1':(15,16.2,90),'C2':(18.8,29,0),'C3':(68.8,19.4,0),
    'C4':(31.5,19.4,0),'C5':(55.5,19.4,0),'C6':(47.5,29.4,0),
    'C7':(33.5,33.4,0),'C8':(39.5,19.4,0),'C9':(47.5,19.4,0),
    'C10':(38.9,39.5,90),'C11':(55.9,39.5,90),'C12':(46.5,39.4,0),
    'C13':(68.5,43.4,0),'C14':(44,34.5,0),'C15':(12,13,0),
    'C16':(72,14,0),'C17':(65.5,16,0),'C18':(24.5,42,90),'C19':(30.2,42,90),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def capture_accepted_layout():
    reports=OUT/'pcb_validation'
    drc=json.loads((reports/'drc.json').read_text())
    erc=json.loads((reports/'erc.json').read_text())
    commands=json.loads((reports/'commands.json').read_text())
    assert not drc['violations'] and not drc['unconnected_items'] and not drc['schematic_parity']
    assert all(not sheet['violations'] for sheet in erc['sheets'])
    assert all(c['exit_code']==0 for c in commands)
    board=pcbnew.LoadBoard(str(OUT/(NAME+'.kicad_pcb')))
    layout={'coordinate_units':'nm','board_mm':[WIDTH,HEIGHT],
            'circuit_sha256':sha(OUT/'circuit.json'),
            'footprint_hashes':{str(p.relative_to(OUT)):sha(p) for p in OUT.glob('*.pretty/*.kicad_mod')},
            'tracks':[],'vias':[]}
    for t in board.GetTracks():
        if isinstance(t,pcbnew.PCB_VIA):
            p=t.GetPosition()
            layout['vias'].append({'net':t.GetNetname(),'position':[p.x,p.y],
                                  'diameter':t.GetWidth(pcbnew.F_Cu),'drill':t.GetDrill()})
        else:
            a,b=t.GetStart(),t.GetEnd()
            layout['tracks'].append({'net':t.GetNetname(),'start':[a.x,a.y],
                'end':[b.x,b.y],'width':t.GetWidth(),'layer':t.GetLayerName()})
    ACCEPTED_LAYOUT.write_text(json.dumps(layout,indent=2)+'\n')


def apply_accepted_layout(board,nets):
    layout=json.loads(ACCEPTED_LAYOUT.read_text())
    assert layout['circuit_sha256']==sha(OUT/'circuit.json'),'Circuit changed; accepted routes require a new review'
    assert layout['board_mm']==[WIDTH,HEIGHT]
    assert all(sha(OUT/p)==h for p,h in layout['footprint_hashes'].items()),'Footprint changed; re-review placement/routing'
    for record in layout['tracks']:
        t=pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(*record['start']));t.SetEnd(pcbnew.VECTOR2I(*record['end']))
        t.SetWidth(record['width']);t.SetLayer(pcbnew.F_Cu if record['layer']=='F.Cu' else pcbnew.B_Cu)
        t.SetNet(nets[record['net']]);board.Add(t)
    for record in layout['vias']:
        v=pcbnew.PCB_VIA(board);v.SetPosition(pcbnew.VECTOR2I(*record['position']))
        v.SetWidth(record['diameter']);v.SetDrill(record['drill'])
        v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu)
        v.SetNet(nets[record['net']]);board.Add(v)
    add_ground_plane(board,nets)
    summary=json.loads((OUT/'pcb_validation/routing_summary.json').read_text())
    summary['rebuild_method']='Accepted geometry manifest with frozen circuit and footprint hashes'
    summary['accepted_layout_manifest']=str(ACCEPTED_LAYOUT.relative_to(ROOT))
    return summary


def sources():
    parts=[p for p in json.loads((OUT/'circuit.json').read_text()) if p['board']]
    assert set(p['ref'] for p in parts)==set(PLACEMENT), 'Placement manifest out of date'
    sch=(OUT/(NAME+'.kicad_sch')).read_text()
    root_uuid=re.search(r'\(uuid "([^"]+)"',sch).group(1)
    symbols={}
    for block in common.blocks(sch,'symbol'):
        if not block.startswith('(symbol (lib_id '):
            continue
        ref=re.search(r'\(property "Reference" "([^"]+)"',block).group(1)
        symbol_uuid=re.search(r'\(uuid "([^"]+)"',block).group(1)
        symbols[ref]=symbol_uuid
    xml=ET.parse(OUT/'netlist.xml').getroot()
    net_by_pin={}
    for net in xml.find('nets'):
        for node in net:
            net_by_pin[node.attrib['ref'],node.attrib['pin']]=net.attrib['name']
    return parts,root_uuid,symbols,net_by_pin


def footprints(parts):
    entries=[]
    for lib in sorted({p['footprint'].split(':')[0] for p in parts}):
        target=OUT/(lib+'.pretty')
        target.mkdir(exist_ok=True)
        for name in sorted({p['footprint'].split(':')[1] for p in parts
                            if p['footprint'].startswith(lib+':')}):
            shutil.copyfile(common.LIB/'footprints'/(lib+'.pretty')/(name+'.kicad_mod'),
                            target/(name+'.kicad_mod'))
        entries.append(f'(lib (name {common.q(lib)}) (type "KiCad") '
                       f'(uri "${{KIPRJMOD}}/{lib}.pretty") (options "") '
                       '(descr "Project-local stock package footprints"))')
    (OUT/'fp-lib-table').write_text('(fp_lib_table (version 7)\n'+'\n'.join(entries)+'\n)\n')


def mechanics(board):
    for a,b in (((0,0),(WIDTH,0)),((WIDTH,0),(WIDTH,HEIGHT)),
                ((WIDTH,HEIGHT),(0,HEIGHT)),((0,HEIGHT),(0,0))):
        line=pcbnew.PCB_SHAPE(board)
        line.SetShape(pcbnew.SHAPE_T_SEGMENT)
        line.SetStart(common.point(*a));line.SetEnd(common.point(*b))
        line.SetWidth(common.mm(0.05));line.SetLayer(pcbnew.Edge_Cuts)
        board.Add(line)
    for i,(x,y) in enumerate(MOUNTS,1):
        fp=pcbnew.FOOTPRINT(board)
        fp.SetReference('H'+str(i));fp.SetValue('MountingHole_3.2mm')
        fp.SetPosition(common.point(x,y));fp.SetBoardOnly(True)
        fp.SetExcludedFromBOM(True);fp.SetExcludedFromPosFiles(True)
        fp.Reference().SetVisible(False);fp.Value().SetVisible(False)
        pad=pcbnew.PAD(fp)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH);pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetSize(common.point(3.2,3.2));pad.SetDrillSize(common.point(3.2,3.2))
        layers=pcbnew.LSET(pcbnew.LSET.AllCuMask())
        layers.AddLayer(pcbnew.F_Mask);layers.AddLayer(pcbnew.B_Mask)
        pad.SetLayerSet(layers);pad.SetPosition(common.point(x,y))
        fp.Add(pad);board.Add(fp)
        circle=pcbnew.PCB_SHAPE(board)
        circle.SetShape(pcbnew.SHAPE_T_CIRCLE)
        circle.SetStart(common.point(x,y));circle.SetEnd(common.point(x+1.6,y))
        circle.SetWidth(common.mm(0.12));circle.SetLayer(pcbnew.Dwgs_User)
        board.Add(circle)
    common.board_text(board,'MiLa SUPERVISOR Rev A / BENCH ONLY',40,58,1.0)
    common.board_text(board,'NO VEHICLE / REGULATED 3V3 + 5V',40,56.5,0.85)


def polish_assembly_references(board):
    for fp in board.GetFootprints():
        ref=fp.GetReference()
        if ref not in PLACEMENT or not ref.startswith(('R','C','D')):continue
        x,y,angle=PLACEMENT[ref]
        offset=-2.5 if angle==90 else -1.8
        if ref in ('R9','R18','R19','C16'):offset=1.8
        if ref=='C18':offset=2.5
        fp.Reference().SetPosition(common.point(x,y+offset))


def build_placement(parts,root_uuid,symbols,net_by_pin):
    board=pcbnew.BOARD()
    board.SetFileName(str(OUT/(NAME+'.kicad_pcb')))
    board.GetDesignSettings().SetBoardThickness(common.mm(1.6))
    board.GetDesignSettings().m_MinClearance=common.mm(0.2)
    board.GetDesignSettings().m_CopperEdgeClearance=common.mm(0.5)
    nets={}
    for name in sorted(set(net_by_pin.values())):
        info=pcbnew.NETINFO_ITEM(board,name);board.Add(info);nets[name]=info
    pads=[];pad_by_ref={};fps={}
    for p in parts:
        ref=p['ref'];lib,name=p['footprint'].split(':')
        fp=pcbnew.FootprintLoad(str(OUT/(lib+'.pretty')),name)
        assert fp,'Missing footprint '+p['footprint']
        fp.SetReference(ref);fp.SetValue(p['value']);fp.SetFPIDAsString(p['footprint'])
        fp.GetField(pcbnew.FIELD_T_DATASHEET).SetText(p['source'])
        fp.GetField(pcbnew.FIELD_T_DESCRIPTION).SetText(p['role'])
        fp.SetPath(pcbnew.KIID_PATH('/'+root_uuid+'/'+symbols[ref]))
        fp.SetUuid(pcbnew.KIID(symbols[ref]))
        x,y,angle=PLACEMENT[ref]
        fp.SetPosition(common.point(x,y));fp.SetOrientationDegrees(angle)
        board.Add(fp);fps[ref]=fp
        fp.Value().SetVisible(False)
        fp.Reference().SetTextSize(common.point(0.85,0.85))
        fp.Reference().SetTextThickness(common.mm(0.12))
        fp.Reference().SetTextAngle(pcbnew.EDA_ANGLE(0,pcbnew.DEGREES_T))
        fp.Reference().SetPosition(common.point(x,y-2.5))
        # Dense passives are labeled in the assembly artwork, not under soldermask.
        if ref.startswith(('R','C','D')):
            fp.Reference().SetLayer(pcbnew.F_Fab)
        elif ref in ('U10','U11'):
            fp.Reference().SetPosition(common.point(x,y-4))
        elif ref=='U1':
            fp.Reference().SetPosition(common.point(x+3.7,y-2.5))
        elif ref=='U14':
            fp.Reference().SetPosition(common.point(x,y+2.5))
        elif ref=='J5':
            fp.Reference().SetPosition(common.point(x+7.62,y-2.3))
        elif ref in ('J1','J6'):
            fp.Reference().SetPosition(common.point(x+5,y-2.2))
        elif ref.startswith('J'):
            fp.Reference().SetPosition(common.point(x-2.5,y))
        for pad in fp.Pads():
            if not pad.GetNumber() or not pad.GetLayerSet().Contains(pcbnew.F_Cu):
                continue
            key=(ref,pad.GetNumber())
            assert key in net_by_pin,'No schematic net for '+str(key)
            pad.SetNet(nets[net_by_pin[key]])
            pads.append(pad);pad_by_ref.setdefault(key,pad)
        expected={pin[0] for pin in p['pins']}
        actual={pad.GetNumber() for pad in fp.Pads() if pad.GetNumber()}
        assert expected==actual,(ref,'Manufacturer pin count/package mismatch',expected,actual)
    mechanics(board)
    polish_assembly_references(board)
    return board,nets,pads,pad_by_ref,fps


def virtual_pad(board,net,x,y,pth=False,layer=pcbnew.F_Cu):
    owner=pcbnew.FOOTPRINT(board)
    pad=pcbnew.PAD(owner)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH if pth else pcbnew.PAD_ATTRIB_SMD)
    if not pth:
        layers=pcbnew.LSET();layers.AddLayer(layer);pad.SetLayerSet(layers)
    pad.SetPosition(common.point(x,y));pad.SetSize(common.point(0.1,0.1));pad.SetNet(net)
    return pad,owner


def new_length(board,before):
    return sum(pcbnew.ToMM(t.GetLength()) for t in board.GetTracks()
               if t.m_Uuid.AsString() not in before
               if isinstance(t,pcbnew.PCB_TRACK) and not isinstance(t,pcbnew.PCB_VIA))


def add_via(board,net,x,y,router):
    via=pcbnew.PCB_VIA(board)
    via.SetPosition(common.point(x,y));via.SetWidth(common.mm(0.7))
    via.SetDrill(common.mm(0.3));via.SetViaType(pcbnew.VIATYPE_THROUGH)
    via.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);via.SetNet(net)
    board.Add(via);router.via_points.append((x,y,net.GetNetname()))
    for layer in (0,1):router.disk(layer,net.GetNetname(),x,y,router.VIA_BLOCK_RADIUS)


def ground_fanout(board,router,pads,nets):
    name=next(n for n in nets if n.lstrip('/')=='GND')
    net=nets[name];failed=[];locations=[]
    # Each surface ground pad gets a local via into the continuous bottom pour.
    # EP extensions overlap the EP center and only require one connection.
    seen=[]
    for pad in pads:
        if pad.GetNetname()!=name or pad.GetAttribute()==pcbnew.PAD_ATTRIB_PTH:
            continue
        ref=pad.GetParentFootprint().GetReference();number=pad.GetNumber()
        if ref=='U1' and number=='11':
            if (ref,number) in seen:continue
            seen.append((ref,number))
        x,y=common.pos_mm(pad)
        candidates=[]
        if ref=='U1' and number=='11':
            candidates.append((15,22.8))
        for distance in (1.5,2.1,2.7,3.3):
            for dx,dy in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)):
                candidates.append((round(x+dx*distance,1),round(y+dy*distance,1)))
        success=False
        for vx,vy in candidates:
            gx,gy=router.grid((vx,vy))
            if not router.via_free(gx,gy,name):continue
            # Finish on the top copper, then add the intended ground via.
            # A virtual PTH goal allowed ending on the plane side and created
            # a redundant via with no top-layer connection.
            target,owner=virtual_pad(board,net,vx,vy,pth=False)
            if router.route(pad,target,name):
                if not any(math.dist((vx,vy),(px,py))<0.01 and pn==name
                           for px,py,pn in router.via_points):
                    add_via(board,net,vx,vy,router)
                locations.append({'reference':ref,'pin':number,'via_mm':[vx,vy]})
                success=True;break
        if not success:failed.append(ref+':'+number)
    return locations,failed


def add_ground_plane(board,nets):
    name=next(n for n in nets if n.lstrip('/')=='GND')
    zone=pcbnew.ZONE(board)
    zone.SetLayer(pcbnew.B_Cu);zone.SetNet(nets[name])
    zone.SetLocalClearance(common.mm(0.2));zone.SetMinThickness(common.mm(0.2))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    outline=zone.Outline();outline.NewOutline()
    for x,y in ((0.6,0.6),(WIDTH-0.6,0.6),(WIDTH-0.6,HEIGHT-0.6),(0.6,HEIGHT-0.6)):
        outline.Append(common.mm(x),common.mm(y))
    board.Add(zone)


def route_board(board,nets,pads,byref):
    router=FinePitchRouter(board,pads,width=WIDTH,height=HEIGHT,step=0.1,
                         mounts=MOUNTS,track_width=0.25,search_limit=100000,
                         goal_tiebreak=True,heuristic_weight=1.1)
    clock=next(n for n in nets if n.lstrip('/')=='HB_CLK')
    star,owner=virtual_pad(board,nets[clock],35,39)
    clock_lengths={}
    for key,label in ((('U6','6'),'shared_trunk'),(('U10','3'),'stage1_branch'),
                      (('U10','11'),'stage2_branch')):
        before={t.m_Uuid.AsString() for t in board.GetTracks()}
        assert router.route(byref[key],star,clock),'Clock star route failed '+label
        clock_lengths[label]=new_length(board,before)
    print('HB clock star',clock_lengths,flush=True)
    # Connect each local decoupler straight to its assigned supply pin before buses.
    for i in range(1,15):
        cref='C'+str(i) if i<=13 else 'C19'
        supply=[p for p in pads if p.GetParentFootprint().GetReference()=='U'+str(i)
                and p.GetNetname().lstrip('/') in ('V3V3','V5_SUP','V_PG5_SUP')]
        for pin in supply:
            cap=byref[(cref,'1')]
            if pin.GetNetname()==cap.GetNetname():
                router.route(pin,cap,pin.GetNetname())
    bynet={}
    for pad in pads:bynet.setdefault(pad.GetNetname(),[]).append(pad)
    critical=('HB_STAGE_RC','HB_ONE_SAFE','HB_ONE','WD_CRST','WD_CWD',
              'PG33_CT','PG5_CT','V5_SENSE','READY','WDI','V5_COIL_SWITCHED',
              'HEALTH_N','QUALIFIED')
    order=sorted(bynet,key=lambda n:(0 if n.lstrip('/') in critical else
                                   2 if n.lstrip('/') in ('V3V3','V5_SUP') else 1,
                                   critical.index(n.lstrip('/')) if n.lstrip('/') in critical else 0,
                                   len(bynet[n]),n))
    failed=[]
    ground_locations=[];ground_failed=[];ground_done=False
    for name in order:
        if name.lstrip('/') in ('GND','HB_CLK'):continue
        if name.lstrip('/') not in critical and not ground_done:
            ground_locations,ground_failed=ground_fanout(board,router,pads,nets)
            print('Ground fanouts',len(ground_locations),'failed',ground_failed,flush=True)
            ground_done=True
        nodes=bynet[name];connected=[nodes[0]];remaining=nodes[1:]
        while remaining:
            options=sorted((math.dist(common.pos_mm(a),common.pos_mm(b)),i,j,a,b)
                           for i,b in enumerate(remaining) for j,a in enumerate(connected))
            success=False
            for _,i,j,a,b in options:
                if router.route(a,b,name):
                    connected.append(b);remaining.pop(i);success=True;break
            if not success:
                failed.append(name)
                for pad in remaining:
                    gx,gy=router.grid(common.pos_mm(pad))
                    print('  blocked endpoint',pad.GetParentFootprint().GetReference(),
                          pad.GetNumber(),common.pos_mm(pad),
                          sorted(router.occupied[0].get((gx,gy),set())),flush=True)
                break
        print('Routed',name,'pads',len(nodes),'FAILED' if name in failed else 'OK',flush=True)
    add_ground_plane(board,nets)
    return {'board_mm':[WIDTH,HEIGHT],'signal_track_mm':0.25,
            'copper_layers':2,'clock_star_mm':clock_lengths,
            'clock_branch_skew_mm':abs(clock_lengths['stage1_branch']-clock_lengths['stage2_branch']),
            'ground_fanouts':ground_locations,'failed_ground_fanouts':ground_failed,
            'failed_nets':failed,'physical_components':len(PLACEMENT),
            'track_and_via_count':len(list(board.GetTracks()))}


def repair_loaded_board():
    """Preserve completed routes and reconnect native DRC endpoint pairs."""
    board=pcbnew.LoadBoard(str(OUT/(NAME+'.kicad_pcb')))
    report=json.loads((OUT/'pcb_validation/drc.json').read_text())
    escapes=[];extra_links=[];clock_delta=0;retired_items=[];extra_grounds=[]
    def reroute_polyline(net,a,b,points):
        removed=0
        for t in list(board.GetTracks()):
            if isinstance(t,pcbnew.PCB_VIA) or t.GetLayer()!=pcbnew.F_Cu or t.GetNetname()!=net:continue
            start=(pcbnew.ToMM(t.GetStart().x),pcbnew.ToMM(t.GetStart().y))
            end=(pcbnew.ToMM(t.GetEnd().x),pcbnew.ToMM(t.GetEnd().y))
            if (math.dist(start,a)<.001 and math.dist(end,b)<.001) or (
                math.dist(start,b)<.001 and math.dist(end,a)<.001):
                retired_items.append(t);board.Remove(t);removed+=1
        if removed:
            for first,last in zip(points,points[1:]):
                t=pcbnew.PCB_TRACK(board);t.SetStart(common.point(*first));t.SetEnd(common.point(*last))
                t.SetWidth(common.mm(.25));t.SetLayer(pcbnew.F_Cu)
                t.SetNet(board.FindNet(net));board.Add(t)
            escapes.append({'net':net,'old':[a,b],'new':points})
        return removed
    remaining={re.search(r'\[([^]]+)\]',p['items'][0]['description']).group(1)
               for p in report['unconnected_items']}
    if '/WDI' in remaining:
        if reroute_polyline('/HB_CLK',(44.1,28.8),(36,28.8),
                            [(44.1,28.8),(44.1,28.4),(36,28.4),(36,28.8)]):clock_delta=.8
    if '/ZERO_REQ' in remaining:
        reroute_polyline('/HB_GOOD',(42.2,39.4),(39.8,39.4),
                         [(42.2,39.4),(42.2,38.7),(39.8,38.7),(39.8,39.4)])
        removed=sum(reroute_polyline('/V3V3',a,b,[]) for a,b in (
                    ((31.7,35.2),(31.7,34.1)),((30.8,35.2),(31.7,35.2)),
                    ((30.8,38.9),(30.8,35.2))))
        if removed:extra_links.append(('/V3V3',(30.8,38.9),(32.7,34.0)))
        reroute_polyline('/V3V3',(31.7,34.1),(30.8,34.1),[])
        reroute_polyline('/V3V3',(30.8,34.1),(30.8,34.0),[])
        # The west ground escape fenced the middle input into a tiny area
        # above it. Move that ground escape below U12, leaving room for a
        # ZERO_REQ via west of pins 1–3. The circuit and pin nets are unchanged.
        if reroute_polyline('/GND',(42.2,40.6),(40.7,40.6),[]):
            for t in list(board.GetTracks()):
                if isinstance(t,pcbnew.PCB_VIA) and t.GetNetname()=='/GND' and (
                    math.dist(common.pos_mm(t),(40.7,40.6))<.01):
                    retired_items.append(t);board.Remove(t)
            extra_grounds.append(((42.2,40.6),(42.2,42.2)))
    if '/GND' in remaining:
        # Leave the local ground pin room after the ZERO_REQ escape connects.
        # The accepted signal route used the row immediately below GND; its
        # lower leg is moved 0.8 mm down and keeps both original endpoints.
        if reroute_polyline('/ZERO_REQ',(41.3,41.2),(43.3,41.2),
                            [(41.3,41.2),(41.3,42.0),(43.3,42.0),(43.3,41.2)]):
            extra_grounds.append(((42.2,40.6),(42.2,41.2)))
    items={p.m_Uuid.AsString():p for fp in board.GetFootprints() for p in fp.Pads()}
    items.update({t.m_Uuid.AsString():t for t in board.GetTracks()})
    removed=[]
    for warning in report['violations']:
        if warning['type']!='via_dangling':continue
        for record in warning['items']:
            item=items.get(record['uuid'])
            if isinstance(item,pcbnew.PCB_VIA):
                removed.append(record['uuid']);board.Remove(item)
    pads=[p for fp in board.GetFootprints() for p in fp.Pads()
          if p.GetNumber() and p.GetLayerSet().Contains(pcbnew.F_Cu)]
    router=FinePitchRouter(board,pads,width=WIDTH,height=HEIGHT,step=0.1,
                          mounts=MOUNTS,track_width=0.25,search_limit=200000,
                          goal_tiebreak=True,heuristic_weight=1.2)
    for track in board.GetTracks():
        name=track.GetNetname()
        if isinstance(track,pcbnew.PCB_VIA):
            x,y=common.pos_mm(track)
            router.via_points.append((x,y,name))
            for layer in (0,1):router.disk(layer,name,x,y,router.VIA_BLOCK_RADIUS)
        else:
            a=track.GetStart();b=track.GetEnd()
            ax,ay=pcbnew.ToMM(a.x),pcbnew.ToMM(a.y)
            bx,by=pcbnew.ToMM(b.x),pcbnew.ToMM(b.y)
            steps=max(1,int(math.ceil(math.dist((ax,ay),(bx,by))/0.1)))
            layer=0 if track.GetLayer()==pcbnew.F_Cu else 1
            for i in range(steps+1):
                router.disk(layer,name,ax+(bx-ax)*i/steps,ay+(by-ay)*i/steps,0.49)
    owners=[];failed=[];repaired=[]
    for problem in report['unconnected_items']:
        endpoints=[]
        for record in problem['items']:
            item=items[record['uuid']]
            if isinstance(item,pcbnew.PAD):endpoints.append(item)
            else:
                x,y=record['pos']['x'],record['pos']['y']
                pad,owner=virtual_pad(board,item.GetNet(),x,y,
                                      pth=isinstance(item,pcbnew.PCB_VIA),layer=item.GetLayer())
                owners.append(owner);endpoints.append(pad)
        a,b=endpoints;name=a.GetNetname()
        ok=router.route(a,b,name)
        if not ok and name.lstrip('/')=='GND':
            ground_pads=[p for p in endpoints if isinstance(p,pcbnew.PAD)
                         and p.GetParentFootprint().GetReference()=='U12']
            locations,ground_failed=ground_fanout(board,router,ground_pads,{name:a.GetNet()})
            if ground_pads and locations and not ground_failed:
                ok=True
                escapes.append({'net':name,'new_local_ground_fanout':locations})
        (repaired if ok else failed).append(name)
        print('Local repair',name,'OK' if ok else 'FAILED',flush=True)
    for name,start,end in extra_links:
        a,owner=virtual_pad(board,board.FindNet(name),*start);owners.append(owner)
        b,owner=virtual_pad(board,board.FindNet(name),*end);owners.append(owner)
        ok=router.route(a,b,name)
        (repaired if ok else failed).append(name)
        print('Local power escape repair',name,'OK' if ok else 'FAILED',flush=True)
    for start,end in extra_grounds:
        name='/GND';net=board.FindNet(name)
        a,owner=virtual_pad(board,net,*start);owners.append(owner)
        b,owner=virtual_pad(board,net,*end);owners.append(owner)
        ok=router.via_free(*router.grid(end),name) and router.route(a,b,name)
        if ok:add_via(board,net,*end,router)
        (repaired if ok else failed).append(name)
        print('Local ground escape repair',name,'OK' if ok else 'FAILED',flush=True)
    summary=json.loads((OUT/'pcb_validation/routing_summary.json').read_text())
    summary.update({'local_repaired_links':repaired,'local_failed_links':failed,
                    'redundant_ground_vias_removed':removed,
                    'track_and_via_count':len(list(board.GetTracks()))})
    summary.setdefault('pin_escape_reroutes',[]).extend(escapes)
    summary['clock_star_mm']['shared_trunk']+=clock_delta
    pcbnew.SaveBoard(str(OUT/(NAME+'.kicad_pcb')),board)
    (OUT/'pcb_validation/routing_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return board


def validate_export(placement_only=False):
    reports=OUT/'pcb_validation';manu=OUT/'manufacture'
    reports.mkdir(exist_ok=True);manu.mkdir(exist_ok=True)
    board=str(OUT/(NAME+'.kicad_pcb'))
    drc=['pcb','drc','--schematic-parity','--format','json','--severity-all',
         '--exit-code-violations','-o',str(reports/'drc.json')]
    if not placement_only:drc+=['--refill-zones','--save-board']
    jobs=[drc+[board],
        ['sch','erc','--format','json','--severity-all','--exit-code-violations',
         '-o',str(reports/'erc.json'),str(OUT/(NAME+'.kicad_sch'))],
        ['pcb','export','svg','--layers','F.Cu,F.Silkscreen,User.Drawings,Edge.Cuts',
         '--fit-page-to-board','--exclude-drawing-sheet','--mode-single','-o',str(reports/'board_top.svg'),board],
        ['pcb','export','svg','--layers','B.Cu,User.Drawings,Edge.Cuts',
         '--fit-page-to-board','--exclude-drawing-sheet','--mode-single','-o',str(reports/'board_bottom.svg'),board],
        ['pcb','export','svg','--layers','F.Fab,F.Silkscreen,User.Drawings,Edge.Cuts',
         '--sketch-pads-on-fab-layers','--fit-page-to-board','--exclude-drawing-sheet',
         '--mode-single','-o',str(reports/'board_assembly.svg'),board]]
    commands=[]
    for args in jobs:
        result=subprocess.run([str(common.CLI)]+args,text=True,capture_output=True)
        commands.append({'command':args,'exit_code':result.returncode,
                         'stdout':result.stdout,'stderr':result.stderr})
        print(args[:3],result.returncode,result.stdout.strip(),result.stderr.strip(),flush=True)
    if all(command['exit_code']==0 for command in commands) and not placement_only:
        jobs=[['pcb','export','gerbers','-o',str(manu)+'/',board],
              ['pcb','export','drill','--excellon-separate-th','--generate-map',
               '--map-format','svg','--generate-report','--report-path',str(manu/'drill_report.txt'),
               '-o',str(manu)+'/',board],
              ['pcb','export','pos','--format','csv','--units','mm','--side','both',
               '-o',str(manu/'positions.csv'),board]]
        for args in jobs:
            result=subprocess.run([str(common.CLI)]+args,text=True,capture_output=True)
            commands.append({'command':args,'exit_code':result.returncode,
                             'stdout':result.stdout,'stderr':result.stderr})
            print(args[:3],result.returncode,result.stdout.strip(),result.stderr.strip(),flush=True)
    (reports/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
    ok=all(command['exit_code']==0 for command in commands) and not placement_only
    if ok:
        summary=json.loads((reports/'routing_summary.json').read_text())
        summary.setdefault('initial_search_failures',summary.get('failed_nets',[]))
        summary.setdefault('search_history',[]).append({
            'provisional_failed_links':summary.get('local_failed_links',[]),
            'repaired_links':summary.get('local_repaired_links',[])})
        summary.update({'failed_nets':[],'local_failed_links':[],
                        'failed_ground_fanouts':[],
                        'native_verification':{'erc_violations':0,'drc_violations':0,
                                               'unconnected_items':0,'schematic_parity':0,
                                               'all_export_commands_exit_zero':True}})
        board_data=pcbnew.LoadBoard(board)
        summary['physical_vias']=[{'net':v.GetNetname(),
                                  'position_mm':list(common.pos_mm(v))}
                                 for v in board_data.GetTracks() if isinstance(v,pcbnew.PCB_VIA)]
        summary['track_and_via_count']=len(list(board_data.GetTracks()))
        summary['trace_length_mm']=sum(pcbnew.ToMM(t.GetLength())
                                      for t in board_data.GetTracks() if not isinstance(t,pcbnew.PCB_VIA))
        summary['actual_clock_track_total_mm']=sum(pcbnew.ToMM(t.GetLength())
            for t in board_data.GetTracks() if not isinstance(t,pcbnew.PCB_VIA)
            and t.GetNetname().lstrip('/')=='HB_CLK')
        pad_map={(fp.GetReference(),p.GetNumber()):p for fp in board_data.GetFootprints()
                 for p in fp.Pads() if p.GetNumber()}
        power_pins={(p['ref'],pin[0]) for p in json.loads((OUT/'circuit.json').read_text())
                    for pin in p['pins'] if pin[2]=='power_in'
                    and pin[3] in ('V3V3','V5_SUP','V_PG5_SUP')}
        decouplers=[]
        for i in range(1,15):
            ref='U'+str(i);cap='C'+str(i) if i<=13 else 'C19'
            for (r,number),pad in pad_map.items():
                if r!=ref or (r,number) not in power_pins:continue
                cp=pad_map[(cap,'1')]
                if cp.GetNetname()!=pad.GetNetname():continue
                decouplers.append({'ic':ref,'power_pin':number,'capacitor':cap,
                    'pin_spacing_mm':math.dist(common.pos_mm(pad),common.pos_mm(cp))})
        summary['decoupler_pin_spacing']=decouplers
        summary['maximum_decoupler_pin_spacing_mm']=max(d['pin_spacing_mm'] for d in decouplers)
        actual_vias={tuple(v['position_mm']) for v in summary['physical_vias'] if v['net'].lstrip('/')=='GND'}
        summary.setdefault('initial_ground_fanout_candidates',summary.get('ground_fanouts',[]))
        summary['ground_fanouts']=[g for g in summary.get('ground_fanouts',[])
                                  if tuple(g['via_mm']) in actual_vias]
        summary['ground_connectivity_verified_by_native_drc']=True
        (reports/'routing_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return ok


def main():
    args=argparse.ArgumentParser()
    args.add_argument('--placement-only',action='store_true')
    args.add_argument('--repair-loaded',action='store_true')
    args.add_argument('--validate-existing',action='store_true')
    args.add_argument('--polish-assembly',action='store_true')
    args.add_argument('--capture-accepted',action='store_true')
    args.add_argument('--reroute',action='store_true',help='Discard accepted routes and run exploratory A* routing')
    options=args.parse_args()
    app=wx.App(False)
    parts,root_uuid,symbols,net_by_pin=sources()
    source_paths=[OUT/'circuit.json',OUT/'netlist.xml',OUT/(NAME+'.kicad_sch')]
    hashes={str(p.relative_to(ROOT)):sha(p) for p in source_paths}
    if options.capture_accepted:
        capture_accepted_layout()
        return 0
    if options.polish_assembly:
        board=pcbnew.LoadBoard(str(OUT/(NAME+'.kicad_pcb')))
        polish_assembly_references(board)
        pcbnew.SaveBoard(str(OUT/(NAME+'.kicad_pcb')),board)
        return 0 if validate_export() else 1
    if options.validate_existing:
        (OUT/'pcb_validation/source_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
        return 0 if validate_export() else 1
    if options.repair_loaded:
        repair_loaded_board()
        (OUT/'pcb_validation/source_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
        assert all(sha(ROOT/p)==h for p,h in hashes.items()),'Circuit source changed during repair'
        return 0 if validate_export() else 1
    footprints(parts)
    board,nets,pads,byref,fps=build_placement(parts,root_uuid,symbols,net_by_pin)
    summary={'board_mm':[WIDTH,HEIGHT],'placement_only':True}
    if not options.placement_only:
        summary=(apply_accepted_layout(board,nets) if ACCEPTED_LAYOUT.exists() and not options.reroute
                 else route_board(board,nets,pads,byref))
    pcbnew.SaveBoard(str(OUT/(NAME+'.kicad_pcb')),board)
    reports=OUT/'pcb_validation';reports.mkdir(exist_ok=True)
    (reports/'routing_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (reports/'source_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
    assert all(sha(ROOT/p)==h for p,h in hashes.items()),'Circuit owner changed sources during routing'
    ok=validate_export(options.placement_only)
    print('SUPERVISOR CAD PASS' if ok else 'SUPERVISOR CAD needs repair',flush=True)
    return 0 if ok else 1


if __name__=='__main__':raise SystemExit(main())
