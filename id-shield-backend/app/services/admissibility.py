"""
Evidence Admissibility Service

Computes quality metrics, viability scores, admissibility grades, and limitations
for forensic evidence. All computations are deterministic and reproducible.

This service implements:
1. Quality Metrics Computation (blur, resolution, brightness, SNR, etc.)
2. Viability Score Derivation (0-100)
3. Admissibility Grade Derivation (A/B/C/D)
4. Suitability Tags (Identity, Manipulation, Timeline, Audio)
5. Limitations Engine (structured, court-neutral statements)
"""

import os
import json
import subprocess
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from PIL import Image
import numpy as np
from sqlalchemy.orm import Session

from app.models.evidence import Evidence, EvidenceType
from app.models.admissibility import (
    EvidenceQualityMetrics,
    EvidenceAdmissibility,
    AdmissibilityGrade,
    IdentitySuitability,
    SuitabilityLevel
)
from app.models.analysis import AnalysisResult, AnalysisType
from app.models.audit import AuditLog, AuditAction


# =============================================================================
# THRESHOLDS CONFIGURATION (Tunable)
# =============================================================================

THRESHOLDS_VERSION = "1.0.0"

# Image thresholds
MIN_IMAGE_WIDTH = 640
MIN_IMAGE_HEIGHT = 480
MIN_FACE_RESOLUTION = 80  # Minimum face bounding box width in pixels
BLUR_THRESHOLD_HIGH = 100  # Variance of Laplacian - above this is sharp
BLUR_THRESHOLD_LOW = 30    # Below this is too blurry
BRIGHTNESS_MIN = 40        # Minimum mean brightness (0-255)
BRIGHTNESS_MAX = 220       # Maximum mean brightness (0-255)
COMPRESSION_RATIO_MAX = 0.15  # Max file_size / (width * height * 3) for high quality

# Video thresholds
MIN_VIDEO_BITRATE = 500000  # 500 kbps minimum
MIN_VIDEO_FRAMES = 24       # At least 1 second at 24fps
MIN_KEYFRAME_INTERVAL = 300 # Max frames between keyframes

# Audio thresholds
MIN_SNR_DB = 10            # Minimum signal-to-noise ratio in dB
MIN_SPEECH_CONFIDENCE = 0.5 # Minimum speech presence confidence

# Viability score weights
WEIGHTS = {
    "resolution": 0.20,
    "blur": 0.25,
    "brightness": 0.15,
    "compression": 0.10,
    "metadata": 0.15,
    "integrity": 0.15
}

# Grade thresholds
GRADE_A_MIN = 80
GRADE_B_MIN = 60
GRADE_C_MIN = 40
# Below GRADE_C_MIN = Grade D


# =============================================================================
# LIMITATION CODES AND TEMPLATES
# =============================================================================

LIMITATION_TEMPLATES = {
    "LOW_RESOLUTION": {
        "what": "Image resolution is below recommended threshold",
        "why": "Resolution {width}x{height} is below minimum {min_width}x{min_height}",
        "impact": "Fine detail analysis may be limited",
        "severity": "medium"
    },
    "LOW_FACE_RESOLUTION": {
        "what": "Identity attribution was not performed",
        "why": "Insufficient facial resolution (no face detected or face too small)",
        "impact": "Cannot assess identity consistency for this evidence",
        "severity": "high"
    },
    "HIGH_BLUR": {
        "what": "Image exhibits significant blur",
        "why": "Blur score {blur_score:.1f} is below threshold {threshold}",
        "impact": "Detail-dependent analysis reliability is reduced",
        "severity": "high"
    },
    "MODERATE_BLUR": {
        "what": "Image exhibits moderate blur",
        "why": "Blur score {blur_score:.1f} is below optimal threshold {threshold}",
        "impact": "Some fine detail analysis may be affected",
        "severity": "medium"
    },
    "LOW_BRIGHTNESS": {
        "what": "Image is underexposed (too dark)",
        "why": "Mean brightness {brightness:.1f} is below minimum {threshold}",
        "impact": "Shadow detail and manipulation detection may be limited",
        "severity": "medium"
    },
    "HIGH_BRIGHTNESS": {
        "what": "Image is overexposed (too bright)",
        "why": "Mean brightness {brightness:.1f} exceeds maximum {threshold}",
        "impact": "Highlight detail and manipulation detection may be limited",
        "severity": "medium"
    },
    "HIGH_COMPRESSION": {
        "what": "High compression artifacts detected",
        "why": "Compression ratio {ratio:.3f} indicates significant compression",
        "impact": "Fine-grained manipulation localization reliability is reduced",
        "severity": "medium"
    },
    "MISSING_METADATA_TIMESTAMPS": {
        "what": "Metadata timestamps are missing or incomplete",
        "why": "EXIF/metadata does not contain reliable timestamp information",
        "impact": "Timeline confidence is reduced; temporal context cannot be verified",
        "severity": "medium"
    },
    "MISSING_METADATA_DEVICE": {
        "what": "Device information is missing from metadata",
        "why": "EXIF/metadata does not contain camera/device information",
        "impact": "Source verification is limited",
        "severity": "low"
    },
    "LOW_VIDEO_BITRATE": {
        "what": "Video bitrate is below recommended threshold",
        "why": "Bitrate {bitrate} kbps is below minimum {threshold} kbps",
        "impact": "Frame-level analysis quality may be reduced",
        "severity": "medium"
    },
    "LOW_VIDEO_FRAMES": {
        "what": "Video has insufficient frame count",
        "why": "Frame count {frames} is below minimum {threshold}",
        "impact": "Temporal analysis and motion detection are limited",
        "severity": "medium"
    },
    "LOW_SNR": {
        "what": "Audio signal-to-noise ratio is insufficient",
        "why": "Estimated SNR {snr:.1f} dB is below minimum {threshold} dB",
        "impact": "Audio content interpretation is not reliable",
        "severity": "high"
    },
    "LOW_SPEECH_CONFIDENCE": {
        "what": "Speech presence confidence is low",
        "why": "Speech detection confidence {confidence:.1%} is below threshold {threshold:.1%}",
        "impact": "Audio content analysis may not be meaningful",
        "severity": "medium"
    },
    "FILE_UNREADABLE": {
        "what": "Evidence file could not be read or processed",
        "why": "File is missing, corrupted, or in an unsupported format",
        "impact": "No quality metrics could be computed; evidence is not suitable for analysis",
        "severity": "critical"
    },
    "UNSUPPORTED_FORMAT": {
        "what": "Evidence format is not fully supported",
        "why": "File type {file_type} has limited analysis support",
        "impact": "Some quality metrics could not be computed",
        "severity": "medium"
    },
    "INTEGRITY_WARNINGS": {
        "what": "Integrity analysis detected potential issues",
        "why": "{warning_summary}",
        "impact": "Evidence authenticity confidence is reduced",
        "severity": "high"
    }
}


