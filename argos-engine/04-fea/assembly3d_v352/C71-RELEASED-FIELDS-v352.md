# v3.5.2 released c71 fields and their regeneration recipes

fea3d, 2026-10-20T19:15:14Z (date -u).  Lead 16:56:23Z R5 (A) (one hub note at the end of chain E, with the regeneration recipe); 19:09:50Z (6).  Evidence: RECORD (release log, PRUNED lines) + checks re-run at this note's time.  Nothing here is physical approval.

9 c71 `fields.npz` files were released (deleted) in v3.5.2 under the R3 replacement rule (lead 14:11Z (i)) and option (A) (lead 16:56:23Z), 456.8 MB in all.  Each was replaced as an input by its v3.5.2 R3 run (named below), which passed release_c71.py check1 (DONE, ccx rc 0, all steps converged, posts / K / lever env / env npz present, fbd max residual <= 0.02 N, linear connector model) and check2 (12 K values inside the band of its pose class), and cite_guard found no citation of the field (sha or path) in the hub, the reviews, the archive tree and history, the images page or the lead's notes.  The run-folder token search of (A) 1 ran before the seven releases from 17:23:51Z on and found no file that reads, cites or plots the field.  For stop315_c71 (16:13:29Z) and stop090_c71 (16:45:01Z) it ran only afterwards (process slip; SUPPLEMENT lines 17:33:10Z / 17:34:22Z): stop090_c71 0 blocking files of 64; stop315_c71 2 of 71, both the lead's own notes (scratchpad cl/next_lead_line_notes.txt and its .bak-1654, classed 'cites': 'fields.npz' within 300 characters of the run name).  The lead accepted both releases retroactively (16:56:23Z (5)).

What each run folder KEEPS ((A) 2), checked again now: the deck `B1_21.65/f1.inp.gz` (gz sha256 and raw sha256 by streaming gunzip), `model.json` (sha256), the K entries, the posts and the env npz.  All 9 are regenerable now (every kept file present, every sha matches, the field itself absent).

| c71 run | released (UTC) | size B | raw sha256 of the released field | R3 replacement | deck raw sha256 | kept files now |
|---|---|---|---|---|---|---|
| pose_stop315_c71 | 2026-10-20T16:13:29Z | 51,288,795 | `bfd434b6068b0c80d22307f165cf009267f9073e7130340c406854082bc1e911` | pose_stop315_v352r3R3 | `bfa94ebf0ee04de356aedb80ce8f1b2ecbc2aba2e0210425ec8d6ee99bb693ff` | all present, shas match |
| pose_stop090_c71 | 2026-10-20T16:45:01Z | 51,068,618 | `b90456a3ca8e465f087e6062b785e27f7f0e7906e947d7f4f9f4ba6359f95b4f` | pose_stop090_v352r3R3 | `225da59bcba783001af33a03c72bdd056611284709110ea372df83d4779eca8f` | all present, shas match |
| pose_stop180_c71 | 2026-10-20T17:23:51Z | 51,188,200 | `4565a1b376723cf052959d863938520d9f8d18202009fc13ac5861e57c16b326` | pose_stop180_v352r3R3 | `a07d12dbe6007a04533446d8fd036e27fb05bd16f64f573a78f9aef3350498ba` | all present, shas match |
| pose_stop270_c71 | 2026-10-20T17:26:05Z | 51,206,635 | `021fc7027625f38c40f87dd83c8f37b74ccd4f39a9a228ca87d5941a56255d3d` | pose_stop270_v352r3R3 | `6b668a1ddb7c2659c1787058d937e2aed80de6142dc83fa84b742c92a612256e` | all present, shas match |
| pose_beta-_c71 | 2026-10-20T17:29:11Z | 50,354,411 | `f5489bbb782081c72c98ccfca8d919c6c0c8ba2bdf31bba7ff301c194d214229` | pose_beta-_v352r3R3 | `7cb71b223f55552ad9ca7a2de3dadb87ae434576f5fee649ae26866900993c54` | all present, shas match |
| pose_combined135_c71 | 2026-10-20T17:38:34Z | 50,370,699 | `2187d83869ba5f5b98c34c11ad9c37ecb0852cb64abb34d789bb607aaab6db2d` | pose_combined135_v352r3R3 | `e10c7aab20599c28fc9059fb86f3c8e282b8ae29b6f12c02dc52b8208f981508` | all present, shas match |
| pose_combined045_c71 | 2026-10-20T18:08:38Z | 50,320,884 | `13e6a4389e22cde41fa3566662015c35b9f64d482b483145978dbea60910fb11` | pose_combined045_v352r3R3 | `a0f70274a100e3d82a3dc486723cb977ad83b1bf4c7cd4ef1cd69d410e4eae51` | all present, shas match |
| pose_combined225_c71 | 2026-10-20T18:10:19Z | 50,528,574 | `71172bf7f8047fd99d859deb1675ec0a9166cabe1e04932591c2f3c645deb44f` | pose_combined225_v352r3R3 | `2d2b0cbd4e9233f6d3bccb6cd36ff483e6c63ed34a718576b063bed9160816da` | all present, shas match |
| pose_combined315_c71 | 2026-10-20T18:12:47Z | 50,472,942 | `8f8af931353f1fbefc0715d819909020a4250f8a3dc88b2b2e282c08e4881b28` | pose_combined315_v352r3R3 | `6f7af495ea2ef68e8205ece253e6e542373efe8ba6e4044fda6dd70cefd76ace` | all present, shas match |

