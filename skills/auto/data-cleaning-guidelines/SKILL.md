---
name: data-cleaning-guidelines
description: Use this skill to standardize data cleaning processes for consistency and accuracy.
---
1. **Date Formatting**: Convert all date fields to a standard format (e.g., YYYY-MM-DDTHH:MM:SSZ) and ensure they are in UTC.
2. **Value Normalization**: Standardize categorical values (e.g., region names) to a consistent format (e.g., lowercase, trimmed).
3. **Missing Values**: Define a strategy for handling missing values, such as replacing placeholders with NaN or appropriate defaults.
4. **Duplicate Removal**: Implement checks to identify and remove duplicate entries from datasets.
5. **Data Type Consistency**: Ensure that numeric values are stored in appropriate formats (e.g., integers for counts, decimals for prices).
6. **Output Structure**: Follow a predefined structure for output files, including required fields and their formats.
7. **Validation Checks**: Include validation checks to ensure that the cleaned data meets expected criteria before final output.
