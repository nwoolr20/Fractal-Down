"""
Test the comprehensive proposal generator.
"""

import pytest
import os
import json
import tempfile
from trimble.proposal_generator import generate_comprehensive_proposal, save_proposal, render_proposal_as_markdown


def test_generate_comprehensive_proposal():
    """Test that comprehensive proposal generation works."""
    proposal = generate_comprehensive_proposal()
    
    # Check required top-level keys
    required_keys = [
        "metadata", "executive_summary", "technical_assessment", 
        "benefits_analysis", "integration_roadmap", "kpi_mapping",
        "market_research_text", "implementation_examples_text", "case_study_content"
    ]
    
    for key in required_keys:
        assert key in proposal, f"Missing required key: {key}"
    
    # Check metadata structure
    metadata = proposal["metadata"]
    assert metadata["title"] == "Trimble Inc. - Fractal-Down Integration Proposal"
    assert metadata["version"] == "1.0"
    assert "generated_date" in metadata
    
    # Check that text content exists
    assert len(proposal["market_research_text"]) > 1000
    assert len(proposal["implementation_examples_text"]) > 1000
    assert len(proposal["case_study_content"]) > 1000


def test_render_proposal_as_markdown():
    """Test markdown rendering of proposal."""
    proposal = generate_comprehensive_proposal()
    markdown = render_proposal_as_markdown(proposal)
    
    # Check that markdown contains expected sections
    assert "# Trimble Inc. - Fractal-Down Integration Proposal" in markdown
    assert "## Executive Summary" in markdown
    assert "## Benefits Analysis" in markdown
    assert "## Integration Roadmap" in markdown
    assert "## Market Research & Competitive Analysis" in markdown
    assert "## Implementation Examples" in markdown
    
    # Check that key metrics are included
    assert "PROCEED with Trimble-Fractal-Down integration" in markdown
    assert "$11.5M annually" in markdown
    assert "2.4 months" in markdown


def test_save_proposal():
    """Test saving proposal to files."""
    proposal = generate_comprehensive_proposal()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        file_paths = save_proposal(proposal, temp_dir)
        
        # Check that all files were created
        assert os.path.exists(file_paths["json"])
        assert os.path.exists(file_paths["markdown"])
        assert os.path.exists(file_paths["summary"])
        
        # Check JSON file structure
        with open(file_paths["json"], 'r') as f:
            saved_proposal = json.load(f)
        
        assert saved_proposal["metadata"]["title"] == proposal["metadata"]["title"]
        
        # Check markdown file has content
        with open(file_paths["markdown"], 'r') as f:
            markdown_content = f.read()
        
        assert len(markdown_content) > 5000  # Should be substantial
        assert "Trimble Inc. - Fractal-Down Integration Proposal" in markdown_content


if __name__ == "__main__":
    test_generate_comprehensive_proposal()
    test_render_proposal_as_markdown()
    test_save_proposal()
    print("✓ All proposal generator tests passed!")