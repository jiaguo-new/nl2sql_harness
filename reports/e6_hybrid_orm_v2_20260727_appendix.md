# E6 详细题目级附录

本节记录本次实验中被触发替换的 **25 道题**、它们替换前后的完整输入/输出，以及修复情况。

## 汇总表：空结果/报错触发（25 题）

| qid | db_id | 最终修复 | k5 结果 | 选中模型 | 选中 score | 备注 |
|---|---|---|---|---|---|---|
| 122 | financial | True | error | omnisql | 0.9526 | fixed |
| 606 | codebase_community | True | empty(0) | omnisql | 0.8670 | fixed |
| 766 | superhero | True | empty(0) | omnisql | 0.9526 | fixed |
| 851 | formula_1 | True | empty(0) | qwen3 | 0.4378 | fixed |
| 990 | formula_1 | True | empty(0) | qwen3 | 0.8933 | fixed |
| 1108 | european_football_2 | True | empty(0) | agentar | 0.8670 | fixed |
| 1168 | thrombosis_prediction | True | empty(0) | omnisql-921 | 0.5000 | fixed |
| 1314 | student_club | True | empty(0) | agentar | 0.8933 | fixed |
| 1453 | student_club | True | empty(0) | omnisql-921 | 0.3486 | fixed |
| 86 | california_schools | False | empty(0) | omnisql | 0.1480 | still wrong |
| 143 | financial | False | empty(0) | omnisql-921 | 0.2942 | still wrong |
| 231 | toxicology | False | empty(0) | agentar | 0.2227 | still wrong |
| 340 | card_games | False | empty(0) | omnisql | 0.2689 | still wrong |
| 428 | card_games | False | empty(0) | omnisql | 0.2018 | still wrong |
| 515 | card_games | False | empty(0) | omnisql-921 | 0.3208 | still wrong |
| 519 | card_games | False | empty(0) | omnisql | 0.1645 | still wrong |
| 529 | card_games | False | empty(0) | qwen3 | 0.3208 | still wrong |
| 630 | codebase_community | False | empty(0) | agentar | 0.1824 | still wrong |
| 706 | codebase_community | False | empty(0) | agentar | 0.2451 | still wrong |
| 959 | formula_1 | False | empty(0) | agentar | 0.8808 | still wrong |
| 998 | formula_1 | False | empty(0) | agentar | 0.4688 | still wrong |
| 1041 | european_football_2 | False | empty(0) | omnisql-921 | 0.5927 | still wrong |
| 1259 | thrombosis_prediction | False | empty(0) | omnisql | 0.1480 | still wrong |
| 1269 | thrombosis_prediction | False | empty(0) | omnisql-921 | 0.2227 | still wrong |
| 1468 | student_club | False | empty(0) | omnisql | 0.5000 | still wrong |

---

## 逐题输入输出详情

### qid 122（financial）

**Question：** State the district and region for loan ID '4990'. (Evidence: A2, A3 contains the information about district and region respectively.)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**True**
- 是否修复：**True**

**Baseline k5 SQL：**
```sql
SELECT T2.A2, T2.A3 FROM loan AS T1 INNER JOIN account AS T2 ON T1.account_id = T2.account_id INNER JOIN district AS T3 ON T2.district_id = T3.district_id WHERE T1.loan_id = 4990
```

**Baseline k5 result：**
```
execution error
```

**ORM 选中候选：** idx=5，model=omnisql，score=0.9526

**Selected SQL：**
```sql
SELECT T3.A2, T3.A3 FROM loan AS T1 INNER JOIN account AS T2 ON T1.account_id = T2.account_id INNER JOIN district AS T3 ON T2.district_id = T3.district_id WHERE T1.loan_id = 4990
```

**Selected result：**
```
Liberec | north Bohemia
```

---

### qid 606（codebase_community）

**Question：** List out the name of badges that users obtained on 7/19/2010 7:39:08 PM. (Evidence: on 7/19/2010 7:39:08 PM refers to Date = '2010-07-19 19:39:08')

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**True**
- 是否修复：**True**

