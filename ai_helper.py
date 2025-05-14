#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI Helper for Telegram File Storage Bot
Provides AI-powered file analysis, tagging, categorization, and recommendations
"""

import os
import json
import logging
import base64
import mimetypes
import datetime
from openai import OpenAI

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
client = OpenAI(api_key=OPENAI_API_KEY)

# Constants
DEFAULT_CATEGORIES = [
    "Documents", "Images", "Videos", "Audio", "Archives", 
    "Presentations", "Spreadsheets", "Code", "Books", "Other"
]

DEFAULT_TAGS = [
    "work", "personal", "important", "draft", "final", 
    "project", "backup", "reference", "tutorial", "template"
]

# File metadata storage
METADATA_DIR = "data"
FILE_METADATA = os.path.join(METADATA_DIR, "file_metadata.json")
USER_PREFERENCES = os.path.join(METADATA_DIR, "user_preferences.json")

# In-memory databases
file_metadata = {}  # file_id: metadata
user_preferences = {}  # user_id: preferences

def ensure_metadata_directory():
    """Ensure the metadata directory exists"""
    os.makedirs(METADATA_DIR, exist_ok=True)

def load_file_metadata():
    """Load file metadata from JSON file"""
    global file_metadata
    try:
        if os.path.exists(FILE_METADATA):
            with open(FILE_METADATA, 'r') as f:
                file_metadata = json.load(f)
                logger.info(f"Loaded metadata for {len(file_metadata)} files")
    except Exception as e:
        logger.error(f"Error loading file metadata: {e}")

def load_user_preferences():
    """Load user preferences from JSON file"""
    global user_preferences
    try:
        if os.path.exists(USER_PREFERENCES):
            with open(USER_PREFERENCES, 'r') as f:
                user_preferences = json.load(f)
                logger.info(f"Loaded preferences for {len(user_preferences)} users")
    except Exception as e:
        logger.error(f"Error loading user preferences: {e}")

def save_file_metadata():
    """Save file metadata to JSON file"""
    try:
        ensure_metadata_directory()
        with open(FILE_METADATA, 'w') as f:
            json.dump(file_metadata, f, indent=2)
        logger.debug(f"Saved metadata for {len(file_metadata)} files")
    except Exception as e:
        logger.error(f"Error saving file metadata: {e}")

def save_user_preferences():
    """Save user preferences to JSON file"""
    try:
        ensure_metadata_directory()
        with open(USER_PREFERENCES, 'w') as f:
            json.dump(user_preferences, f, indent=2)
        logger.debug(f"Saved preferences for {len(user_preferences)} users")
    except Exception as e:
        logger.error(f"Error saving user preferences: {e}")

def load_data():
    """Load all AI data from storage"""
    ensure_metadata_directory()
    load_file_metadata()
    load_user_preferences()

def save_all_data():
    """Save all AI data to storage"""
    save_file_metadata()
    save_user_preferences()

def analyze_file_name(file_name, file_type):
    """
    Analyze the file name and type to extract initial metadata
    without using OpenAI API
    """
    try:
        # Get file extension
        extension = ""
        if "." in file_name:
            extension = file_name.split(".")[-1].lower()

        # Initial category based on file type and extension
        category = "Other"
        if file_type == "photo":
            category = "Images"
        elif file_type == "video":
            category = "Videos"
        elif file_type == "audio":
            category = "Audio"
        elif file_type == "document":
            if extension in ["pdf", "doc", "docx", "txt", "rtf"]:
                category = "Documents"
            elif extension in ["jpg", "jpeg", "png", "gif", "bmp", "svg", "webp"]:
                category = "Images"
            elif extension in ["mp4", "avi", "mov", "wmv", "flv", "mkv", "webm"]:
                category = "Videos"
            elif extension in ["mp3", "wav", "ogg", "aac", "flac", "m4a"]:
                category = "Audio"
            elif extension in ["zip", "rar", "tar", "gz", "7z"]:
                category = "Archives"
            elif extension in ["ppt", "pptx"]:
                category = "Presentations"
            elif extension in ["xls", "xlsx", "csv"]:
                category = "Spreadsheets"
            elif extension in ["py", "js", "html", "css", "java", "cpp", "c", "php", "go", "rb"]:
                category = "Code"
            elif extension in ["epub", "mobi", "azw", "azw3", "fb2"]:
                category = "Books"

        # Generate basic metadata
        metadata = {
            "category": category,
            "extension": extension,
            "tags": [],
            "ai_analyzed": False,
            "last_accessed": None,
            "access_count": 0,
            "created_at": datetime.datetime.now().isoformat()
        }

        return metadata
    except Exception as e:
        logger.error(f"Error analyzing file name: {e}")
        return {
            "category": "Other",
            "extension": "",
            "tags": [],
            "ai_analyzed": False,
            "last_accessed": None,
            "access_count": 0,
            "created_at": datetime.datetime.now().isoformat()
        }

def analyze_file_with_ai(file_info, file_content=None):
    """
    Analyze file using OpenAI API to extract metadata, categorize, and tag
    If file_content is provided, content-based analysis will be performed
    Otherwise, only name-based analysis will be done
    """
    try:
        if not OPENAI_API_KEY:
            logger.warning("No OpenAI API key available for AI analysis")
            return analyze_file_name(file_info.get("name", ""), file_info.get("type", "document"))
        
        # Get basic info from file
        file_name = file_info.get("name", "")
        file_type = file_info.get("type", "document")
        file_size = file_info.get("size", 0)
        
        # Prepare the prompt for OpenAI
        content_description = ""
        if file_content:
            # If we have file content to analyze
            if isinstance(file_content, str) and len(file_content) > 500:
                # For text content, truncate if too long
                content_description = f"File content excerpt: {file_content[:500]}..."
            elif isinstance(file_content, str):
                content_description = f"File content: {file_content}"
            else:
                # For binary content, just mention we have it
                content_description = "Binary file content is available for analysis."
        else:
            content_description = "No file content available for analysis."
            
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": 
                 "You are an AI file analyzer that processes file metadata to categorize and tag files."
                 "Based on the file name, type, and any available content, determine:"
                 "1. The most appropriate category from this list: Documents, Images, Videos, Audio, Archives, Presentations, Spreadsheets, Code, Books, Other"
                 "2. A list of relevant tags (5 maximum)"
                 "3. A short description of what the file likely contains"
                 "Respond with JSON format only."
                },
                {"role": "user", "content": 
                 f"Analyze this file:\n"
                 f"Filename: {file_name}\n"
                 f"File type: {file_type}\n"
                 f"File size: {file_size} bytes\n"
                 f"{content_description}"
                }
            ],
            response_format={"type": "json_object"}
        )
        
        # Process the response
        result = json.loads(response.choices[0].message.content)
        
        # Create metadata
        metadata = {
            "category": result.get("category", "Other"),
            "tags": result.get("tags", [])[:5],  # Limit to 5 tags
            "description": result.get("description", ""),
            "extension": file_name.split(".")[-1].lower() if "." in file_name else "",
            "ai_analyzed": True,
            "last_accessed": None,
            "access_count": 0,
            "created_at": datetime.datetime.now().isoformat()
        }
        
        return metadata
    except Exception as e:
        logger.error(f"Error in AI analysis: {e}")
        # Fall back to basic analysis
        return analyze_file_name(file_info.get("name", ""), file_info.get("type", "document"))

def track_file_access(file_id):
    """Track file access for better recommendations"""
    if file_id in file_metadata:
        metadata = file_metadata[file_id]
        metadata["last_accessed"] = datetime.datetime.now().isoformat()
        metadata["access_count"] = metadata.get("access_count", 0) + 1
        file_metadata[file_id] = metadata
        save_file_metadata()

def update_user_preferences(user_id, file_id=None, category=None, tags=None, explicit_preference=None):
    """
    Update user preferences based on interactions
    - file_id: when user accesses a file
    - category/tags: when user shows interest in specific categories/tags
    - explicit_preference: when user explicitly sets preferences
    """
    if str(user_id) not in user_preferences:
        user_preferences[str(user_id)] = {
            "favorite_categories": {},
            "favorite_tags": {},
            "recently_accessed": [],
            "explicit_preferences": {}
        }
    
    user_prefs = user_preferences[str(user_id)]
    
    # Update based on file access
    if file_id and file_id in file_metadata:
        # Add to recently accessed
        recent = user_prefs.get("recently_accessed", [])
        if file_id in recent:
            recent.remove(file_id)
        recent.insert(0, file_id)
        user_prefs["recently_accessed"] = recent[:10]  # Keep only 10 most recent
        
        # Update category and tag preferences
        metadata = file_metadata[file_id]
        category = metadata.get("category")
        if category:
            user_prefs["favorite_categories"][category] = user_prefs["favorite_categories"].get(category, 0) + 1
        
        for tag in metadata.get("tags", []):
            user_prefs["favorite_tags"][tag] = user_prefs["favorite_tags"].get(tag, 0) + 1
    
    # Update based on explicit category/tag interest
    if category:
        user_prefs["favorite_categories"][category] = user_prefs["favorite_categories"].get(category, 0) + 3
    
    if tags:
        for tag in tags:
            user_prefs["favorite_tags"][tag] = user_prefs["favorite_tags"].get(tag, 0) + 3
    
    # Update explicit preferences
    if explicit_preference:
        user_prefs["explicit_preferences"].update(explicit_preference)
    
    # Save changes
    user_preferences[str(user_id)] = user_prefs
    save_user_preferences()

def get_recommendations(user_id, stored_files, count=5):
    """
    Get file recommendations for a user based on preferences and file metadata
    
    Args:
        user_id: The user ID
        stored_files: Dictionary of all stored files
        count: Number of recommendations to return
        
    Returns:
        List of file_ids recommended for the user
    """
    try:
        if str(user_id) not in user_preferences:
            # No preferences yet, return random files
            file_ids = list(stored_files.keys())
            return file_ids[:min(count, len(file_ids))]
        
        user_prefs = user_preferences[str(user_id)]
        fav_categories = user_prefs.get("favorite_categories", {})
        fav_tags = user_prefs.get("favorite_tags", {})
        recent_files = user_prefs.get("recently_accessed", [])
        
        # Calculate scores for each file
        file_scores = {}
        
        for file_id, file_info in stored_files.items():
            # Skip files the user has recently accessed
            if file_id in recent_files:
                continue
                
            score = 0
            
            # Get metadata if available
            meta_id = file_info.get("unique_id", file_id)
            if meta_id in file_metadata:
                metadata = file_metadata[meta_id]
                
                # Score based on category preferences
                category = metadata.get("category")
                if category and category in fav_categories:
                    score += fav_categories[category]
                
                # Score based on tag preferences
                for tag in metadata.get("tags", []):
                    if tag in fav_tags:
                        score += fav_tags[tag]
            
            file_scores[file_id] = score
        
        # Sort files by score (highest first)
        sorted_files = sorted(file_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return top N recommendations
        return [file_id for file_id, _ in sorted_files[:count]]
    
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        # Fallback to returning some random files
        file_ids = list(stored_files.keys())
        return file_ids[:min(count, len(file_ids))]

def get_similar_files(file_id, stored_files, count=3):
    """
    Find files similar to the given file based on metadata
    
    Args:
        file_id: The file ID to find similar files for
        stored_files: Dictionary of all stored files
        count: Number of similar files to return
        
    Returns:
        List of file_ids similar to the given file
    """
    try:
        # Get metadata for the reference file
        meta_id = stored_files.get(file_id, {}).get("unique_id", file_id)
        
        if meta_id not in file_metadata:
            # No metadata, can't find similar files
            return []
        
        ref_metadata = file_metadata[meta_id]
        ref_category = ref_metadata.get("category")
        ref_tags = set(ref_metadata.get("tags", []))
        
        # Calculate similarity scores
        similarity_scores = {}
        
        for f_id, file_info in stored_files.items():
            # Skip the reference file itself
            if f_id == file_id:
                continue
                
            meta_id = file_info.get("unique_id", f_id)
            if meta_id not in file_metadata:
                continue
                
            metadata = file_metadata[meta_id]
            score = 0
            
            # Category match
            if metadata.get("category") == ref_category:
                score += 5
            
            # Tag overlap
            file_tags = set(metadata.get("tags", []))
            common_tags = ref_tags.intersection(file_tags)
            score += len(common_tags) * 2
            
            similarity_scores[f_id] = score
        
        # Sort by similarity score
        sorted_files = sorted(similarity_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return top N similar files
        return [f_id for f_id, _ in sorted_files[:count]]
    
    except Exception as e:
        logger.error(f"Error finding similar files: {e}")
        return []

def organize_files_by_category(stored_files):
    """
    Organize files by category for a better file browsing experience
    
    Args:
        stored_files: Dictionary of all stored files
        
    Returns:
        Dictionary with categories as keys and lists of file_ids as values
    """
    categories = {category: [] for category in DEFAULT_CATEGORIES}
    
    for file_id, file_info in stored_files.items():
        meta_id = file_info.get("unique_id", file_id)
        category = "Other"  # Default category
        
        if meta_id in file_metadata:
            category = file_metadata[meta_id].get("category", "Other")
        
        if category in categories:
            categories[category].append(file_id)
        else:
            categories["Other"].append(file_id)
    
    # Remove empty categories
    categories = {cat: files for cat, files in categories.items() if files}
    
    return categories