"""
Language compliance checker for concept files.

This module provides functionality for checking concept files for prohibited words
or phrases that may violate legal or compliance requirements.
"""

import os
import json
import glob
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from glow.compliance.prohibited_words import DEFAULT_PROHIBITED_WORDS
from glow.core.logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

class ComplianceIssue:
    """
    Represents a language compliance issue found in a concept file.
    """
    
    def __init__(self, word: str, location: str, context: str):
        """
        Initialize a compliance issue.
        
        Args:
            word: The prohibited word or phrase found.
            location: The location in the concept file where the issue was found.
            context: The context in which the issue was found.
        """
        self.word = word
        self.location = location
        self.context = context
    
    def __str__(self) -> str:
        """
        Return a string representation of the compliance issue.
        """
        return f"Prohibited word '{self.word}' found in {self.location}: {self.context}"


class LanguageChecker:
    """
    Checks concept files for language compliance issues.
    """
    
    def __init__(self, prohibited_words: Optional[List[str]] = None, custom_words_file: Optional[str] = None):
        """
        Initialize the language checker.
        
        Args:
            prohibited_words: Optional list of prohibited words to check for.
            custom_words_file: Optional path to a file containing custom prohibited words.
        """
        self.prohibited_words = prohibited_words or []
        if custom_words_file:
            self.load_custom_words(custom_words_file)
        else:
            self.load_default_words()
        
        logger.info(f"Initialized LanguageChecker with {len(self.prohibited_words)} prohibited words")
    
    def load_default_words(self) -> None:
        """
        Load the default list of prohibited words.
        """
        self.prohibited_words.extend(DEFAULT_PROHIBITED_WORDS)
        logger.info(f"Loaded {len(DEFAULT_PROHIBITED_WORDS)} default prohibited words")
    
    def load_custom_words(self, file_path: str) -> None:
        """
        Load custom prohibited words from a file.
        
        Args:
            file_path: Path to the file containing custom prohibited words.
        """
        try:
            with open(file_path, 'r') as f:
                words = [line.strip() for line in f.readlines() if line.strip()]
                self.prohibited_words.extend(words)
                logger.info(f"Loaded {len(words)} custom prohibited words from {file_path}")
        except Exception as e:
            logger.error(f"Error loading custom prohibited words from {file_path}: {str(e)}")
            raise
    
    def check_text(self, text: str, location: str) -> List[ComplianceIssue]:
        """
        Check a text string for prohibited words.
        
        Args:
            text: The text to check.
            location: The location of the text in the concept file.
            
        Returns:
            List of compliance issues found.
        """
        issues = []
        
        # Convert text to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        for word in self.prohibited_words:
            # Use word boundaries to match whole words only
            pattern = r'\b' + re.escape(word.lower()) + r'\b'
            matches = re.finditer(pattern, text_lower)
            
            for match in matches:
                # Extract context (up to 50 chars before and after the match)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                # Add ellipsis if context is truncated
                if start > 0:
                    context = "..." + context
                if end < len(text):
                    context = context + "..."
                
                issues.append(ComplianceIssue(word, location, context))
        
        return issues
    
    def check_value(self, value: Any, path: str) -> List[ComplianceIssue]:
        """
        Check a value for prohibited words.
        
        Args:
            value: The value to check.
            path: The path to the value in the concept file.
            
        Returns:
            List of compliance issues found.
        """
        issues = []
        
        if isinstance(value, str):
            # Check string values
            issues.extend(self.check_text(value, path))
        elif isinstance(value, dict):
            # Recursively check dictionary values
            for key, val in value.items():
                issues.extend(self.check_value(val, f"{path}.{key}"))
        elif isinstance(value, list):
            # Recursively check list values
            for i, val in enumerate(value):
                issues.extend(self.check_value(val, f"{path}[{i}]"))
        
        return issues
    
    def check_concept_file(self, concept_file_path: str) -> List[ComplianceIssue]:
        """
        Check a single concept file for language compliance issues.
        
        Args:
            concept_file_path: Path to the concept file to check.
            
        Returns:
            List of compliance issues found.
        """
        logger.info(f"Checking concept file: {concept_file_path}")
        
        try:
            # Load the concept file
            with open(concept_file_path, 'r') as f:
                concept_data = json.load(f)
            
            # Check the concept data
            issues = self.check_value(concept_data, "root")
            
            logger.info(f"Found {len(issues)} compliance issues in {concept_file_path}")
            
            return issues
        except Exception as e:
            logger.error(f"Error checking concept file {concept_file_path}: {str(e)}")
            raise
    
    def check_multiple_files(self, file_pattern: str, recursive: bool = False) -> Dict[str, List[ComplianceIssue]]:
        """
        Check multiple concept files for language compliance issues.
        
        Args:
            file_pattern: Glob pattern to match concept files.
            recursive: Whether to search subdirectories recursively.
                       This is automatically set to True if the pattern contains '**'.
            
        Returns:
            Dictionary mapping file paths to lists of compliance issues.
        """
        logger.info(f"Checking multiple files with pattern: {file_pattern}, recursive: {recursive}")
        
        # Use glob to find matching files
        # Note: recursive must be True when using ** patterns
        matching_files = glob.glob(file_pattern, recursive=recursive)
        
        # Filter to only include files (not directories)
        matching_files = [path for path in matching_files if os.path.isfile(path)]
        
        logger.info(f"Found {len(matching_files)} files matching pattern")
        
        # Check each file
        results = {}
        for file_path in matching_files:
            try:
                issues = self.check_concept_file(file_path)
                results[file_path] = issues
            except Exception as e:
                logger.error(f"Error checking file {file_path}: {str(e)}")
                results[file_path] = [ComplianceIssue("ERROR", "file", str(e))]
        
        return results
    
    def generate_report(self, results: Dict[str, List[ComplianceIssue]], output_file: Optional[str] = None) -> str:
        """
        Generate a report of language compliance issues.
        
        Args:
            results: Dictionary mapping file paths to lists of compliance issues.
            output_file: Optional path to save the report to.
            
        Returns:
            Report as a string.
        """
        logger.info("Generating language compliance report")
        
        # Count total issues
        total_issues = sum(len(issues) for issues in results.values())
        
        # Generate report header
        report = [
            "Language Compliance Report",
            "=========================",
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Files Checked: {len(results)}",
            f"Issues Found: {total_issues}",
            ""
        ]
        
        # Generate report for each file
        files_with_issues = 0
        for file_path, issues in results.items():
            if issues:
                files_with_issues += 1
                report.append(f"File: {file_path}")
                report.append("-" * (len(file_path) + 6))
                
                for i, issue in enumerate(issues, 1):
                    report.append(f"{i}. {issue}")
                
                report.append("")
        
        # Add summary for files without issues
        files_without_issues = len(results) - files_with_issues
        if files_without_issues > 0:
            report.append(f"No issues found in {files_without_issues} other files.")
        
        # Join report lines
        report_text = "\n".join(report)
        
        # Save report to file if requested
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write(report_text)
                logger.info(f"Saved report to {output_file}")
            except Exception as e:
                logger.error(f"Error saving report to {output_file}: {str(e)}")
        
        return report_text