# =============================================================================
# QUALITY METRICS COMPUTATION
# =============================================================================

def compute_blur_score(image: Image.Image) -> float:
    """Compute blur score using variance of Laplacian.
    
    Higher values indicate sharper images.
    """
    gray = image.convert('L')
    img_array = np.array(gray, dtype=np.float64)
    
    # Laplacian kernel
    laplacian_kernel = np.array([
        [0, 1, 0],
        [1, -4, 1],
        [0, 1, 0]
    ], dtype=np.float64)
    
    # Apply convolution manually (avoiding scipy dependency)
    h, w = img_array.shape
    padded = np.pad(img_array, 1, mode='edge')
    result = np.zeros_like(img_array)
    
    for i in range(h):
        for j in range(w):
            result[i, j] = np.sum(padded[i:i+3, j:j+3] * laplacian_kernel)
    
    # Variance of Laplacian
    variance = np.var(result)
    return float(variance)


def compute_brightness_stats(image: Image.Image) -> Dict[str, float]:
    """Compute brightness statistics from image histogram."""
    gray = image.convert('L')
    histogram = gray.histogram()
    
    # Compute mean brightness
    total_pixels = sum(histogram)
    mean_brightness = sum(i * count for i, count in enumerate(histogram)) / total_pixels
    
    # Compute histogram spread (std dev)
    variance = sum(count * (i - mean_brightness) ** 2 for i, count in enumerate(histogram)) / total_pixels
    std_brightness = variance ** 0.5
    
    # Compute percentiles
    cumsum = 0
    p5, p95 = 0, 255
    for i, count in enumerate(histogram):
        cumsum += count
        if cumsum >= total_pixels * 0.05 and p5 == 0:
            p5 = i
        if cumsum >= total_pixels * 0.95:
            p95 = i
            break
    
    return {
        "mean": mean_brightness,
        "std": std_brightness,
        "p5": p5,
        "p95": p95,
        "dynamic_range": p95 - p5
    }


def compute_compression_ratio(file_path: str, width: int, height: int) -> float:
    """Compute compression ratio as file_size / uncompressed_size."""
    file_size = os.path.getsize(file_path)
    uncompressed_size = width * height * 3  # RGB
    return file_size / uncompressed_size if uncompressed_size > 0 else 1.0


def get_video_metadata(file_path: str) -> Optional[Dict[str, Any]]:
    """Extract video metadata using ffprobe."""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass
    return None


def get_audio_metadata(file_path: str) -> Optional[Dict[str, Any]]:
    """Extract audio metadata using ffprobe."""
    return get_video_metadata(file_path)  # Same command works for audio


