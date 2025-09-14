import os
import json
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import aiofiles

logger = logging.getLogger(__name__)

class DocumentLoader:
    """Utility for loading documents from various sources"""
    
    @staticmethod
    async def load_from_directory(directory_path: str, file_extensions: List[str] = None) -> List[Dict[str, Any]]:
        """Load documents from a directory"""
        if file_extensions is None:
            file_extensions = ['.txt', '.md', '.pdf', '.docx']
        
        documents = []
        directory = Path(directory_path)
        
        if not directory.exists():
            logger.error(f"Directory does not exist: {directory_path}")
            return documents
        
        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in file_extensions:
                try:
                    doc = await DocumentLoader._load_single_file(file_path)
                    if doc:
                        documents.append(doc)
                except Exception as e:
                    logger.error(f"Error loading file {file_path}: {e}")
        
        logger.info(f"Loaded {len(documents)} documents from {directory_path}")
        return documents
    
    @staticmethod
    async def _load_single_file(file_path: Path) -> Optional[Dict[str, Any]]:
        """Load a single file"""
        try:
            if file_path.suffix.lower() == '.txt':
                return await DocumentLoader._load_text_file(file_path)
            elif file_path.suffix.lower() == '.md':
                return await DocumentLoader._load_markdown_file(file_path)
            elif file_path.suffix.lower() == '.json':
                return await DocumentLoader._load_json_file(file_path)
            else:
                logger.warning(f"Unsupported file type: {file_path.suffix}")
                return None
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None
    
    @staticmethod
    async def _load_text_file(file_path: Path) -> Dict[str, Any]:
        """Load a text file"""
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        return {
            "id": str(file_path),
            "title": file_path.stem,
            "content": content,
            "metadata": {
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size,
                "file_type": "text"
            }
        }
    
    @staticmethod
    async def _load_markdown_file(file_path: Path) -> Dict[str, Any]:
        """Load a markdown file"""
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        # Extract title from first header or filename
        title = file_path.stem
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break
        
        return {
            "id": str(file_path),
            "title": title,
            "content": content,
            "metadata": {
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size,
                "file_type": "markdown"
            }
        }
    
    @staticmethod
    async def _load_json_file(file_path: Path) -> Dict[str, Any]:
        """Load a JSON file"""
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            data = json.loads(await f.read())
        
        # Handle different JSON structures
        if isinstance(data, dict):
            if 'content' in data:
                return {
                    "id": data.get('id', str(file_path)),
                    "title": data.get('title', file_path.stem),
                    "content": data['content'],
                    "metadata": data.get('metadata', {})
                }
            else:
                # Convert dict to content
                content = json.dumps(data, indent=2)
                return {
                    "id": str(file_path),
                    "title": file_path.stem,
                    "content": content,
                    "metadata": {"file_type": "json"}
                }
        
        return None