**Baseline k5 SQL：**
```sql
SELECT Name FROM badges WHERE Date = '2010-07-19 19:39:08'
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=7，model=omnisql，score=0.8670

**Selected SQL：**
```sql
SELECT Name FROM badges WHERE Date = '2010-07-19 19:39:08.0'
```

**Selected result：**
```
Student
Student
Student
Student
Student
```

---

### qid 766（superhero）

**Question：** What is the hero's full name with the highest attribute in strength? (Evidence: highest attribute in strength refers to MAX(attribute_value) WHERE attribute_name = 'strength';)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**True**
- 是否修复：**True**

**Baseline k5 SQL：**
```sql
SELECT T1.full_name FROM superhero AS T1 INNER JOIN hero_attribute AS T2 ON T1.id = T2.hero_id INNER JOIN attribute AS T3 ON T2.attribute_id = T3.id WHERE T3.attribute_name = 'strength' AND T2.attribute_value = ( SELECT MAX(T4.attribute_value) FROM hero_attribute AS T4 INNER JOIN attribute AS T5 ON T4.attribute_id = T5.id WHERE T5.attribute_name = 'strength' )
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=7，model=omnisql，score=0.9526

**Selected SQL：**
```sql
SELECT T3.full_name FROM attribute AS T1 INNER JOIN hero_attribute AS T2 ON T1.id = T2.attribute_id INNER JOIN superhero AS T3 ON T2.hero_id = T3.id WHERE T1.attribute_name = 'Strength' ORDER BY T2.attribute_value DESC LIMIT 1
```

**Selected result：**
```
Richard Milhouse Jones
```

---

### qid 851（formula_1）

**Question：** Please list the positions of the circuits built by the constructor Renault. (Evidence: Renault is a name of constructor;)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**True**
- 是否修复：**True**

**Baseline k5 SQL：**
```sql

```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=13，model=qwen3，score=0.4378

**Selected SQL：**
```sql
SELECT T1.position FROM constructorStandings AS T1 INNER JOIN constructors AS T2 ON T1.constructorId = T2.constructorId WHERE T2.name = 'Renault'
```

**Selected result：**
```
4
5
6
7
7
```

---

### qid 990（formula_1）

**Question：** What is the constructor reference name of the champion in the 2009 Singapore Grand Prix? Please give its website. (Evidence: the time of the champion shows in the format of "minutes: seconds.millionsecond" in which Max(time); constructor reference name refers to constructorRef; website refers to url)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**True**
- 是否修复：**True**

**Baseline k5 SQL：**
```sql
SELECT T3.constructorRef, T3.url FROM results AS T1 INNER JOIN races AS T2 ON T1.raceId = T2.raceId INNER JOIN constructors AS T3 ON T1.constructorId = T3.constructorId WHERE T2.name = 'Singapore Grand Prix' AND T2.year = 2009 AND T1.time LIKE '_:%:.___'
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=13，model=qwen3，score=0.8933

**Selected SQL：**
```sql
SELECT T2.constructorRef, T2.url FROM results AS T1 INNER JOIN constructors AS T2 ON T1.constructorId = T2.constructorId INNER JOIN races AS T3 ON T1.raceId = T3.raceId WHERE T3.name = 'Singapore Grand Prix' AND T3.year = 2009 ORDER BY T1.time DESC LIMIT 1
```

**Selected result：**
```
mclaren | http://en.wikipedia.org/wiki/McLaren
```

---

### qid 1108（european_football_2）

**Question：** What was the build up play speed class for "Willem II" on 2011/2/22? (Evidence: "Willem II" refers to team_long_name = 'Willem II'; on 2011/2/22 refers to date = '2012-02-22 00:00:00')

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**True**
- 是否修复：**True**

**Baseline k5 SQL：**
```sql
SELECT t2.buildUpPlaySpeedClass FROM Team AS t1 INNER JOIN Team_Attributes AS t2 ON t1.team_api_id = t2.team_api_id WHERE t1.team_long_name = 'Willem II' AND SUBSTR(t2.`date`, 1, 10) = '2012-02-22'
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=2，model=agentar，score=0.8670

**Selected SQL：**
```sql
SELECT T2.buildUpPlaySpeedClass
FROM Team AS T1
INNER JOIN Team_Attributes AS T2
ON T1.team_api_id = T2.team_api_id
WHERE T1.team_long_name = 'Willem II'
  AND T2.date = '2011-02-22 00:00:00';
```

