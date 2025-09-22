"""
Logging sinks for flexible progress output handling.

This module provides a protocol-based system for writing progress logs to multiple
destinations including console, files, and UI components.
"""

from typing import Protocol, List, Iterable
import os


class ProgressSink(Protocol):
    """Protocol for writing progress logs to various destinations."""
    
    def write(self, line: str) -> None:
        """Write a line of progress output."""
        ...
    
    def flush(self) -> None:
        """Flush any buffered output."""
        ...


class ConsoleSink:
    """Progress sink that writes to console output."""
    
    def write(self, line: str) -> None:
        """Write line to console without adding newline."""
        print(line, end="")
    
    def flush(self) -> None:
        """Flush console output."""
        pass


class FileSink:
    """Progress sink that appends to a file."""
    
    def __init__(self, path: str):
        """
        Initialize file sink.
        
        Args:
            path (str): Path to the file for writing progress logs
        """
        self.path = path
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    
    def write(self, line: str) -> None:
        """Write line to file, appending to existing content."""
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line)
    
    def flush(self) -> None:
        """Flush file output (no-op since we open/close for each write)."""
        pass


class UISink:
    """Progress sink that holds content in a list buffer for UI rendering."""
    
    def __init__(self, buffer: List[str]):
        """
        Initialize UI sink with a reference to a buffer list.
        
        Args:
            buffer (List[str]): List to append progress lines to
        """
        self.buffer = buffer
    
    def write(self, line: str) -> None:
        """Append line to the buffer list."""
        self.buffer.append(line)
    
    def flush(self) -> None:
        """Flush UI output (no-op for list buffer)."""
        pass


class MultiSink:
    """Progress sink that writes to multiple sinks simultaneously."""
    
    def __init__(self, sinks: Iterable[ProgressSink]):
        """
        Initialize multi-sink with multiple destination sinks.
        
        Args:
            sinks (Iterable[ProgressSink]): Collection of sinks to write to
        """
        self.sinks = list(sinks)
    
    def write(self, line: str) -> None:
        """Write line to all configured sinks."""
        for sink in self.sinks:
            sink.write(line)
    
    def flush(self) -> None:
        """Flush all configured sinks."""
        for sink in self.sinks:
            sink.flush()
    
    def add_sink(self, sink: ProgressSink) -> None:
        """
        Add an additional sink to the multi-sink.
        
        Args:
            sink (ProgressSink): Sink to add to the collection
        """
        self.sinks.append(sink)
    
    def remove_sink(self, sink: ProgressSink) -> None:
        """
        Remove a sink from the multi-sink.
        
        Args:
            sink (ProgressSink): Sink to remove from the collection
        """
        if sink in self.sinks:
            self.sinks.remove(sink)