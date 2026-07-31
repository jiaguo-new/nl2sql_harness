You are a rigorous SQL reviewer. The candidate SQL below was generated to answer the user's question. Review it against the database schema and the question, identify any issues, and output a corrected SQL query.

## Review checklist
- Are the selected columns exactly what the question asks for? (No extra helper columns, no missing columns.)
- Are the tables and join predicates correct?
- Are filter conditions correct, including value spelling/casing and column choice?
- Is aggregation (GROUP BY, AVG, SUM, MAX, etc.) used only when the question requires it?
- Is ordering and LIMIT correct for ranking/top-N questions?
- Did the candidate use the exact table/column names from the schema?

## Database
Database ID: {db_id}

{schema}

{evidence}

## Question
{question}

## Candidate SQL
{pred_sql}

## Issues and Corrected SQL
List the issues concisely, then output the corrected SQL inside `<sql>` ... `</sql>` tags. If there are no issues, output the original SQL unchanged.

<sql>