## Regeneration recipe ((A) 3), per field

CalculiX 2.21 with 2 threads (the solver build and thread count of the original runs); the deck is the kept one, so the instance geometry and mesh are those of the original build.  The npz zip member times differ, so the npz bytes are not expected to repeat; the arrays are expected to repeat to solver round-off (not verified).

### pose_stop315_c71

- released 2026-10-20T16:13:29Z: `runs/pose_stop315_c71/B1_21.65/fields.npz`, 51,288,795 B, raw sha256 `bfd434b6068b0c80d22307f165cf009267f9073e7130340c406854082bc1e911`
- kept: deck `runs/pose_stop315_c71/B1_21.65/f1.inp.gz` (gz sha256 `a7391f8dcbaa6ad1f2124dafa598cffaee6dab601c2097f5e85fb3ec571a63a4`, raw sha256 `bfa94ebf0ee04de356aedb80ce8f1b2ecbc2aba2e0210425ec8d6ee99bb693ff`, 10,416,694 B); `runs/pose_stop315_c71/model.json` sha256 `388f9e5aa3f962e863271ff8299aacdf97d4fd33527cd129bdedceb887f191b6`; `results/f1_post_lc3_pose_stop315_c71.json`; `results/lc3_env_pose_stop315_c71.npz`; `results/k_stop_c71.json`; `results/k_stop_c71_v352.json`
- steps OP, GX, GY, GZ, EAX, EAY, R1, R2, BUMP; R3 replacement pose_stop315_v352r3R3
- recipe: cd runs/pose_stop315_c71/B1_21.65 && gunzip -c f1.inp.gz > f1.inp (raw sha256 bfa94ebf0ee04de356aedb80ce8f1b2ecbc2aba2e0210425ec8d6ee99bb693ff) && OMP_NUM_THREADS=2 CCX_NPROC_EQUATION_SOLVER=2 CCX_NPROC_STIFFNESS=2 CCX_NPROC_RESULTS=2 ccx -i f1 (CalculiX 2.21); then FEA3D_CAD=v351 python -I -B scripts/run_f1.py --extract pose_stop315_c71 B1_21.65 OP,GX,GY,GZ,EAX,EAY,R1,R2,BUMP (writes fields.npz from f1.frd, removes f1.frd); zip member times differ, so the npz bytes are not expected to repeat; the arrays are expected to repeat to solver round-off (not verified)

### pose_stop090_c71

