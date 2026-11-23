# Live bolt inspection: from parts to a scored test

One bolt type first (e.g. M8-M10). Classes: `thread_damage`, `deformation`, `rust`.

1. **Parts.** About 40 good and 40 defective bolts (13 or more per defect). Write an id on a bag or tag for each: `B001`, `B002`, ...
   One defect type per bolt. A good bolt that you damage later gets a new id, and its old photos stay under the old id;
   keep both ids out of the test set by hand, because the tool cannot know they are the same bolt.
2. **Rig.** Fixed camera straight above, plain matte background, diffuse light from two sides, focus and exposure locked.
   Use the same rig, `--crop` and resolution for capture, live test and demo.
3. **Capture.** `python training/capture_images.py --out data/raw/captures/day1 --shots 4`
   Mix good and defective bolts in random order within each session. If all rusty bolts are photographed in one sitting,
   the model can learn the lighting instead of the rust.
4. **Label** in CVAT or Label Studio, class order as in `configs/profiles/fasteners.yaml`, YOLO export, keep file names.
   If the defect is not visible in a photo, export an empty label file for it.
5. **Split by part.** `python training/prepare_fasteners.py --images data/raw/captures/day1 --labels data/raw/labels/day1`
6. **Train, calibrate, evaluate.**
   `python training/train.py --profile fasteners --epochs 100`
   `python training/calibrate_severity.py --profile fasteners`
   `python training/evaluate.py --profile fasteners --backend torch --map`
7. **Live test** with bolts not used for training or validation (others are refused):
   `python training/live_test.py --backend torch` (on the Jetson: `--backend tensorrt` after `training/export.py`).
8. **Demo.** `python -m qc serve --set profile=fasteners --set source.type=camera --set source.camera.crop=square
   --set source.camera.trigger=stable --set source.fps_limit=0`

Photos of one bolt are not independent. Report the number of bolts beside every percentage.
