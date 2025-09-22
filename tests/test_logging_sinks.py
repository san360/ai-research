"""
Unit tests for logging sinks.

Tests for MultiSink writing to all sinks, FileSink appending, 
and UISink appending to an in-memory buffer.
"""

import os
import tempfile
import pytest
from deep_research_ui.utils.logging_sinks import (
    ConsoleSink,
    FileSink,
    UISink,
    MultiSink
)


class TestConsoleSink:
    """Test cases for ConsoleSink."""
    
    def test_console_sink_write(self, capsys):
        """Test that ConsoleSink writes to stdout without newline."""
        sink = ConsoleSink()
        sink.write("test message")
        
        captured = capsys.readouterr()
        assert captured.out == "test message"
        assert captured.err == ""
    
    def test_console_sink_flush(self):
        """Test that ConsoleSink flush method works."""
        sink = ConsoleSink()
        # Should not raise any exceptions
        sink.flush()


class TestFileSink:
    """Test cases for FileSink."""
    
    def test_file_sink_write_new_file(self):
        """Test writing to a new file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.txt")
            sink = FileSink(file_path)
            
            sink.write("test message\n")
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            assert content == "test message\n"
    
    def test_file_sink_append_existing_file(self):
        """Test appending to an existing file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.txt")
            
            # Create initial file content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("initial content\n")
            
            sink = FileSink(file_path)
            sink.write("appended content\n")
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            assert content == "initial content\nappended content\n"
    
    def test_file_sink_multiple_writes(self):
        """Test multiple writes to the same file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.txt")
            sink = FileSink(file_path)
            
            sink.write("line 1\n")
            sink.write("line 2\n")
            sink.write("line 3\n")
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            assert content == "line 1\nline 2\nline 3\n"
    
    def test_file_sink_creates_directory(self):
        """Test that FileSink creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = os.path.join(temp_dir, "nested", "dirs", "test.txt")
            sink = FileSink(nested_path)
            
            sink.write("test content\n")
            
            assert os.path.exists(nested_path)
            with open(nested_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert content == "test content\n"
    
    def test_file_sink_flush(self):
        """Test that FileSink flush method works."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.txt")
            sink = FileSink(file_path)
            
            # Should not raise any exceptions
            sink.flush()


class TestUISink:
    """Test cases for UISink."""
    
    def test_ui_sink_write_to_buffer(self):
        """Test writing to UI buffer."""
        buffer = []
        sink = UISink(buffer)
        
        sink.write("message 1")
        sink.write("message 2")
        
        assert buffer == ["message 1", "message 2"]
    
    def test_ui_sink_shared_buffer(self):
        """Test that multiple UISinks can share the same buffer."""
        buffer = []
        sink1 = UISink(buffer)
        sink2 = UISink(buffer)
        
        sink1.write("from sink 1")
        sink2.write("from sink 2")
        
        assert buffer == ["from sink 1", "from sink 2"]
    
    def test_ui_sink_existing_buffer_content(self):
        """Test UI sink with pre-existing buffer content."""
        buffer = ["existing content"]
        sink = UISink(buffer)
        
        sink.write("new content")
        
        assert buffer == ["existing content", "new content"]
    
    def test_ui_sink_flush(self):
        """Test that UISink flush method works."""
        buffer = []
        sink = UISink(buffer)
        
        # Should not raise any exceptions
        sink.flush()


class TestMultiSink:
    """Test cases for MultiSink."""
    
    def test_multi_sink_write_to_all_sinks(self):
        """Test that MultiSink writes to all configured sinks."""
        buffer1 = []
        buffer2 = []
        
        sink1 = UISink(buffer1)
        sink2 = UISink(buffer2)
        multi_sink = MultiSink([sink1, sink2])
        
        multi_sink.write("test message")
        
        assert buffer1 == ["test message"]
        assert buffer2 == ["test message"]
    
    def test_multi_sink_with_different_sink_types(self, capsys):
        """Test MultiSink with different types of sinks."""
        buffer = []
        ui_sink = UISink(buffer)
        console_sink = ConsoleSink()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.txt")
            file_sink = FileSink(file_path)
            
            multi_sink = MultiSink([ui_sink, console_sink, file_sink])
            multi_sink.write("test message")
            
            # Check UI sink
            assert buffer == ["test message"]
            
            # Check console sink
            captured = capsys.readouterr()
            assert captured.out == "test message"
            
            # Check file sink
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert content == "test message"
    
    def test_multi_sink_flush_all_sinks(self):
        """Test that MultiSink flushes all configured sinks."""
        buffer1 = []
        buffer2 = []
        
        sink1 = UISink(buffer1)
        sink2 = UISink(buffer2)
        multi_sink = MultiSink([sink1, sink2])
        
        # Should not raise any exceptions
        multi_sink.flush()
    
    def test_multi_sink_add_sink(self):
        """Test adding a sink to MultiSink."""
        buffer1 = []
        buffer2 = []
        
        sink1 = UISink(buffer1)
        sink2 = UISink(buffer2)
        multi_sink = MultiSink([sink1])
        
        multi_sink.write("before add")
        assert buffer1 == ["before add"]
        assert buffer2 == []
        
        multi_sink.add_sink(sink2)
        multi_sink.write("after add")
        
        assert buffer1 == ["before add", "after add"]
        assert buffer2 == ["after add"]
    
    def test_multi_sink_remove_sink(self):
        """Test removing a sink from MultiSink."""
        buffer1 = []
        buffer2 = []
        
        sink1 = UISink(buffer1)
        sink2 = UISink(buffer2)
        multi_sink = MultiSink([sink1, sink2])
        
        multi_sink.write("before remove")
        assert buffer1 == ["before remove"]
        assert buffer2 == ["before remove"]
        
        multi_sink.remove_sink(sink2)
        multi_sink.write("after remove")
        
        assert buffer1 == ["before remove", "after remove"]
        assert buffer2 == ["before remove"]  # No new content
    
    def test_multi_sink_remove_nonexistent_sink(self):
        """Test removing a sink that wasn't added to MultiSink."""
        buffer1 = []
        buffer2 = []
        
        sink1 = UISink(buffer1)
        sink2 = UISink(buffer2)
        multi_sink = MultiSink([sink1])
        
        # Should not raise any exceptions
        multi_sink.remove_sink(sink2)
        
        multi_sink.write("test")
        assert buffer1 == ["test"]
        assert buffer2 == []
    
    def test_multi_sink_empty_sinks_list(self):
        """Test MultiSink with empty sinks list."""
        multi_sink = MultiSink([])
        
        # Should not raise any exceptions
        multi_sink.write("test message")
        multi_sink.flush()
    
    def test_multi_sink_iterable_constructor(self):
        """Test MultiSink constructor with different iterable types."""
        buffer1 = []
        buffer2 = []
        
        sink1 = UISink(buffer1)
        sink2 = UISink(buffer2)
        
        # Test with tuple
        multi_sink = MultiSink((sink1, sink2))
        multi_sink.write("test")
        
        assert buffer1 == ["test"]
        assert buffer2 == ["test"]


if __name__ == "__main__":
    pytest.main([__file__])