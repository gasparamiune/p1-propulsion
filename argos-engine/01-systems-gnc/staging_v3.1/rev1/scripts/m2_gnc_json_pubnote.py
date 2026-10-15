"""Add the publication note to a built gnc.json (record of what changed between the build and the publication).

gnc.json v2 was built at 19:58Z on sim6 v2.4 (v1 interface snapshot) and published later, after the lead had taken
decisions that supersede some of its items. The note lists them so that a reader of v2 is not misled; the numbers
themselves enter gnc.json v3. Input GNC_GJ_IN (default out/gnc_json/gnc_v2.json), output GNC_GJ_OUT (default
out/gnc_json/gnc_v2_published.json). Run: python scripts/m2_gnc_json_pubnote.py
"""
import json
import os

IN = os.environ.get("GNC_GJ_IN", "/home/claude/work/space/out/gnc_json/gnc_v2.json")
OUT = os.environ.get("GNC_GJ_OUT", "/home/claude/work/space/out/gnc_json/gnc_v2_published.json")
NOTE = {
    "published": "2026-10-12, to the lead's fallback hub (interfaces/gnc.json); built 19:58Z",
    "built_on": "sim6 v2.4 with the v1 interface snapshot recorded in inputs_read (combustion.json v1 x relay factors, "
                "mechanical.json v1, electronics.json v1). A first build recorded the hub's combustion.json v2 in "
                "inputs_read although the runs used v1; it is kept as 01-systems-gnc/results/history/"
                "gnc_v2_build_1958_inputs_record_wrong.json.",
    "superseded_since_build": [
        "Gimbal/mount/rod structural design load: 26.5 N m -> engine moment 35.3 N m (both servos at 8.4 V stall, "
        "n 4.8; lead decision 2026-10-12). requirements.gimbal.hinge_moment and requests[mechanical] still quote 26.5.",
        "TVC linkage ratio n 4.8 FINAL on the as-drawn supply, V_val = 6.6 V (both-stall plug voltage), ARM rule "
        "predicted both-stall plug voltage >= 6.6 V and rest >= 8.1 V (lead decision on the GNC actuator study, "
        "sim6 v2.5: P(landing) 0.982 [0.966, 0.991] at 6.6 V with supply sag, 0 lost / 0 gained against the same "
        "vehicle with the reference servo model).",
        "New requirements (lead decisions 2026-10-12): ENG-07b no actuator saturation episode longer than 0.1 s in "
        "the landing burn; ENG-07c servo rotor inertia at the output J_int <= 1e-3 kg m2 (provisional); ENG-07d flex "
        "gain margin >= 6 dB, otherwise an ECU notch at the measured rocking mode; close-out test B-TVC-1.",
    ],
    "next": "gnc.json v3 after the re-baseline on mechanical.json v2 (CAD v3.2/3.3 mass properties) and combustion.json "
            "v2 (map published 2026-10-12)",
}


def main():
    g = json.load(open(IN))
    if g.get("version") != "v2":
        raise SystemExit(f"expected gnc.json v2, got {g.get('version')}")
    out = {}
    for k, v in g.items():
        out[k] = v
        if k == "status":
            out["publication_note"] = NOTE
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    print("written", OUT)


if __name__ == "__main__":
    main()