**Selected result：**
```
Fast
```

---

### qid 1168（thrombosis_prediction）

**Question：** The oldest SJS patient's medical laboratory work was completed on what date, and what age was the patient when they initially arrived at the hospital? (Evidence: The oldest patient refers to MAX(Birthday); 'SJS' refers to diagnosis; (SUBTRACT(year(`First Date`)), year(Birthday)); age of the patients when they initially arrived at the hospital refers to year(Birthday))

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**True**
- 是否修复：**True**

**Baseline k5 SQL：**
```sql
SELECT T2.Date, STRFTIME('%Y', T1.`First Date`) - STRFTIME('%Y', T1.Birthday)
FROM Patient AS T1
INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID
WHERE T1.Diagnosis = 'SJS'
  AND T1.Birthday = (SELECT MAX(Birthday) FROM Patient WHERE Diagnosis = 'SJS')
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=10，model=omnisql-921，score=0.5000

**Selected SQL：**
```sql
SELECT T2.Date, strftime('%Y', T1.`First Date`) - strftime('%Y', T1.Birthday) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.Diagnosis = 'SJS' ORDER BY T1.Birthday LIMIT 1
```

**Selected result：**
```
1981-07-31 | 69
```

---

### qid 1314（student_club）

**Question：** Please list the full names of the students in the Student_Club that come from the Art and Design Department. (Evidence: full name refers to first_name, last_name;)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**True**
- 是否修复：**True**

**Baseline k5 SQL：**
```sql
SELECT T1.first_name, T1.last_name FROM member AS T1 INNER JOIN major AS T2 ON T1.link_to_major = T2.major_id WHERE T2.department = 'Art and Design'
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=1，model=agentar，score=0.8933

**Selected SQL：**
```sql
SELECT member.first_name, member.last_name
FROM member
INNER JOIN major ON member.link_to_major = major.major_id
WHERE major.department = 'Art and Design Department';
```

**Selected result：**
```
Amy | Firth
```

---

### qid 1453（student_club）

**Question：** List the name of events with less than average parking cost. (Evidence: name of events refers to event_name; less than average parking cost refers to cost < DIVIDE(SUM(cost), COUNT(event_id)) where category = 'Parking')

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**True**
- 是否修复：**True**

