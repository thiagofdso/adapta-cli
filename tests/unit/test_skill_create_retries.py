import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from adapta.models import SkillCreateRequest
from adapta.services.skill_service import _run_stage1_for_folder, SkillDocument

@pytest.mark.anyio
async def test_run_stage1_for_folder_respects_max_retries(tmp_path: Path):
    # Setup
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    db_path = tmp_path / "skill-create.db"
    
    doc_path = input_dir / "test.txt"
    doc_path.write_text("content")
    
    doc = SkillDocument(
        source_path=doc_path,
        source_name="test.txt",
        folder_path=input_dir,
        relative_path="test.txt",
        file_type=".txt"
    )
    
    request = SkillCreateRequest(
        input_dir_path=input_dir,
        output_dir_path=output_dir,
        db_path=db_path,
        max_retries=2,
        retry_delay_seconds=0.1
    )
    
    client = MagicMock()
    # Mock _call_skill_prompt to fail twice then succeed
    with patch("adapta.services.skill_service._call_skill_prompt", new_callable=AsyncMock) as mock_prompt:
        mock_prompt.side_effect = [
            httpx.HTTPError("Transient error 1"),
            "{\"skills\": [{\"id\": \"skill1\", \"name\": \"Skill 1\", \"description\": \"Desc\", \"files\": [{\"name\": \"test.txt\", \"contribution\": \"cont\"}]}]}"
        ]
        
        # We need a connection
        import sqlite3
        from adapta.services.skill_service import _initialize_database
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        _initialize_database(connection)
        
        await _run_stage1_for_folder(
            client,
            connection,
            request,
            folder_path=input_dir,
            documents=[doc],
            model_backend="test-backend",
            progress_callback=None
        )
        
        assert mock_prompt.call_count == 2
        connection.close()

@pytest.mark.anyio
async def test_run_stage1_for_folder_fails_after_max_retries(tmp_path: Path):
    # Setup
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    db_path = tmp_path / "skill-create.db"
    
    doc_path = input_dir / "test.txt"
    doc_path.write_text("content")
    
    doc = SkillDocument(
        source_path=doc_path,
        source_name="test.txt",
        folder_path=input_dir,
        relative_path="test.txt",
        file_type=".txt"
    )
    
    request = SkillCreateRequest(
        input_dir_path=input_dir,
        output_dir_path=output_dir,
        db_path=db_path,
        max_retries=2,
        retry_delay_seconds=0.1
    )
    
    client = MagicMock()
    # Mock _call_skill_prompt to always fail
    with patch("adapta.services.skill_service._call_skill_prompt", new_callable=AsyncMock) as mock_prompt:
        mock_prompt.side_effect = httpx.HTTPError("Permanent error")
        
        import sqlite3
        from adapta.services.skill_service import _initialize_database
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        _initialize_database(connection)
        with pytest.raises(httpx.HTTPError):
            await _run_stage1_for_folder(
                client,
                connection,
                request,
                folder_path=input_dir,
                documents=[doc],
                model_backend="test-backend",
                progress_callback=None
            )
        
        assert mock_prompt.call_count == 2
        connection.close()