def estimate_audio_snr(file_path: str) -> Optional[float]:
    """Estimate audio SNR using ffmpeg volumedetect filter.
    
    This is a heuristic based on the difference between max and mean volume.
    """
    try:
        cmd = [
            'ffmpeg', '-i', file_path, '-af', 'volumedetect',
            '-f', 'null', '-'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        stderr = result.stderr
        
        # Parse volumedetect output
        max_volume = None
        mean_volume = None
        
        for line in stderr.split('\n'):
            if 'max_volume' in line:
                try:
                    max_volume = float(line.split(':')[1].strip().split()[0])
                except (IndexError, ValueError):
                    pass
            if 'mean_volume' in line:
                try:
                    mean_volume = float(line.split(':')[1].strip().split()[0])
                except (IndexError, ValueError):
                    pass
        
        if max_volume is not None and mean_volume is not None:
            # Estimate SNR as difference between max and mean (simplified heuristic)
            # Higher difference suggests more dynamic range / less noise floor
            snr_estimate = abs(max_volume - mean_volume)
            return snr_estimate
    except Exception:
        pass
    return None


def compute_image_metrics(evidence: Evidence) -> Dict[str, Any]:
    """Compute quality metrics for image evidence."""
    metrics = {
        "type": "image",
        "computed_at": datetime.utcnow().isoformat(),
        "thresholds_version": THRESHOLDS_VERSION
    }
    
    try:
        with Image.open(evidence.file_path) as img:
            width, height = img.size
            
            metrics["resolution"] = {
                "width": width,
                "height": height,
                "megapixels": (width * height) / 1_000_000,
                "meets_threshold": width >= MIN_IMAGE_WIDTH and height >= MIN_IMAGE_HEIGHT
            }
            
            metrics["blur"] = {
                "score": compute_blur_score(img),
                "threshold_high": BLUR_THRESHOLD_HIGH,
                "threshold_low": BLUR_THRESHOLD_LOW
            }
            
            brightness_stats = compute_brightness_stats(img)
            metrics["brightness"] = {
                **brightness_stats,
                "threshold_min": BRIGHTNESS_MIN,
                "threshold_max": BRIGHTNESS_MAX,
                "adequate": BRIGHTNESS_MIN <= brightness_stats["mean"] <= BRIGHTNESS_MAX
            }
            
            compression_ratio = compute_compression_ratio(evidence.file_path, width, height)
            metrics["compression"] = {
                "ratio": compression_ratio,
                "threshold": COMPRESSION_RATIO_MAX,
                "acceptable": compression_ratio <= COMPRESSION_RATIO_MAX
            }
            
            # Check for metadata
            exif = img._getexif() if hasattr(img, '_getexif') else None
            has_timestamp = False
            has_device = False
            
            if exif:
                # Common EXIF tags for timestamp and device
                timestamp_tags = [36867, 36868, 306]  # DateTimeOriginal, DateTimeDigitized, DateTime
                device_tags = [271, 272]  # Make, Model
                
                has_timestamp = any(tag in exif for tag in timestamp_tags)
                has_device = any(tag in exif for tag in device_tags)
            
            metrics["metadata"] = {
                "has_exif": exif is not None,
                "has_timestamp": has_timestamp,
                "has_device_info": has_device
            }
            
            metrics["readable"] = True
            
    except Exception as e:
        metrics["readable"] = False
        metrics["error"] = str(e)
    
    return metrics


def compute_video_metrics(evidence: Evidence) -> Dict[str, Any]:
    """Compute quality metrics for video evidence."""
    metrics = {
        "type": "video",
        "computed_at": datetime.utcnow().isoformat(),
        "thresholds_version": THRESHOLDS_VERSION
    }
    
    video_meta = get_video_metadata(evidence.file_path)
    
    if video_meta is None:
        metrics["readable"] = False
        metrics["error"] = "Could not read video metadata"
        return metrics
    
    metrics["readable"] = True
    
    # Extract video stream info
    video_stream = None
    audio_stream = None
    
    for stream in video_meta.get("streams", []):
        if stream.get("codec_type") == "video" and video_stream is None:
            video_stream = stream
        elif stream.get("codec_type") == "audio" and audio_stream is None:
            audio_stream = stream
    
    if video_stream:
        width = video_stream.get("width", 0)
        height = video_stream.get("height", 0)
        
        metrics["resolution"] = {
            "width": width,
            "height": height,
            "megapixels": (width * height) / 1_000_000,
            "meets_threshold": width >= MIN_IMAGE_WIDTH and height >= MIN_IMAGE_HEIGHT
        }
        
        # Bitrate
        bitrate = int(video_stream.get("bit_rate", 0) or video_meta.get("format", {}).get("bit_rate", 0) or 0)
        metrics["bitrate"] = {
            "value": bitrate,
            "value_kbps": bitrate / 1000 if bitrate else 0,
            "threshold_kbps": MIN_VIDEO_BITRATE / 1000,
            "adequate": bitrate >= MIN_VIDEO_BITRATE
        }
        
        # Frame count
        nb_frames = int(video_stream.get("nb_frames", 0) or 0)
        metrics["frames"] = {
            "count": nb_frames,
            "threshold": MIN_VIDEO_FRAMES,
            "adequate": nb_frames >= MIN_VIDEO_FRAMES
        }
        
        # Duration
        duration = float(video_meta.get("format", {}).get("duration", 0) or 0)
        metrics["duration"] = {
            "seconds": duration
        }
    
    # Metadata timestamps
    format_tags = video_meta.get("format", {}).get("tags", {})
    has_timestamp = any(k.lower() in ['creation_time', 'date', 'datetime'] 
                       for k in format_tags.keys())
    
    metrics["metadata"] = {
        "has_timestamp": has_timestamp,
        "format_name": video_meta.get("format", {}).get("format_name", "unknown")
    }
    
    # Audio SNR if audio stream exists
    if audio_stream:
        snr = estimate_audio_snr(evidence.file_path)
        metrics["audio"] = {
            "present": True,
            "snr_estimate": snr,
            "snr_adequate": snr is not None and snr >= MIN_SNR_DB
        }
    else:
        metrics["audio"] = {"present": False}
    
    return metrics


def compute_audio_metrics(evidence: Evidence) -> Dict[str, Any]:
    """Compute quality metrics for audio evidence."""
    metrics = {
        "type": "audio",
        "computed_at": datetime.utcnow().isoformat(),
        "thresholds_version": THRESHOLDS_VERSION
    }
    
    audio_meta = get_audio_metadata(evidence.file_path)
    
    if audio_meta is None:
        metrics["readable"] = False
        metrics["error"] = "Could not read audio metadata"
        return metrics
    
    metrics["readable"] = True
    
    # Extract audio stream info
    audio_stream = None
    for stream in audio_meta.get("streams", []):
        if stream.get("codec_type") == "audio":
            audio_stream = stream
            break
    
    if audio_stream:
        sample_rate = int(audio_stream.get("sample_rate", 0) or 0)
        channels = int(audio_stream.get("channels", 0) or 0)
        bitrate = int(audio_stream.get("bit_rate", 0) or audio_meta.get("format", {}).get("bit_rate", 0) or 0)
        
        metrics["format"] = {
            "sample_rate": sample_rate,
            "channels": channels,
            "bitrate": bitrate,
            "codec": audio_stream.get("codec_name", "unknown")
        }
        
        # Duration
        duration = float(audio_meta.get("format", {}).get("duration", 0) or 0)
        metrics["duration"] = {
            "seconds": duration
        }
        
        # SNR estimate
        snr = estimate_audio_snr(evidence.file_path)
        metrics["snr"] = {
            "estimate": snr,
            "threshold": MIN_SNR_DB,
            "adequate": snr is not None and snr >= MIN_SNR_DB
        }
        
        # Speech presence (simplified heuristic based on audio characteristics)
        # In production, this would use a speech detection model
        # For now, we use a deterministic heuristic based on file characteristics
        speech_confidence = 0.7 if sample_rate >= 16000 and duration >= 1.0 else 0.3
        metrics["speech"] = {
            "confidence": speech_confidence,
            "threshold": MIN_SPEECH_CONFIDENCE,
            "detected": speech_confidence >= MIN_SPEECH_CONFIDENCE
        }
    
    # Metadata
    format_tags = audio_meta.get("format", {}).get("tags", {})
    has_timestamp = any(k.lower() in ['creation_time', 'date', 'datetime'] 
                       for k in format_tags.keys())
    
    metrics["metadata"] = {
        "has_timestamp": has_timestamp,
        "format_name": audio_meta.get("format", {}).get("format_name", "unknown")
    }
    
    return metrics


def compute_quality_metrics(evidence: Evidence) -> Dict[str, Any]:
    """Compute quality metrics based on evidence type."""
    if evidence.evidence_type in [EvidenceType.PHOTO, EvidenceType.SCREENSHOT]:
        return compute_image_metrics(evidence)
    elif evidence.evidence_type == EvidenceType.VIDEO:
        return compute_video_metrics(evidence)
    elif evidence.evidence_type == EvidenceType.AUDIO:
        return compute_audio_metrics(evidence)
    else:
        return {
            "type": "document",
            "computed_at": datetime.utcnow().isoformat(),
            "thresholds_version": THRESHOLDS_VERSION,
            "readable": True,
            "note": "Document type - limited quality metrics available"
        }


# =============================================================================
# VIABILITY SCORE COMPUTATION
# =============================================================================

def compute_viability_score(metrics: Dict[str, Any], integrity_score: Optional[float] = None) -> int:
    """Compute viability score (0-100) from quality metrics.
    
    The score is a weighted combination of various quality factors.
    """
    if not metrics.get("readable", False):
        return 0
    
    scores = {}
    
    evidence_type = metrics.get("type", "unknown")
    
    if evidence_type in ["image", "video"]:
        # Resolution score
        resolution = metrics.get("resolution", {})
        if resolution.get("meets_threshold", False):
            mp = resolution.get("megapixels", 0)
            scores["resolution"] = min(100, 50 + mp * 25)  # 0.5MP = 62.5, 2MP = 100
        else:
            width = resolution.get("width", 0)
            height = resolution.get("height", 0)
            ratio = min(width / MIN_IMAGE_WIDTH, height / MIN_IMAGE_HEIGHT, 1.0)
            scores["resolution"] = ratio * 50
        
        # Blur score (for images)
        if evidence_type == "image":
            blur = metrics.get("blur", {})
            blur_score = blur.get("score", 0)
            if blur_score >= BLUR_THRESHOLD_HIGH:
                scores["blur"] = 100
            elif blur_score >= BLUR_THRESHOLD_LOW:
                scores["blur"] = 50 + 50 * (blur_score - BLUR_THRESHOLD_LOW) / (BLUR_THRESHOLD_HIGH - BLUR_THRESHOLD_LOW)
            else:
                scores["blur"] = 50 * blur_score / BLUR_THRESHOLD_LOW
        else:
            # For video, use bitrate as proxy for quality
            bitrate = metrics.get("bitrate", {})
            if bitrate.get("adequate", False):
                scores["blur"] = 80
            else:
                ratio = bitrate.get("value", 0) / MIN_VIDEO_BITRATE if MIN_VIDEO_BITRATE > 0 else 0
                scores["blur"] = min(80, ratio * 80)
        
        # Brightness score
        brightness = metrics.get("brightness", {})
        if brightness.get("adequate", True):
            scores["brightness"] = 100
        else:
            mean = brightness.get("mean", 128)
            if mean < BRIGHTNESS_MIN:
                scores["brightness"] = 50 * mean / BRIGHTNESS_MIN
            else:
                scores["brightness"] = 50 * (255 - mean) / (255 - BRIGHTNESS_MAX)
        
        # Compression score
        compression = metrics.get("compression", {})
        if compression.get("acceptable", True):
            scores["compression"] = 100
        else:
            ratio = compression.get("ratio", 1.0)
            scores["compression"] = max(0, 100 - (ratio - COMPRESSION_RATIO_MAX) * 200)
    
    elif evidence_type == "audio":
        # Audio-specific scoring
        snr = metrics.get("snr", {})
        if snr.get("adequate", False):
            scores["resolution"] = 80
            scores["blur"] = 80
        else:
            snr_val = snr.get("estimate", 0) or 0
            ratio = snr_val / MIN_SNR_DB if MIN_SNR_DB > 0 else 0
            scores["resolution"] = min(80, ratio * 80)
            scores["blur"] = min(80, ratio * 80)
        
        scores["brightness"] = 80  # N/A for audio
        scores["compression"] = 80  # N/A for audio
    
    else:
        # Document or unknown type
        scores["resolution"] = 70
        scores["blur"] = 70
        scores["brightness"] = 70
        scores["compression"] = 70
    
    # Metadata score
    metadata = metrics.get("metadata", {})
    metadata_score = 50
    if metadata.get("has_timestamp", False):
        metadata_score += 30
    if metadata.get("has_device_info", False) or metadata.get("has_exif", False):
        metadata_score += 20
    scores["metadata"] = metadata_score
    
    # Integrity score (from existing analysis if available)
    if integrity_score is not None:
        scores["integrity"] = integrity_score
    else:
        scores["integrity"] = 70  # Default if no integrity analysis
    
    # Weighted average
    total_weight = sum(WEIGHTS.values())
    weighted_sum = sum(scores.get(k, 70) * w for k, w in WEIGHTS.items())
    viability = int(weighted_sum / total_weight)
    
    return max(0, min(100, viability))


# =============================================================================
# LIMITATIONS ENGINE
# =============================================================================

def generate_limitations(
    metrics: Dict[str, Any],
    integrity_warnings: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Generate structured limitation statements based on metrics.
    
    Returns a list of limitations sorted by severity then code.
    """
    limitations = []
    
    if not metrics.get("readable", False):
        limitations.append({
            "code": "FILE_UNREADABLE",
            **LIMITATION_TEMPLATES["FILE_UNREADABLE"],
            "severity": "critical"
        })
        return limitations
    
    evidence_type = metrics.get("type", "unknown")
    
    # Resolution limitations
    resolution = metrics.get("resolution", {})
    if not resolution.get("meets_threshold", True):
        width = resolution.get("width", 0)
        height = resolution.get("height", 0)
        template = LIMITATION_TEMPLATES["LOW_RESOLUTION"]
        limitations.append({
            "code": "LOW_RESOLUTION",
            "what": template["what"],
            "why": template["why"].format(
                width=width, height=height,
                min_width=MIN_IMAGE_WIDTH, min_height=MIN_IMAGE_HEIGHT
            ),
            "impact": template["impact"],
            "severity": template["severity"]
        })
    
    # Blur limitations (images only)
    if evidence_type == "image":
        blur = metrics.get("blur", {})
        blur_score = blur.get("score", 0)
        
        if blur_score < BLUR_THRESHOLD_LOW:
            template = LIMITATION_TEMPLATES["HIGH_BLUR"]
            limitations.append({
                "code": "HIGH_BLUR",
                "what": template["what"],
                "why": template["why"].format(blur_score=blur_score, threshold=BLUR_THRESHOLD_LOW),
                "impact": template["impact"],
                "severity": template["severity"]
            })
            # High blur also means no identity attribution
            limitations.append({
                "code": "LOW_FACE_RESOLUTION",
                **LIMITATION_TEMPLATES["LOW_FACE_RESOLUTION"]
            })
        elif blur_score < BLUR_THRESHOLD_HIGH:
            template = LIMITATION_TEMPLATES["MODERATE_BLUR"]
            limitations.append({
                "code": "MODERATE_BLUR",
                "what": template["what"],
                "why": template["why"].format(blur_score=blur_score, threshold=BLUR_THRESHOLD_HIGH),
                "impact": template["impact"],
                "severity": template["severity"]
            })
    
    # Brightness limitations
    brightness = metrics.get("brightness", {})
    if not brightness.get("adequate", True):
        mean = brightness.get("mean", 128)
        if mean < BRIGHTNESS_MIN:
            template = LIMITATION_TEMPLATES["LOW_BRIGHTNESS"]
            limitations.append({
                "code": "LOW_BRIGHTNESS",
                "what": template["what"],
                "why": template["why"].format(brightness=mean, threshold=BRIGHTNESS_MIN),
                "impact": template["impact"],
                "severity": template["severity"]
            })
        elif mean > BRIGHTNESS_MAX:
            template = LIMITATION_TEMPLATES["HIGH_BRIGHTNESS"]
            limitations.append({
                "code": "HIGH_BRIGHTNESS",
                "what": template["what"],
                "why": template["why"].format(brightness=mean, threshold=BRIGHTNESS_MAX),
                "impact": template["impact"],
                "severity": template["severity"]
            })
    
    # Compression limitations
    compression = metrics.get("compression", {})
    if not compression.get("acceptable", True):
        ratio = compression.get("ratio", 0)
        template = LIMITATION_TEMPLATES["HIGH_COMPRESSION"]
        limitations.append({
            "code": "HIGH_COMPRESSION",
            "what": template["what"],
            "why": template["why"].format(ratio=ratio),
            "impact": template["impact"],
            "severity": template["severity"]
        })
    
    # Metadata limitations
    metadata = metrics.get("metadata", {})
    if not metadata.get("has_timestamp", False):
        limitations.append({
            "code": "MISSING_METADATA_TIMESTAMPS",
            **LIMITATION_TEMPLATES["MISSING_METADATA_TIMESTAMPS"]
        })
    if not metadata.get("has_device_info", True) and not metadata.get("has_exif", True):
        limitations.append({
            "code": "MISSING_METADATA_DEVICE",
            **LIMITATION_TEMPLATES["MISSING_METADATA_DEVICE"]
        })
    
    # Video-specific limitations
    if evidence_type == "video":
        bitrate = metrics.get("bitrate", {})
        if not bitrate.get("adequate", True):
            template = LIMITATION_TEMPLATES["LOW_VIDEO_BITRATE"]
            limitations.append({
                "code": "LOW_VIDEO_BITRATE",
                "what": template["what"],
                "why": template["why"].format(
                    bitrate=bitrate.get("value_kbps", 0),
                    threshold=MIN_VIDEO_BITRATE / 1000
                ),
                "impact": template["impact"],
                "severity": template["severity"]
            })
        
        frames = metrics.get("frames", {})
        if not frames.get("adequate", True):
            template = LIMITATION_TEMPLATES["LOW_VIDEO_FRAMES"]
            limitations.append({
                "code": "LOW_VIDEO_FRAMES",
                "what": template["what"],
                "why": template["why"].format(
                    frames=frames.get("count", 0),
                    threshold=MIN_VIDEO_FRAMES
                ),
                "impact": template["impact"],
                "severity": template["severity"]
            })
    
    # Audio limitations
    audio = metrics.get("audio", {}) if evidence_type == "video" else metrics.get("snr", {})
    if evidence_type == "audio" or (evidence_type == "video" and metrics.get("audio", {}).get("present", False)):
        snr_adequate = audio.get("snr_adequate", True) if evidence_type == "video" else audio.get("adequate", True)
        if not snr_adequate:
            snr_val = audio.get("snr_estimate", 0) if evidence_type == "video" else audio.get("estimate", 0)
            template = LIMITATION_TEMPLATES["LOW_SNR"]
            limitations.append({
                "code": "LOW_SNR",
                "what": template["what"],
                "why": template["why"].format(snr=snr_val or 0, threshold=MIN_SNR_DB),
                "impact": template["impact"],
                "severity": template["severity"]
            })
    
    # Speech confidence limitations (audio only)
    if evidence_type == "audio":
        speech = metrics.get("speech", {})
        if not speech.get("detected", True):
            template = LIMITATION_TEMPLATES["LOW_SPEECH_CONFIDENCE"]
            limitations.append({
                "code": "LOW_SPEECH_CONFIDENCE",
                "what": template["what"],
                "why": template["why"].format(
                    confidence=speech.get("confidence", 0),
                    threshold=MIN_SPEECH_CONFIDENCE
                ),
                "impact": template["impact"],
                "severity": template["severity"]
            })
    
    # Integrity warnings
    if integrity_warnings:
        template = LIMITATION_TEMPLATES["INTEGRITY_WARNINGS"]
        limitations.append({
            "code": "INTEGRITY_WARNINGS",
            "what": template["what"],
            "why": template["why"].format(warning_summary="; ".join(integrity_warnings[:3])),
            "impact": template["impact"],
            "severity": template["severity"]
        })
    
    # Sort by severity (critical > high > medium > low) then by code
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    limitations.sort(key=lambda x: (severity_order.get(x["severity"], 4), x["code"]))
    
    return limitations


# =============================================================================
# SUITABILITY TAGS
# =============================================================================

def compute_suitability_tags(
    metrics: Dict[str, Any],
    viability_score: int,
    limitations: List[Dict[str, Any]]
) -> Dict[str, str]:
    """Compute suitability tags based on metrics and limitations."""
    
    limitation_codes = {lim["code"] for lim in limitations}
    
    # Identity Attribution Suitability
    identity_blocked = (
        viability_score < GRADE_C_MIN or
        "LOW_FACE_RESOLUTION" in limitation_codes or
        "HIGH_BLUR" in limitation_codes or
        "FILE_UNREADABLE" in limitation_codes
    )
    identity_suitability = IdentitySuitability.NOT_ALLOWED.value if identity_blocked else IdentitySuitability.ALLOWED.value
    
    # Manipulation Detection Suitability
    if viability_score >= GRADE_A_MIN and "HIGH_COMPRESSION" not in limitation_codes:
        manipulation_suitability = SuitabilityLevel.STRONG.value
    elif viability_score >= GRADE_B_MIN:
        manipulation_suitability = SuitabilityLevel.MODERATE.value
    else:
        manipulation_suitability = SuitabilityLevel.LIMITED.value
    
    # Timeline/Context Suitability
    if "MISSING_METADATA_TIMESTAMPS" in limitation_codes:
        timeline_suitability = SuitabilityLevel.LIMITED.value
    elif viability_score >= GRADE_B_MIN:
        timeline_suitability = SuitabilityLevel.STRONG.value
    else:
        timeline_suitability = SuitabilityLevel.MODERATE.value
    
    # Audio Content Suitability
    evidence_type = metrics.get("type", "unknown")
    if evidence_type == "audio" or (evidence_type == "video" and metrics.get("audio", {}).get("present", False)):
        if "LOW_SNR" in limitation_codes:
            audio_suitability = SuitabilityLevel.NOT_RELIABLE.value
        elif "LOW_SPEECH_CONFIDENCE" in limitation_codes:
            audio_suitability = SuitabilityLevel.LIMITED.value
        elif viability_score >= GRADE_B_MIN:
            audio_suitability = SuitabilityLevel.STRONG.value
        else:
            audio_suitability = SuitabilityLevel.MODERATE.value
    else:
        audio_suitability = "n/a"
    
    return {
        "identity_attribution": identity_suitability,
        "manipulation_detection": manipulation_suitability,
        "timeline_context": timeline_suitability,
        "audio_content": audio_suitability
    }


# =============================================================================
# ADMISSIBILITY GRADE DERIVATION
# =============================================================================

def derive_admissibility_grade(
    viability_score: int,
    limitations: List[Dict[str, Any]],
    integrity_score: Optional[float] = None
) -> str:
    """Derive admissibility grade (A/B/C/D) from viability score and limitations.
    
    Grade is NOT a legal decision - it's a technical reliability grade.
    """
    # Check for critical limitations
    critical_limitations = [lim for lim in limitations if lim.get("severity") == "critical"]
    if critical_limitations:
        return AdmissibilityGrade.D.value
    
    # Check for high-severity limitations
    high_limitations = [lim for lim in limitations if lim.get("severity") == "high"]
    
    # Factor in integrity score if available
    adjusted_score = viability_score
    if integrity_score is not None:
        # Blend viability and integrity (70/30 weight)
        adjusted_score = int(viability_score * 0.7 + integrity_score * 0.3)
    
    # Determine grade
    if adjusted_score >= GRADE_A_MIN and len(high_limitations) == 0:
        return AdmissibilityGrade.A.value
    elif adjusted_score >= GRADE_B_MIN and len(high_limitations) <= 1:
        return AdmissibilityGrade.B.value
    elif adjusted_score >= GRADE_C_MIN:
        return AdmissibilityGrade.C.value
    else:
        return AdmissibilityGrade.D.value


# =============================================================================
# MAIN COMPUTATION FUNCTION
# =============================================================================

def compute_admissibility(
    db: Session,
    evidence: Evidence,
    user_id: Optional[int] = None
) -> Tuple[EvidenceQualityMetrics, EvidenceAdmissibility]:
    """Main entry point: compute and store admissibility data for evidence.
    
    This is the single deterministic entry point for admissibility computation.
    Both API endpoints and report generation should call this function.
    
    Returns tuple of (EvidenceQualityMetrics, EvidenceAdmissibility).
    """
    # Check if already computed
    existing_metrics = db.query(EvidenceQualityMetrics).filter(
        EvidenceQualityMetrics.evidence_id == evidence.id
    ).first()
    
    existing_admissibility = db.query(EvidenceAdmissibility).filter(
        EvidenceAdmissibility.evidence_id == evidence.id
    ).first()
    
    if existing_metrics and existing_admissibility:
        return existing_metrics, existing_admissibility
    
    # Compute quality metrics
    metrics = compute_quality_metrics(evidence)
    
    # Get integrity analysis results if available
    integrity_result = db.query(AnalysisResult).filter(
        AnalysisResult.evidence_id == evidence.id,
        AnalysisResult.analysis_type == AnalysisType.INTEGRITY_CHECK
    ).first()
    
    integrity_score = None
    integrity_warnings = None
    if integrity_result:
        integrity_score = integrity_result.confidence_score
        if integrity_result.warnings:
            integrity_warnings = [w.get("message", str(w)) if isinstance(w, dict) else str(w) 
                                 for w in integrity_result.warnings]
    
    # Compute viability score
    viability_score = compute_viability_score(metrics, integrity_score)
    
    # Generate limitations
    limitations = generate_limitations(metrics, integrity_warnings)
    
    # Compute suitability tags
    suitability = compute_suitability_tags(metrics, viability_score, limitations)
    
    # Derive admissibility grade
    grade = derive_admissibility_grade(viability_score, limitations, integrity_score)
    
    # Create or update EvidenceQualityMetrics
    if existing_metrics:
        existing_metrics.metrics_json = metrics
        existing_metrics.viability_score = viability_score
        existing_metrics.thresholds_version = THRESHOLDS_VERSION
        existing_metrics.computed_at = datetime.utcnow()
        existing_metrics.computed_by = user_id
        quality_metrics = existing_metrics
    else:
        quality_metrics = EvidenceQualityMetrics(
            evidence_id=evidence.id,
            metrics_json=metrics,
            viability_score=viability_score,
            thresholds_version=THRESHOLDS_VERSION,
            computed_by=user_id
        )
        db.add(quality_metrics)
    
    # Create or update EvidenceAdmissibility
    if existing_admissibility:
        existing_admissibility.grade = grade
        existing_admissibility.suitability_json = suitability
        existing_admissibility.limitations_json = limitations
        existing_admissibility.thresholds_version = THRESHOLDS_VERSION
        existing_admissibility.computed_at = datetime.utcnow()
        existing_admissibility.computed_by = user_id
        admissibility = existing_admissibility
    else:
        admissibility = EvidenceAdmissibility(
            evidence_id=evidence.id,
            grade=grade,
            suitability_json=suitability,
            limitations_json=limitations,
            thresholds_version=THRESHOLDS_VERSION,
            computed_by=user_id
        )
        db.add(admissibility)
    
    # Create audit log
    audit_log = AuditLog(
        user_id=user_id,
        action=AuditAction.EVIDENCE_ADMISSIBILITY_COMPUTED,
        resource_type="evidence",
        resource_id=evidence.id,
        resource_uuid=evidence.uuid,
        details={
            "viability_score": viability_score,
            "grade": grade,
            "suitability": suitability,
            "limitations_count": len(limitations),
            "thresholds_version": THRESHOLDS_VERSION
        },
        success=1
    )
    db.add(audit_log)
    
    db.commit()
    db.refresh(quality_metrics)
    db.refresh(admissibility)
    
    return quality_metrics, admissibility


def get_admissibility(
    db: Session,
    evidence_id: int
) -> Optional[Tuple[EvidenceQualityMetrics, EvidenceAdmissibility]]:
    """Retrieve stored admissibility data for evidence.
    
    Returns None if not computed yet.
    """
    metrics = db.query(EvidenceQualityMetrics).filter(
        EvidenceQualityMetrics.evidence_id == evidence_id
    ).first()
    
    admissibility = db.query(EvidenceAdmissibility).filter(
        EvidenceAdmissibility.evidence_id == evidence_id
    ).first()
    
    if metrics and admissibility:
        return metrics, admissibility
    return None