**Baseline k5 SQL：**
```sql
SELECT DISTINCT T1.event_name
FROM event AS T1
INNER JOIN budget AS T2 ON T1.event_id = T2.link_to_event
INNER JOIN expense AS T3 ON T2.budget_id = T3.link_to_budget
WHERE T2.category = 'Parking'
  AND T3.cost < (
    SELECT SUM(T6.cost) / COUNT(T4.event_id)
    FROM event AS T4
    INNER JOIN budget AS T5 ON T4.event_id = T5.link_to_event
    INNER JOIN expense AS T6 ON T5.budget_id = T6.link_to_budget
    WHERE T5.category = 'Parking'
  )
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=12，model=omnisql-921，score=0.3486

**Selected SQL：**
```sql
SELECT T1.event_name FROM event AS T1 INNER JOIN budget AS T2 ON T1.event_id = T2.link_to_event INNER JOIN expense AS T3 ON T2.budget_id = T3.link_to_budget WHERE T2.category = 'Parking' AND T3.cost < ( SELECT AVG(cost) FROM expense WHERE category = 'Parking' )
```

**Selected result：**
```
November Speaker
October Speaker
September Speaker
```

---

### qid 86（california_schools）

**Question：** What is the administrator's last name that oversees the school with Charter number 40? Indicate the district, the county where the school is situated, and the name of the school.

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT AdmLName1, District, County, School FROM schools WHERE CharterNum = '40'
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=6，model=omnisql，score=0.1480

**Selected SQL：**
```sql
SELECT AdmLName1, District, County, School FROM schools WHERE CharterNum = '40'
```

**Selected result：**
```
empty result set (0 rows)
```

---

### qid 143（financial）

**Question：** What are the accounts that have both gold and junior credit cards?

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT T2.account_id FROM card AS T1 INNER JOIN disp AS T2 ON T1.disp_id = T2.disp_id WHERE T1.type IN ('gold', 'junior') GROUP BY T2.account_id HAVING COUNT(DISTINCT T1.type) = 2
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=9，model=omnisql-921，score=0.2942

**Selected SQL：**
```sql
SELECT T1.account_id FROM account AS T1 INNER JOIN disp AS T2 ON T1.account_id = T2.account_id INNER JOIN card AS T3 ON T2.disp_id = T3.disp_id WHERE T3.type = 'junior' INTERSECT SELECT T1.account_id FROM account AS T1 INNER JOIN disp AS T2 ON T1.account_id = T2.account_id INNER JOIN card AS T3 ON T2.disp_id = T3.disp_id WHERE T3.type = 'gold'
```

**Selected result：**
```
empty result set (0 rows)
```

---

### qid 231（toxicology）

**Question：** Which bond type accounted for the majority of the bonds found in molecule TR018 and state whether or not this molecule is carcinogenic? (Evidence: TR018 is the molecule id; majority of the bond found refers to MAX(COUNT(bond_type)); label = '+' mean molecules are carcinogenic; label = '-' means molecules are non-carcinogenic)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT T.bond_type, IIF(M.label = '+', 'YES', 'NO') AS carcinogenic
FROM (
  SELECT bond_type
  FROM bond
  WHERE molecule_id = 'TR018'
  GROUP BY bond_type
  ORDER BY COUNT(bond_id) DESC
  LIMIT 1
) AS T
INNER JOIN molecule AS M ON M.molecule_id = 'TR018'
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=1，model=agentar，score=0.2227

**Selected SQL：**
```sql
SELECT b.bond_type, m.label
FROM bond b
INNER JOIN molecule m ON b.molecule_id = m.molecule_id
WHERE b.molecule_id = 'TR018'
GROUP BY b.bond_type
ORDER BY COUNT(b.bond_type) DESC
LIMIT 1;
```

**Selected result：**
```
empty result set (0 rows)
```

---

### qid 340（card_games）

**Question：** Which are the cards that have incredibly powerful foils. (Evidence: poweful foils refers to cardKingdomFoilId = cardKingdomId AND cardKingdomId is not null)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT id FROM cards WHERE cardKingdomFoilId = cardKingdomId AND cardKingdomId IS NOT NULL
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=5，model=omnisql，score=0.2689

**Selected SQL：**
```sql
SELECT name FROM cards WHERE cardKingdomFoilId = cardKingdomId AND cardKingdomId IS NOT NULL
```

**Selected result：**
```
empty result set (0 rows)
```

---

### qid 428（card_games）

**Question：** What is the name of set number 5 and its translation? (Evidence: set number 5 refers to id = 5)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT T1.name, T2.translation FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T1.id = 5
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=5，model=omnisql，score=0.2018

**Selected SQL：**
```sql
SELECT T1.name, T2.translation FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T1.id = 5
```

**Selected result：**
```
empty result set (0 rows)
```

---

### qid 515（card_games）

**Question：** When was the oldest mythic card released and what are its legal play formats? (Evidence: the oldest card refers to MIN(originalReleaseDate); mythic card refers to rarity = 'mythic'; legal play refers to status = 'legal'; play format refers to format)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT T1.originalReleaseDate, T2.format
FROM cards AS T1
INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid
WHERE T1.rarity = 'mythic'
  AND T2.status = 'legal'
  AND T1.originalReleaseDate = (
    SELECT MIN(originalReleaseDate)
    FROM cards
    WHERE rarity = 'mythic'
  )
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=10，model=omnisql-921，score=0.3208

**Selected SQL：**
```sql
SELECT T1.originalReleaseDate, T2.format FROM cards AS T1 INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid WHERE T1.rarity = 'mythic' AND T2.status = 'Legal' ORDER BY T1.originalReleaseDate LIMIT 1
```

**Selected result：**
```
None | commander
```

---

### qid 519（card_games）

**Question：** What is the language of the "Battlebond" set? (Evidence: "Battlebond" set refers to name = 'Battlebond')

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT T2.language FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T1.name = 'Battlebond'
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=5，model=omnisql，score=0.1645

**Selected SQL：**
```sql
SELECT T1.language FROM set_translations AS T1 INNER JOIN sets AS T2 ON T1.setCode = T2.code WHERE T2.name = 'Battlebond'
```

**Selected result：**
```
empty result set (0 rows)
```

---

### qid 529（card_games）

**Question：** Find and list the names of sets which doesn't have Japanese translation but have Korean translation. (Evidence: names of sets refers to name; doesn't have Japanese translation refers to language not like '%Japanese%'; have Korean translation refers to language = 'Korean')

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT name FROM sets WHERE code IN (SELECT setCode FROM set_translations WHERE language = 'Korean') AND code NOT IN (SELECT setCode FROM set_translations WHERE language LIKE '%Japanese%')
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=13，model=qwen3，score=0.3208

**Selected SQL：**
```sql
SELECT T2.name FROM set_translations AS T1 INNER JOIN sets AS T2 ON T1.setCode = T2.code WHERE T1.language = 'Korean' AND T1.setCode NOT IN ( SELECT setCode FROM set_translations WHERE language LIKE '%Japanese%' )
```

**Selected result：**
```
empty result set (0 rows)
```

---

### qid 630（codebase_community）

**Question：** What is the name of tags used by John Stauffer's? (Evidence: DisplayName = 'John Stauffer';)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT T3.Tags FROM users AS T1 INNER JOIN postHistory AS T2 ON T1.Id = T2.UserId INNER JOIN posts AS T3 ON T2.PostId = T3.Id WHERE T1.DisplayName = 'John Stauffer'
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=3，model=agentar，score=0.1824

**Selected SQL：**
```sql
SELECT DISTINCT T2.Tags
FROM users AS T1
INNER JOIN posts AS T2 ON T1.Id = T2.OwnerUserId
WHERE T1.DisplayName = 'John Stauffer';
```

**Selected result：**
```
empty result set (0 rows)
```

---

### qid 706（codebase_community）

**Question：** Give the texts commented on the post about linear regression. (Evidence: Title = 'How can I adapt ANOVA for binary data?';)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT T1.Text FROM comments AS T1 INNER JOIN posts AS T2 ON T1.PostId = T2.Id WHERE T2.Title = 'How can I adapt ANOVA for binary data?'
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=1，model=agentar，score=0.2451

**Selected SQL：**
```sql
SELECT comments.Text
FROM comments
INNER JOIN posts ON comments.PostId = posts.Id
WHERE posts.Title = 'How can I adapt ANOVA for binary data?';
```

**Selected result：**
```
empty result set (0 rows)
```

---

### qid 959（formula_1）

**Question：** What is the fastest lap number of the champion in 2009? (Evidence: in 2009 refers to year = 2009; Only the time of the champion shows in the format of "hour: minutes: seconds.millionsecond")

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql

```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=4，model=agentar，score=0.8808

