# Verification Guidance for Fractal-Down

**IMPORTANT NOTICE: This document provides non-binding best practices and guidance only. It does not modify or alter the license terms in any way. Please refer to the LICENSE files for the actual legal terms governing the use of this software.**

## Overview

This document provides advisory guidance for implementing deterministic verification and validation practices when using Fractal-Down. These recommendations are designed to help ensure consistent, reliable results across different environments and use cases.

## Deterministic Verification

### Hash-based Verification

Fractal-Down includes built-in cryptographic verification through its digest system. To ensure deterministic results:

1. **Enable verification by default**: Always use `verify=True` when running evaluations in production
2. **Consistent hash providers**: Use the same hash provider across all environments
3. **Reproducible inputs**: Ensure input data is identical across verification runs

```python
# Recommended verification approach
evaluator = Evaluator(dag, inputs)
result = evaluator.run(plan, verify=True)

# Verify digest consistency
assert result.digest == expected_digest
```

### Deterministic Plan Generation

To ensure consistent plan generation:

1. **Fixed random seeds**: When using stochastic algorithms, always set deterministic seeds
2. **Consistent parameter ordering**: Use identical fractal parameters across environments
3. **Stable node ordering**: Ensure DAG nodes are processed in a consistent order

## Memory Bound Validation

### Resource Constraint Verification

Monitor and validate memory usage with LRU cache-based memory management:

1. **Peak memory tracking**: Monitor `peak_rss_bytes` during evaluation
2. **Budget validation**: Verify that budget constraints are respected
3. **Memory leak detection**: Check for gradual memory increases over multiple runs

```python
# Memory monitoring example
import psutil
import os

process = psutil.Process(os.getpid())
memory_before = process.memory_info().rss

result = evaluator.run(plan, verify=True)

memory_after = process.memory_info().rss
memory_used = memory_after - memory_before

# Validate memory usage is within expected bounds
assert memory_used <= expected_memory_bound
```

### Performance Validation

1. **Benchmark consistency**: Run performance benchmarks across environments
2. **Scaling verification**: Validate that memory usage scales as expected with problem size
3. **Regression testing**: Monitor for performance regressions in new versions

## Caching Integrity

### Cache Validation

Ensure plan cache integrity and consistency:

1. **Fingerprint verification**: Validate that cache fingerprints match expectations
2. **Cache hit consistency**: Verify that cache hits produce identical results
3. **Cross-environment cache**: Test cache portability across different environments

```python
# Cache integrity verification
cache = PlanCache()
fingerprint = cache.fingerprint(dag, output, fractal_params, budget_nodes)

# Verify fingerprint determinism
assert fingerprint == expected_fingerprint

# Verify cache hit produces same result
cached_plan = cache.get(fingerprint)
if cached_plan:
    result1 = evaluator.run(cached_plan, verify=True)
    result2 = evaluator.run(cached_plan, verify=True)
    assert result1.digest == result2.digest
```

### Cache Maintenance

1. **Regular validation**: Periodically verify cached plans still produce correct results
2. **Version compatibility**: Ensure cache invalidation when software versions change
3. **Storage integrity**: Validate binary plan serialization/deserialization

## Production Deployment Best Practices

### Environment Consistency

1. **Python version**: Use identical Python versions across all environments
2. **Dependency versions**: Pin exact dependency versions in production
3. **System libraries**: Ensure consistent system-level dependencies

### Testing and Validation

1. **Comprehensive test suite**: Run full test suite before deployment
2. **Integration testing**: Test with realistic workloads
3. **Smoke testing**: Implement basic verification checks in monitoring

```python
# Smoke test example
def smoke_test():
    # Simple verification that core functionality works
    dag = create_test_dag()
    inputs = get_test_inputs()
    
    evaluator = Evaluator(dag, inputs)
    plan = build_plan(dag, target_node, budget_nodes=10)
    result = evaluator.run(plan, verify=True)
    
    # Basic sanity checks
    assert result.value is not None
    assert result.digest is not None
    assert len(result.digest) == 32  # SHA-256 digest length
    
    return True
```

### Monitoring and Alerting

1. **Digest validation**: Monitor for unexpected digest changes
2. **Performance monitoring**: Track evaluation times and memory usage
3. **Error tracking**: Log and alert on verification failures

## Troubleshooting

### Common Issues

1. **Non-deterministic results**: Check for floating-point precision issues, random seeds
2. **Memory constraints**: Verify budget settings and actual memory usage
3. **Cache misses**: Investigate fingerprint generation and parameter consistency

### Debugging Tools

1. **Verbose logging**: Enable detailed logging for plan execution
2. **Memory profiling**: Use memory profilers to identify usage patterns
3. **Performance analysis**: Utilize the built-in benchmarking suite

## Disclaimer

**This guidance document is provided for informational purposes only and does not constitute legal advice. It does not modify, supersede, or alter the license terms governing this software. Users are solely responsible for ensuring compliance with applicable licenses and implementing appropriate verification practices for their specific use cases.**

For license terms, please refer to:
- LICENSE (dual license with choice between Apache 2.0 and Fractal-Down License)
- LICENSE-APACHE (Apache License 2.0)
- LICENSE-FRACTAL-DOWN (Fractal-Down License)