- released 2026-10-20T16:45:01Z: `runs/pose_stop090_c71/B1_21.65/fields.npz`, 51,068,618 B, raw sha256 `b90456a3ca8e465f087e6062b785e27f7f0e7906e947d7f4f9f4ba6359f95b4f`
- kept: deck `runs/pose_stop090_c71/B1_21.65/f1.inp.gz` (gz sha256 `bdc62ebb1621707ba8b20f33c012116ae313772de4109c6a748e64209f64972d`, raw sha256 `225da59bcba783001af33a03c72bdd056611284709110ea372df83d4779eca8f`, 9,798,578 B); `runs/pose_stop090_c71/model.json` sha256 `b6692a6857d495e8d9d792bd6fae3136eca029ba01f54d51847d16d98eb8b1cd`; `results/f1_post_lc3_pose_stop090_c71.json`; `results/lc3_env_pose_stop090_c71.npz`; `results/k_stop_c71.json`; `results/k_stop_c71_v352.json`
- steps OP, GX, GY, GZ, EAX, EAY, R1, R2, BUMP; R3 replacement pose_stop090_v352r3R3
- recipe: cd runs/pose_stop090_c71/B1_21.65 && gunzip -c f1.inp.gz > f1.inp (raw sha256 225da59bcba783001af33a03c72bdd056611284709110ea372df83d4779eca8f) && OMP_NUM_THREADS=2 CCX_NPROC_EQUATION_SOLVER=2 CCX_NPROC_STIFFNESS=2 CCX_NPROC_RESULTS=2 ccx -i f1 (CalculiX 2.21); then FEA3D_CAD=v351 python -I -B scripts/run_f1.py --extract pose_stop090_c71 B1_21.65 OP,GX,GY,GZ,EAX,EAY,R1,R2,BUMP (writes fields.npz from f1.frd, removes f1.frd); zip member times differ, so the npz bytes are not expected to repeat; the arrays are expected to repeat to solver round-off (not verified)

### pose_stop180_c71

- released 2026-10-20T17:23:51Z: `runs/pose_stop180_c71/B1_21.65/fields.npz`, 51,188,200 B, raw sha256 `4565a1b376723cf052959d863938520d9f8d18202009fc13ac5861e57c16b326`
- kept: deck `runs/pose_stop180_c71/B1_21.65/f1.inp.gz` (gz sha256 `e1eb719bf6312df43ac2531f14aa0b6c601f6f65cbd86cac215128b33f8494b1`, raw sha256 `a07d12dbe6007a04533446d8fd036e27fb05bd16f64f573a78f9aef3350498ba`, 9,030,808 B); `runs/pose_stop180_c71/model.json` sha256 `b4725ec40ce94d6f3759eec821b57d524f81821f548aaceda4eec22a03eea6d5`; `results/f1_post_lc3_pose_stop180_c71.json`; `results/lc3_env_pose_stop180_c71.npz`; `results/k_stop_c71.json`; `results/k_stop_c71_v352.json`
- steps OP, GX, GY, GZ, EAX, EAY, R1, R2, BUMP; R3 replacement pose_stop180_v352r3R3
- recipe: cd runs/pose_stop180_c71/B1_21.65 && gunzip -c f1.inp.gz > f1.inp (raw sha256 a07d12dbe6007a04533446d8fd036e27fb05bd16f64f573a78f9aef3350498ba) && OMP_NUM_THREADS=2 CCX_NPROC_EQUATION_SOLVER=2 CCX_NPROC_STIFFNESS=2 CCX_NPROC_RESULTS=2 ccx -i f1 (CalculiX 2.21); then FEA3D_CAD=v351 python -I -B scripts/run_f1.py --extract pose_stop180_c71 B1_21.65 OP,GX,GY,GZ,EAX,EAY,R1,R2,BUMP (writes fields.npz from f1.frd, removes f1.frd); zip member times differ, so the npz bytes are not expected to repeat; the arrays are expected to repeat to solver round-off (not verified)

### pose_stop270_c71

