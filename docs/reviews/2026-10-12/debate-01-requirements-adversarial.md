# Requirements ↔ adversarial challenge outcome

2026-10-12. Participants: requirements and adversarial specialists, after independent memos. Outcome: **preserve existing hardware; prototype only a bounded isolated transfer experiment**. No hardware changes or physical measurements occurred.

## Challenges and accepted corrections

Requirements challenged the adversarial “cheapest decisive” coupon: a low-side driver/flyback-only experiment could miss the proposed common-high-side and physical-feed interruption behavior. The adversarial reviewer accepted that the coupon must retain the exact G6K-2P-Y DC5, AO3400A low-side, AO3401A high-side/cutoff control, fitted flyback and physical coil-feed interruption. Separate request-off, high-side-off, physical-feed-off and total-supply-collapse stimuli are necessary. Command-off alone cannot establish the other recirculation or decay paths. Sources: `docs/passive-bypass-design.md:117–158,250–261`.

Requirements also challenged describing bounded simulator results as transfer of the “real signal envelope.” Accepted correction: the objective is fixture transfer characterization. Actual endpoint limits remain UNKNOWN; no passing coupon establishes vehicle acceptance.

Adversarial challenged overinterpreting the area calculation. Requirements accepted: 7,800 mm² summed new boards versus the old 6,929 mm² module rectangle compares different functions. It establishes neither complete installation growth nor defeat of compactness. Compare complete envelopes with equal supervision, held enable, connectors, clearance and mounting requirements before awarding a size benefit. Both original memos already cautioned that this was not installed-volume evidence.

Adversarial clarified KEEP EXISTING HARDWARE means preserve the comparison and defer integration, compatible with PROTOTYPE FIRST. Requirements accepted testing an existing assembled Rev A carrier instead of rebuilding a coupon if physical inventory and assembly checks confirm its availability. Availability remains UNKNOWN.

## Resolving experiment and residual limits

On the same isolated, independently bounded fixture, compare original module and proposed contact hardware. Capture both COMs, upstream rail, switched COIL_5V and coil current for all four stimuli; measure gap, bounce, skew, overlap and selected-dead-source duration. Source containment and probe loading must be included. Stop on unexpected current, source contention or mapping disagreement. No application threshold is invented.

No substantive design-choice disagreement remains after these corrections. Experiment selection still depends on actual inventory, instrument access and cost; unknowns are not consensus facts. Coupon success cannot close six-path, supervisor, USB/rail-order, individual-wire reconnect or endpoint gates.

Coordinator evidence reviewed: `validation/fresh-validation.json` records 60 passing host tests, 18 contact terminals, 207 populated pin nets, four clean native KiCad checks and 69 preserved files. All 34 main physical entries and 33 supervisor probes remain pending. These automated results do not alter the physical decision.
