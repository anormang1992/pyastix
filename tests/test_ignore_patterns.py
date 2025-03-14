"""
Tests for the .pyastixignore functionality.
"""

import os
import sys
import pytest
from pathlib import Path
import tempfile

# Ensure pyastix module is in the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyastix.core.parser import IgnorePattern, IgnorePatternList


class TestIgnorePattern:
    """Test cases for the IgnorePattern class."""
    
    def test_simple_filename(self):
        pattern = IgnorePattern("file.py")
        assert pattern.matches("file.py")
        assert not pattern.matches("other.py")
        assert pattern.matches("dir/file.py")
        assert not pattern.matches("file.py.bak")
    
    def test_directory_pattern(self):
        pattern = IgnorePattern("dir/")
        assert pattern.matches("dir")
        assert pattern.matches("dir/")
        assert pattern.matches("dir/file.py")
        assert pattern.matches("dir/subdir/file.py")
        assert not pattern.matches("other/file.py")
    
    def test_wildcard_patterns(self):
        pattern = IgnorePattern("*.py")
        assert pattern.matches("file.py")
        assert pattern.matches("dir/file.py")
        assert not pattern.matches("file.txt")
    
    def test_double_wildcard(self):
        pattern = IgnorePattern("**/logs/**")
        assert pattern.matches("logs/file.log")
        assert pattern.matches("dir/logs/file.log")
        assert pattern.matches("dir/logs/subdir/file.log")
        assert not pattern.matches("dir/file.log")
    
    def test_question_mark(self):
        pattern = IgnorePattern("file?.py")
        assert pattern.matches("file1.py")
        assert pattern.matches("fileA.py")
        assert not pattern.matches("file.py")
        assert not pattern.matches("file12.py")
    
    def test_rooted_pattern(self):
        pattern = IgnorePattern("/node_modules")
        assert pattern.matches("node_modules")
        assert pattern.matches("node_modules/file.js")
        assert not pattern.matches("dir/node_modules")
    
    def test_negated_pattern(self):
        pattern = IgnorePattern("!important.py")
        assert pattern.is_negated
        assert pattern.matches("important.py")
        assert not pattern.matches("unimportant.py")


class TestIgnorePatternList:
    """Test cases for the IgnorePatternList class with temporary files."""
    
    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tempdir:
            project_dir = Path(tempdir)
            
            # Create .pyastixignore file
            ignore_file = project_dir / ".pyastixignore"
            with open(ignore_file, "w") as f:
                f.write("# Test ignore file\n")
                f.write("*.log\n")
                f.write("temp/\n")
                f.write("**/__pycache__/**\n")
                f.write("!important.log\n")
            
            # Create some test files and directories
            (project_dir / "file.py").touch()
            (project_dir / "file.log").touch()
            (project_dir / "important.log").touch()
            (project_dir / "temp").mkdir()
            (project_dir / "temp" / "file.py").touch()
            (project_dir / "src").mkdir()
            (project_dir / "src" / "module.py").touch()
            (project_dir / "src" / "__pycache__").mkdir()
            (project_dir / "src" / "__pycache__" / "module.cpython-38.pyc").touch()
            
            yield project_dir
    
    def test_ignore_patterns_list(self, temp_project):
        ignore_list = IgnorePatternList(temp_project)
        
        # Should be ignored
        assert ignore_list.should_ignore(temp_project / "file.log")
        assert ignore_list.should_ignore(temp_project / "temp")
        assert ignore_list.should_ignore(temp_project / "temp" / "file.py")
        assert ignore_list.should_ignore(temp_project / "src" / "__pycache__" / "module.cpython-38.pyc")
        
        # Should not be ignored
        assert not ignore_list.should_ignore(temp_project / "file.py")
        assert not ignore_list.should_ignore(temp_project / "important.log")  # Negated pattern
        assert not ignore_list.should_ignore(temp_project / "src")
        assert not ignore_list.should_ignore(temp_project / "src" / "module.py")


if __name__ == "__main__":
    pytest.main(["-v", __file__]) 