- released 2026-10-20T17:26:05Z: `runs/pose_stop270_c71/B1_21.65/fields.npz`, 51,206,635 B, raw sha256 `021fc7027625f38c40f87dd83c8f37b74ccd4f39a9a228ca87d5941a56255d3d`
- kept: deck `runs/pose_stop270_c71/B1_21.65/f1.inp.gz` (gz sha256 `e7873168beb06488cc6366886d94b76be518713592b893faf9553c4f585052f7`, raw sha256 `6b668a1ddb7c2659c1787058d937e2aed80de6142dc83fa84b742c92a612256e`, 9,799,917 B); `runs/pose_stop270_c71/model.json` sha256 `8c8c01dc68e88365939f9bf9f9eb2582ecbeb7f6c288959df67832e0f0927e45`; `results/f1_post_lc3_pose_stop270_c71.json`; `results/lc3_env_pose_stop270_c71.npz`; `results/k_stop_c71.json`; `results/k_stop_c71_v352.json`
- steps OP, GX, GY, GZ, EAX, EAY, R1, R2, BUMP; R3 replacement pose_stop270_v352r3R3
- recipe: cd runs/pose_stop270_c71/B1_21.65 && gunzip -c f1.inp.gz > f1.inp (raw sha256 6b668a1ddb7c2659c1787058d937e2aed80de6142dc83fa84b742c92a612256e) && OMP_NUM_THREADS=2 CCX_NPROC_EQUATION_SOLVER=2 CCX_NPROC_STIFFNESS=2 CCX_NPROC_RESULTS=2 ccx -i f1 (CalculiX 2.21); then FEA3D_CAD=v351 python -I -B scripts/run_f1.py --extract pose_stop270_c71 B1_21.65 OP,GX,GY,GZ,EAX,EAY,R1,R2,BUMP (writes fields.npz from f1.frd, removes f1.frd); zip member times differ, so the npz bytes are not expected to repeat; the arrays are expected to repeat to solver round-off (not verified)

### pose_beta-_c71

- released 2026-10-20T17:29:11Z: `runs/pose_beta-_c71/B1_21.65/fields.npz`, 50,354,411 B, raw sha256 `f5489bbb782081c72c98ccfca8d919c6c0c8ba2bdf31bba7ff301c194d214229`
- kept: deck `runs/pose_beta-_c71/B1_21.65/f1.inp.gz` (gz sha256 `46910be0466000136a495195474f6ca8b532316bfbb4444959cce79e553ecdd2`, raw sha256 `7cb71b223f55552ad9ca7a2de3dadb87ae434576f5fee649ae26866900993c54`, 10,176,336 B); `runs/pose_beta-_c71/model.json` sha256 `164d467ceb67f79e7e71b1b92ead3415fb3b687e55901ca712b74778dec5b3f8`; `results/s3d_pose_beta-_c71.json`; `results/s3d_env_pose_beta-_c71.npz`; `results/k_cone_c71.json`; `results/k_cone_c71_v352.json`
- steps OP, GX, GY, GZ, EAX, EAY, R1, R2; R3 replacement pose_beta-_v352r3R3
- recipe: cd runs/pose_beta-_c71/B1_21.65 && gunzip -c f1.inp.gz > f1.inp (raw sha256 7cb71b223f55552ad9ca7a2de3dadb87ae434576f5fee649ae26866900993c54) && OMP_NUM_THREADS=2 CCX_NPROC_EQUATION_SOLVER=2 CCX_NPROC_STIFFNESS=2 CCX_NPROC_RESULTS=2 ccx -i f1 (CalculiX 2.21); then FEA3D_CAD=v351 python -I -B scripts/run_f1.py --extract pose_beta-_c71 B1_21.65 OP,GX,GY,GZ,EAX,EAY,R1,R2 (writes fields.npz from f1.frd, removes f1.frd); zip member times differ, so the npz bytes are not expected to repeat; the arrays are expected to repeat to solver round-off (not verified)

### pose_combined135_c71

