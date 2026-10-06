---
name: logging-standards
description: Use this skill to ensure logs are structured and contain necessary information for troubleshooting.
---
1. **Log Levels**: Use appropriate log levels (ERROR, WARNING, INFO) to categorize log messages.
2. **Timestamp Format**: Ensure all timestamps are in UTC and follow the format YYYY-MM-DDTHH:MM:SSZ.
3. **Service Naming**: Standardize service names to lowercase and replace hyphens with underscores (e.g., payment-service -> payment_service).
4. **Error Details**: Capture detailed error information, including exception types and messages.
5. **Repeat Counts**: Track and log the number of times an error message has been repeated.
6. **Sorting**: Sort log entries by service name and timestamp for easier analysis.
7. **Schema Compliance**: Ensure that the log output adheres to a defined schema, including versioning and metadata.
