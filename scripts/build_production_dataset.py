import os
import json
import shutil
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BATCH_MANIFEST = os.path.join(PROJECT_ROOT, "datasets", "batches", "svbatch_20260421_151306", "batch_manifest.json")
PRODUCTION_BASE = os.path.join(PROJECT_ROOT, "datasets", "production", "sign_verse_v1")

# Subdirectories
DIRS = {
    "kinematics": os.path.join(PRODUCTION_BASE, "kinematics"),
    "simulation": os.path.join(PRODUCTION_BASE, "simulation"),
    "animation": os.path.join(PRODUCTION_BASE, "animation"),
    "previews": os.path.join(PRODUCTION_BASE, "previews"),
    "metadata": os.path.join(PRODUCTION_BASE, "metadata"),
}

def extract_info_from_name(name):
    # Format: 01_category_Title_VideoID.mp4
    parts = name.split("_")
    category = "unknown"
    if len(parts) > 1:
        category = parts[1]
    
    # Video ID is usually the last part before extension
    video_id = name.split("_")[-1].split(".")[0]
    return category, video_id

def build_dataset():
    print(f"Loading manifest: {BATCH_MANIFEST}")
    with open(BATCH_MANIFEST, "r") as f:
        manifest = json.load(f)

    # Pre-parse all videos to get categories
    parsed_videos = []
    for vid in manifest["videos"]:
        cat, vid_id = extract_info_from_name(vid["inspection"]["name"])
        vid["_extracted_category"] = cat
        vid["_extracted_id"] = vid_id
        parsed_videos.append(vid)

    categories = sorted(list(set(v["_extracted_category"] for v in parsed_videos)))

    index = {
        "dataset_name": "Sign-Verse Production Dataset V1",
        "version": "1.0.0",
        "release_date": time.strftime("%Y-%m-%d"),
        "total_videos": len(manifest["videos"]),
        "categories": categories,
        "videos": []
    }

    for vid in parsed_videos:
        category = vid["_extracted_category"]
        video_id = vid["_extracted_id"]
        slug = vid["session_name"].replace("svbatch_20260421_151306_", "")[:50].strip("_")
        
        print(f"Processing: {category} | {slug}")

        video_entry = {
            "category": category,
            "slug": slug,
            "video_id": video_id,
            "duration_s": vid["inspection"]["duration_s"],
            "fps": vid["workflow"]["sample_fps"],
            "files": {}
        }

        # Mapping of artifact keys to our production structure
        mapping = {
            "training_set_npy": ("kinematics", f"{slug}_training.npy"),
            "training_set_csv": ("kinematics", f"{slug}_training.csv"),
            "simulation_3d": ("simulation", f"{slug}_sim3d.json"),
            "retargeted_motion": ("simulation", f"{slug}_retargeted.json"),
            "blender_export_bvh": ("animation", f"{slug}_animation.bvh"),
            "gltf_animation": ("animation", f"{slug}_animation_gltf.json"),
            "annotated_preview": ("previews", f"{slug}_preview.mp4")
        }

        for key, (folder, new_filename) in mapping.items():
            src_rel = vid["summary"]["artifacts"].get(key)
            if not src_rel:
                continue
                
            src_abs = os.path.join(PROJECT_ROOT, src_rel)
            dst_abs = os.path.join(DIRS[folder], new_filename)
            
            if os.path.exists(src_abs):
                shutil.copy2(src_abs, dst_abs)
                video_entry["files"][key] = os.path.relpath(dst_abs, PRODUCTION_BASE)
            else:
                print(f"  [WARNING] Missing artifact: {key} at {src_abs}")

        # Also copy the source manifest to metadata
        src_manifest = os.path.join(PROJECT_ROOT, vid["session_path"], "source_manifest.json")
        if os.path.exists(src_manifest):
            dst_manifest = os.path.join(DIRS["metadata"], f"{slug}_manifest.json")
            shutil.copy2(src_manifest, dst_manifest)
            video_entry["files"]["source_manifest"] = os.path.relpath(dst_manifest, PRODUCTION_BASE)

        index["videos"].append(video_entry)

    # Write global index
    index_path = os.path.join(PRODUCTION_BASE, "index.json")
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)
    
    print(f"\nSuccess! Production dataset built at: {PRODUCTION_BASE}")
    print(f"Indexed {len(index['videos'])} videos.")

if __name__ == "__main__":
    build_dataset()