- released 2026-10-20T17:38:34Z: `runs/pose_combined135_c71/B1_21.65/fields.npz`, 50,370,699 B, raw sha256 `2187d83869ba5f5b98c34c11ad9c37ecb0852cb64abb34d789bb607aaab6db2d`
- kept: deck `runs/pose_combined135_c71/B1_21.65/f1.inp.gz` (gz sha256 `627cfe4ce470dd2576e8601612a9a3fb16e1686554df043a4fefb6a683aa21ba`, raw sha256 `e10c7aab20599c28fc9059fb86f3c8e282b8ae29b6f12c02dc52b8208f981508`, 11,775,418 B); `runs/pose_combined135_c71/model.json` sha256 `f490c29a3a0d29d02ea324d56a6a495e759dc995d8c484e3313b7627a470b316`; `results/s3d_pose_combined135_c71.json`; `results/s3d_env_pose_combined135_c71.npz`; `results/k_cone_c71.json`; `results/k_cone_c71_v352.json`
- steps OP, GX, GY, GZ, EAX, EAY, R1, R2; R3 replacement pose_combined135_v352r3R3
- recipe: cd runs/pose_combined135_c71/B1_21.65 && gunzip -c f1.inp.gz > f1.inp (raw sha256 e10c7aab20599c28fc9059fb86f3c8e282b8ae29b6f12c02dc52b8208f981508) && OMP_NUM_THREADS=2 CCX_NPROC_EQUATION_SOLVER=2 CCX_NPROC_STIFFNESS=2 CCX_NPROC_RESULTS=2 ccx -i f1 (CalculiX 2.21); then FEA3D_CAD=v351 python -I -B scripts/run_f1.py --extract pose_combined135_c71 B1_21.65 OP,GX,GY,GZ,EAX,EAY,R1,R2 (writes fields.npz from f1.frd, removes f1.frd); zip member times differ, so the npz bytes are not expected to repeat; the arrays are expected to repeat to solver round-off (not verified)

### pose_combined045_c71

- released 2026-10-20T18:08:38Z: `runs/pose_combined045_c71/B1_21.65/fields.npz`, 50,320,884 B, raw sha256 `13e6a4389e22cde41fa3566662015c35b9f64d482b483145978dbea60910fb11`
- kept: deck `runs/pose_combined045_c71/B1_21.65/f1.inp.gz` (gz sha256 `5dda99f19a4f7004b36fc458804a3d37b9d47310e5837de786f0639a155fb52d`, raw sha256 `a0f70274a100e3d82a3dc486723cb977ad83b1bf4c7cd4ef1cd69d410e4eae51`, 11,762,379 B); `runs/pose_combined045_c71/model.json` sha256 `1773c0cc0147bdd43489fe44e07b96805b01fb49da947d6f53a31effbf390a32`; `results/s3d_pose_combined045_c71.json`; `results/s3d_env_pose_combined045_c71.npz`; `results/k_cone_c71.json`; `results/k_cone_c71_v352.json`
- steps OP, GX, GY, GZ, EAX, EAY, R1, R2; R3 replacement pose_combined045_v352r3R3
- recipe: cd runs/pose_combined045_c71/B1_21.65 && gunzip -c f1.inp.gz > f1.inp (raw sha256 a0f70274a100e3d82a3dc486723cb977ad83b1bf4c7cd4ef1cd69d410e4eae51) && OMP_NUM_THREADS=2 CCX_NPROC_EQUATION_SOLVER=2 CCX_NPROC_STIFFNESS=2 CCX_NPROC_RESULTS=2 ccx -i f1 (CalculiX 2.21); then FEA3D_CAD=v351 python -I -B scripts/run_f1.py --extract pose_combined045_c71 B1_21.65 OP,GX,GY,GZ,EAX,EAY,R1,R2 (writes fields.npz from f1.frd, removes f1.frd); zip member times differ, so the npz bytes are not expected to repeat; the arrays are expected to repeat to solver round-off (not verified)

### pose_combined225_c71

