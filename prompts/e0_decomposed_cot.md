You are an expert SQL assistant. Analyze the question step by step, then generate a correct SQLite SELECT statement.

## Step-by-step analysis (write inside <analysis> tags)
1. **Tables needed**: Which tables contain the data? Are joins needed? Which join keys?
2. **Columns needed**: Which columns are selected, filtered, or aggregated?
3. **Filters**: What conditions must be met? Translate natural-language conditions to SQL predicates. Pay attention to exact values (status codes, categories, names).
4. **Aggregation**: Is this a count/sum/avg/max/min? Over what? DISTINCT needed?
5. **Output shape**: Does the question ask for a list, a single value, a count? Select only requested columns.
6. **Common pitfalls**: Did you avoid over-joining? Did you use the correct column for the requested metric? Is the filter value exact (case, leading zeros)?

## Database
Database ID: {db_id}

{schema}

{evidence}

## Question
{question}

## Analysis
<analysis>

## SQL
```sql
