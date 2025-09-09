# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Fractal-Down
# SPDX-FileCopyrightText: 2025 Nicholas Woolridge & NOCTRL™ (Nô)

"""
Complete scenario execution runner.

Runs all Trimble integration scenarios and provides consolidated results.
"""

from .construction_site_scenario import construction_site_workflow
from .precision_agriculture_scenario import precision_agriculture_workflow  
from .survey_mapping_scenario import survey_mapping_workflow
from .fleet_telematics_scenario import fleet_telematics_workflow
from .edge_deployment_scenario import edge_deployment_workflow


def run_all_scenarios():
    """
    Execute all Trimble integration scenarios.
    
    Returns:
        Consolidated results from all scenario executions
    """
    print("=" * 60)
    print("TRIMBLE FRACTAL-DOWN INTEGRATION SCENARIOS")
    print("=" * 60)
    print()
    
    results = {}
    
    # Execute each scenario
    scenarios = [
        ("construction", construction_site_workflow),
        ("agriculture", precision_agriculture_workflow),
        ("survey", survey_mapping_workflow),
        ("fleet", fleet_telematics_workflow),
        ("edge", edge_deployment_workflow)
    ]
    
    for scenario_name, scenario_func in scenarios:
        try:
            print(f"Executing {scenario_name} scenario...")
            results[scenario_name] = scenario_func()
            print(f"✓ {scenario_name} scenario completed successfully")
        except Exception as e:
            print(f"✗ {scenario_name} scenario failed: {e}")
            results[scenario_name] = {"error": str(e)}
        print()
    
    # Print consolidated summary
    print("=" * 60)
    print("CONSOLIDATED SCENARIO RESULTS")
    print("=" * 60)
    
    successful_scenarios = sum(1 for r in results.values() if "error" not in r)
    total_scenarios = len(scenarios)
    
    print(f"Scenarios executed: {successful_scenarios}/{total_scenarios}")
    print(f"Success rate: {successful_scenarios/total_scenarios:.1%}")
    print()
    
    for scenario_name, result in results.items():
        if "error" not in result:
            print(f"✓ {scenario_name.title()}: Operational")
        else:
            print(f"✗ {scenario_name.title()}: {result['error']}")
    
    return results


if __name__ == "__main__":
    run_all_scenarios()