- released 2026-10-20T18:10:19Z: `runs/pose_combined225_c71/B1_21.65/fields.npz`, 50,528,574 B, raw sha256 `71172bf7f8047fd99d859deb1675ec0a9166cabe1e04932591c2f3c645deb44f`
- kept: deck `runs/pose_combined225_c71/B1_21.65/f1.inp.gz` (gz sha256 `a46ba56af816402618e59e093b475eddac1c918920e276ba0db2ecdbb3cf6f89`, raw sha256 `2d2b0cbd4e9233f6d3bccb6cd36ff483e6c63ed34a718576b063bed9160816da`, 11,759,966 B); `runs/pose_combined225_c71/model.json` sha256 `9541528613a9c118ca4cbbfeed8cab3359e90e48b2c944128b5b9c507863a35c`; `results/s3d_pose_combined225_c71.json`; `results/s3d_env_pose_combined225_c71.npz`; `results/k_cone_c71.json`; `results/k_cone_c71_v352.json`
- steps OP, GX, GY, GZ, EAX, EAY, R1, R2; R3 replacement pose_combined225_v352r3R3
- recipe: cd runs/pose_combined225_c71/B1_21.65 && gunzip -c f1.inp.gz > f1.inp (raw sha256 2d2b0cbd4e9233f6d3bccb6cd36ff483e6c63ed34a718576b063bed9160816da) && OMP_NUM_THREADS=2 CCX_NPROC_EQUATION_SOLVER=2 CCX_NPROC_STIFFNESS=2 CCX_NPROC_RESULTS=2 ccx -i f1 (CalculiX 2.21); then FEA3D_CAD=v351 python -I -B scripts/run_f1.py --extract pose_combined225_c71 B1_21.65 OP,GX,GY,GZ,EAX,EAY,R1,R2 (writes fields.npz from f1.frd, removes f1.frd); zip member times differ, so the npz bytes are not expected to repeat; the arrays are expected to repeat to solver round-off (not verified)

### pose_combined315_c71

- released 2026-10-20T18:12:47Z: `runs/pose_combined315_c71/B1_21.65/fields.npz`, 50,472,942 B, raw sha256 `8f8af931353f1fbefc0715d819909020a4250f8a3dc88b2b2e282c08e4881b28`
- kept: deck `runs/pose_combined315_c71/B1_21.65/f1.inp.gz` (gz sha256 `425bace485daa4776e5dd8cf9cdb0ed330c5c2fcc92136e0bcebe183562bd65e`, raw sha256 `6f7af495ea2ef68e8205ece253e6e542373efe8ba6e4044fda6dd70cefd76ace`, 11,780,466 B); `runs/pose_combined315_c71/model.json` sha256 `8e881e27523d1964b18185def1381141508cbc35b0d5b48ed4235707b1086664`; `results/s3d_pose_combined315_c71.json`; `results/s3d_env_pose_combined315_c71.npz`; `results/k_cone_c71.json`; `results/k_cone_c71_v352.json`
- steps OP, GX, GY, GZ, EAX, EAY, R1, R2; R3 replacement pose_combined315_v352r3R3
- recipe: cd runs/pose_combined315_c71/B1_21.65 && gunzip -c f1.inp.gz > f1.inp (raw sha256 6f7af495ea2ef68e8205ece253e6e542373efe8ba6e4044fda6dd70cefd76ace) && OMP_NUM_THREADS=2 CCX_NPROC_EQUATION_SOLVER=2 CCX_NPROC_STIFFNESS=2 CCX_NPROC_RESULTS=2 ccx -i f1 (CalculiX 2.21); then FEA3D_CAD=v351 python -I -B scripts/run_f1.py --extract pose_combined315_c71 B1_21.65 OP,GX,GY,GZ,EAX,EAY,R1,R2 (writes fields.npz from f1.frd, removes f1.frd); zip member times differ, so the npz bytes are not expected to repeat; the arrays are expected to repeat to solver round-off (not verified)

## Pre-fix samples.py (lead 17:17:49Z (ii))

`samples.py.bak_v352` beside this note: sha256 `a79a2defaeb496cb5bf2ad24622d41875fdaef840297ea2ea1a31f904455a3f7`, 1,660 B.  It is the samples.py of the fea3d tree when the c71 runs above were built (their decks and model.json date from 2026-10-19 18:07-20:21Z), before the v3.5.2 port fix of `instance_surface` (samples.py mtime 2026-10-20T02:19:48Z): before the fix every CAD version read the v3.5 instance BREPs (geom/v35_neutral; cache geom/samples/<stem>_h<h>.npz), after it the CAD's own.  The recipes re-solve the kept decks and do not need it; it is kept as provenance (lead 17:17:49Z (ii)).  Nothing reads or imports this copy (the v3.5.2 tree imports the fixed samples.py; scripts/modal_isolate_rbe3.py re-implements the pre-fix instance_surface inline for the RM2-06 isolation).

Sources (sha256/16): runs/PRUNED_v352.txt 1127cfa4d2e425d6, results/v352/release_c71_log.json ed776b40b27dec69, scripts/release_c71.py 077fcf37a8d27a61
