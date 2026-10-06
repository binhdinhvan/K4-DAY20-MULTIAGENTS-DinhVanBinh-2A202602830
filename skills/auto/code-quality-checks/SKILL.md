---
name: code-quality-checks
description: Use this skill to ensure code adheres to quality standards and conventions.
---
1. **Test Integrity**: Ensure that original test files remain unmodified. New test files can be created as needed.
2. **Type Annotations**: All public functions must have type annotations for parameters and return values.
3. **Changelog Updates**: Document each fix in the CHANGELOG.md under '## Unreleased' with at least three bullet points.
4. **CSV Formatting**: Ensure that CSV outputs follow the specified quoting and formatting rules, especially for monetary values.
5. **Error Handling**: Implement robust error handling to manage exceptions gracefully and log them appropriately.
6. **Function Documentation**: Each function should have a clear docstring explaining its purpose, parameters, and return values.
7. **Code Review**: Conduct peer reviews to catch potential issues before merging code changes.
