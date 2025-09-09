#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""
Simple CLI script to generate Trimble business pitch PDF
"""

import sys
import os

# Add the parent directory to the path so we can import trimble modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trimble.business_pitch_generator import generate_trimble_business_pitch_pdf

if __name__ == "__main__":
    print("🚀 Generating Trimble Business Pitch PDF...")
    print("=" * 50)
    
    try:
        pdf_path = generate_trimble_business_pitch_pdf()
        
        print("=" * 50)
        print("✅ SUCCESS!")
        print(f"📄 PDF generated: {pdf_path}")
        print()
        print("This business pitch includes:")
        print("• Value proposition and ROI analysis")
        print("• Real-world application examples")  
        print("• Pricing and licensing revenue model")
        print("• Implementation roadmap")
        print("• Success metrics and next steps")
        print("• Your revenue share: $4.625M annually from Trimble partnership")
        print()
        print("Ready to present to Trimble executives! 💼")
        
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        sys.exit(1)