**Selected SQL：**
```sql
SELECT results.fastestLap
FROM results
INNER JOIN races ON results.raceId = races.raceId
WHERE races.year = 2009
ORDER BY results.time ASC
LIMIT 1;
```

**Selected result：**
```
38
```

---

### qid 998（formula_1）

**Question：** In terms of number of points acquired, how many victories did the driver who ranked 91st acquired? (Evidence: victories refer to wins; 91st refers to points

)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql

```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=1，model=agentar，score=0.4688

**Selected SQL：**
```sql
SELECT wins 
FROM driverStandings 
ORDER BY points DESC 
LIMIT 1 OFFSET 90;
```

**Selected result：**
```
0
```

---

### qid 1041（european_football_2）

**Question：** For the teams with normal build-up play dribbling class in 2014, List the names of the teams with less than average chance creation passing, in descending order of chance creation passing. (Evidence: normal build-up play dribbling class refers to buildUpPlayDribblingClass = 'Normal'; in 2014 refers to date > = '2014-01-01 00:00:00' AND date < = '2014-01-31 00:00:00'; names of the teams refers to team_long_name; less than average chance creation passing = DIVIDE(SUM(chanceCreationPassing), COUNT(id)) > chanceCreationPassing;)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT t3.team_long_name FROM Team AS t3 INNER JOIN Team_Attributes AS t4 ON t3.team_api_id = t4.team_api_id WHERE t4.buildUpPlayDribblingClass = 'Normal' AND t4.date >= '2014-01-01 00:00:00' AND t4.date <= '2014-01-31 00:00:00' AND t4.chanceCreationPassing < ( SELECT CAST(SUM(t2.chanceCreationPassing) AS REAL) / COUNT(t1.id) FROM Team AS t1 INNER JOIN Team_Attributes AS t2 ON t1.team_api_id = t2.team_api_id WHERE t2.buildUpPlayDribblingClass = 'Normal' AND t2.date >= '2014-01-01 00:00:00' AND t2.date <= '2014-01-31 00:00:00' ) ORDER BY t4.chanceCreationPassing DESC
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=9，model=omnisql-921，score=0.5927

**Selected SQL：**
```sql
SELECT T1.team_long_name FROM Team AS T1 INNER JOIN Team_Attributes AS T2 ON T1.team_api_id = T2.team_api_id WHERE T2.buildUpPlayDribblingClass = 'Normal' AND T2.date LIKE '2014%' AND T2.chanceCreationPassing < ( SELECT AVG(chanceCreationPassing) FROM Team_Attributes WHERE date LIKE '2014%' ) ORDER BY T2.chanceCreationPassing DESC
```

**Selected result：**
```
Athletic Club de Bilbao
KSV Cercle Brugge
Chievo Verona
Dundee United
FC Energie Cottbus
```

---

### qid 1259（thrombosis_prediction）

**Question：** Please list the diseases of the patients born after 1995-1-1 and have a normal Rhuematoid Factor. (Evidence: diseases refers to Diagnosis; born after 1995/1/1 refers to YEAR(Birthday) > = 1995; normal Rhuematoid Factor refers to RA IN('-', '+-');)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT T1.Diagnosis FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE (T2.RA = '-' OR T2.RA = '+-') AND STRFTIME('%Y', T1.Birthday) >= '1995'
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=5，model=omnisql，score=0.1480

**Selected SQL：**
```sql
SELECT DISTINCT T1.Diagnosis FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.Birthday > '1995-01-01' AND T2.RA IN ('-', '+-')
```

**Selected result：**
```
empty result set (0 rows)
```

---

### qid 1269（thrombosis_prediction）

**Question：** Please list the IDs of the patients who had the examination done after 1997/1/1 and had a normal anti-scl70. (Evidence: examination done after 1997/1/1 refers to `Examination Date` > = 1997-01-01; normal anti-scl70 refers to SC170 IN('-', '+-');)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT T1.ID FROM Patient AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID INNER JOIN Laboratory AS T3 ON T1.ID = T3.ID WHERE T2.`Examination Date` >= '1997-01-01' AND T3.SC170 IN ('-', '+-')
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=10，model=omnisql-921，score=0.2227

**Selected SQL：**
```sql
SELECT T1.ID FROM Laboratory AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID WHERE T2.`Examination Date` >= '1997-01-01' AND T1.SC170 IN ('-', '+-')
```

**Selected result：**
```
empty result set (0 rows)
```

---

### qid 1468（student_club）

**Question：** Where is the hometown of Garrett Girke? (Evidence: hometown refers to city)

- Baseline（k5）是否正确：**False**
- Final（替换后）是否正确：**False**
- 是否修复：**False**

**Baseline k5 SQL：**
```sql
SELECT T2.city FROM member AS T1 INNER JOIN zip_code AS T2 ON T2.zip_code = T1.zip WHERE T1.first_name = 'Garrett' AND T1.last_name = 'Girke'
```

**Baseline k5 result：**
```
empty result set (0 rows)
```

**ORM 选中候选：** idx=5，model=omnisql，score=0.5000

**Selected SQL：**
```sql
SELECT T2.city FROM member AS T1 INNER JOIN zip_code AS T2 ON T2.zip_code = T1.zip WHERE T1.first_name = 'Garrett' AND T1.last_name = 'Girke'
```

**Selected result：**
```
empty result set (0 rows)
```

---

