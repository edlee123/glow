"""
Tests for the language compliance checker.
"""

import os
import json
import tempfile
from unittest import TestCase

from glow.compliance.language_checker import LanguageChecker, ComplianceIssue


class TestLanguageChecker(TestCase):
    """
    Tests for the LanguageChecker class.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.checker = LanguageChecker()
        
        # Create a temporary concept file for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.concept_file = os.path.join(self.temp_dir.name, "test_concept.json")
        
        # Create a test concept file
        concept_data = {
            "generation_id": "test-concept-20251019",
            "product": "Test Product",
            "aspect_ratio": "1:1",
            "concept": "concept1",
            "generated_concept": {
                "text2image_prompt": "Create an image showing our best product",
                "text_overlay_config": {
                    "primary_text": "Guaranteed results with our product!",
                    "secondary_text": "The perfect cure for your problems"
                }
            }
        }
        
        with open(self.concept_file, 'w') as f:
            json.dump(concept_data, f)
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()
    
    def test_check_text(self):
        """Test checking text for prohibited words."""
        issues = self.checker.check_text(
            "This product offers guaranteed results and is the best in its class.",
            "test.location"
        )
        
        self.assertEqual(len(issues), 2)
        self.assertEqual(issues[0].word, "guaranteed")
        self.assertEqual(issues[1].word, "best")
    
    def test_check_concept_file(self):
        """Test checking a concept file for prohibited words."""
        issues = self.checker.check_concept_file(self.concept_file)
        
        self.assertEqual(len(issues), 4)
        
        # Check that the expected prohibited words were found
        words_found = [issue.word for issue in issues]
        self.assertIn("best", words_found)
        self.assertIn("guaranteed", words_found)
        self.assertIn("cure", words_found)
        self.assertIn("perfect", words_found)
    
    def test_custom_words(self):
        """Test using custom prohibited words."""
        # Create a temporary file with custom prohibited words
        custom_words_file = os.path.join(self.temp_dir.name, "custom_words.txt")
        with open(custom_words_file, 'w') as f:
            f.write("product\nresults\n")
        
        # Create a checker with custom words
        custom_checker = LanguageChecker(custom_words_file=custom_words_file)
        
        # Check the concept file
        issues = custom_checker.check_concept_file(self.concept_file)
        
        # Check that the custom prohibited words were found
        words_found = [issue.word for issue in issues]
        self.assertIn("product", words_found)
        self.assertIn("results", words_found)
    
    def test_generate_report(self):
        """Test generating a report."""
        # Check multiple files (just one in this case)
        results = {
            self.concept_file: self.checker.check_concept_file(self.concept_file)
        }
        
        # Generate a report
        report = self.checker.generate_report(results)
        
        # Check that the report contains the expected information
        self.assertIn("Language Compliance Report", report)
        self.assertIn(f"Files Checked: 1", report)
        self.assertIn(f"Issues Found: 4", report)
        self.assertIn(f"File: {self.concept_file}", report)
        self.assertIn("Prohibited word 'best'", report)
        self.assertIn("Prohibited word 'guaranteed'", report)
        self.assertIn("Prohibited word 'cure'", report)
        self.assertIn("Prohibited word 'perfect'", report)