export interface TrainingMetrics {
  epoch: number;
  loss: number;
  accuracy: number;
  val_loss: number;
  dataset_size: number;
  is_training: boolean;
}

export interface TelemetryMetrics {
  current_intent?: string;
  intent_confidence?: number;
  stability_health?: number;
  rl_latency_ms?: number;
  control_latency_ms?: number;
  reward?: number;
  fps?: number;
  skeleton_version?: string;
  robot_payload?: Record<string, number>;
  contact_forces?: number[];
  cpu_usage?: number;
  robot_velocity?: number[];
  total_power_drain?: number;
  hand_embedding?: number[];
  hand_joints?: number[][];
  bridge_status?: { blender: boolean; isaac: boolean };
  training?: TrainingMetrics;
}

export interface HealthReport {
  is_recording?: boolean;
  metrics?: Record<string, TelemetryMetrics>;
}

export interface MotionFrame {
  timestamp: number;
  confidence: number;
  joints: number[][];
  metadata?: {
    pose_2d?: Array<{ x: number; y: number; z: number; visibility?: number }>;
    subject_id?: number;
    bbox?: number[];
    tracking?: {
      missing_count?: number;
      last_seen_frame?: number;
      drift_warning?: boolean;
      centroid_distance?: number;
    };
  };
}

export interface SessionSummary {
  name: string;
  path: string;
  frame_count: number;
  motion_frame_count: number;
  duration_s: number;
  processed_frames: number;
  tracked_frames: number;
  effective_fps?: number;
  source_video?: string;
  chunk_frames?: number;
  has_thumbnail: boolean;
  has_preview: boolean;
  has_training_export: boolean;
  artifact_files: string[];
  workflow_summary?: Record<string, unknown>;
}

export interface Simulation2DFrame {
  frame_index: number;
  timestamp: number;
  subject_id: number;
  bbox: number[];
  pose: Array<{ x: number; y: number; z: number; visibility?: number }>;
  tracking?: Record<string, unknown>;
}

export interface Simulation3DFrame {
  frame_index: number;
  timestamp: number;
  subject_id: number;
  joints: number[][];
  centroid: number[];
  velocity: number[];
  confidence: number;
}

export interface RetargetFrame {
  frame_index: number;
  timestamp: number;
  subject_id: number;
  robot_joints: Record<string, number>;
}

export interface BatchVideoEntry {
  session_name: string;
  session_path: string;
  inspection?: {
    name?: string;
    path?: string;
    fps?: number;
    frame_count?: number;
    duration_s?: number;
    width?: number;
    height?: number;
    source_kind?: string;
    likely_youtube_video?: boolean;
  };
  workflow?: {
    sample_fps?: number;
    chunk_frames?: number;
    elapsed_s?: number;
    verification_ok?: boolean;
  };
  summary?: {
    processed_frames?: number;
    tracked_frames?: number;
    effective_fps?: number;
  };
}

export interface BatchSummary {
  batch_id: string;
  path: string;
  video_folder?: string;
  video_count: number;
  completed_count: number;
  verified_count: number;
  processed_frames_total: number;
  tracked_frames_total: number;
  artifacts?: {
    manifest?: boolean;
    report_csv?: boolean;
    report_json?: boolean;
  };
  videos: BatchVideoEntry[];
}

export interface AutoYouTubePipelineJob {
  job_id: string;
  status: string;
  phase: string;
  message: string;
  started_at?: number | null;
  finished_at?: number | null;
  error?: string | null;
  categories: string[];
  results_per_category: number;
  sample_fps?: number | null;
  chunk_frames: number;
  download_dir: string;
  downloaded_videos: Array<{
    title?: string;
    url?: string;
    video_id?: string;
    duration?: number;
    local_path?: string;
    category?: string;
  }>;
  batch_dir?: string | null;
  batch_id?: string | null;
  report_paths?: Record<string, string>;
}
