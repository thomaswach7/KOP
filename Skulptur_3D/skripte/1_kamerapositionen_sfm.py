import sys, shutil
from pathlib import Path
import pycolmap

root = Path(sys.argv[1])
img, db, sp = root / "img", root / "db.db", root / "sparse"
db.unlink(missing_ok=True)
shutil.rmtree(sp, ignore_errors=True)
sp.mkdir()

ext = pycolmap.FeatureExtractionOptions()
ext.sift.max_num_features = 8192
ro = pycolmap.ImageReaderOptions()
ro.camera_model = "SIMPLE_RADIAL"
pycolmap.extract_features(db, img, camera_mode=pycolmap.CameraMode.SINGLE,
                          reader_options=ro, extraction_options=ext)
po = pycolmap.SequentialPairingOptions()
po.overlap = 40
po.quadratic_overlap = True
po.loop_detection = False
pycolmap.match_sequential(db, pairing_options=po)

opt = pycolmap.IncrementalPipelineOptions()
opt.min_num_matches = 10
opt.structure_less_registration_fallback = True
opt.mapper.abs_pose_min_num_inliers = 12
opt.mapper.abs_pose_min_inlier_ratio = 0.15
opt.mapper.init_min_num_inliers = 50
recs = pycolmap.incremental_mapping(db, img, sp, options=opt)
for i, r in recs.items():
    ids = sorted(int(im.name[:4]) for im in r.images.values())
    print("MODEL", i, len(ids), ids[0], ids[-1], "missing:", sorted(set(range(ids[0], ids[-1] + 1)) - set(ids)))
