# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""
Test the business pitch PDF generation.
"""

import os
import sys
import tempfile
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from trimble.business_pitch_generator import (
    generate_business_pitch_data,
    create_business_pitch_pdf,
    generate_trimble_business_pitch_pdf
)


def test_generate_business_pitch_data():
    """Test that business pitch data generation works."""
    data = generate_business_pitch_data()
    
    # Check required top-level sections
    assert "metadata" in data
    assert "executive_summary" in data
    assert "market_opportunity" in data
    assert "real_world_applications" in data
    assert "pricing_and_licensing" in data
    assert "implementation_roadmap" in data
    assert "success_metrics" in data
    assert "next_steps" in data
    
    # Check executive summary has financial data
    exec_summary = data["executive_summary"]
    assert "financial_impact" in exec_summary
    assert "annual_value" in exec_summary["financial_impact"]
    assert "$11.5M" in exec_summary["financial_impact"]["annual_value"]
    
    # Check pricing includes revenue sharing
    pricing = data["pricing_and_licensing"]
    assert "revenue_sharing" in pricing
    assert "fractal_down_annual_cut" in pricing["revenue_sharing"]
    assert "$4.625M" in pricing["revenue_sharing"]["fractal_down_annual_cut"]
    
    # Check real-world applications
    apps = data["real_world_applications"]
    assert "construction" in apps
    assert "agriculture" in apps
    assert "transportation" in apps
    
    for sector, details in apps.items():
        assert "use_case" in details
        assert "current_limitation" in details
        assert "fractal_down_solution" in details
        assert "estimated_savings" in details


def test_create_business_pitch_pdf():
    """Test PDF creation from business pitch data."""
    data = generate_business_pitch_data()
    
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        pdf_path = tmp_file.name
    
    try:
        # Create the PDF
        result_path = create_business_pitch_pdf(data, pdf_path)
        
        # Check that PDF was created
        assert os.path.exists(result_path)
        assert result_path == pdf_path
        
        # Check that PDF has reasonable size (should be several KB)
        file_size = os.path.getsize(pdf_path)
        assert file_size > 5000  # At least 5KB
        assert file_size < 100000  # Less than 100KB (reasonable for a business document)
        
    finally:
        # Clean up
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


def test_generate_trimble_business_pitch_pdf():
    """Test the complete PDF generation workflow."""
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = generate_trimble_business_pitch_pdf(temp_dir)
        
        # Check that PDF was created in the right location
        expected_path = os.path.join(temp_dir, "trimble_business_pitch.pdf")
        assert pdf_path == expected_path
        assert os.path.exists(pdf_path)
        
        # Check PDF has content
        file_size = os.path.getsize(pdf_path)
        assert file_size > 5000


if __name__ == "__main__":
    test_generate_business_pitch_data()
    test_create_business_pitch_pdf()
    test_generate_trimble_business_pitch_pdf()
    print("✓ All business pitch PDF tests passed!")