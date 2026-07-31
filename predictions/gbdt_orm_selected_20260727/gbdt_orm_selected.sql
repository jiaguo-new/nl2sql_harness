SELECT MAX(`Percent (%) Eligible Free (K-12)`) FROM frpm WHERE `County Name` = 'Alameda'
SELECT CAST(`Free Meal Count (Ages 5-17)` AS REAL) / `Enrollment (Ages 5-17)` FROM frpm ORDER BY CAST(`Free Meal Count (Ages 5-17)` AS REAL) / `Enrollment (Ages 5-17)` ASC LIMIT 3
SELECT DISTINCT T1.Zip FROM schools AS T1 INNER JOIN frpm AS T2 ON T1.CDSCode = T2.CDSCode WHERE T2.`Charter School (Y/N)` = 1 AND T2.`District Name` = 'Fresno County Office of Education'
SELECT T2.MailStreet FROM frpm AS T1 INNER JOIN schools AS T2 ON T1.CDSCode = T2.CDSCode ORDER BY T1.`FRPM Count (K-12)` DESC LIMIT 1
SELECT DISTINCT T2.Phone FROM frpm AS T1 INNER JOIN schools AS T2 ON T1.CDSCode = T2.CDSCode WHERE T1.`Charter Funding Type` = 'Directly funded' AND T2.OpenDate > '2000-01-01'
SELECT COUNT(*) FROM satscores INNER JOIN schools ON satscores.cds = schools.CDSCode WHERE satscores.AvgScrMath < 400 AND schools.Virtual = 'F';
SELECT T2.School FROM satscores AS T1 INNER JOIN schools AS T2 ON T1.cds = T2.CDSCode WHERE T2.Magnet = 1 AND T1.NumTstTakr > 500
SELECT T2.Phone FROM satscores AS T1 INNER JOIN schools AS T2 ON T2.CDSCode = T1.cds WHERE T1.NumGE1500 > 1500 ORDER BY T1.NumGE1500 DESC LIMIT 1
SELECT T2.NumTstTakr FROM frpm AS T1 INNER JOIN satscores AS T2 ON T1.CDSCode = T2.cds ORDER BY T1.`FRPM Count (K-12)` DESC LIMIT 1
SELECT COUNT(T1.CDSCode) FROM frpm AS T1 INNER JOIN satscores AS T2 ON T1.CDSCode = T2.cds WHERE T1.`Charter Funding Type` = 'Directly funded' AND T2.AvgScrMath > 560
SELECT T2.`FRPM Count (Ages 5-17)` FROM satscores AS T1 INNER JOIN frpm AS T2 ON T1.cds = T2.CDSCode ORDER BY T1.AvgScrRead DESC LIMIT 1
SELECT CDSCode FROM frpm WHERE (`Enrollment (K-12)` + `Enrollment (Ages 5-17)`) > 500;
SELECT MAX(T2.`Percent (%) Eligible Free (Ages 5-17)`) AS HighestEligibleFreeRate FROM satscores AS T1 INNER JOIN frpm AS T2 ON T1.cds = T2.CDSCode WHERE CAST(T1.NumGE1500 AS REAL) / T1.NumTstTakr > 0.3;
SELECT T2.Phone FROM satscores AS T1 INNER JOIN schools AS T2 ON T1.cds = T2.CDSCode ORDER BY T1.NumGE1500 / T1.NumTstTakr DESC LIMIT 3
SELECT T1.NCESSchool FROM schools AS T1 INNER JOIN satscores AS T2 ON T1.CDSCode = T2.cds ORDER BY T2.enroll12 DESC LIMIT 5
SELECT T2.dname FROM schools AS T1 INNER JOIN satscores AS T2 ON T1.CDSCode = T2.cds WHERE T1.StatusType = 'Active' GROUP BY T2.dname ORDER BY AVG(T2.AvgScrRead) DESC LIMIT 1
SELECT COUNT(T1.cds) FROM satscores AS T1 INNER JOIN schools AS T2 ON T1.cds = T2.CDSCode WHERE T2.StatusType = 'Merged' AND T1.NumTstTakr < 100
SELECT DISTINCT T1.CharterNum FROM schools AS T1 INNER JOIN satscores AS T2 ON T1.CDSCode = T2.cds WHERE T2.AvgScrWrite = 499;
SELECT COUNT(T1.CDSCode) FROM schools AS T1 INNER JOIN satscores AS T2 ON T1.CDSCode = T2.cds WHERE T1.District = 'Contra Costa County Office of Education' AND T2.NumTstTakr <= 250
SELECT T1.Phone FROM schools AS T1 INNER JOIN satscores AS T2 ON T1.CDSCode = T2.cds ORDER BY T2.AvgScrMath DESC LIMIT 1
SELECT COUNT(*)  FROM frpm  WHERE `County Name` = 'Amador'    AND `Low Grade` = '9'    AND `High Grade` = '12';
SELECT COUNT(CDSCode) FROM frpm WHERE `Free Meal Count (K-12)` > 500 AND `FRPM Count (K-12)` < 700
SELECT sname FROM satscores WHERE cname = 'Contra Costa' ORDER BY NumTstTakr DESC LIMIT 1;
SELECT T1.`School Name`, T1.`Enrollment (K-12)`, T1.`Enrollment (Ages 5-17)`, T2.Street FROM frpm AS T1 INNER JOIN schools AS T2 ON T1.CDSCode = T2.CDSCode WHERE ABS(T1.`Enrollment (K-12)` - T1.`Enrollment (Ages 5-17)`) > 30
SELECT T1.School FROM schools AS T1 INNER JOIN frpm AS T2 ON T1.CDSCode = T2.CDSCode INNER JOIN satscores AS T3 ON T3.cds = T2.CDSCode WHERE T2.`Percent (%) Eligible Free (K-12)` > 0.1 AND T3.NumGE1500 > 1000
SELECT T1.sname, T2.`Charter Funding Type` FROM satscores AS T1 INNER JOIN frpm AS T2 ON T1.cds = T2.CDSCode WHERE T2.`District Name` LIKE 'Riverside%' GROUP BY T1.sname, T2.`Charter Funding Type` HAVING CAST(SUM(T1.AvgScrMath) AS REAL) / COUNT(T1.cds) > 400
SELECT DISTINCT T2.School, T2.Street, T2.City, T2.Zip, T2.State FROM frpm AS T1 INNER JOIN schools AS T2 ON T1.CDSCode = T2.CDSCode WHERE T2.County = 'Monterey' AND T1.`FRPM Count (Ages 5-17)` > 800 AND T1.`High Grade` = '12'
SELECT T1.School, T2.AvgScrWrite, T1.Phone FROM schools AS T1 INNER JOIN satscores AS T2 ON T2.cds = T1.CDSCode WHERE T1.OpenDate > '1991-01-01' OR T1.ClosedDate < '2000-01-01'
SELECT T2.School, T2.DOC FROM frpm AS T1 INNER JOIN schools AS T2 ON T1.CDSCode = T2.CDSCode WHERE T2.FundingType = 'Locally funded' AND (T1.`Enrollment (K-12)` - T1.`Enrollment (Ages 5-17)`) > (SELECT AVG(T3.`Enrollment (K-12)` - T3.`Enrollment (Ages 5-17)`) FROM frpm AS T3 INNER JOIN schools AS T4 ON T3.CDSCode = T4.CDSCode WHERE T4.FundingType = 'Locally funded')
SELECT T2.OpenDate FROM frpm AS T1 INNER JOIN schools AS T2 ON T1.CDSCode = T2.CDSCode WHERE T1.`Enrollment (K-12)` = ( SELECT MAX(T1.`Enrollment (K-12)`) FROM frpm AS T1 INNER JOIN schools AS T2 ON T1.CDSCode = T2.CDSCode WHERE T2.GSserved = 'K-12' )
SELECT schools.City FROM schools INNER JOIN satscores ON schools.CDSCode = satscores.cds ORDER BY satscores.enroll12 ASC LIMIT 5;
SELECT `Percent (%) Eligible Free (K-12)` FROM frpm ORDER BY `Enrollment (K-12)` DESC LIMIT 10, 2
SELECT T2.`FRPM Count (K-12)` / T2.`Enrollment (K-12)` FROM schools AS T1 INNER JOIN frpm AS T2 ON T1.CDSCode = T2.CDSCode WHERE T1.SOC = '66' ORDER BY T2.`FRPM Count (K-12)` DESC LIMIT 5
SELECT DISTINCT T2.Website, T2.School FROM frpm AS T1 INNER JOIN schools AS T2 ON T1.CDSCode = T2.CDSCode WHERE T1.`Free Meal Count (Ages 5-17)` BETWEEN 1900 AND 2000;
SELECT CAST(SUM(T2.`Free Meal Count (Ages 5-17)`) AS REAL) * 100 / SUM(T2.`Enrollment (Ages 5-17)`) FROM schools AS T1 INNER JOIN frpm AS T2 ON T1.CDSCode = T2.CDSCode WHERE T1.AdmFName1 = 'Kacey' AND T1.AdmLName1 = 'Gibson'
SELECT T2.AdmEmail1 FROM frpm AS T1 INNER JOIN schools AS T2 ON T1.CDSCode = T2.CDSCode WHERE T1.`Charter School (Y/N)` = 1 ORDER BY T1.`Enrollment (K-12)` ASC LIMIT 1
SELECT T2.AdmFName1, T2.AdmLName1 FROM satscores AS T1 INNER JOIN schools AS T2 ON T1.cds = T2.CDSCode ORDER BY T1.NumGE1500 DESC LIMIT 1;
SELECT T2.Street, T2.City, T2.Zip, T2.State FROM satscores AS T1 INNER JOIN schools AS T2 ON T1.cds = T2.CDSCode ORDER BY CAST(T1.NumGE1500 AS REAL) / T1.NumTstTakr ASC LIMIT 1
SELECT T2.Website FROM satscores AS T1 INNER JOIN schools AS T2 ON T1.cds = T2.CDSCode WHERE T1.NumTstTakr BETWEEN 2000 AND 3000 AND T2.County = 'Los Angeles'
SELECT AVG(T2.NumTstTakr) FROM schools AS T1 INNER JOIN satscores AS T2 ON T1.CDSCode = T2.cds WHERE T1.OpenDate BETWEEN '1980-01-01' AND '1980-12-31' AND T1.City = 'FRESNO'
SELECT T2.Phone FROM satscores AS T1 INNER JOIN schools AS T2 ON T1.cds = T2.CDSCode WHERE T2.District = 'Fresno Unified' AND T1.AvgScrRead IS NOT NULL ORDER BY T1.AvgScrRead ASC LIMIT 1
SELECT T1.School FROM schools AS T1 INNER JOIN satscores AS T2 ON T1.CDSCode = T2.cds WHERE T1.Virtual = 'F' ORDER BY T2.AvgScrRead DESC LIMIT 5;
SELECT T2.EdOpsName FROM satscores AS T1 INNER JOIN schools AS T2 ON T1.cds = T2.CDSCode ORDER BY T1.AvgScrMath DESC LIMIT 1;
SELECT T2.AvgScrMath, T1.County FROM schools AS T1 INNER JOIN satscores AS T2 ON T2.cds = T1.CDSCode GROUP BY T2.AvgScrMath ORDER BY T2.AvgScrMath + T2.AvgScrRead + T2.AvgScrWrite LIMIT 1
SELECT AVG(T2.AvgScrWrite) , T1.City FROM schools AS T1 INNER JOIN satscores AS T2 ON T1.CDSCode = T2.cds GROUP BY T2.NumGE1500 ORDER BY T2.NumGE1500 DESC LIMIT 1
SELECT T2.School, AVG(T1.AvgScrWrite) FROM satscores AS T1 INNER JOIN schools AS T2 ON T1.cds = T2.CDSCode WHERE T2.AdmFName1 = 'Ricci' AND T2.AdmLName1 = 'Ulrich'
SELECT T1.School FROM schools AS T1 INNER JOIN satscores AS T2 ON T1.CDSCode = T2.cds WHERE T1.DOC = 31 ORDER BY T2.enroll12 DESC LIMIT 1;
SELECT CAST(SUM(CASE WHEN STRFTIME('%Y', OpenDate) = '1980' THEN 1 ELSE 0 END) AS REAL) / 12 FROM schools WHERE DOC = 52
SELECT CAST(SUM(CASE WHEN DOC = 54 AND StatusType = 'Merged' THEN 1 ELSE 0 END) AS REAL) / SUM(CASE WHEN DOC = 52 AND StatusType = 'Merged' THEN 1 ELSE 0 END) FROM schools
SELECT County, School, ClosedDate FROM schools WHERE StatusType = 'Closed'
SELECT T2.Street, T2.School FROM satscores AS T1 INNER JOIN schools AS T2 ON T1.cds = T2.CDSCode ORDER BY T1.AvgScrMath DESC LIMIT 5, 1;
SELECT T2.MailStreet, T2.School FROM satscores AS T1 INNER JOIN schools AS T2 ON T1.cds = T2.CDSCode WHERE T1.AvgScrRead IS NOT NULL ORDER BY T1.AvgScrRead ASC LIMIT 1
SELECT COUNT(T1.cds) FROM satscores AS T1 INNER JOIN schools AS T2 ON T1.cds = T2.CDSCode WHERE T2.MailCity = 'Lakeport' AND (T1.AvgScrRead + T1.AvgScrMath + T1.AvgScrWrite) >= 1500
SELECT COUNT(T2.NumTstTakr) FROM schools AS T1 INNER JOIN satscores AS T2 ON T1.CDSCode = T2.cds WHERE T1.MailCity = 'Fresno'
SELECT School, MailZip FROM schools WHERE AdmFName1 = 'Avetik' AND AdmLName1 = 'Atoian'
SELECT      CAST(SUM(CASE WHEN County = 'Colusa' THEN 1 ELSE 0 END) AS REAL) /      SUM(CASE WHEN County = 'Humboldt' THEN 1 ELSE 0 END) AS Ratio FROM      schools WHERE      MailState = 'CA';
SELECT COUNT(CDSCode) FROM schools WHERE County = 'San Joaquin' AND StatusType = 'Active' AND MailState = 'CA'
SELECT T2.Phone, T2.Ext FROM satscores AS T1 INNER JOIN schools AS T2 ON T1.cds = T2.CDSCode ORDER BY T1.AvgScrWrite DESC LIMIT 332, 1
SELECT Phone, Ext, School FROM schools WHERE Zip = '95203-3704';
SELECT Website FROM schools WHERE (AdmFName1 = 'Mike' AND AdmLName1 = 'Larson')    OR (AdmFName1 = 'Dante' AND AdmLName1 = 'Alvarez');
SELECT Website FROM schools WHERE County = 'San Joaquin' AND Virtual = 'P' AND Charter = 1
SELECT COUNT(*)  FROM schools  WHERE Charter = 1    AND City = 'Hickman'    AND DOC = 52;
SELECT COUNT(T1.CDSCode) FROM frpm AS T1 INNER JOIN schools AS T2 ON T1.CDSCode = T2.CDSCode WHERE T2.County = 'Los Angeles' AND T1.`Charter School (Y/N)` = 0 AND CAST(T1.`Free Meal Count (K-12)` AS REAL) * 100 / T1.`Enrollment (K-12)` < 0.18
SELECT AdmFName1, AdmLName1, School, City FROM schools WHERE Charter = 1 AND CharterNum = '00D2'
SELECT COUNT(CharterNum) FROM schools WHERE MailCity = 'Hickman' AND CharterNum = '00D4'
SELECT      CAST(SUM(CASE WHEN T2.`Charter Funding Type` = 'Locally funded' THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(*) AS RatioInPercentage FROM      schools AS T1 INNER JOIN      frpm AS T2 ON      T1.CDSCode = T2.CDSCode WHERE      T1.County = 'Santa Clara' AND T1.Charter = 1;
SELECT COUNT(T1.CDSCode) FROM schools AS T1 INNER JOIN frpm AS T2 ON T1.CDSCode = T2.CDSCode WHERE T1.County = 'Stanislaus' AND T1.FundingType = 'Directly funded' AND T2.`Academic Year` BETWEEN '2000-2001' AND '2005-2006'
SELECT COUNT(City) FROM schools WHERE City = 'San Francisco' AND ClosedDate LIKE '1989%'
SELECT County FROM schools WHERE ClosedDate LIKE '198%' AND SOC = 11 GROUP BY County ORDER BY COUNT(County) DESC LIMIT 1
SELECT NCESDist  FROM schools  WHERE SOC = '31';
SELECT COUNT(DISTINCT CDSCode) FROM schools WHERE County = 'Alpine' AND SOCType = 'District Community Day Schools'
SELECT DISTINCT District  FROM schools  WHERE City = 'Fresno' AND Magnet = 0;
SELECT SUM(T2.`Enrollment (Ages 5-17)`) FROM schools AS T1 INNER JOIN frpm AS T2 ON T1.CDSCode = T2.CDSCode WHERE T1.EdOpsCode = 'SSS' AND T1.District = 'California School for the Deaf-Fremont (State Special Schools)'
SELECT SUM(T1.`FRPM Count (Ages 5-17)`) FROM frpm AS T1 INNER JOIN schools AS T2 ON T1.CDSCode = T2.CDSCode WHERE T2.MailStreet = 'PO Box 1040' AND T2.SOCType = 'Youth Authority Facilities (CEA)'
SELECT MIN(T1.`Low Grade`) FROM frpm AS T1 INNER JOIN schools AS T2 ON T1.CDSCode = T2.CDSCode WHERE T2.NCESDist = 613360 AND T2.EdOpsCode = 'SPECON'
SELECT DISTINCT schools.EILName, schools.School FROM frpm INNER JOIN schools ON frpm.CDSCode = schools.CDSCode WHERE frpm.`NSLP Provision Status` = 'Breakfast Provision 2'   AND frpm.`County Code` = '37';
SELECT T1.City FROM schools AS T1 INNER JOIN frpm AS T2 ON T1.CDSCode = T2.CDSCode WHERE T1.EILCode = 'HS' AND T2.`Low Grade` = 9 AND T2.`High Grade` = 12 AND T1.County = 'Merced' AND T2.`NSLP Provision Status` = 'Provision 2'
SELECT T2.School, CAST(T1.`Free Meal Count (Ages 5-17)` AS REAL) * 100 / T1.`Enrollment (Ages 5-17)` FROM frpm AS T1 INNER JOIN schools AS T2 ON T1.CDSCode = T2.CDSCode WHERE T2.County = 'Los Angeles' AND T2.GSserved = 'K-9'
SELECT GSserved FROM schools WHERE City = 'Adelanto' GROUP BY GSserved ORDER BY COUNT(GSserved) DESC LIMIT 1;
SELECT County, COUNT(*) AS SchoolCount FROM schools WHERE County IN ('San Diego', 'Santa Barbara') AND Virtual = 'F' GROUP BY County ORDER BY SchoolCount DESC LIMIT 1;
SELECT School, Latitude FROM schools ORDER BY Latitude DESC LIMIT 1
SELECT City, GSoffered, School FROM schools WHERE State = 'CA' ORDER BY Latitude LIMIT 1
SELECT GSoffered FROM schools ORDER BY Longitude DESC LIMIT 1
SELECT COUNT(City), City FROM schools WHERE Magnet = 1 AND GSserved = 'K-8' GROUP BY City
SELECT AdmFName1, District FROM schools GROUP BY AdmFName1 ORDER BY COUNT(AdmFName1) DESC LIMIT 2
SELECT T1.`Percent (%) Eligible Free (K-12)` * 100, T1.`District Code` FROM frpm AS T1 INNER JOIN schools AS T2 ON T1.CDSCode = T2.CDSCode WHERE T2.AdmFName1 = 'Alusine'
SELECT DISTINCT AdmLName1, District, County, School FROM schools WHERE CharterNum = 40;
SELECT AdmEmail1 FROM schools WHERE County = 'San Bernardino' AND District = 'San Bernardino City Unified' AND SOC = 62 AND DOC = 54 AND OpenDate BETWEEN '2009-01-01' AND '2010-12-31'
SELECT T2.AdmEmail1, T2.School FROM satscores AS T1 INNER JOIN schools AS T2 ON T1.cds = T2.CDSCode ORDER BY T1.NumGE1500 DESC LIMIT 1
SELECT COUNT(*)  FROM account  INNER JOIN district  ON account.district_id = district.district_id  WHERE account.frequency = 'POPLATEK PO OBRATU'    AND district.A3 = 'east Bohemia';
SELECT COUNT(T1.account_id) FROM account AS T1 INNER JOIN district AS T2 ON T1.district_id = T2.district_id WHERE T2.A3 = 'Prague'
SELECT AVG(A12), AVG(A13) FROM district
SELECT COUNT(district_id)  FROM district  WHERE A11 > 6000 AND A11 < 10000;
SELECT COUNT(*)  FROM client  INNER JOIN district  ON client.district_id = district.district_id  WHERE client.gender = 'M'    AND district.A3 = 'north Bohemia'    AND district.A11 > 8000;
SELECT T1.account_id, T2.A11 FROM disp AS T1 INNER JOIN district AS T2 ON T1.account_id = T2.district_id INNER JOIN client AS T3 ON T3.client_id = T1.client_id WHERE T3.gender = 'F' ORDER BY T3.birth_date DESC LIMIT 1
SELECT a.account_id FROM client c INNER JOIN district d ON c.district_id = d.district_id INNER JOIN account a ON c.district_id = a.district_id ORDER BY c.birth_date DESC, d.A11 DESC LIMIT 1;
SELECT COUNT(DISTINCT T1.client_id) FROM disp AS T1 INNER JOIN account AS T2 ON T1.account_id = T2.account_id WHERE T2.frequency = 'POPLATEK TYDNE' AND T1.type = 'OWNER'
SELECT disp.client_id FROM disp INNER JOIN account ON disp.account_id = account.account_id WHERE disp.type = 'DISPONENT' AND account.frequency = 'POPLATEK PO OBRATU';
SELECT T1.account_id FROM loan AS T1 INNER JOIN account AS T2 ON T1.account_id = T2.account_id WHERE T1.date LIKE '1997%' AND T2.frequency = 'POPLATEK TYDNE' ORDER BY T1.amount LIMIT 1
SELECT account_id FROM loan WHERE duration > 12 AND strftime('%Y', date) = '1993' ORDER BY amount DESC LIMIT 1
SELECT COUNT(T1.client_id) FROM client AS T1 INNER JOIN district AS T2 ON T1.district_id = T2.district_id WHERE T1.gender = 'F' AND T1.birth_date < '1950-01-01' AND T2.A2 = 'Sokolov'
SELECT account_id FROM trans WHERE STRFTIME('%Y', date) = '1995' ORDER BY date ASC LIMIT 1
SELECT DISTINCT T2.account_id FROM trans AS T1 INNER JOIN account AS T2 ON T1.account_id = T2.account_id WHERE STRFTIME('%Y', T2.date) < '1997' AND T1.amount > 3000
SELECT T1.client_id FROM client AS T1 INNER JOIN disp AS T2 ON T1.client_id = T2.client_id INNER JOIN card AS T3 ON T2.disp_id = T3.disp_id WHERE T3.issued = '1994-03-03'
SELECT DISTINCT account.date FROM account INNER JOIN trans ON account.account_id = trans.account_id WHERE trans.amount = 840 AND trans.date = '1998-10-14';
SELECT account.district_id FROM loan INNER JOIN account ON loan.account_id = account.account_id WHERE loan.date = '1994-08-25';
SELECT MAX(T3.amount) FROM card AS T1 INNER JOIN disp AS T2 ON T1.disp_id = T2.disp_id INNER JOIN trans AS T3 ON T2.account_id = T3.account_id WHERE T1.issued = '1996-10-21'
SELECT T1.gender FROM client AS T1 INNER JOIN district AS T2 ON T1.district_id = T2.district_id ORDER BY T1.birth_date LIMIT 1
SELECT T2.amount FROM loan AS T1 INNER JOIN trans AS T2 ON T1.account_id = T2.account_id WHERE T1.status = 'A' ORDER BY T1.amount DESC LIMIT 1
SELECT COUNT(client.client_id) FROM client INNER JOIN district ON client.district_id = district.district_id WHERE client.gender = 'F' AND district.A2 = 'Jesenik';
SELECT T2.disp_id FROM trans AS T1 INNER JOIN disp AS T2 ON T1.account_id = T2.account_id WHERE T1.amount = 5100 AND T1.date = '1998-09-02';
SELECT COUNT(*) AS account_count FROM account INNER JOIN district ON account.district_id = district.district_id WHERE district.A2 = 'Litomerice' AND account.date LIKE '96%';
SELECT T3.A2 FROM client AS T1 INNER JOIN disp AS T2 ON T1.client_id = T2.client_id INNER JOIN district AS T3 ON T1.district_id = T3.district_id WHERE T1.gender = 'F' AND T1.birth_date = '1976-01-29'
SELECT T2.birth_date FROM loan AS T1 INNER JOIN client AS T2 ON T1.account_id = T2.client_id WHERE T1.amount = 98832 AND T1.date = '1996-01-03'
SELECT account.account_id FROM account INNER JOIN district ON account.district_id = district.district_id WHERE district.A3 = 'Prague' ORDER BY account.date ASC LIMIT 1;
SELECT CAST(SUM(CASE WHEN T1.gender = 'M' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.client_id) FROM client AS T1 INNER JOIN district AS T2 ON T1.district_id = T2.district_id WHERE T2.A3 = 'south Bohemia'
SELECT CAST((T2.balance - T1.balance) AS REAL) * 100 / T1.balance FROM trans AS T1 INNER JOIN trans AS T2 ON T1.account_id = T2.account_id INNER JOIN account AS T3 ON T1.account_id = T3.account_id INNER JOIN loan AS T4 ON T3.account_id = T4.account_id WHERE T4.date = '1993-07-05' AND T1.date = '1993-03-22' AND T2.date = '1998-12-27'
SELECT CAST(SUM(CASE WHEN T1.status = 'A' THEN T1.amount ELSE 0 END) AS REAL) * 100 / SUM(T1.amount) FROM loan AS T1
SELECT CAST(SUM(CASE WHEN status = 'C' THEN amount ELSE 0 END) AS REAL) * 100 / SUM(amount) FROM loan WHERE amount < 100000
SELECT T1.account_id, T2.A2, T2.A3 FROM account AS T1 INNER JOIN district AS T2 ON T1.district_id = T2.district_id WHERE T1.frequency = 'POPLATEK PO OBRATU' AND T1.date LIKE '1993%'
SELECT T1.account_id, T1.frequency FROM account AS T1 INNER JOIN district AS T2 ON T1.district_id = T2.district_id WHERE T2.A3 = 'east Bohemia' AND T1.date LIKE '199%'
SELECT account.account_id, account.date FROM district INNER JOIN account ON district.district_id = account.district_id WHERE district.A2 = 'Prachatice';
SELECT T3.A2, T3.A3 FROM loan AS T1 INNER JOIN account AS T2 ON T1.account_id = T2.account_id INNER JOIN district AS T3 ON T2.district_id = T3.district_id WHERE T1.loan_id = 4990;
SELECT T1.account_id, T2.A2, T2.A3 FROM loan AS T1 INNER JOIN district AS T2 ON T1.account_id = T2.district_id WHERE T1.amount > 300000
SELECT T2.loan_id, T1.A3, T1.A11 FROM district AS T1 INNER JOIN loan AS T2 ON T1.district_id = T2.account_id WHERE T2.duration = 60
SELECT T2.A2, CAST((T2.A13 - T2.A12) AS REAL) * 100 / T2.A12 FROM loan AS T1 INNER JOIN district AS T2 ON T1.account_id = T2.district_id WHERE T1.status = 'D'
SELECT CAST(SUM(CASE WHEN T2.A2 = 'Decin' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.account_id) FROM account AS T1 INNER JOIN district AS T2 ON T1.district_id = T2.district_id WHERE STRFTIME('%Y', T1.date) = '1993'
SELECT account_id  FROM account  WHERE frequency = 'POPLATEK MESICNE';
SELECT T2.A2, COUNT(T1.client_id) FROM client AS T1 INNER JOIN district AS T2 ON T1.district_id = T2.district_id WHERE T1.gender = 'F' GROUP BY T2.district_id, T2.A2 ORDER BY COUNT(T1.client_id) DESC LIMIT 10
SELECT T2.A2 FROM trans AS T1 INNER JOIN district AS T2 ON T1.account_id = T2.district_id WHERE T1.type = 'VYDAJ' AND T1.date LIKE '1996-01%' ORDER BY T2.A2 DESC LIMIT 10
SELECT COUNT(T1.client_id) FROM client AS T1 INNER JOIN district AS T2 ON T1.district_id = T2.district_id WHERE T2.A3 = 'south Bohemia' AND T1.client_id NOT IN ( SELECT T1.client_id FROM client AS T1 INNER JOIN disp AS T2 ON T1.client_id = T2.client_id INNER JOIN card AS T3 ON T2.disp_id = T3.disp_id )
SELECT T2.A3 FROM account AS T1 INNER JOIN district AS T2 ON T1.district_id = T2.district_id INNER JOIN loan AS T3 ON T1.account_id = T3.account_id WHERE T3.status IN ('C', 'D') GROUP BY T2.A3 ORDER BY SUM(T3.amount) DESC LIMIT 1
SELECT AVG(T3.amount) FROM client AS T1 INNER JOIN disp AS T2 ON T1.client_id = T2.client_id INNER JOIN loan AS T3 ON T2.account_id = T3.account_id WHERE T1.gender = 'M';
SELECT district_id, A2  FROM district  ORDER BY A13 DESC;
SELECT COUNT(account_id) FROM account WHERE district_id = (SELECT district_id FROM district ORDER BY A16 DESC LIMIT 1)
SELECT COUNT(T1.account_id) FROM trans AS T1 INNER JOIN account AS T2 ON T1.account_id = T2.account_id WHERE T1.operation = 'VYBER KARTOU'   AND T1.balance < 0   AND T2.frequency = 'POPLATEK MESICNE';
SELECT COUNT(DISTINCT T1.account_id) FROM loan AS T1 INNER JOIN account AS T2 ON T1.account_id = T2.account_id WHERE T2.frequency = 'POPLATEK MESICNE' AND T1.amount >= 250000 AND T1.date BETWEEN '1995-01-01' AND '1997-12-31'
SELECT COUNT(account_id) FROM loan WHERE status = 'C' OR status = 'D' AND account_id IN ( SELECT account_id FROM account WHERE district_id = 1 )
SELECT COUNT(T1.client_id) FROM client AS T1 INNER JOIN district AS T2 ON T1.district_id = T2.district_id ORDER BY T2.A15 DESC LIMIT 1
SELECT COUNT(*) FROM card AS T1 INNER JOIN disp AS T2 ON T1.disp_id = T2.disp_id WHERE T1.type = 'gold' AND T2.type = 'DISPONENT'
SELECT COUNT(T1.account_id) FROM account AS T1 INNER JOIN district AS T2 ON T1.district_id = T2.district_id WHERE T2.A2 = 'Pisek';
SELECT DISTINCT T2.district_id FROM trans AS T1 INNER JOIN account AS T2 ON T1.account_id = T2.account_id WHERE T1.amount > 10000 AND STRFTIME('%Y', T1.date) = '1997'
SELECT account_id FROM `order` WHERE k_symbol = 'SIPO'
SELECT T1.account_id FROM disp AS T1 INNER JOIN card AS T2 ON T1.disp_id = T2.disp_id WHERE T2.type = 'junior' OR T2.type = 'gold'
SELECT AVG(amount) FROM trans WHERE STRFTIME('%Y', date) = '2021' AND operation = 'VYBER KARTOU'
SELECT T1.account_id FROM trans AS T1 INNER JOIN account AS T2 ON T1.account_id = T2.account_id WHERE STRFTIME('%Y', T1.date) = '1998' AND T1.operation = 'VYBER KARTOU' AND T1.amount < (SELECT AVG(amount) FROM trans WHERE STRFTIME('%Y', date) = '1998')
SELECT DISTINCT T1.client_id FROM client AS T1 INNER JOIN disp AS T2 ON T1.client_id = T2.client_id INNER JOIN card AS T3 ON T2.disp_id = T3.disp_id INNER JOIN loan AS T4 ON T2.account_id = T4.account_id WHERE T1.gender = 'F'
SELECT COUNT(client.client_id) FROM client INNER JOIN district ON client.district_id = district.district_id WHERE client.gender = 'F' AND district.A3 = 'south Bohemia';
SELECT T1.account_id FROM account AS T1 INNER JOIN disp AS T2 ON T1.account_id = T2.account_id INNER JOIN district AS T3 ON T2.account_id = T3.district_id WHERE T3.A2 = 'Tabor' AND T2.type = 'OWNER'
SELECT DISTINCT disp.type FROM disp INNER JOIN account ON disp.account_id = account.account_id INNER JOIN district ON account.district_id = district.district_id WHERE disp.type != 'OWNER'   AND district.A11 > 8000   AND district.A11 <= 9000;
SELECT COUNT(DISTINCT T1.account_id) FROM account AS T1 INNER JOIN district AS T2 ON T1.district_id = T2.district_id INNER JOIN trans AS T3 ON T1.account_id = T3.account_id WHERE T2.A3 = 'North Bohemia' AND T3.bank = 'AB'
SELECT DISTINCT district.A2 FROM district INNER JOIN account ON district.district_id = account.district_id INNER JOIN trans ON account.account_id = trans.account_id WHERE trans.type = 'VYDAJ';
SELECT CAST(SUM(T1.A15) AS REAL) / COUNT(T1.A15) FROM district AS T1 INNER JOIN account AS T2 ON T1.district_id = T2.district_id WHERE T1.A15 > 4000 AND strftime('%Y', T2.date) = '1997'
SELECT COUNT(*)  FROM card  INNER JOIN disp ON card.disp_id = disp.disp_id  WHERE card.type = 'classic' AND disp.type = 'OWNER';
SELECT COUNT(client.client_id) FROM client INNER JOIN district ON client.district_id = district.district_id WHERE client.gender = 'M' AND district.A2 = 'Hl.m. Praha';
SELECT CAST(SUM(type = 'gold') AS REAL) * 100 / COUNT(card_id) FROM card WHERE STRFTIME('%Y', issued) < '1998'
SELECT T2.client_id FROM loan AS T1 INNER JOIN disp AS T2 ON T1.account_id = T2.account_id ORDER BY T1.amount DESC LIMIT 1
SELECT T2.A15 FROM account AS T1 INNER JOIN district AS T2 ON T1.district_id = T2.district_id WHERE T1.account_id = 532
SELECT account.district_id FROM `order` INNER JOIN account ON `order`.account_id = account.account_id WHERE `order`.order_id = 33333;
SELECT COUNT(*) FROM trans AS T1 INNER JOIN account AS T2 ON T1.account_id = T2.account_id INNER JOIN disp AS T3 ON T2.account_id = T3.account_id INNER JOIN client AS T4 ON T3.client_id = T4.client_id WHERE T4.client_id = 3356 AND T1.operation = 'VYBER'
SELECT COUNT(DISTINCT T1.account_id) FROM account AS T1 INNER JOIN loan AS T2 ON T1.account_id = T2.account_id WHERE T1.frequency = 'POPLATEK TYDNE' AND T2.amount < 200000
SELECT card.type FROM client INNER JOIN disp ON client.client_id = disp.client_id INNER JOIN card ON disp.disp_id = card.disp_id WHERE client.client_id = 13539;
SELECT T2.A3 FROM client AS T1 INNER JOIN district AS T2 ON T1.district_id = T2.district_id WHERE T1.client_id = 3541;
SELECT T2.district_id FROM loan AS T1 INNER JOIN account AS T2 ON T1.account_id = T2.account_id WHERE T1.status = 'A' GROUP BY T2.district_id ORDER BY COUNT(T1.loan_id) DESC LIMIT 1
SELECT T2.client_id FROM `order` AS T1 INNER JOIN disp AS T2 ON T1.account_id = T2.account_id WHERE T1.order_id = 32423;
SELECT T1.* FROM trans AS T1 INNER JOIN account AS T2 ON T1.account_id = T2.account_id WHERE T2.district_id = 5
SELECT COUNT(account_id) FROM account WHERE district_id = ( SELECT district_id FROM district WHERE A3 = 'Jesenik' )
SELECT T3.client_id FROM card AS T1 INNER JOIN disp AS T2 ON T1.disp_id = T2.disp_id INNER JOIN client AS T3 ON T2.client_id = T3.client_id WHERE T1.type = 'junior' AND T1.issued > '1996-12-31'
SELECT CAST(COUNT(T1.client_id) AS REAL) * 100 / ( SELECT COUNT(T1.client_id) FROM client AS T1 INNER JOIN account AS T2 ON T1.client_id = T2.account_id INNER JOIN district AS T3 ON T2.district_id = T3.district_id WHERE T3.A11 > 10000 ) FROM client AS T1 INNER JOIN account AS T2 ON T1.client_id = T2.account_id INNER JOIN district AS T3 ON T2.district_id = T3.district_id WHERE T3.A11 > 10000 AND T1.gender = 'F'
SELECT CAST((SUM(CASE WHEN STRFTIME('%Y', T1.date) = '1997' THEN T1.amount ELSE 0 END) - SUM(CASE WHEN STRFTIME('%Y', T1.date) = '1996' THEN T1.amount ELSE 0 END)) AS REAL) * 100 / SUM(CASE WHEN STRFTIME('%Y', T1.date) = '1996' THEN T1.amount ELSE 0 END) FROM loan AS T1 INNER JOIN account AS T2 ON T1.account_id = T2.account_id INNER JOIN disp AS T3 ON T3.account_id = T2.account_id INNER JOIN client AS T4 ON T4.client_id = T3.client_id WHERE T4.gender = 'M' AND T3.type = 'OWNER'
SELECT COUNT(*)  FROM trans  WHERE operation = 'VYBER KARTOU'    AND date > '1995-01-01';
SELECT SUM(IIF(A3 = 'North Bohemia', A16, 0)) - SUM(IIF(A3 = 'East Bohemia', A16, 0)) FROM district
SELECT COUNT(DISTINCT type) FROM disp WHERE account_id BETWEEN 1 AND 10
SELECT COUNT(DISTINCT CASE WHEN k_symbol = 'SLUZBY' THEN order_id ELSE NULL END), k_symbol FROM `order` WHERE account_id = 3
SELECT SUBSTR(birth_date, 1, 4) AS year_of_birth FROM client WHERE client_id = 130;
SELECT COUNT(T1.account_id) FROM account AS T1 INNER JOIN disp AS T2 ON T1.account_id = T2.account_id INNER JOIN trans AS T3 ON T1.account_id = T3.account_id WHERE T1.frequency = 'POPLATEK PO OBRATU' AND T2.type = 'OWNER'
SELECT T1.amount, T1.status FROM loan AS T1 INNER JOIN account AS T2 ON T1.account_id = T2.account_id INNER JOIN disp AS T3 ON T2.account_id = T3.account_id WHERE T3.client_id = 992
SELECT      SUM(trans.balance) AS total_balance,      client.gender  FROM      trans INNER JOIN      account ON trans.account_id = account.account_id INNER JOIN      disp ON account.account_id = disp.account_id INNER JOIN      client ON disp.client_id = client.client_id WHERE      trans.trans_id = 851      AND client.client_id = 4;
SELECT card.type FROM client INNER JOIN disp ON client.client_id = disp.client_id INNER JOIN card ON disp.disp_id = card.disp_id WHERE client.client_id = 9;
SELECT SUM(T2.amount) FROM disp AS T1 INNER JOIN trans AS T2 ON T1.account_id = T2.account_id WHERE T1.client_id = 617 AND T2.date LIKE '1998%'
SELECT T1.client_id, T3.account_id FROM client AS T1 INNER JOIN district AS T2 ON T1.district_id = T2.district_id INNER JOIN account AS T3 ON T2.district_id = T3.district_id WHERE T2.A3 = 'east Bohemia' AND STRFTIME('%Y', T1.birth_date) BETWEEN '1983' AND '1987'
SELECT T1.client_id FROM client AS T1 INNER JOIN loan AS T2 ON T1.client_id = T2.account_id WHERE T1.gender = 'F' ORDER BY T2.amount DESC LIMIT 3
SELECT COUNT(*) FROM client INNER JOIN disp ON client.client_id = disp.client_id INNER JOIN account ON disp.account_id = account.account_id INNER JOIN `order` ON account.account_id = `order`.account_id WHERE client.gender = 'M'   AND client.birth_date BETWEEN '1974-01-01' AND '1976-12-31'   AND `order`.k_symbol = 'SIPO'   AND `order`.amount > 4000;
SELECT COUNT(*)  FROM account  INNER JOIN district  ON account.district_id = district.district_id  WHERE district.A2 = 'Beroun'    AND STRFTIME('%Y', account.date) > '1996';
SELECT COUNT(T1.client_id) FROM client AS T1 INNER JOIN disp AS T2 ON T1.client_id = T2.client_id INNER JOIN card AS T3 ON T2.disp_id = T3.disp_id WHERE T1.gender = 'F' AND T3.type = 'junior'
SELECT CAST(COUNT(T1.client_id) AS REAL) * 100 / ( SELECT COUNT(DISTINCT T1.client_id) FROM client AS T1 INNER JOIN account AS T2 ON T1.client_id = T2.account_id INNER JOIN district AS T3 ON T2.district_id = T3.district_id WHERE T3.A3 = 'Prague' ) FROM client AS T1 INNER JOIN account AS T2 ON T1.client_id = T2.account_id INNER JOIN district AS T3 ON T2.district_id = T3.district_id WHERE T1.gender = 'F' AND T3.A3 = 'Prague'
SELECT CAST(SUM(T1.gender = 'M') AS REAL) * 100 / COUNT(T1.client_id) FROM client AS T1 INNER JOIN account AS T2 ON T1.district_id = T2.district_id WHERE T2.frequency = 'POPLATEK TYDNE'
SELECT COUNT(DISTINCT T2.client_id) FROM account AS T1 INNER JOIN disp AS T2 ON T1.account_id = T2.account_id WHERE T1.frequency = 'POPLATEK TYDNE' AND T2.type = 'USER'
SELECT account_id FROM loan WHERE duration > 24 AND date < '1997-01-01' ORDER BY amount LIMIT 1
SELECT T1.account_id FROM account AS T1 INNER JOIN client AS T2 ON T1.district_id = T2.district_id INNER JOIN district AS T3 ON T2.district_id = T3.district_id WHERE T2.gender = 'F' ORDER BY T2.birth_date, T3.A11 LIMIT 1
SELECT COUNT(T1.client_id) FROM client AS T1 INNER JOIN district AS T2 ON T1.district_id = T2.district_id WHERE T1.birth_date LIKE '%1920%' AND T2.A3 = 'east Bohemia'
SELECT COUNT(DISTINCT T1.account_id) FROM loan AS T1 INNER JOIN account AS T2 ON T1.account_id = T2.account_id WHERE T1.duration = 24 AND T2.frequency = 'POPLATEK TYDNE'
SELECT AVG(loan.amount) FROM loan INNER JOIN account ON loan.account_id = account.account_id WHERE loan.status IN ('C', 'D') AND account.frequency = 'POPLATEK PO OBRATU';
SELECT client_id, district_id FROM client WHERE client_id IN ( SELECT client_id FROM disp WHERE type = 'OWNER' )
SELECT T1.client_id, T1.birth_date FROM client AS T1 INNER JOIN disp AS T2 ON T1.client_id = T2.client_id INNER JOIN card AS T3 ON T2.disp_id = T3.disp_id WHERE T3.type = 'gold'
SELECT bond_type  FROM bond  GROUP BY bond_type  ORDER BY COUNT(bond_type) DESC  LIMIT 1;
SELECT COUNT(DISTINCT T1.molecule_id) FROM molecule AS T1 INNER JOIN atom AS T2 ON T1.molecule_id = T2.molecule_id WHERE T2.element = 'cl' AND T1.label = '-'
SELECT AVG(CASE WHEN atom.element = 'o' THEN 1 ELSE 0 END) AS avg_oxygen_atoms FROM atom INNER JOIN connected ON atom.atom_id = connected.atom_id INNER JOIN bond ON connected.bond_id = bond.bond_id WHERE bond.bond_type = '-';
SELECT CAST(SUM(CASE WHEN T2.bond_type = '-' THEN 1 ELSE 0 END) AS REAL) / COUNT(T2.bond_id) AS average_single_bonded FROM molecule AS T1 INNER JOIN bond AS T2 ON T1.molecule_id = T2.molecule_id WHERE T1.label = '+';
SELECT COUNT(DISTINCT T2.molecule_id) FROM atom AS T1 INNER JOIN molecule AS T2 ON T1.molecule_id = T2.molecule_id WHERE T1.element = 'na' AND T2.label = '-';
SELECT DISTINCT T1.molecule_id FROM bond AS T1 INNER JOIN molecule AS T2 ON T1.molecule_id = T2.molecule_id WHERE T1.bond_type = '#' AND T2.label = '+'
SELECT CAST(SUM(CASE WHEN T1.element = 'c' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.atom_id) FROM atom AS T1 INNER JOIN connected AS T2 ON T1.atom_id = T2.atom_id INNER JOIN bond AS T3 ON T2.bond_id = T3.bond_id
SELECT COUNT(*)  FROM bond  WHERE bond_type = '#';
SELECT COUNT(*) FROM atom WHERE element != 'br'
SELECT COUNT(T.molecule_id) FROM molecule AS T WHERE molecule_id BETWEEN 'TR000' AND 'TR099' AND T.label = '+'
SELECT molecule_id FROM atom WHERE element = 'si'
SELECT      a1.element,      a2.element  FROM      connected AS c INNER JOIN      atom AS a1  ON      c.atom_id = a1.atom_id INNER JOIN      atom AS a2  ON      c.atom_id2 = a2.atom_id WHERE      c.bond_id = 'TR004_8_9';
SELECT DISTINCT a1.element FROM bond b INNER JOIN connected c ON b.bond_id = c.bond_id INNER JOIN atom a1 ON c.atom_id = a1.atom_id WHERE b.bond_type = '='  UNION  SELECT DISTINCT a2.element FROM bond b INNER JOIN connected c ON b.bond_id = c.bond_id INNER JOIN atom a2 ON c.atom_id2 = a2.atom_id WHERE b.bond_type = '=';
SELECT T2.label FROM atom AS T1 INNER JOIN molecule AS T2 ON T1.molecule_id = T2.molecule_id WHERE T1.element = 'h' GROUP BY T2.label ORDER BY COUNT(T2.label) DESC LIMIT 1
SELECT DISTINCT bond.bond_type FROM atom INNER JOIN connected ON atom.atom_id = connected.atom_id INNER JOIN bond ON connected.bond_id = bond.bond_id WHERE atom.element = 'te';
SELECT T1.atom_id, T1.atom_id2 FROM connected AS T1 INNER JOIN bond AS T2 ON T1.bond_id = T2.bond_id WHERE T2.bond_type = '-';
SELECT DISTINCT T1.atom_id, T1.atom_id2 FROM connected AS T1 INNER JOIN bond AS T2 ON T1.bond_id = T2.bond_id INNER JOIN molecule AS T3 ON T2.molecule_id = T3.molecule_id WHERE T3.label = '-';
SELECT T2.element FROM molecule AS T1 INNER JOIN atom AS T2 ON T1.molecule_id = T2.molecule_id WHERE T1.label = '-' GROUP BY T2.element ORDER BY COUNT(T2.element) LIMIT 1
SELECT T1.bond_type FROM bond AS T1 INNER JOIN connected AS T2 ON T1.bond_id = T2.bond_id WHERE T2.atom_id = 'TR004_8' AND T2.atom_id2 = 'TR004_20'
SELECT DISTINCT label FROM molecule WHERE molecule_id NOT IN (     SELECT molecule_id     FROM atom     WHERE element = 'sn' );
SELECT COUNT(T1.molecule_id) FROM atom AS T1 INNER JOIN connected AS T2 ON T1.atom_id = T2.atom_id INNER JOIN bond AS T3 ON T2.bond_id = T3.bond_id WHERE T1.element IN ('i', 's') AND T3.bond_type = '-'
SELECT T1.atom_id, T1.atom_id2 FROM connected AS T1 INNER JOIN bond AS T2 ON T1.bond_id = T2.bond_id WHERE T2.bond_type = '#';
SELECT T1.atom_id FROM atom AS T1 INNER JOIN connected AS T2 ON T1.atom_id = T2.atom_id INNER JOIN bond AS T3 ON T2.bond_id = T3.bond_id WHERE T3.molecule_id = 'TR181'
SELECT CAST(COUNT(DISTINCT CASE WHEN T1.molecule_id NOT IN (SELECT molecule_id FROM atom WHERE element = 'f') THEN T1.molecule_id ELSE NULL END) AS REAL) * 100 / COUNT(DISTINCT T1.molecule_id) FROM molecule AS T1 WHERE T1.label = '+'
SELECT CAST(SUM(CASE WHEN T2.bond_type = '#' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM molecule AS T1 INNER JOIN bond AS T2 ON T1.molecule_id = T2.molecule_id WHERE T1.label = '+'
SELECT DISTINCT element FROM atom WHERE molecule_id = 'TR000' ORDER BY element LIMIT 3
SELECT atom_id, atom_id2 FROM connected WHERE bond_id = 'TR001_2_6'
SELECT SUM(IIF(label = '+', 1, 0)) - SUM(IIF(label = '-', 1, 0)) FROM molecule
SELECT atom_id, atom_id2 FROM connected WHERE bond_id = 'TR000_2_5'
SELECT bond_id  FROM connected  WHERE atom_id2 = 'TR000_2';
SELECT DISTINCT T.molecule_id FROM bond AS T WHERE T.bond_type = '=' ORDER BY T.molecule_id LIMIT 5
SELECT CAST(SUM(IIF(bond_type = '=', 1, 0)) AS REAL) * 100 / COUNT(molecule_id) FROM bond WHERE molecule_id = 'TR008'
SELECT CAST(SUM(IIF(label = '+', 1, 0)) AS REAL) * 100 / COUNT(molecule_id) FROM molecule
SELECT CAST(SUM(CASE WHEN element = 'h' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM atom WHERE molecule_id = 'TR206'
SELECT DISTINCT T.bond_type FROM bond AS T WHERE T.molecule_id = 'TR000'
SELECT DISTINCT atom.element, molecule.label FROM atom INNER JOIN molecule ON atom.molecule_id = molecule.molecule_id WHERE molecule.molecule_id = 'TR060';
SELECT T.bond_type, IIF(M.label = '+', 'YES', 'NO') AS carcinogenic FROM (   SELECT bond_type   FROM bond   WHERE molecule_id = 'TR018'   GROUP BY bond_type   ORDER BY COUNT(bond_id) DESC   LIMIT 1 ) AS T INNER JOIN molecule AS M ON M.molecule_id = 'TR018'
SELECT DISTINCT T1.molecule_id FROM molecule AS T1 INNER JOIN bond AS T2 ON T1.molecule_id = T2.molecule_id WHERE T1.label = '-' AND T2.bond_type = '-' ORDER BY T1.molecule_id LIMIT 3;
SELECT DISTINCT bond_id FROM bond WHERE molecule_id = 'TR006' ORDER BY bond_id LIMIT 2
SELECT COUNT(bond_id) FROM connected WHERE atom_id = 'TR009_12' OR atom_id2 = 'TR009_12'
SELECT COUNT(DISTINCT molecule.molecule_id) FROM molecule INNER JOIN atom ON molecule.molecule_id = atom.molecule_id WHERE molecule.label = '+' AND atom.element = 'br';
SELECT T1.bond_type, T2.atom_id, T2.atom_id2 FROM bond AS T1 INNER JOIN connected AS T2 ON T1.bond_id = T2.bond_id WHERE T2.bond_id = 'TR001_6_9'
SELECT T2.molecule_id , IIF(T2.label = '+', 'YES', 'NO') AS flag_carcinogenic FROM atom AS T1 INNER JOIN molecule AS T2 ON T1.molecule_id = T2.molecule_id WHERE T1.atom_id = 'TR001_10'
SELECT COUNT(*)  FROM bond  WHERE bond_type = '#';
SELECT COUNT(T.bond_id) FROM connected AS T WHERE SUBSTR(T.atom_id, -2) = '19'
SELECT element FROM atom WHERE molecule_id = 'TR004'
SELECT COUNT(*)  FROM molecule  WHERE label = '-';
SELECT DISTINCT T1.molecule_id FROM molecule AS T1 INNER JOIN atom AS T2 ON T1.molecule_id = T2.molecule_id WHERE T2.atom_id LIKE 'TR000_2%' AND T1.label = '+'
SELECT T1.bond_id FROM connected AS T1 INNER JOIN atom AS T2 ON T1.atom_id = T2.atom_id WHERE T2.element = 'p' INTERSECT SELECT T1.bond_id FROM connected AS T1 INNER JOIN atom AS T2 ON T1.atom_id2 = T2.atom_id WHERE T2.element = 'n'
SELECT CASE WHEN SUM(CASE WHEN T2.bond_type = ' = ' THEN 1 ELSE 0 END) > 0 THEN '+' ELSE '-' END AS label FROM molecule AS T1 INNER JOIN bond AS T2 ON T1.molecule_id = T2.molecule_id
SELECT CAST(COUNT(T2.bond_id) AS REAL) / COUNT(DISTINCT T1.atom_id) AS average_bonds FROM atom AS T1 INNER JOIN connected AS T2     ON T1.atom_id = T2.atom_id WHERE T1.element = 'i';
SELECT DISTINCT b.bond_type, b.bond_id FROM atom AS a INNER JOIN connected AS c ON a.atom_id = c.atom_id INNER JOIN bond AS b ON c.bond_id = b.bond_id WHERE SUBSTR(a.atom_id, 7, 2) = '45';
SELECT element FROM atom WHERE atom_id NOT IN ( SELECT atom_id FROM connected )
SELECT connected.atom_id, connected.atom_id2 FROM bond INNER JOIN connected ON bond.bond_id = connected.bond_id WHERE bond.molecule_id = 'TR447' AND bond.bond_type = '#';
SELECT DISTINCT a.element FROM bond b INNER JOIN connected c ON b.bond_id = c.bond_id INNER JOIN atom a ON c.atom_id = a.atom_id OR c.atom_id2 = a.atom_id WHERE b.bond_id = 'TR144_8_19';
SELECT m.molecule_id FROM molecule AS m INNER JOIN bond AS b ON m.molecule_id = b.molecule_id WHERE m.label = '+' AND b.bond_type = '=' GROUP BY m.molecule_id ORDER BY COUNT(b.bond_id) DESC LIMIT 1;
SELECT T2.element FROM molecule AS T1 INNER JOIN atom AS T2 ON T1.molecule_id = T2.molecule_id WHERE T1.label = '+' GROUP BY T2.element ORDER BY COUNT(T2.element) LIMIT 1
SELECT T2.atom_id2 FROM atom AS T1 INNER JOIN connected AS T2 ON T1.atom_id = T2.atom_id WHERE T1.element = 'pb' UNION SELECT T2.atom_id FROM atom AS T1 INNER JOIN connected AS T2 ON T1.atom_id = T2.atom_id2 WHERE T1.element = 'pb'
SELECT DISTINCT atom.element FROM bond INNER JOIN connected ON bond.bond_id = connected.bond_id INNER JOIN atom ON connected.atom_id = atom.atom_id WHERE bond.bond_type = '#';
SELECT CAST(COUNT(T2.bond_id) AS REAL) * 100 / ( SELECT COUNT(T1.atom_id) FROM atom AS T1 INNER JOIN connected AS T2 ON T1.atom_id = T2.atom_id INNER JOIN bond AS T3 ON T2.bond_id = T3.bond_id WHERE T1.element = 'c' AND T1.element = 'cl' ) FROM atom AS T1 INNER JOIN connected AS T2 ON T1.atom_id = T2.atom_id INNER JOIN bond AS T3 ON T2.bond_id = T3.bond_id WHERE T1.element = 'c' AND T1.element = 'cl'
SELECT      CAST(SUM(CASE WHEN M.label = '+' THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(*) AS proportion FROM      bond B INNER JOIN      molecule M ON      B.molecule_id = M.molecule_id WHERE      B.bond_type = '-';
SELECT COUNT(*) FROM atom WHERE element IN ('c', 'h')
SELECT atom_id2 FROM connected WHERE atom_id IN ( SELECT atom_id FROM atom WHERE element = 's' )
SELECT DISTINCT bond.bond_type FROM atom INNER JOIN connected ON atom.atom_id = connected.atom_id INNER JOIN bond ON connected.bond_id = bond.bond_id WHERE atom.element = 'sn';
SELECT COUNT(DISTINCT T2.element) FROM bond AS T1 INNER JOIN atom AS T2 ON T1.molecule_id = T2.molecule_id WHERE T1.bond_type = '-'
SELECT COUNT(T1.molecule_id) FROM molecule AS T1 INNER JOIN atom AS T2 ON T1.molecule_id = T2.molecule_id INNER JOIN bond AS T3 ON T2.molecule_id = T3.molecule_id WHERE T3.bond_type = '#' AND T2.element IN ('p', 'br')
SELECT DISTINCT T1.bond_id FROM bond AS T1 INNER JOIN molecule AS T2 ON T1.molecule_id = T2.molecule_id WHERE T2.label = '+'
SELECT DISTINCT molecule.molecule_id FROM molecule INNER JOIN bond ON molecule.molecule_id = bond.molecule_id WHERE bond.bond_type = '-' AND molecule.label = '-';
SELECT CAST(SUM(IIF(T1.element = 'cl', 1, 0)) AS REAL) * 100 / COUNT(T1.atom_id) FROM atom AS T1 INNER JOIN bond AS T2 ON T1.molecule_id = T2.molecule_id WHERE T2.bond_type = '-'
SELECT molecule_id, label FROM molecule WHERE molecule_id IN ('TR000', 'TR001', 'TR002')
SELECT molecule_id FROM molecule WHERE label = '-'
SELECT COUNT(T.molecule_id) FROM molecule AS T WHERE T.molecule_id BETWEEN 'TR000' AND 'TR030' AND T.label = '+'
SELECT DISTINCT bond_type  FROM bond  WHERE molecule_id BETWEEN 'TR000' AND 'TR050';
SELECT      a1.element,      a2.element  FROM      connected AS c INNER JOIN      atom AS a1  ON      c.atom_id = a1.atom_id INNER JOIN      atom AS a2  ON      c.atom_id2 = a2.atom_id WHERE      c.bond_id = 'TR001_10_11';
SELECT COUNT(DISTINCT T1.bond_id) FROM connected AS T1 INNER JOIN atom AS T2 ON T1.atom_id = T2.atom_id WHERE T2.element = 'i'
SELECT      CASE          WHEN SUM(CASE WHEN T2.label = '+' THEN 1 ELSE 0 END) >               SUM(CASE WHEN T2.label = '-' THEN 1 ELSE 0 END)          THEN 'Carcinogenic'          ELSE 'Non-Carcinogenic'      END AS result FROM      atom AS T1 INNER JOIN      molecule AS T2  ON      T1.molecule_id = T2.molecule_id WHERE      T1.element = 'ca';
SELECT DISTINCT CASE      WHEN (T3.element = 'cl' AND T4.element = 'c') OR (T3.element = 'c' AND T4.element = 'cl') THEN 1      ELSE 0  END AS has_chlorine_and_carbon FROM bond AS T1 INNER JOIN connected AS T2 ON T1.bond_id = T2.bond_id INNER JOIN atom AS T3 ON T2.atom_id = T3.atom_id INNER JOIN atom AS T4 ON T2.atom_id2 = T4.atom_id WHERE T1.bond_id = 'TR001_1_8';
SELECT T1.molecule_id FROM atom AS T1 INNER JOIN connected AS T2 ON T1.atom_id = T2.atom_id INNER JOIN bond AS T3 ON T2.bond_id = T3.bond_id INNER JOIN molecule AS T4 ON T1.molecule_id = T4.molecule_id WHERE T1.element = 'c' AND T3.bond_type = '#' AND T4.label = '-'
SELECT CAST(SUM(CASE WHEN T2.element = 'cl' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM molecule AS T1 INNER JOIN atom AS T2 ON T1.molecule_id = T2.molecule_id WHERE T1.label = '+'
SELECT element FROM atom WHERE molecule_id = 'TR001'
SELECT molecule_id FROM bond WHERE bond_type = '='
SELECT T2.atom_id, T2.atom_id2 FROM bond AS T1 INNER JOIN connected AS T2 ON T1.bond_id = T2.bond_id WHERE T1.bond_type = '#'
SELECT DISTINCT a1.element FROM bond b INNER JOIN connected c ON b.bond_id = c.bond_id INNER JOIN atom a1 ON c.atom_id = a1.atom_id WHERE b.bond_id = 'TR005_16_26'  UNION  SELECT DISTINCT a2.element FROM bond b INNER JOIN connected c ON b.bond_id = c.bond_id INNER JOIN atom a2 ON c.atom_id2 = a2.atom_id WHERE b.bond_id = 'TR005_16_26';
SELECT COUNT(DISTINCT T2.molecule_id) FROM bond AS T1 INNER JOIN molecule AS T2 ON T1.molecule_id = T2.molecule_id WHERE T2.label = '-' AND T1.bond_type = '-'
SELECT T2.label FROM bond AS T1 INNER JOIN molecule AS T2 ON T1.molecule_id = T2.molecule_id WHERE T1.bond_id = 'TR001_10_11'
SELECT T1.bond_id, T2.label FROM bond AS T1 INNER JOIN molecule AS T2 ON T1.molecule_id = T2.molecule_id WHERE T1.bond_type = '#'
SELECT element FROM atom WHERE atom_id LIKE '%_4' AND molecule_id IN ( SELECT molecule_id FROM molecule WHERE label = '+' )
SELECT CAST(SUM(IIF(T1.element = 'h', 1, 0)) AS REAL) / COUNT(T1.element) , T2.label FROM atom AS T1 INNER JOIN molecule AS T2 ON T1.molecule_id = T2.molecule_id WHERE T1.molecule_id = 'TR006'
SELECT DISTINCT T2.label FROM atom AS T1 INNER JOIN molecule AS T2 ON T1.molecule_id = T2.molecule_id WHERE T1.element = 'ca'
SELECT DISTINCT T1.bond_type FROM bond AS T1 INNER JOIN connected AS T2 ON T1.bond_id = T2.bond_id INNER JOIN atom AS T3 ON T2.atom_id = T3.atom_id WHERE T3.element = 'te'
SELECT T1.element FROM atom AS T1 INNER JOIN connected AS T2 ON T1.atom_id = T2.atom_id WHERE T2.bond_id = 'TR001_10_11' UNION SELECT T1.element FROM atom AS T1 INNER JOIN connected AS T2 ON T1.atom_id = T2.atom_id2 WHERE T2.bond_id = 'TR001_10_11'
SELECT      CAST(SUM(CASE WHEN bond.bond_type = '#' THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(DISTINCT molecule.molecule_id) AS percentage FROM      bond INNER JOIN      molecule ON bond.molecule_id = molecule.molecule_id;
SELECT CAST(SUM(CASE WHEN T1.bond_type = '=' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.bond_id) FROM bond AS T1 INNER JOIN connected AS T2 ON T1.bond_id = T2.bond_id WHERE T1.molecule_id = 'TR047'
SELECT IIF(T2.label = '+', 'YES', 'NO') AS flag_carcinogenic FROM atom AS T1 INNER JOIN molecule AS T2 ON T1.molecule_id = T2.molecule_id WHERE T1.atom_id = 'TR001_1'
SELECT label FROM molecule WHERE molecule_id = 'TR151'
SELECT element FROM atom WHERE molecule_id = 'TR151'
SELECT COUNT(molecule_id) FROM molecule WHERE label = '+'
SELECT atom_id FROM atom WHERE CAST(SUBSTR(molecule_id, 3, 3) AS INTEGER) BETWEEN 10 AND 50   AND element = 'c';
SELECT COUNT(T2.molecule_id) FROM molecule AS T1 INNER JOIN atom AS T2 ON T1.molecule_id = T2.molecule_id WHERE T1.label = '+'
SELECT b.bond_id FROM bond b INNER JOIN molecule m ON b.molecule_id = m.molecule_id WHERE b.bond_type = '=' AND m.label = '+';
SELECT COUNT(T1.atom_id) AS atomnums_h FROM atom AS T1 INNER JOIN molecule AS T2 ON T1.molecule_id = T2.molecule_id WHERE T2.label = '+' AND T1.element = 'h'
SELECT DISTINCT T1.molecule_id FROM bond AS T1 INNER JOIN connected AS T2 ON T1.bond_id = T2.bond_id WHERE T1.bond_id = 'TR000_1_2' AND T2.atom_id = 'TR000_1';
SELECT atom.atom_id FROM atom INNER JOIN molecule ON atom.molecule_id = molecule.molecule_id WHERE atom.element = 'c' AND molecule.label = '-';
SELECT CAST(SUM(CASE WHEN T1.label = '+' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM molecule AS T1 INNER JOIN atom AS T2 ON T1.molecule_id = T2.molecule_id WHERE T2.element = 'h'
SELECT label FROM molecule WHERE molecule_id = 'TR124'
SELECT atom_id FROM atom WHERE molecule_id = 'TR186'
SELECT bond_type  FROM bond  WHERE bond_id = 'TR007_4_19';
SELECT      a1.element,      a2.element  FROM      connected AS c INNER JOIN      atom AS a1  ON      c.atom_id = a1.atom_id INNER JOIN      atom AS a2  ON      c.atom_id2 = a2.atom_id WHERE      c.bond_id = 'TR001_2_4';
SELECT COUNT(T2.bond_id), T1.label FROM molecule AS T1 INNER JOIN bond AS T2 ON T1.molecule_id = T2.molecule_id WHERE T2.bond_type = ' = ' AND T1.molecule_id = 'TR006'
SELECT DISTINCT molecule.molecule_id, atom.element FROM molecule INNER JOIN atom ON molecule.molecule_id = atom.molecule_id WHERE molecule.label = '+';
SELECT T1.atom_id, T1.atom_id2 FROM connected AS T1 INNER JOIN bond AS T2 ON T1.bond_id = T2.bond_id WHERE T2.bond_type = '-'
SELECT T2.molecule_id, T1.element FROM atom AS T1 INNER JOIN molecule AS T2 ON T1.molecule_id = T2.molecule_id INNER JOIN bond AS T3 ON T2.molecule_id = T3.molecule_id WHERE T3.bond_type = '#'
SELECT T1.element FROM atom AS T1 INNER JOIN connected AS T2 ON T1.atom_id = T2.atom_id WHERE T2.bond_id = 'TR000_2_3' UNION SELECT T1.element FROM atom AS T1 INNER JOIN connected AS T2 ON T1.atom_id = T2.atom_id2 WHERE T2.bond_id = 'TR000_2_3'
SELECT COUNT(*) FROM atom AS T1 INNER JOIN connected AS T2 ON T1.atom_id = T2.atom_id WHERE T1.element = 'cl'
SELECT T1.atom_id, COUNT(T2.bond_type) FROM atom AS T1 INNER JOIN bond AS T2 ON T1.molecule_id = T2.molecule_id WHERE T1.molecule_id = 'TR346'
SELECT COUNT(T1.molecule_id) , SUM(CASE WHEN T2.label = '+' THEN 1 ELSE 0 END) FROM bond AS T1 INNER JOIN molecule AS T2 ON T1.molecule_id = T2.molecule_id WHERE T1.bond_type = ' = '
SELECT COUNT(DISTINCT T1.molecule_id) FROM molecule AS T1 INNER JOIN atom AS T2 ON T1.molecule_id = T2.molecule_id INNER JOIN bond AS T3 ON T2.molecule_id = T3.molecule_id WHERE T2.element != 's' AND T3.bond_type != '='
SELECT molecule.label FROM bond INNER JOIN molecule ON bond.molecule_id = molecule.molecule_id WHERE bond.bond_id = 'TR001_2_4';
SELECT COUNT(atom_id) FROM atom WHERE molecule_id = 'TR005'
SELECT COUNT(*)  FROM bond  WHERE bond_type = '-';
SELECT DISTINCT T2.molecule_id FROM atom AS T1 INNER JOIN molecule AS T2 ON T1.molecule_id = T2.molecule_id WHERE T1.element = 'cl' AND T2.label = '+'
SELECT DISTINCT molecule.molecule_id FROM molecule INNER JOIN atom ON molecule.molecule_id = atom.molecule_id WHERE atom.element = 'c' AND molecule.label = '-';
SELECT CAST(SUM(CASE WHEN T1.label = '+' AND T2.element = 'cl' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.molecule_id) FROM molecule AS T1 INNER JOIN atom AS T2 ON T1.molecule_id = T2.molecule_id
SELECT molecule_id  FROM bond  WHERE bond_id = 'TR001_1_7';
SELECT COUNT(T1.element) FROM atom AS T1 INNER JOIN connected AS T2 ON T1.atom_id = T2.atom_id WHERE T2.bond_id = 'TR001_3_4'
SELECT bond.bond_type FROM bond INNER JOIN connected ON bond.bond_id = connected.bond_id WHERE connected.atom_id = 'TR000_1' AND connected.atom_id2 = 'TR000_2';
SELECT DISTINCT T1.molecule_id FROM atom AS T1 INNER JOIN connected AS T2 ON T1.atom_id = T2.atom_id WHERE T2.atom_id = 'TR000_2' AND T2.atom_id2 = 'TR000_4';
SELECT element FROM atom WHERE atom_id = 'TR000_1'
SELECT label FROM molecule WHERE molecule_id = 'TR000'
SELECT      CAST(SUM(CASE WHEN bond.bond_type = '-' THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(bond.bond_id) AS percentage FROM      bond JOIN      connected ON bond.bond_id = connected.bond_id;
SELECT COUNT(DISTINCT molecule.molecule_id) FROM molecule INNER JOIN atom ON molecule.molecule_id = atom.molecule_id WHERE molecule.label = '+' AND atom.element = 'n';
SELECT DISTINCT a.molecule_id FROM atom AS a INNER JOIN connected AS c ON a.atom_id = c.atom_id INNER JOIN bond AS b ON c.bond_id = b.bond_id WHERE a.element = 's' AND b.bond_type = '=';
SELECT molecule_id FROM atom WHERE molecule_id IN ( SELECT molecule_id FROM molecule WHERE label = '-' ) GROUP BY molecule_id HAVING COUNT(molecule_id) > 5
SELECT DISTINCT a.element FROM atom AS a INNER JOIN connected AS c ON a.atom_id = c.atom_id INNER JOIN bond AS b ON c.bond_id = b.bond_id WHERE b.bond_type = '=' AND a.molecule_id = 'TR024';
SELECT molecule.molecule_id FROM molecule INNER JOIN atom ON molecule.molecule_id = atom.molecule_id WHERE molecule.label = '+' GROUP BY molecule.molecule_id ORDER BY COUNT(atom.atom_id) DESC LIMIT 1;
SELECT      CAST(SUM(CASE WHEN m.label = '+' THEN 1 ELSE 0 END) AS FLOAT) * 100.0 / COUNT(*) AS percentage FROM      molecule AS m INNER JOIN      atom AS a ON m.molecule_id = a.molecule_id INNER JOIN      connected AS c ON a.atom_id = c.atom_id INNER JOIN      bond AS b ON c.bond_id = b.bond_id WHERE      a.element = 'h' AND b.bond_type = '#';
SELECT COUNT(molecule_id) FROM molecule WHERE label = '+'
SELECT COUNT(DISTINCT molecule_id) FROM bond WHERE bond_type = '-' AND molecule_id BETWEEN 'TR004' AND 'TR010'
SELECT COUNT(*) FROM atom WHERE molecule_id = 'TR008' AND element = 'c'
SELECT atom.element FROM atom INNER JOIN molecule ON atom.molecule_id = molecule.molecule_id WHERE atom.atom_id = 'TR004_7' AND molecule.label = '-';
SELECT COUNT(DISTINCT T3.molecule_id) FROM connected AS T1 INNER JOIN bond AS T2 ON T1.bond_id = T2.bond_id INNER JOIN atom AS T3 ON T1.atom_id = T3.atom_id WHERE T3.element = 'o' AND T2.bond_type = '='
SELECT COUNT(DISTINCT T2.molecule_id) FROM bond AS T1 INNER JOIN molecule AS T2 ON T1.molecule_id = T2.molecule_id WHERE T1.bond_type = '#' AND T2.label = '-'
SELECT T3.element, T1.bond_type FROM bond AS T1 INNER JOIN connected AS T2 ON T1.bond_id = T2.bond_id INNER JOIN atom AS T3 ON T2.atom_id = T3.atom_id WHERE T1.molecule_id = 'TR016'
SELECT DISTINCT T1.atom_id FROM atom AS T1 INNER JOIN connected AS T2 ON T1.atom_id = T2.atom_id INNER JOIN bond AS T3 ON T2.bond_id = T3.bond_id WHERE T1.molecule_id = 'TR012'   AND T3.bond_type = '='   AND T1.element = 'c';
SELECT atom.atom_id FROM atom INNER JOIN molecule ON atom.molecule_id = molecule.molecule_id WHERE molecule.label = '+' AND atom.element = 'o';
SELECT id FROM cards WHERE cardKingdomFoilId = cardKingdomId AND cardKingdomId IS NOT NULL
SELECT id FROM cards WHERE borderColor = 'borderless' AND (cardKingdomId IS NULL OR cardKingdomFoilId IS NULL)
SELECT name FROM cards ORDER BY faceConvertedManaCost DESC LIMIT 1
SELECT name FROM cards WHERE frameVersion = '2015' AND edhrecRank < 100;
SELECT DISTINCT cards.name FROM cards INNER JOIN legalities ON cards.uuid = legalities.uuid WHERE cards.rarity = 'mythic'   AND legalities.format = 'gladiator'   AND legalities.status = 'Banned';
SELECT DISTINCT legalities.status FROM cards INNER JOIN legalities ON cards.uuid = legalities.uuid WHERE cards.types = 'Artifact'   AND cards.side IS NULL   AND legalities.format = 'vintage';
SELECT T1.id, T1.artist FROM cards AS T1 INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid WHERE T1.power IS NULL OR T1.power = '*' AND T2.format = 'commander' AND T2.status = 'Legal'
SELECT rulings.text, cards.hasContentWarning FROM cards INNER JOIN rulings ON cards.uuid = rulings.uuid WHERE cards.artist = 'Stephen Daniele';
SELECT rulings.text FROM rulings INNER JOIN cards ON rulings.uuid = cards.uuid WHERE cards.name = 'Sublime Epiphany' AND cards.number = '74s';
SELECT cards.name, cards.artist, cards.isPromo FROM cards INNER JOIN rulings ON cards.uuid = rulings.uuid GROUP BY cards.uuid ORDER BY COUNT(rulings.uuid) DESC LIMIT 1;
SELECT DISTINCT foreign_data.language FROM cards INNER JOIN foreign_data ON cards.uuid = foreign_data.uuid WHERE cards.name = 'Annul' AND cards.number = '29';
SELECT name FROM foreign_data WHERE language = 'Japanese'
SELECT CAST(SUM(CASE WHEN T2.language = 'Chinese Simplified' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.id) FROM cards AS T1 INNER JOIN set_translations AS T2 ON T1.setCode = T2.setCode
SELECT sets.name, sets.totalSetSize FROM sets INNER JOIN set_translations ON sets.code = set_translations.setCode WHERE set_translations.language = 'Italian';
SELECT COUNT(DISTINCT types)  FROM cards  WHERE artist = 'Aaron Boyd';
SELECT DISTINCT keywords  FROM cards  WHERE name = 'Angel of Mercy';
SELECT COUNT(*)  FROM cards  WHERE power = '*';
SELECT promoTypes FROM cards WHERE name = 'Duress'
SELECT DISTINCT borderColor FROM cards WHERE name = 'Ancestor''s Chosen'
SELECT DISTINCT originalType FROM cards WHERE name = 'Ancestor''s Chosen'
SELECT language FROM set_translations WHERE setCode IN (SELECT setCode FROM cards WHERE name = 'Angel of Mercy')
SELECT COUNT(cards.id) FROM cards INNER JOIN legalities ON cards.uuid = legalities.uuid WHERE legalities.status = 'restricted' AND cards.isTextless = 0;
SELECT rulings.text FROM cards INNER JOIN rulings ON cards.uuid = rulings.uuid WHERE cards.name = 'Condemn';
SELECT COUNT(*) FROM cards WHERE isStarter = 1
SELECT DISTINCT legalities.status FROM cards INNER JOIN legalities ON cards.uuid = legalities.uuid WHERE cards.name = 'Cloudchaser Eagle';
SELECT type FROM cards WHERE name = 'Benalish Knight'
SELECT T2.format FROM cards AS T1 INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid WHERE T1.name = 'Benalish Knight'
SELECT DISTINCT T1.artist FROM cards AS T1 INNER JOIN foreign_data AS T2 ON T1.uuid = T2.uuid WHERE T2.language = 'Phyrexian'
SELECT CAST(SUM(borderColor = 'borderless') AS REAL) * 100 / COUNT(id) FROM cards
SELECT COUNT(*) FROM foreign_data INNER JOIN cards ON foreign_data.uuid = cards.uuid WHERE foreign_data.language = 'German' AND cards.isReprint = 1;
SELECT COUNT(*) FROM cards INNER JOIN foreign_data ON cards.uuid = foreign_data.uuid WHERE cards.borderColor = 'borderless' AND foreign_data.language = 'Russian';
SELECT CAST(SUM(CASE WHEN T2.language = 'French' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM cards AS T1 INNER JOIN foreign_data AS T2 ON T1.uuid = T2.uuid WHERE T1.isStorySpotlight = 1
SELECT COUNT(*) FROM cards WHERE toughness = 99
SELECT name FROM cards WHERE artist = 'Aaron Boyd'
SELECT COUNT(*)  FROM cards  WHERE borderColor = 'black'    AND availability = 'mtgo';
SELECT id FROM cards WHERE convertedManaCost = 0
SELECT DISTINCT layout FROM cards WHERE keywords = 'Flying'
SELECT COUNT(id) FROM cards WHERE originalType = 'Summon - Angel' AND subtypes != 'Angel'
SELECT id FROM cards WHERE cardKingdomFoilId IS NOT NULL AND cardKingdomId IS NOT NULL
SELECT DISTINCT id FROM cards WHERE duelDeck = 'a';
SELECT edhrecRank FROM cards WHERE frameVersion = 2015
SELECT DISTINCT cards.artist FROM foreign_data INNER JOIN cards ON foreign_data.uuid = cards.uuid WHERE foreign_data.language = 'Chinese Simplified';
SELECT DISTINCT cards.name FROM cards INNER JOIN foreign_data ON cards.uuid = foreign_data.uuid WHERE cards.availability = 'paper' AND foreign_data.language = 'Japanese';
SELECT COUNT(*) FROM cards WHERE borderColor = 'white'
SELECT T1.uuid, T3.language FROM cards AS T1 INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid INNER JOIN foreign_data AS T3 ON T1.uuid = T3.uuid WHERE T2.format = 'legacy'
SELECT rulings.text FROM rulings INNER JOIN cards ON rulings.uuid = cards.uuid WHERE cards.name = 'Beacon of Immortality';
SELECT COUNT(*) AS card_count, legalities.status FROM cards INNER JOIN legalities ON cards.uuid = legalities.uuid WHERE cards.frameVersion = 'future' AND legalities.status = 'Legal';
SELECT name, colors FROM cards WHERE setCode = 'OGW'
SELECT DISTINCT T2.translation, T2.language FROM cards AS T1 INNER JOIN set_translations AS T2 ON T1.setCode = T2.setCode WHERE T1.setCode = '10E' AND T1.convertedManaCost = 5
SELECT T1.name, T2.date FROM cards AS T1 INNER JOIN rulings AS T2 ON T1.uuid = T2.uuid WHERE T1.originalType = 'Creature - Elf'
SELECT DISTINCT cards.colors, legalities.format FROM cards INNER JOIN legalities ON cards.uuid = legalities.uuid WHERE cards.id BETWEEN 1 AND 20;
SELECT DISTINCT T1.name FROM cards AS T1 INNER JOIN foreign_data AS T2 ON T1.uuid = T2.uuid WHERE T1.colors LIKE '%B%' AND T1.originalType = 'Artifact' AND T2.language <> 'English'
SELECT cards.name FROM cards INNER JOIN rulings ON cards.uuid = rulings.uuid WHERE cards.rarity = 'uncommon' ORDER BY rulings.date ASC LIMIT 3;
SELECT COUNT(id) FROM cards WHERE (cardKingdomId IS NULL OR cardKingdomFoilId IS NULL) AND artist = 'John Avon'
SELECT COUNT(id) FROM cards WHERE cardKingdomFoilId = cardKingdomId AND borderColor = 'white'
SELECT COUNT(id) FROM cards WHERE artist = 'UDON' AND availability = 'mtgo' AND hand = -1
SELECT COUNT(id) FROM cards WHERE frameVersion = '1993' AND availability = 'paper' AND hasContentWarning = 1
SELECT manaCost FROM cards WHERE layout = 'normal'   AND frameVersion = '2003'   AND borderColor = 'black'   AND availability LIKE '%paper%'   AND availability LIKE '%mtgo%';
SELECT SUM(CAST(SUBSTR(manaCost, 2, 1) AS INTEGER)) FROM cards WHERE artist = 'Rob Alexander'
SELECT DISTINCT subtypes, supertypes FROM cards WHERE availability = 'arena'
SELECT DISTINCT T1.setCode FROM set_translations AS T1 WHERE T1.language = 'Spanish';
SELECT CAST(COUNT(CASE WHEN hand = '+3' THEN 1 ELSE NULL END) AS REAL) * 100 / COUNT(id) FROM cards WHERE frameEffects = 'legendary'
SELECT CAST(SUM(IIF(isStorySpotlight = 1, 1, 0)) AS REAL) * 100 / COUNT(id) FROM cards
SELECT      CAST(SUM(CASE WHEN T1.language = 'Spanish' THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(T1.id) AS percentage_spanish,     T2.name FROM      foreign_data AS T1 INNER JOIN      cards AS T2 ON      T1.uuid = T2.uuid;
SELECT DISTINCT T2.language FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T1.baseSetSize = 309;
SELECT COUNT(*) AS brazilian_portuguese_commander_sets FROM sets INNER JOIN set_translations ON sets.code = set_translations.setCode WHERE sets.block = 'Commander'   AND set_translations.language = 'Portuguese (Brasil)';
SELECT T1.id FROM cards AS T1 INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid WHERE T2.status = 'Legal' AND T1.type = 'Creature'
SELECT DISTINCT cards.subtypes, cards.supertypes FROM cards INNER JOIN foreign_data ON cards.uuid = foreign_data.uuid WHERE foreign_data.language = 'German';
SELECT COUNT(*)  FROM cards  WHERE power IS NULL AND text LIKE '%triggered ability%';
SELECT COUNT(cards.id) FROM cards INNER JOIN rulings ON cards.uuid = rulings.uuid INNER JOIN legalities ON cards.uuid = legalities.uuid WHERE legalities.format = 'pre-modern'   AND rulings.text = 'This is a triggered mana ability'   AND cards.side IS NULL;
SELECT T1.id FROM cards AS T1 INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid WHERE T1.artist = 'Erica Yang' AND T1.availability = 'paper' AND T2.format = 'pauper' AND T2.status = 'Legal'
SELECT DISTINCT T1.artist FROM cards AS T1 INNER JOIN foreign_data AS T2 ON T1.uuid = T2.uuid WHERE T2.flavorText LIKE '%Das perfekte Gegenmittel zu einer dichten Formation%'
SELECT name FROM foreign_data WHERE uuid IN ( SELECT uuid FROM cards WHERE types = 'Creature' AND layout = 'normal' AND borderColor = 'black' AND artist = 'Matthew D. Wilson' ) AND language = 'French'
SELECT COUNT(DISTINCT T1.id) FROM cards AS T1 INNER JOIN rulings AS T2 ON T1.uuid = T2.uuid WHERE T1.rarity = 'rare' AND T2.date = '2009-01-10'
SELECT T2.language FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T1.baseSetSize = 180
SELECT CAST(SUM(CASE WHEN T1.hasContentWarning = 0 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.id) FROM cards AS T1 INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid WHERE T2.format = 'commander' AND T2.status = 'legal'
SELECT CAST(SUM(CASE WHEN T1.power IS NULL OR T1.power = '*' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM cards AS T1 INNER JOIN foreign_data AS T2 ON T1.uuid = T2.uuid WHERE T2.language = 'French'
SELECT CAST(SUM(CASE WHEN T2.language = 'Japanese' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.id) FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T1.type = 'expansion'
SELECT availability FROM cards WHERE artist = 'Daren Bader'
SELECT COUNT(*)  FROM cards  WHERE edhrecRank > 12000 AND borderColor = 'borderless';
SELECT COUNT(id) FROM cards WHERE isOversized = 1 AND isReprint = 1 AND isPromo = 1
SELECT name FROM cards WHERE power IS NULL OR power = '*' AND promoTypes = 'arenaleague' ORDER BY name LIMIT 3
SELECT language FROM foreign_data WHERE multiverseid = 149934
SELECT id FROM cards WHERE cardKingdomFoilId IS NOT NULL AND cardKingdomId IS NOT NULL ORDER BY cardKingdomFoilId LIMIT 3
SELECT CAST(SUM(CASE WHEN isTextless = 1 AND layout = 'normal' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM cards
SELECT number  FROM cards  WHERE side IS NULL    AND subtypes LIKE '%Angel%'    AND subtypes LIKE '%Wizard%';
SELECT code, name FROM sets WHERE mtgoCode IS NULL OR mtgoCode = '' ORDER BY name ASC LIMIT 3
SELECT DISTINCT T2.language FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T1.mcmName = 'Archenemy' AND T2.setCode = 'ARC';
SELECT sets.name, set_translations.translation FROM sets INNER JOIN set_translations ON sets.code = set_translations.setCode WHERE sets.id = 5;
SELECT T2.language, T1.type FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T2.id = 206
SELECT DISTINCT T1.code, T1.id FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T1.block = 'Shadowmoor' AND T2.language = 'Italian'
SELECT T1.name, T1.id FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T2.language = 'Japanese' AND T1.isFoilOnly = 1 AND T1.isForeignOnly = 0
SELECT T1.name FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T2.language = 'Russian' ORDER BY T1.baseSetSize DESC LIMIT 1;
SELECT CAST(SUM(CASE WHEN T1.isOnlineOnly = 1 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.isOnlineOnly) FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T2.language = 'Chinese Simplified'
SELECT COUNT(*) FROM sets WHERE mtgoCode IS NULL OR mtgoCode = ''
SELECT COUNT(id) AS total_black_borders, id  FROM cards  WHERE borderColor = 'black';
SELECT COUNT(DISTINCT id) AS card_count, id FROM cards WHERE frameEffects = 'extendedart';
SELECT name  FROM cards  WHERE borderColor = 'black' AND isFullArt = 1;
SELECT DISTINCT language  FROM set_translations  WHERE id = 174;
SELECT name FROM sets WHERE code = 'ALL'
SELECT DISTINCT language FROM foreign_data WHERE name = 'A Pedra Fellwar'
SELECT code FROM sets WHERE releaseDate = '2007-07-13'
SELECT baseSetSize, code FROM sets WHERE block IN ('Masques', 'Mirage')
SELECT code FROM sets WHERE type = 'expansion';
SELECT foreign_data.name, foreign_data.type FROM cards INNER JOIN foreign_data ON cards.uuid = foreign_data.uuid WHERE cards.watermark = 'boros';
SELECT foreign_data.language, foreign_data.flavorText, foreign_data.type FROM foreign_data INNER JOIN cards ON foreign_data.uuid = cards.uuid WHERE cards.watermark = 'colorpie';
SELECT CAST(SUM(CASE WHEN T1.convertedManaCost = 10 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM cards AS T1 INNER JOIN sets AS T2 ON T1.setCode = T2.code WHERE T2.name = 'Abyssal Horror'
SELECT code FROM sets WHERE type = 'commander'
SELECT foreign_data.name, foreign_data.type FROM foreign_data INNER JOIN cards ON foreign_data.uuid = cards.uuid WHERE cards.watermark = 'abzan';
SELECT T2.language, T2.type FROM cards AS T1 INNER JOIN foreign_data AS T2 ON T1.uuid = T2.uuid WHERE T1.watermark = 'azorius'
SELECT SUM(CASE WHEN artist = 'Aaron Miller' AND cardKingdomFoilId IS NOT NULL AND cardKingdomId IS NOT NULL THEN 1 ELSE 0 END) FROM cards
SELECT COUNT(*)  FROM cards  WHERE availability LIKE '%paper%'    AND hand LIKE '+%';
SELECT name  FROM cards  WHERE isTextless = 0;
SELECT DISTINCT manaCost FROM cards WHERE name = 'Ancestor''s Chosen';
SELECT SUM(CASE WHEN power = '*' OR power IS NULL THEN 1 ELSE 0 END) FROM cards WHERE borderColor = 'white'
SELECT name FROM cards WHERE isPromo = 1 AND side IS NOT NULL;
SELECT DISTINCT subtypes, supertypes  FROM cards  WHERE name = 'Molimo, Maro-Sorcerer';
SELECT purchaseUrls FROM cards WHERE promoTypes = 'bundle'
SELECT COUNT(CASE WHEN availability LIKE '%arena,mtgo%' THEN 1 ELSE NULL END) FROM cards
SELECT name FROM cards WHERE name IN ('Serra Angel', 'Shrine Keeper') ORDER BY convertedManaCost DESC LIMIT 1
SELECT DISTINCT artist  FROM cards  WHERE flavorName = 'Battra, Dark Destroyer';
SELECT name FROM cards WHERE frameVersion = 2003 ORDER BY convertedManaCost DESC LIMIT 3
SELECT DISTINCT T3.translation FROM cards AS T1 INNER JOIN sets AS T2 ON T1.setCode = T2.code INNER JOIN set_translations AS T3 ON T2.code = T3.setCode WHERE T1.name = 'Ancestor''s Chosen' AND T3.language = 'Italian';
SELECT COUNT(*) FROM set_translations WHERE setCode = ( SELECT setCode FROM cards WHERE name = 'Angel of Mercy' )
SELECT T3.name FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode INNER JOIN cards AS T3 ON T1.code = T3.setCode WHERE T2.translation = 'Hauptset Zehnte Edition'
SELECT EXISTS (     SELECT 1     FROM cards     INNER JOIN foreign_data ON cards.uuid = foreign_data.uuid     WHERE cards.name = 'Ancestor''s Chosen' AND foreign_data.language = 'Korean' );
SELECT COUNT(T3.id) FROM set_translations AS T1 INNER JOIN cards AS T3 ON T1.setCode = T3.setCode INNER JOIN sets AS T2 ON T1.setCode = T2.code WHERE T1.translation = 'Hauptset Zehnte Edition' AND T3.artist = 'Adam Rex'
SELECT T1.baseSetSize FROM sets AS T1 INNER JOIN set_translations AS T2 ON T2.setCode = T1.code WHERE T2.translation = 'Hauptset Zehnte Edition'
SELECT translation FROM set_translations WHERE setCode = '8ED' AND language = 'Chinese Simplified'
SELECT CASE WHEN T2.mtgoCode IS NOT NULL THEN 1 ELSE 0 END AS appears_on_mtgo FROM cards AS T1 INNER JOIN sets AS T2 ON T1.setCode = T2.code WHERE T1.name = 'Angel of Mercy';
SELECT DISTINCT sets.releaseDate FROM cards INNER JOIN sets ON cards.setCode = sets.code WHERE cards.name = 'Ancestor''s Chosen';
SELECT DISTINCT T2.type FROM set_translations AS T1 INNER JOIN sets AS T2 ON T1.setCode = T2.code WHERE T1.translation = 'Hauptset Zehnte Edition';
SELECT COUNT(*) FROM sets INNER JOIN set_translations ON sets.code = set_translations.setCode WHERE sets.block = 'Ice Age' AND set_translations.language = 'Italian';
SELECT DISTINCT T2.isForeignOnly FROM cards AS T1 INNER JOIN sets AS T2 ON T1.setCode = T2.code WHERE T1.name = 'Adarkar Valkyrie';
SELECT COUNT(*)  FROM sets  INNER JOIN set_translations  ON sets.code = set_translations.setCode  WHERE set_translations.language = 'Italian'    AND sets.baseSetSize < 10;
SELECT SUM(CASE WHEN T1.borderColor = 'black' THEN 1 ELSE 0 END) FROM cards AS T1 INNER JOIN sets AS T2 ON T2.code = T1.setCode WHERE T2.name = 'Coldsnap'
SELECT T1.name FROM cards AS T1 INNER JOIN sets AS T2 ON T2.code = T1.setCode WHERE T2.name = 'Coldsnap' ORDER BY T1.convertedManaCost DESC LIMIT 1
SELECT DISTINCT cards.artist FROM cards INNER JOIN sets ON cards.setCode = sets.code WHERE sets.name = 'Coldsnap'   AND cards.artist IN ('Jeremy Jarvis', 'Aaron Miller', 'Chippy');
SELECT name FROM cards WHERE number = '4' AND setCode = 'CSP'
SELECT SUM(CASE WHEN T1.power LIKE '%*%' OR T1.power IS NULL THEN 1 ELSE 0 END) FROM cards AS T1 INNER JOIN sets AS T2 ON T2.code = T1.setCode WHERE T2.name = 'Coldsnap' AND T1.convertedManaCost > 5
SELECT foreign_data.flavorText FROM foreign_data INNER JOIN cards ON foreign_data.uuid = cards.uuid WHERE foreign_data.language = 'Italian'   AND cards.name = 'Ancestor''s Chosen';
SELECT DISTINCT T2.language FROM cards AS T1 INNER JOIN foreign_data AS T2 ON T1.uuid = T2.uuid WHERE T1.name = 'Ancestor''s Chosen' AND T2.flavorText IS NOT NULL;
SELECT DISTINCT foreign_data.type FROM foreign_data INNER JOIN cards ON foreign_data.uuid = cards.uuid WHERE foreign_data.language = 'German' AND cards.name = 'Ancestor''s Chosen';
SELECT DISTINCT T2.text, T3.text FROM cards AS T1 INNER JOIN foreign_data AS T2 ON T1.uuid = T2.uuid INNER JOIN rulings AS T3 ON T1.uuid = T3.uuid WHERE T1.setCode IN (SELECT code FROM sets WHERE name = 'Coldsnap') AND T2.language = 'Italian'
SELECT T1.name FROM foreign_data AS T1 INNER JOIN cards AS T2 ON T2.uuid = T1.uuid INNER JOIN sets AS T3 ON T3.code = T2.setCode WHERE T3.name = 'Coldsnap' AND T1.language = 'Italian' ORDER BY T2.convertedManaCost DESC LIMIT 1
SELECT rulings.date FROM cards INNER JOIN rulings ON cards.uuid = rulings.uuid WHERE cards.name = 'Reminisce';
SELECT CAST(SUM(CASE WHEN T2.convertedManaCost = 7 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM sets AS T1 INNER JOIN cards AS T2 ON T1.code = T2.setCode WHERE T1.name = 'Coldsnap'
SELECT CAST(SUM(IIF(T1.cardKingdomFoilId = T1.cardKingdomId, 1, 0)) AS REAL) * 100 / COUNT(*) FROM cards AS T1 INNER JOIN sets AS T2 ON T1.setCode = T2.code WHERE T2.name = 'Coldsnap'
SELECT code FROM sets WHERE releaseDate = '2017-07-14'
SELECT keyruneCode FROM sets WHERE code = 'PKHC'
SELECT mcmId FROM sets WHERE code = 'SS2'
SELECT mcmName  FROM sets  WHERE releaseDate = '2017-06-09';
SELECT type FROM sets WHERE name = 'From the Vault: Lore'
SELECT DISTINCT parentCode  FROM sets  WHERE name = 'Commander 2014 Oversized';
SELECT T2.text, CASE WHEN T1.hasContentWarning = 1 THEN 'YES' ELSE 'NO' END FROM cards AS T1 INNER JOIN rulings AS T2 ON T2.uuid = T1.uuid WHERE T1.artist = 'Jim Pavelec'
SELECT DISTINCT T2.releaseDate FROM cards AS T1 INNER JOIN sets AS T2 ON T1.setCode = T2.code WHERE T1.name = 'Evacuation';
SELECT T1.baseSetSize FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T2.translation = 'Rinascita di Alara';
SELECT DISTINCT sets.type FROM set_translations INNER JOIN sets ON set_translations.setCode = sets.code WHERE set_translations.translation = 'Huitième édition';
SELECT T3.translation FROM cards AS T1 INNER JOIN sets AS T2 ON T1.setCode = T2.code INNER JOIN set_translations AS T3 ON T3.setCode = T2.code WHERE T3.language = 'French' AND T1.name = 'Tendo Ice Bridge'
SELECT COUNT(T1.setCode) FROM set_translations AS T1 INNER JOIN sets AS T2 ON T1.setCode = T2.code WHERE T2.name = 'Salvat 2011'
SELECT T3.translation FROM cards AS T1 INNER JOIN sets AS T2 ON T1.setCode = T2.code INNER JOIN set_translations AS T3 ON T2.code = T3.setCode WHERE T1.name = 'Fellwar Stone' AND T3.language = 'Japanese'
SELECT cards.name FROM cards INNER JOIN sets ON cards.setCode = sets.code WHERE sets.name = 'Journey into Nyx Hero''s Path' ORDER BY cards.convertedManaCost DESC LIMIT 1;
SELECT DISTINCT T1.releaseDate FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T2.translation = 'Ola de frío';
SELECT T2.type FROM cards AS T1 INNER JOIN sets AS T2 ON T2.code = T1.setCode WHERE T1.name = 'Samite Pilgrim'
SELECT COUNT(*) AS card_count FROM sets INNER JOIN cards ON sets.code = cards.setCode WHERE sets.name = 'World Championship Decks 2004'   AND cards.convertedManaCost = 3;
SELECT translation FROM set_translations WHERE setCode = 'MRD' AND language = 'Chinese Simplified'
SELECT CAST(SUM(CASE WHEN T1.isNonFoilOnly = 1 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.code) FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T2.language = 'Japanese'
SELECT CAST(SUM(IIF(T1.isOnlineOnly = 1, 1, 0)) AS REAL) * 100 / SUM(IIF(T2.language = 'Portuguese (Brazil)', 1, 0)) FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode
SELECT availability  FROM cards  WHERE artist = 'Aleksi Briclot'    AND isTextless = 1;
SELECT id FROM sets ORDER BY baseSetSize DESC LIMIT 1
SELECT artist  FROM cards  WHERE side IS NULL  ORDER BY convertedManaCost DESC  LIMIT 1;
SELECT frameEffects FROM cards WHERE cardKingdomFoilId IS NOT NULL AND cardKingdomId IS NOT NULL
SELECT SUM(CASE WHEN power LIKE '%*%' OR power IS NULL THEN 1 ELSE 0 END) FROM cards WHERE hasFoil = 0 AND duelDeck = 'a'
SELECT id  FROM sets  WHERE type = 'commander'  ORDER BY totalSetSize DESC  LIMIT 1;
SELECT c.name FROM cards c INNER JOIN legalities l ON c.uuid = l.uuid WHERE l.format = 'duel' ORDER BY c.manaCost DESC LIMIT 10;
SELECT c.originalReleaseDate, l.format FROM cards c INNER JOIN legalities l ON c.uuid = l.uuid WHERE c.rarity = 'mythic' AND l.status = 'Legal' ORDER BY c.originalReleaseDate ASC LIMIT 1;
SELECT COUNT(*) FROM cards INNER JOIN foreign_data ON cards.uuid = foreign_data.uuid WHERE cards.artist = 'Volkan Baǵa' AND foreign_data.language = 'French';
SELECT COUNT(T1.name) FROM cards AS T1 INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid WHERE T1.rarity = 'rare' AND T1.types = 'Enchantment' AND T1.name = 'Abundance' AND T2.status = 'Legal'
SELECT L.format, C.name FROM legalities AS L INNER JOIN cards AS C ON L.uuid = C.uuid WHERE L.status = 'Banned' GROUP BY L.format ORDER BY COUNT(L.uuid) DESC LIMIT 1;
SELECT DISTINCT T3.language FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode INNER JOIN foreign_data AS T3 ON T2.setCode = T3.uuid WHERE T1.name = 'Battlebond';
SELECT T1.artist, T2.format FROM cards AS T1 INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid GROUP BY T1.artist, T2.format ORDER BY COUNT(T1.artist) ASC LIMIT 1
SELECT DISTINCT T2.status FROM cards AS T1 INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid WHERE T1.frameVersion = '1997'   AND T1.artist = 'D. Alexander Gregory'   AND T1.hasContentWarning = 1   AND T2.format = 'legacy';
SELECT T1.name, T2.format FROM cards AS T1 INNER JOIN legalities AS T2 ON T2.uuid = T1.uuid WHERE T1.edhrecRank = 1 AND T2.status = 'Banned' GROUP BY T1.name, T2.format
SELECT CAST(COUNT(T1.id) AS REAL) / (SELECT COUNT(id) FROM sets WHERE releaseDate LIKE '2012%' OR releaseDate LIKE '2013%' OR releaseDate LIKE '2014%' OR releaseDate LIKE '2015%') AS average_num FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T1.releaseDate LIKE '2012%' OR T1.releaseDate LIKE '2013%' OR T1.releaseDate LIKE '2014%' OR T1.releaseDate LIKE '2015%'
SELECT DISTINCT artist FROM cards WHERE borderColor = 'black' AND availability = 'arena'
SELECT uuid FROM legalities WHERE format = 'oldschool' AND status IN ('Banned', 'Restricted')
SELECT COUNT(id) FROM cards WHERE artist = 'Matthew D. Wilson' AND availability = 'paper'
SELECT T2.text FROM cards AS T1 INNER JOIN rulings AS T2 ON T2.uuid = T1.uuid WHERE T1.artist = 'Kev Walker' ORDER BY T2.date DESC
SELECT T3.name, T2.format FROM cards AS T1 INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid INNER JOIN sets AS T3 ON T3.code = T1.setCode WHERE T3.name = 'Hour of Devastation'
SELECT T1.name FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T2.language = 'Korean' EXCEPT SELECT T1.name FROM sets AS T1 INNER JOIN set_translations AS T2 ON T1.code = T2.setCode WHERE T2.language = 'Japanese'
SELECT DISTINCT T1.frameVersion, T1.name , IIF(T2.status = 'Banned', T1.name, 'NO') FROM cards AS T1 INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid WHERE T1.artist = 'Allen Williams'
SELECT DisplayName FROM users WHERE DisplayName IN ('Harlan', 'Jarrod Dixon') ORDER BY Reputation DESC LIMIT 1
SELECT DisplayName FROM users WHERE CAST(STRFTIME('%Y', CreationDate) AS int) = 2014
SELECT COUNT(Id)  FROM users  WHERE LastAccessDate > '2014-09-01 00:00:00';
SELECT DisplayName FROM users WHERE Views = ( SELECT MAX(Views) FROM users )
SELECT COUNT(*)  FROM users  WHERE UpVotes > 100 AND DownVotes > 1;
SELECT COUNT(id) FROM users WHERE STRFTIME('%Y', CreationDate) > '2013' AND Views > 10
SELECT COUNT(T2.OwnerUserId) FROM users AS T1 INNER JOIN posts AS T2 ON T1.Id = T2.OwnerUserId WHERE T1.DisplayName = 'csgillespie'
SELECT T1.Title FROM posts AS T1 INNER JOIN users AS T2 ON T1.OwnerUserId = T2.Id WHERE T2.DisplayName = 'csgillespie'
SELECT OwnerDisplayName FROM posts WHERE Title = 'Eliciting priors from experts'
SELECT p.Title FROM posts p INNER JOIN users u ON p.OwnerUserId = u.Id WHERE u.DisplayName = 'csgillespie' ORDER BY p.ViewCount DESC LIMIT 1;
SELECT T2.DisplayName FROM posts AS T1 INNER JOIN users AS T2 ON T1.OwnerUserId = T2.Id ORDER BY T1.FavoriteCount DESC LIMIT 1
SELECT SUM(T1.CommentCount) FROM posts AS T1 INNER JOIN users AS T2 ON T1.OwnerUserId = T2.Id WHERE T2.DisplayName = 'csgillespie'
SELECT T2.AnswerCount FROM users AS T1 INNER JOIN posts AS T2 ON T1.Id = T2.OwnerUserId WHERE T1.DisplayName = 'csgillespie' ORDER BY T2.AnswerCount DESC LIMIT 1
SELECT LastEditorDisplayName  FROM posts  WHERE Title = 'Examples for teaching: Correlation does not mean causation';
SELECT COUNT(Id)  FROM posts  WHERE OwnerDisplayName = 'csgillespie'    AND ParentId IS NULL;
SELECT DISTINCT OwnerDisplayName FROM posts WHERE ClosedDate IS NOT NULL
SELECT COUNT(T1.Id) FROM posts AS T1 INNER JOIN users AS T2 ON T1.OwnerUserId = T2.Id WHERE T1.Score >= 20 AND T2.Age > 65
SELECT T2.Location FROM posts AS T1 INNER JOIN users AS T2 ON T1.OwnerUserId = T2.Id WHERE T1.Title = 'Eliciting priors from experts'
SELECT T2.Body FROM tags AS T1 INNER JOIN posts AS T2 ON T1.ExcerptPostId = T2.Id WHERE T1.TagName = 'bayesian'
SELECT Body FROM posts WHERE Id = ( SELECT ExcerptPostId FROM tags ORDER BY Count DESC LIMIT 1 )
SELECT COUNT(badges.Id)  FROM badges  INNER JOIN users ON badges.UserId = users.Id  WHERE users.DisplayName = 'csgillespie';
SELECT badges.Name FROM badges INNER JOIN users ON badges.UserId = users.Id WHERE users.DisplayName = 'csgillespie';
SELECT COUNT(*)  FROM badges AS T1  INNER JOIN users AS T2  ON T1.UserId = T2.Id  WHERE T2.DisplayName = 'csgillespie'    AND STRFTIME('%Y', T1.Date) = '2011';
SELECT u.DisplayName FROM badges b INNER JOIN users u ON b.UserId = u.Id GROUP BY b.UserId ORDER BY COUNT(b.Id) DESC LIMIT 1;
SELECT AVG(Score)  FROM posts  WHERE OwnerDisplayName = 'csgillespie';
SELECT CAST(COUNT(T1.Id) AS REAL) / COUNT(DISTINCT T1.UserId) FROM badges AS T1 INNER JOIN users AS T2 ON T1.UserId = T2.Id WHERE T2.Views > 200
SELECT CAST(SUM(CASE WHEN T1.Age > 65 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T2.OwnerUserId) FROM users AS T1 INNER JOIN posts AS T2 ON T1.Id = T2.OwnerUserId WHERE T2.Score > 20
SELECT COUNT(CreationDate) FROM votes WHERE UserId = 58 AND CreationDate = '2010-07-19'
SELECT CreationDate FROM votes GROUP BY CreationDate ORDER BY COUNT(Id) DESC LIMIT 1;
SELECT COUNT(Id) FROM badges WHERE Name = 'Revival'
SELECT Title FROM posts WHERE Id = ( SELECT PostId FROM comments ORDER BY Score DESC LIMIT 1 )
SELECT COUNT(*)  FROM posts  INNER JOIN comments ON posts.Id = comments.PostId  WHERE posts.ViewCount = 1910;
SELECT DISTINCT posts.FavoriteCount FROM comments INNER JOIN posts ON comments.PostId = posts.Id WHERE comments.UserId = 3025   AND comments.CreationDate = '2014-04-23 20:29:39.0';
SELECT T2.Text FROM posts AS T1 INNER JOIN comments AS T2 ON T1.Id = T2.PostId WHERE T1.ParentId = 107829
SELECT CASE WHEN T2.ClosedDate IS NULL THEN 'not well-finished' ELSE 'well-finished' END AS result FROM comments AS T1 INNER JOIN posts AS T2 ON T1.PostId = T2.Id WHERE T1.UserId = 23853 AND T1.CreationDate = '2013-07-12 09:08:18.0'
SELECT T1.Reputation FROM users AS T1 INNER JOIN posts AS T2 ON T1.Id = T2.OwnerUserId WHERE T2.Id = 65041
SELECT COUNT(*) FROM users WHERE DisplayName = 'Tiago Pasqualini'
SELECT T1.DisplayName FROM users AS T1 INNER JOIN votes AS T2 ON T1.Id = T2.UserId WHERE T2.Id = 6347
SELECT SUM(CASE WHEN T1.Title LIKE '%data visualization%' THEN 1 ELSE 0 END) FROM posts AS T1 INNER JOIN votes AS T2 ON T1.Id = T2.PostId
SELECT T2.Name FROM users AS T1 INNER JOIN badges AS T2 ON T1.Id = T2.UserId WHERE T1.DisplayName = 'DatEpicCoderGuyWhoPrograms'
SELECT      CAST((SELECT COUNT(*) FROM posts WHERE OwnerUserId = 24) AS REAL) /      (SELECT COUNT(*) FROM votes WHERE UserId = 24) AS post_to_vote_ratio;
SELECT ViewCount FROM posts WHERE Title = 'Integration of Weka and/or RapidMiner into Informatica PowerCenter/Developer'
SELECT Text  FROM comments  WHERE Score = 17;
SELECT DISTINCT DisplayName  FROM users  WHERE WebsiteUrl = 'http://stackoverflow.com';
SELECT badges.Name FROM users INNER JOIN badges ON users.Id = badges.UserId WHERE users.DisplayName = 'SilentGhost';
SELECT UserDisplayName FROM comments WHERE Text LIKE 'thank you user93!'
SELECT Text FROM comments WHERE UserId = ( SELECT Id FROM users WHERE DisplayName = 'A Lion' )
SELECT users.DisplayName, users.Reputation FROM posts INNER JOIN users ON posts.OwnerUserId = users.Id WHERE posts.Title = 'Understanding what Dassault iSight is doing?';
SELECT T1.Text FROM comments AS T1 INNER JOIN posts AS T2 ON T1.PostId = T2.Id WHERE T2.Title = 'How does gentle boosting differ from AdaBoost?'
SELECT DISTINCT users.DisplayName FROM badges INNER JOIN users ON badges.UserId = users.Id WHERE badges.Name = 'Necromancer' LIMIT 10;
SELECT DISTINCT LastEditorDisplayName  FROM posts  WHERE Title = 'Open source tools for visualizing multi-dimensional data?';
SELECT Title FROM posts WHERE LastEditorUserId = ( SELECT Id FROM users WHERE DisplayName = 'Vebjorn Ljosa' )
SELECT SUM(posts.Score), users.WebsiteUrl FROM posts INNER JOIN users ON posts.LastEditorUserId = users.Id WHERE users.DisplayName = 'Yevgeny';
SELECT T3.Text FROM posts AS T1 INNER JOIN postHistory AS T2 ON T1.Id = T2.PostId INNER JOIN comments AS T3 ON T1.Id = T3.PostId WHERE T1.Title = 'Why square the difference instead of taking the absolute value in standard deviation?'
SELECT SUM(v.BountyAmount) FROM votes AS v INNER JOIN posts AS p ON v.PostId = p.Id WHERE p.Title LIKE '%data%';
SELECT T1.DisplayName FROM users AS T1 INNER JOIN votes AS T2 ON T1.Id = T2.UserId INNER JOIN posts AS T3 ON T2.PostId = T3.Id WHERE T2.BountyAmount = 50 AND T3.Title LIKE '%variance%'
SELECT CAST(SUM(ViewCount) AS REAL) / COUNT(ViewCount), T1.Title, T2.Text FROM posts AS T1 INNER JOIN comments AS T2 ON T1.Id = T2.PostId WHERE T1.Tags LIKE '%humor%'
SELECT COUNT(Id) FROM comments WHERE UserId = 13
SELECT Id FROM users ORDER BY Reputation DESC LIMIT 1
SELECT Id  FROM users  ORDER BY Views ASC  LIMIT 1;
SELECT COUNT(Name) FROM badges WHERE Name = 'Supporter' AND STRFTIME('%Y', Date) = '2011'
SELECT COUNT(Name) FROM badges WHERE Name > 5
SELECT COUNT(DISTINCT u.Id) FROM users AS u WHERE u.Location = 'New York' AND EXISTS (SELECT 1 FROM badges AS b1 WHERE b1.UserId = u.Id AND b1.Name = 'Supporter') AND EXISTS (SELECT 1 FROM badges AS b2 WHERE b2.UserId = u.Id AND b2.Name = 'Teachers')
SELECT users.DisplayName, users.Reputation FROM posts INNER JOIN users ON posts.OwnerUserId = users.Id WHERE posts.Id = 1;
SELECT T1.UserId FROM postHistory AS T1 INNER JOIN users AS T2 ON T1.UserId = T2.Id GROUP BY T1.UserId HAVING COUNT(T1.PostId) = 1 AND SUM(T2.Views) > 1000
SELECT T2.UserId, T2.Name FROM comments AS T1 INNER JOIN badges AS T2 ON T1.UserId = T2.UserId GROUP BY T1.UserId ORDER BY COUNT(T1.Id) DESC LIMIT 1
SELECT COUNT(DISTINCT T1.UserId) FROM badges AS T1 INNER JOIN users AS T2 ON T1.UserId = T2.Id WHERE T2.Location = 'India' AND T1.Name = 'Teacher'
SELECT CAST(SUM(CASE WHEN STRFTIME('%Y', Date) = '2010' THEN 1 ELSE 0 END) AS REAL) * 100 / SUM(CASE WHEN STRFTIME('%Y', Date) = '2011' THEN 1 ELSE 0 END) - 100 FROM badges WHERE Name = 'Student'
SELECT PostHistoryTypeId, COUNT(DISTINCT UserId) FROM postHistory WHERE PostId = 3720
SELECT T1.RelatedPostId, T2.ViewCount FROM postLinks AS T1 INNER JOIN posts AS T2 ON T1.PostId = T2.Id WHERE T1.PostId = 61217
SELECT posts.Score, postLinks.LinkTypeId FROM posts INNER JOIN postLinks ON posts.Id = postLinks.PostId WHERE postLinks.PostId = 395;
SELECT Id, OwnerUserId FROM posts WHERE Score > 60
SELECT SUM(T2.FavoriteCount) FROM users AS T1 INNER JOIN posts AS T2 ON T1.Id = T2.OwnerUserId WHERE T1.Id = 686 AND STRFTIME('%Y', T2.CreaionDate) = '2011'
SELECT CAST(SUM(T1.UpVotes) AS REAL) / COUNT(T1.Id), CAST(SUM(T1.Age) AS REAL) / COUNT(T1.Id) FROM users AS T1 INNER JOIN posts AS T2 ON T1.Id = T2.OwnerUserId GROUP BY T1.Id HAVING COUNT(T2.Id) > 10
SELECT COUNT(UserId) FROM badges WHERE Name = 'Announcer'
SELECT Name FROM badges WHERE Date = '2010-07-19 19:39:08.0'
SELECT COUNT(Id) FROM comments WHERE Score > 60
SELECT Text FROM comments WHERE CreationDate = '2010-07-19 19:25:47.0'
SELECT COUNT(Id)  FROM posts  WHERE Score = 10;
SELECT DISTINCT T2.Name FROM users AS T1 INNER JOIN badges AS T2 ON T1.Id = T2.UserId ORDER BY T1.Reputation DESC LIMIT 1
SELECT users.Reputation FROM badges INNER JOIN users ON badges.UserId = users.Id WHERE badges.Date = '2010-07-19 19:39:08.0';
SELECT badges.Name FROM badges INNER JOIN users ON badges.UserId = users.Id WHERE users.DisplayName = 'Pierre';
SELECT T2.Date FROM users AS T1 INNER JOIN badges AS T2 ON T1.Id = T2.UserId WHERE T1.Location = 'Rochester, NY'
SELECT CAST(SUM(IIF(Name = 'Teacher', 1, 0)) AS REAL) * 100 / COUNT(Name) FROM badges
SELECT CAST(SUM(CASE WHEN T2.Age BETWEEN 13 AND 18 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.UserId) FROM badges AS T1 INNER JOIN users AS T2 ON T1.UserId = T2.Id WHERE T1.Name = 'Organizer'
SELECT T1.Score FROM comments AS T1 INNER JOIN posts AS T2 ON T1.PostId = T2.Id WHERE T1.CreationDate = '2010-07-19 19:19:56.0'
SELECT Text FROM comments WHERE CreationDate = '2010-07-19 19:37:33.0'
SELECT DISTINCT users.Age FROM users INNER JOIN badges ON users.Id = badges.UserId WHERE users.Location = 'Vienna, Austria';
SELECT COUNT(users.Id) FROM users INNER JOIN badges ON users.Id = badges.UserId WHERE badges.Name = 'Supporter' AND users.Age BETWEEN 19 AND 65;
SELECT COUNT(T1.Id) FROM users AS T1 INNER JOIN badges AS T2 ON T1.Id = T2.UserId WHERE T2.Date = '2010-07-19 19:39:08.0'
SELECT T1.Name FROM badges AS T1 INNER JOIN users AS T2 ON T1.UserId = T2.Id ORDER BY T2.Reputation ASC LIMIT 1
SELECT badges.Name FROM users INNER JOIN badges ON users.Id = badges.UserId WHERE users.DisplayName = 'Sharpie';
SELECT COUNT(*)  FROM badges  INNER JOIN users ON badges.UserId = users.Id  WHERE badges.Name = 'Supporter' AND users.Age > 65;
SELECT DisplayName FROM users WHERE Id = 30
SELECT COUNT(Id) FROM users WHERE Location LIKE '%New York%'
SELECT COUNT(Id) FROM votes WHERE STRFTIME('%Y', CreationDate) = '2010'
SELECT COUNT(*) FROM users WHERE Age BETWEEN 19 AND 65
SELECT DisplayName  FROM users  WHERE Views = (SELECT MAX(Views) FROM users);
SELECT CAST(SUM(CASE WHEN STRFTIME('%Y', CreationDate) = '2010' THEN 1 ELSE 0 END) AS REAL) * 100 / SUM(CASE WHEN STRFTIME('%Y', CreationDate) = '2011' THEN 1 ELSE 0 END) FROM votes
SELECT T1.TagName FROM tags AS T1 INNER JOIN posts AS T2 ON T1.ExcerptPostId = T2.Id INNER JOIN users AS T3 ON T2.OwnerUserId = T3.Id WHERE T3.DisplayName = 'John Stauffer'
SELECT COUNT(posts.Id)  FROM posts  INNER JOIN users ON posts.OwnerUserId = users.Id  WHERE users.DisplayName = 'Daniel Vassallo';
SELECT COUNT(*)  FROM votes  INNER JOIN users ON votes.UserId = users.Id  WHERE users.DisplayName = 'Harlan';
SELECT T1.Id FROM posts AS T1 INNER JOIN users AS T2 ON T1.OwnerUserId = T2.Id WHERE T2.DisplayName = 'slashnick' ORDER BY T1.AnswerCount DESC LIMIT 1;
SELECT u.DisplayName FROM posts p INNER JOIN users u ON p.OwnerUserId = u.Id WHERE u.DisplayName IN ('Harvey Motulsky', 'Noah Snyder') GROUP BY u.DisplayName ORDER BY SUM(p.ViewCount) DESC LIMIT 1;
SELECT COUNT(T1.Id) FROM posts AS T1 INNER JOIN users AS T2 ON T1.OwnerUserId = T2.Id INNER JOIN votes AS T3 ON T1.Id = T3.PostId WHERE T2.DisplayName = 'Matt Parker' AND T3.PostId > 4
SELECT COUNT(*) AS NegativeCommentCount FROM users INNER JOIN comments ON users.Id = comments.UserId WHERE users.DisplayName = 'Neil McGuigan' AND comments.Score < 60;
SELECT T1.Tags FROM posts AS T1 INNER JOIN users AS T2 ON T1.OwnerUserId = T2.Id WHERE T2.DisplayName = 'Mark Meckes' AND T1.Id NOT IN ( SELECT PostId FROM comments )
SELECT T1.DisplayName FROM users AS T1 INNER JOIN badges AS T2 ON T1.Id = T2.UserId WHERE T2.Name = 'Organizer'
SELECT CAST(SUM(CASE WHEN T2.TagName = 'r' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.Id) FROM posts AS T1 INNER JOIN tags AS T2 ON T1.Tags = T2.TagName WHERE T1.OwnerDisplayName = 'Community'
SELECT SUM(IIF(T2.DisplayName = 'Mornington', T1.ViewCount, 0)) - SUM(IIF(T2.DisplayName = 'Amos', T1.ViewCount, 0)) FROM posts AS T1 INNER JOIN users AS T2 ON T1.OwnerUserId = T2.Id
SELECT COUNT(Id) FROM badges WHERE Name = 'Commentator' AND STRFTIME('%Y', Date) = '2014'
SELECT COUNT(Id) FROM postHistory WHERE CreationDate LIKE '2010-07-21%'
SELECT DisplayName, Age FROM users WHERE Views = ( SELECT MAX(Views) FROM users )
SELECT LastEditDate, LastEditorUserId FROM posts WHERE Title = 'Detecting a given face in a database of facial images';
SELECT COUNT(*) FROM comments WHERE Score < 60 AND UserId = 13
SELECT DISTINCT T1.Title, T2.UserDisplayName FROM posts AS T1 INNER JOIN comments AS T2 ON T1.Id = T2.PostId WHERE T2.Score > 60
SELECT DISTINCT badges.Name FROM badges INNER JOIN users ON badges.UserId = users.Id WHERE users.Location = 'North Pole'   AND STRFTIME('%Y', badges.Date) = '2011';
SELECT u.DisplayName, u.WebsiteUrl FROM posts p INNER JOIN users u ON p.OwnerUserId = u.Id WHERE p.FavoriteCount > 150;
SELECT      COUNT(ph.Id) AS PostHistoryCount,      p.LastEditDate  FROM      posts p INNER JOIN      postHistory ph  ON      p.Id = ph.PostId WHERE      p.Title = 'What is the best introductory Bayesian statistics textbook?';
SELECT DISTINCT users.LastAccessDate, users.Location FROM badges INNER JOIN users ON badges.UserId = users.Id WHERE badges.Name = 'outliers';
SELECT T2.Title FROM postLinks AS T1 INNER JOIN posts AS T2 ON T1.PostId = T2.Id WHERE T2.Title = 'How to tell if something happened in a data set which monitors a value over time'
SELECT DISTINCT ph.PostId, b.Name FROM postHistory AS ph INNER JOIN users AS u ON ph.UserId = u.Id INNER JOIN badges AS b ON u.Id = b.UserId WHERE ph.UserDisplayName = 'Samuel'   AND STRFTIME('%Y', ph.CreationDate) = '2013'   AND STRFTIME('%Y', b.Date) = '2013';
SELECT OwnerDisplayName  FROM posts  ORDER BY ViewCount DESC  LIMIT 1;
SELECT u.DisplayName, u.Location FROM tags t INNER JOIN posts p ON t.ExcerptPostId = p.Id INNER JOIN users u ON p.OwnerUserId = u.Id WHERE t.TagName = 'hypothesis-testing';
SELECT p2.Title, pl.LinkTypeId FROM posts p1 INNER JOIN postLinks pl ON p1.Id = pl.PostId INNER JOIN posts p2 ON pl.RelatedPostId = p2.Id WHERE p1.Title = 'What are principal component scores?';
SELECT T1.OwnerDisplayName FROM posts AS T1 INNER JOIN posts AS T2 ON T1.Id = T2.ParentId ORDER BY T2.Score DESC LIMIT 1
SELECT DisplayName, WebsiteUrl FROM users WHERE Id = ( SELECT UserId FROM votes WHERE VoteTypeId = 8 ORDER BY BountyAmount DESC LIMIT 1 )
SELECT Title  FROM posts  ORDER BY ViewCount DESC  LIMIT 5;
SELECT COUNT(*)  FROM tags  WHERE Count BETWEEN 5000 AND 7000;
SELECT OwnerUserId  FROM posts  WHERE FavoriteCount = (SELECT MAX(FavoriteCount) FROM posts);
SELECT Age FROM users WHERE Reputation = ( SELECT MAX(Reputation) FROM users )
SELECT COUNT(PostId) FROM votes WHERE BountyAmount = 50 AND STRFTIME('%Y', CreationDate) = '2011'
SELECT Id FROM users ORDER BY Age LIMIT 1
SELECT Score FROM posts WHERE Id = ( SELECT ExcerptPostId FROM tags ORDER BY Count DESC LIMIT 1 )
SELECT CAST(COUNT(CASE WHEN T2.AnswerCount <= 2 THEN T1.Id ELSE NULL END) AS REAL) / 12 FROM postLinks AS T1 INNER JOIN posts AS T2 ON T1.PostId = T2.Id WHERE T1.CreationDate LIKE '2010%'
SELECT p.Id FROM votes v INNER JOIN posts p ON v.PostId = p.Id WHERE v.UserId = 1465 ORDER BY p.FavoriteCount DESC LIMIT 1;
SELECT p.Title FROM posts p INNER JOIN postLinks pl ON p.Id = pl.PostId ORDER BY pl.CreationDate ASC LIMIT 1;
SELECT u.DisplayName FROM badges b INNER JOIN users u ON b.UserId = u.Id GROUP BY b.UserId ORDER BY COUNT(b.Name) DESC LIMIT 1;
SELECT MIN(v.CreationDate) FROM votes AS v INNER JOIN users AS u ON v.UserId = u.Id WHERE u.DisplayName = 'chl';
SELECT T2.CreaionDate FROM users AS T1 INNER JOIN posts AS T2 ON T1.Id = T2.OwnerUserId ORDER BY T1.Age LIMIT 1
SELECT T1.DisplayName FROM users AS T1 INNER JOIN badges AS T2 ON T1.Id = T2.UserId WHERE T2.Name = 'Autobiographer' ORDER BY T2.Date ASC LIMIT 1
SELECT COUNT(DISTINCT users.Id)  FROM users  INNER JOIN posts  ON users.Id = posts.OwnerUserId  WHERE users.Location = 'United Kingdom'    AND posts.FavoriteCount >= 4;
SELECT CAST(SUM(T2.PostId) AS REAL) / COUNT(DISTINCT T2.UserId) FROM users AS T1 INNER JOIN votes AS T2 ON T1.Id = T2.UserId WHERE T1.Age = ( SELECT MAX(Age) FROM users )
SELECT DisplayName FROM users WHERE Reputation = ( SELECT MAX(Reputation) FROM users )
SELECT COUNT(*)  FROM users  WHERE Reputation > 2000 AND Views > 1000;
SELECT DisplayName FROM users WHERE Age BETWEEN 19 AND 65
SELECT COUNT(*)  FROM posts  WHERE OwnerDisplayName = 'Jay Stevens'    AND STRFTIME('%Y', CreaionDate) = '2010';
SELECT posts.Id, posts.Title FROM posts INNER JOIN users ON posts.OwnerUserId = users.Id WHERE users.DisplayName = 'Harvey Motulsky' ORDER BY posts.ViewCount DESC LIMIT 1;
SELECT Id, Title FROM posts ORDER BY Score DESC LIMIT 1;
SELECT CAST(SUM(T2.Score) AS REAL) / COUNT(T2.OwnerUserId) FROM users AS T1 INNER JOIN posts AS T2 ON T1.Id = T2.OwnerUserId WHERE T1.DisplayName = 'Stephen Turner'
SELECT DISTINCT OwnerDisplayName FROM posts WHERE ViewCount > 20000   AND STRFTIME('%Y', CreaionDate) = '2011';
SELECT Id, OwnerDisplayName FROM posts WHERE STRFTIME('%Y', CreaionDate) = '2010' ORDER BY FavoriteCount DESC LIMIT 1;
SELECT CAST(SUM(IIF(STRFTIME('%Y', T2.CreaionDate) = '2011' AND T1.Reputation > 1000, 1, 0)) AS REAL) * 100 / COUNT(T1.Id) FROM users AS T1 INNER JOIN posts AS T2 ON T1.Id = T2.OwnerUserId
SELECT CAST(COUNT(CASE WHEN Age BETWEEN 13 AND 18 THEN Id ELSE NULL END) AS REAL) * 100 / COUNT(Id) FROM users
SELECT T2.ViewCount, T3.DisplayName FROM postHistory AS T1 INNER JOIN posts AS T2 ON T1.PostId = T2.Id INNER JOIN users AS T3 ON T2.LastEditorUserId = T3.Id WHERE T1.Text = 'Computer Game Datasets'
SELECT COUNT(ViewCount) FROM posts WHERE ViewCount > ( SELECT AVG(ViewCount) FROM posts )
SELECT COUNT(T1.Id) FROM comments AS T1 INNER JOIN posts AS T2 ON T1.PostId = T2.Id GROUP BY T2.Id ORDER BY T2.Score DESC LIMIT 1
SELECT COUNT(*) FROM posts WHERE ViewCount > 35000 AND CommentCount = 0
SELECT T2.DisplayName, T2.Location FROM posts AS T1 INNER JOIN users AS T2 ON T1.OwnerUserId = T2.Id WHERE T2.Id = 183 ORDER BY T1.LastEditDate DESC LIMIT 1
SELECT badges.Name FROM badges INNER JOIN users ON badges.UserId = users.Id WHERE users.DisplayName = 'Emmett' ORDER BY badges.Date DESC LIMIT 1;
SELECT COUNT(Id) FROM users WHERE Age BETWEEN 19 AND 65 AND UpVotes > 5000
SELECT T1.CreationDate, T2.Date FROM users AS T1 INNER JOIN badges AS T2 ON T1.Id = T2.UserId WHERE T1.DisplayName = 'Zolomon'
SELECT COUNT(T1.Id) FROM posts AS T1 INNER JOIN users AS T2 ON T1.OwnerUserId = T2.Id ORDER BY T2.CreationDate DESC LIMIT 1
SELECT T2.Text, T2.UserDisplayName FROM posts AS T1 INNER JOIN comments AS T2 ON T1.Id = T2.PostId WHERE T1.Title = 'Analysing wind data with R' ORDER BY T2.CreationDate DESC LIMIT 1
SELECT COUNT(DISTINCT UserId) FROM badges WHERE Name = 'Citizen Patrol'
SELECT COUNT(Id) FROM tags WHERE TagName = 'careers'
SELECT Reputation, Views FROM users WHERE DisplayName = 'Jarrod Dixon'
SELECT CommentCount, AnswerCount  FROM posts  WHERE Title = 'Clustering 1D data';
SELECT DISTINCT CreationDate  FROM users  WHERE DisplayName = 'IrishStat';
SELECT COUNT(Id) FROM votes WHERE BountyAmount >= 30
SELECT CAST(SUM(CASE WHEN T2.Score > 50 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T2.Id) FROM users AS T1 INNER JOIN posts AS T2 ON T1.Id = T2.OwnerUserId WHERE T1.Reputation = ( SELECT MAX(Reputation) FROM users )
SELECT COUNT(Id)  FROM posts  WHERE Score < 20;
SELECT COUNT(TagName) FROM tags WHERE ID < 15 AND Count <= 20
SELECT ExcerptPostId, WikiPostId  FROM tags  WHERE TagName = 'sample';
SELECT users.Reputation, users.UpVotes FROM comments INNER JOIN users ON comments.UserId = users.Id WHERE comments.Text = 'fine, you win :)';
SELECT T1.Text FROM comments AS T1 INNER JOIN posts AS T2 ON T1.PostId = T2.Id WHERE T2.Title = 'How can I adapt ANOVA for binary data?'
SELECT Text FROM comments WHERE PostId IN ( SELECT Id FROM posts WHERE ViewCount BETWEEN 100 AND 150 ) ORDER BY Score DESC LIMIT 1
SELECT T2.CreationDate, T1.Age FROM users AS T1 INNER JOIN comments AS T2 ON T1.Id = T2.UserId WHERE T1.WebsiteUrl LIKE 'http%'
SELECT COUNT(T1.PostId) FROM comments AS T1 INNER JOIN posts AS T2 ON T1.PostId = T2.Id WHERE T1.Score = 0 AND T2.ViewCount < 5
SELECT SUM(CASE WHEN T2.Score = 0 THEN 1 ELSE 0 END) FROM posts AS T1 INNER JOIN comments AS T2 ON T1.Id = T2.PostId WHERE T1.CommentCount = 1
SELECT COUNT(*) FROM comments INNER JOIN users ON comments.UserId = users.Id WHERE comments.Score = 0 AND users.Age = 40;
SELECT posts.Id, comments.Text FROM posts INNER JOIN comments ON posts.Id = comments.PostId WHERE posts.Title = 'Group differences on a five point Likert item';
SELECT T2.UpVotes FROM comments AS T1 INNER JOIN users AS T2 ON T1.UserId = T2.Id WHERE T1.Text = 'R is also lazy evaluated.'
SELECT Text FROM comments WHERE UserId = ( SELECT Id FROM users WHERE DisplayName = 'Harvey Motulsky' )
SELECT DISTINCT users.DisplayName FROM comments INNER JOIN users ON comments.UserId = users.Id WHERE comments.Score BETWEEN 1 AND 5   AND users.DownVotes = 0;
SELECT      CAST(SUM(CASE WHEN T2.UpVotes = 0 THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(*) AS percentage FROM      comments AS T1 INNER JOIN      users AS T2 ON      T1.UserId = T2.Id WHERE      T1.Score BETWEEN 5 AND 10;
SELECT sp.power_name FROM superhero AS s INNER JOIN hero_power AS hp ON s.id = hp.hero_id INNER JOIN superpower AS sp ON hp.power_id = sp.id WHERE s.superhero_name = '3-D Man';
SELECT COUNT(*) FROM hero_power AS T1 INNER JOIN superpower AS T2 ON T1.power_id = T2.id WHERE T2.power_name = 'Super Strength'
SELECT COUNT(*) FROM ( SELECT T1.id FROM superhero AS T1 INNER JOIN hero_power AS T2 ON T1.id = T2.hero_id INNER JOIN superpower AS T3 ON T2.power_id = T3.id WHERE T3.power_name = 'Super Strength' AND T1.height_cm > 200 )
SELECT T1.full_name FROM superhero AS T1 INNER JOIN hero_power AS T2 ON T1.id = T2.hero_id GROUP BY T1.id, T1.full_name HAVING COUNT(T2.power_id) > 15
SELECT COUNT(T1.id) FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.eye_colour_id = T2.id WHERE T2.colour = 'Blue'
SELECT T2.colour FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.skin_colour_id = T2.id WHERE T1.superhero_name = 'Apocalypse'
SELECT COUNT(DISTINCT T1.id) FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.eye_colour_id = T2.id INNER JOIN hero_power AS T3 ON T1.id = T3.hero_id INNER JOIN superpower AS T4 ON T3.power_id = T4.id WHERE T2.colour = 'Blue' AND T4.power_name = 'Agility'
SELECT T1.superhero_name FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.eye_colour_id = T2.id WHERE T2.colour = 'Blue' INTERSECT SELECT T1.superhero_name FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.hair_colour_id = T2.id WHERE T2.colour = 'Blond'
SELECT COUNT(superhero.id) FROM superhero INNER JOIN publisher ON superhero.publisher_id = publisher.id WHERE publisher.publisher_name = 'Marvel Comics';
SELECT T1.full_name FROM superhero AS T1 INNER JOIN publisher AS T2 ON T1.publisher_id = T2.id WHERE T2.publisher_name = 'Marvel Comics' ORDER BY T1.height_cm DESC LIMIT 1
SELECT publisher.publisher_name FROM superhero INNER JOIN publisher ON superhero.publisher_id = publisher.id WHERE superhero.superhero_name = 'Sauron';
SELECT COUNT(*) AS blue_eyed_superheroes FROM superhero INNER JOIN colour ON superhero.eye_colour_id = colour.id INNER JOIN publisher ON superhero.publisher_id = publisher.id WHERE colour.colour = 'Blue' AND publisher.publisher_name = 'Marvel Comics';
SELECT AVG(T1.height_cm) FROM superhero AS T1 INNER JOIN publisher AS T2 ON T1.publisher_id = T2.id WHERE T2.publisher_name = 'Marvel Comics'
SELECT      CAST(SUM(CASE WHEN sp.power_name = 'Super Strength' THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(h.id) AS percentage FROM      superhero h INNER JOIN      publisher p ON h.publisher_id = p.id INNER JOIN      hero_power hp ON h.id = hp.hero_id INNER JOIN      superpower sp ON hp.power_id = sp.id WHERE      p.publisher_name = 'Marvel Comics';
SELECT COUNT(*)  FROM superhero  INNER JOIN publisher  ON superhero.publisher_id = publisher.id  WHERE publisher.publisher_name = 'DC Comics';
SELECT p.publisher_name FROM hero_attribute ha INNER JOIN attribute a ON ha.attribute_id = a.id INNER JOIN superhero s ON ha.hero_id = s.id INNER JOIN publisher p ON s.publisher_id = p.id WHERE a.attribute_name = 'Speed' ORDER BY ha.attribute_value ASC LIMIT 1;
SELECT COUNT(*) AS gold_eyed_superheroes FROM superhero INNER JOIN colour ON superhero.eye_colour_id = colour.id INNER JOIN publisher ON superhero.publisher_id = publisher.id WHERE colour.colour = 'Gold' AND publisher.publisher_name = 'Marvel Comics';
SELECT publisher.publisher_name FROM superhero INNER JOIN publisher ON superhero.publisher_id = publisher.id WHERE superhero.superhero_name = 'Blue Beetle II';
SELECT COUNT(*)  FROM superhero  INNER JOIN colour ON superhero.hair_colour_id = colour.id  WHERE colour.colour = 'Blond';
SELECT s.superhero_name FROM hero_attribute ha INNER JOIN attribute a ON ha.attribute_id = a.id INNER JOIN superhero s ON ha.hero_id = s.id WHERE a.attribute_name = 'Intelligence' ORDER BY ha.attribute_value ASC LIMIT 1;
SELECT race.race FROM superhero INNER JOIN race ON superhero.race_id = race.id WHERE superhero.superhero_name = 'Copycat';
SELECT COUNT(T1.attribute_value) FROM hero_attribute AS T1 INNER JOIN attribute AS T2 ON T1.attribute_id = T2.id WHERE T2.attribute_name = 'Durability' AND T1.attribute_value < 50
SELECT T1.superhero_name FROM superhero AS T1 INNER JOIN hero_power AS T2 ON T1.id = T2.hero_id INNER JOIN superpower AS T3 ON T2.power_id = T3.id WHERE T3.power_name = 'Death Touch'
SELECT COUNT(T1.id) FROM superhero AS T1 INNER JOIN hero_attribute AS T2 ON T1.id = T2.hero_id INNER JOIN attribute AS T3 ON T2.attribute_id = T3.id INNER JOIN gender AS T4 ON T1.gender_id = T4.id WHERE T3.attribute_name = 'Strength' AND T2.attribute_value = 100 AND T4.gender = 'Female'
SELECT T1.superhero_name FROM superhero AS T1 INNER JOIN hero_power AS T2 ON T1.id = T2.hero_id GROUP BY T1.superhero_name ORDER BY COUNT(T1.superhero_name) DESC LIMIT 1
SELECT COUNT(*)  FROM superhero  INNER JOIN race ON superhero.race_id = race.id  WHERE race.race = 'Vampire';
SELECT CAST(SUM(CASE WHEN T2.publisher_name = 'Marvel Comics' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.id) FROM alignment AS T1 INNER JOIN publisher AS T2 ON T1.id = T2.id WHERE T1.alignment = 'Bad'
SELECT SUM(IIF(T2.publisher_name = 'Marvel Comics', 1, 0)) - SUM(IIF(T2.publisher_name = 'DC Comics', 1, 0)) FROM superhero AS T1 INNER JOIN publisher AS T2 ON T1.publisher_id = T2.id
SELECT id FROM publisher WHERE publisher_name = 'Star Trek'
SELECT AVG(attribute_value) FROM hero_attribute
SELECT COUNT(*) FROM superhero WHERE full_name IS NULL
SELECT T2.colour FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.eye_colour_id = T2.id WHERE T1.id = 75
SELECT T3.power_name FROM superhero AS T1 INNER JOIN hero_power AS T2 ON T1.id = T2.hero_id INNER JOIN superpower AS T3 ON T2.power_id = T3.id WHERE T1.superhero_name = 'Deathlok'
SELECT AVG(weight_kg)  FROM superhero  WHERE gender_id = 2;
SELECT T3.power_name FROM superhero AS T1 INNER JOIN gender AS T2 ON T1.gender_id = T2.id INNER JOIN superpower AS T3 ON T1.id = T3.id WHERE T2.gender = 'Male' LIMIT 5
SELECT superhero.superhero_name FROM superhero INNER JOIN race ON superhero.race_id = race.id WHERE race.race = 'Alien';
SELECT superhero_name FROM superhero WHERE height_cm BETWEEN 170 AND 190   AND eye_colour_id = 1;
SELECT superpower.power_name FROM hero_power INNER JOIN superpower ON hero_power.power_id = superpower.id WHERE hero_power.hero_id = 56;
SELECT T1.full_name FROM superhero AS T1 INNER JOIN race AS T2 ON T1.race_id = T2.id WHERE T2.race = 'Demi-God'
SELECT COUNT(*)  FROM superhero  INNER JOIN alignment  ON superhero.alignment_id = alignment.id  WHERE alignment.alignment = 'Bad';
SELECT race.race FROM superhero INNER JOIN race ON superhero.race_id = race.id WHERE superhero.weight_kg = 169;
SELECT T2.colour FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.hair_colour_id = T2.id INNER JOIN race AS T3 ON T3.id = T1.race_id WHERE T1.height_cm = 185 AND T3.race = 'Human'
SELECT T2.colour FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.eye_colour_id = T2.id ORDER BY T1.weight_kg DESC LIMIT 1
SELECT CAST(SUM(CASE WHEN T2.publisher_name = 'Marvel Comics' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM superhero AS T1 INNER JOIN publisher AS T2 ON T1.publisher_id = T2.id WHERE T1.height_cm BETWEEN 150 AND 180
SELECT T1.full_name FROM superhero AS T1 INNER JOIN gender AS T2 ON T1.gender_id = T2.id WHERE T1.weight_kg > ( SELECT AVG(T1.weight_kg) FROM superhero AS T1 INNER JOIN gender AS T2 ON T1.gender_id = T2.id WHERE T2.gender = 'Male' ) * 0.79
SELECT T2.power_name FROM hero_power AS T1 INNER JOIN superpower AS T2 ON T1.power_id = T2.id GROUP BY T2.power_name ORDER BY COUNT(T2.power_name) DESC LIMIT 1
SELECT T2.attribute_value FROM superhero AS T1 INNER JOIN hero_attribute AS T2 ON T1.id = T2.hero_id WHERE T1.superhero_name = 'Abomination'
SELECT superpower.power_name FROM hero_power INNER JOIN superpower ON hero_power.power_id = superpower.id WHERE hero_power.hero_id = 1;
SELECT COUNT(hero_power.hero_id) FROM hero_power INNER JOIN superpower ON hero_power.power_id = superpower.id WHERE superpower.power_name = 'Stealth';
SELECT T1.full_name FROM superhero AS T1 INNER JOIN hero_attribute AS T2 ON T1.id = T2.hero_id INNER JOIN attribute AS T3 ON T2.attribute_id = T3.id WHERE T3.attribute_name = 'Strength' ORDER BY T2.attribute_value DESC LIMIT 1
SELECT      CAST(SUM(CASE WHEN colour.colour = 'No Colour' THEN 1 ELSE 0 END) AS REAL) / COUNT(superhero.id) AS average_no_skin_colour FROM      superhero INNER JOIN      colour ON superhero.skin_colour_id = colour.id;
SELECT COUNT(superhero.id) FROM superhero INNER JOIN publisher ON superhero.publisher_id = publisher.id WHERE publisher.publisher_name = 'Dark Horse Comics';
SELECT T1.superhero_name FROM superhero AS T1 INNER JOIN hero_attribute AS T2 ON T1.id = T2.hero_id INNER JOIN attribute AS T3 ON T3.id = T2.attribute_id INNER JOIN publisher AS T4 ON T4.id = T1.publisher_id WHERE T4.publisher_name = 'Dark Horse Comics' AND T3.attribute_name = 'Durability' ORDER BY T2.attribute_value DESC LIMIT 1
SELECT T2.colour FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.eye_colour_id = T2.id WHERE T1.full_name = 'Abraham Sapien'
SELECT T1.superhero_name FROM superhero AS T1 INNER JOIN hero_power AS T2 ON T1.id = T2.hero_id INNER JOIN superpower AS T3 ON T2.power_id = T3.id WHERE T3.power_name = 'Flight'
SELECT T2.colour, T3.colour, T4.colour FROM superhero AS T1 INNER JOIN colour AS T2 ON T2.id = T1.eye_colour_id INNER JOIN colour AS T3 ON T3.id = T1.hair_colour_id INNER JOIN colour AS T4 ON T4.id = T1.skin_colour_id INNER JOIN publisher AS T5 ON T5.id = T1.publisher_id INNER JOIN gender AS T6 ON T6.id = T1.gender_id WHERE T5.publisher_name = 'Dark Horse Comics' AND T6.gender = 'Female'
SELECT T1.superhero_name, T5.publisher_name FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.eye_colour_id = T2.id INNER JOIN colour AS T3 ON T1.hair_colour_id = T3.id INNER JOIN colour AS T4 ON T1.skin_colour_id = T4.id INNER JOIN publisher AS T5 ON T1.publisher_id = T5.id WHERE T1.eye_colour_id = T1.hair_colour_id AND T1.eye_colour_id = T1.skin_colour_id
SELECT T2.race FROM superhero AS T1 INNER JOIN race AS T2 ON T1.race_id = T2.id WHERE T1.superhero_name = 'A-Bomb'
SELECT CAST(SUM(IIF(T4.colour = 'Blue', 1, 0)) AS REAL) * 100 / COUNT(T1.id) FROM superhero AS T1 INNER JOIN gender AS T2 ON T1.gender_id = T2.id INNER JOIN colour AS T4 ON T1.hair_colour_id = T4.id WHERE T2.gender = 'Female'
SELECT superhero.superhero_name, race.race FROM superhero INNER JOIN race ON superhero.race_id = race.id WHERE superhero.full_name = 'Charles Chandler';
SELECT gender.gender FROM superhero INNER JOIN gender ON superhero.gender_id = gender.id WHERE superhero.superhero_name = 'Agent 13';
SELECT T1.superhero_name FROM superhero AS T1 INNER JOIN hero_power AS T2 ON T1.id = T2.hero_id INNER JOIN superpower AS T3 ON T2.power_id = T3.id WHERE T3.power_name = 'Adaptation'
SELECT COUNT(*) AS power_count FROM hero_power INNER JOIN superhero ON hero_power.hero_id = superhero.id WHERE superhero.superhero_name = 'Amazo';
SELECT T3.power_name FROM superhero AS T1 INNER JOIN hero_power AS T2 ON T1.id = T2.hero_id INNER JOIN superpower AS T3 ON T2.power_id = T3.id WHERE T1.full_name = 'Hunter Zolomon'
SELECT superhero.height_cm FROM colour INNER JOIN superhero ON colour.id = superhero.eye_colour_id WHERE colour.colour = 'Amber';
SELECT T1.superhero_name FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.eye_colour_id = T2.id WHERE T2.colour = 'Black' INTERSECT SELECT T1.superhero_name FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.hair_colour_id = T2.id WHERE T2.colour = 'Black'
SELECT T2.colour FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.eye_colour_id = T2.id INNER JOIN colour AS T3 ON T1.skin_colour_id = T3.id WHERE T3.colour = 'Gold'
SELECT T1.full_name FROM superhero AS T1 INNER JOIN race AS T2 ON T1.race_id = T2.id WHERE T2.race = 'Vampire'
SELECT T1.superhero_name FROM superhero AS T1 INNER JOIN alignment AS T2 ON T1.alignment_id = T2.id WHERE T2.alignment = 'Neutral'
SELECT COUNT(T1.hero_id) FROM hero_attribute AS T1 INNER JOIN attribute AS T2 ON T1.attribute_id = T2.id WHERE T2.attribute_name = 'Strength' ORDER BY T1.attribute_value DESC LIMIT 1
SELECT r.race, a.alignment FROM superhero s INNER JOIN race r ON s.race_id = r.id INNER JOIN alignment a ON s.alignment_id = a.id WHERE s.superhero_name = 'Cameron Hicks';
SELECT      CAST(SUM(CASE WHEN g.gender = 'Female' THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(*) AS female_percentage FROM      superhero s INNER JOIN      gender g ON s.gender_id = g.id INNER JOIN      publisher p ON s.publisher_id = p.id WHERE      p.publisher_name = 'Marvel Comics';
SELECT AVG(superhero.weight_kg) FROM superhero INNER JOIN race ON superhero.race_id = race.id WHERE race.race = 'Alien';
SELECT SUM(CASE WHEN T1.full_name = 'Emil Blonsky' THEN T1.weight_kg ELSE 0 END) - SUM(CASE WHEN T1.full_name = 'Charles Chandler' THEN T1.weight_kg ELSE 0 END) AS weight FROM superhero AS T1
SELECT AVG(height_cm) FROM superhero
SELECT T3.power_name FROM superhero AS T1 INNER JOIN hero_power AS T2 ON T1.id = T2.hero_id INNER JOIN superpower AS T3 ON T2.power_id = T3.id WHERE T1.superhero_name = 'Abomination'
SELECT COUNT(*)  FROM superhero  WHERE race_id = 21 AND gender_id = 1;
SELECT T3.superhero_name FROM hero_attribute AS T1 INNER JOIN attribute AS T2 ON T1.attribute_id = T2.id INNER JOIN superhero AS T3 ON T1.hero_id = T3.id WHERE T2.attribute_name = 'Speed' ORDER BY T1.attribute_value DESC LIMIT 1;
SELECT COUNT(id) FROM superhero WHERE alignment_id = 3
SELECT a.attribute_name, ha.attribute_value FROM superhero AS s INNER JOIN hero_attribute AS ha ON s.id = ha.hero_id INNER JOIN attribute AS a ON ha.attribute_id = a.id WHERE s.superhero_name = '3-D Man';
SELECT superhero_name  FROM superhero  WHERE eye_colour_id = 7 AND hair_colour_id = 9;
SELECT DISTINCT publisher.publisher_name FROM superhero INNER JOIN publisher ON superhero.publisher_id = publisher.id WHERE superhero.superhero_name IN ('Hawkman', 'Karate Kid', 'Speedy');
SELECT COUNT(id) FROM superhero WHERE publisher_id = 1
SELECT CAST(SUM(CASE WHEN T1.eye_colour_id = 7 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.superhero_name) FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.eye_colour_id = T2.id
SELECT CAST(SUM(IIF(gender_id = 1, 1, 0)) AS REAL) / SUM(IIF(gender_id = 2, 1, 0)) FROM superhero
SELECT superhero_name FROM superhero WHERE height_cm = ( SELECT MAX(height_cm) FROM superhero )
SELECT id FROM superpower WHERE power_name = 'Cryokinesis';
SELECT superhero_name FROM superhero WHERE id = 294
SELECT full_name FROM superhero WHERE weight_kg = 0 OR weight_kg IS NULL
SELECT colour.colour FROM superhero INNER JOIN colour ON superhero.eye_colour_id = colour.id WHERE superhero.full_name = 'Karen Beecher-Duncan';
SELECT T3.power_name FROM superhero AS T1 INNER JOIN hero_power AS T2 ON T1.id = T2.hero_id INNER JOIN superpower AS T3 ON T2.power_id = T3.id WHERE T1.full_name = 'Helen Parr'
SELECT r.race FROM superhero AS s INNER JOIN race AS r ON s.race_id = r.id WHERE s.weight_kg = 108 AND s.height_cm = 188;
SELECT publisher.publisher_name FROM superhero INNER JOIN publisher ON superhero.publisher_id = publisher.id WHERE superhero.id = 38;
SELECT r.race FROM hero_attribute AS ha INNER JOIN superhero AS s ON ha.hero_id = s.id INNER JOIN race AS r ON s.race_id = r.id ORDER BY ha.attribute_value DESC LIMIT 1;
SELECT T2.alignment, T4.power_name FROM superhero AS T1 INNER JOIN alignment AS T2 ON T1.alignment_id = T2.id INNER JOIN hero_power AS T3 ON T1.id = T3.hero_id INNER JOIN superpower AS T4 ON T3.power_id = T4.id WHERE T1.superhero_name = 'Atom IV'
SELECT T1.full_name FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.eye_colour_id = T2.id WHERE T2.colour = 'Blue' LIMIT 5;
SELECT AVG(T1.attribute_value) FROM hero_attribute AS T1 INNER JOIN superhero AS T2 ON T1.hero_id = T2.id WHERE T2.alignment_id = 3;
SELECT T3.colour FROM superhero AS T1 INNER JOIN hero_attribute AS T2 ON T1.id = T2.hero_id INNER JOIN colour AS T3 ON T1.skin_colour_id = T3.id WHERE T2.attribute_value = 100
SELECT COUNT(*) AS good_female_superheroes FROM superhero WHERE alignment_id = 1 AND gender_id = 2;
SELECT superhero.superhero_name FROM superhero INNER JOIN hero_attribute ON superhero.id = hero_attribute.hero_id WHERE hero_attribute.attribute_value BETWEEN 75 AND 80;
SELECT DISTINCT r.race FROM superhero AS s INNER JOIN race AS r ON s.race_id = r.id INNER JOIN gender AS g ON s.gender_id = g.id INNER JOIN colour AS c ON s.hair_colour_id = c.id WHERE g.gender = 'Male' AND c.colour = 'Blue';
SELECT CAST(SUM(CASE WHEN T1.id = 2 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T2.id) FROM gender AS T1 INNER JOIN superhero AS T2 ON T1.id = T2.gender_id INNER JOIN alignment AS T3 ON T2.alignment_id = T3.id WHERE T3.id = 2
SELECT SUM(IIF(T2.id = 7, 1, 0)) - SUM(IIF(T2.id = 1, 1, 0)) FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.eye_colour_id = T2.id WHERE T1.weight_kg = 0 OR T1.weight_kg IS NULL
SELECT T2.attribute_value FROM superhero AS T1 INNER JOIN hero_attribute AS T2 ON T1.id = T2.hero_id INNER JOIN attribute AS T3 ON T2.attribute_id = T3.id WHERE T1.superhero_name = 'Hulk' AND T3.attribute_name = 'Strength'
SELECT sp.power_name FROM superhero AS s INNER JOIN hero_power AS hp ON s.id = hp.hero_id INNER JOIN superpower AS sp ON hp.power_id = sp.id WHERE s.superhero_name = 'Ajax';
SELECT COUNT(superhero.id) FROM superhero INNER JOIN colour ON superhero.skin_colour_id = colour.id INNER JOIN alignment ON superhero.alignment_id = alignment.id WHERE colour.colour = 'Green' AND alignment.alignment = 'Bad';
SELECT COUNT(*) FROM superhero AS T1 INNER JOIN publisher AS T2 ON T1.publisher_id = T2.id INNER JOIN gender AS T3 ON T1.gender_id = T3.id WHERE T2.publisher_name = 'Marvel Comics' AND T3.gender = 'Female'
SELECT T1.superhero_name FROM superhero AS T1 INNER JOIN hero_power AS T2 ON T1.id = T2.hero_id INNER JOIN superpower AS T3 ON T2.power_id = T3.id WHERE T3.power_name = 'Wind Control' ORDER BY T1.superhero_name;
SELECT T4.gender FROM superhero AS T1 INNER JOIN hero_power AS T2 ON T1.id = T2.hero_id INNER JOIN superpower AS T3 ON T2.power_id = T3.id INNER JOIN gender AS T4 ON T1.gender_id = T4.id WHERE T3.power_name = 'Phoenix Force'
SELECT T1.superhero_name FROM superhero AS T1 INNER JOIN publisher AS T2 ON T1.publisher_id = T2.id WHERE T2.publisher_name = 'DC Comics' ORDER BY T1.weight_kg DESC LIMIT 1
SELECT AVG(superhero.height_cm) FROM superhero INNER JOIN race ON superhero.race_id = race.id INNER JOIN publisher ON superhero.publisher_id = publisher.id WHERE race.race <> 'Human'   AND publisher.publisher_name = 'Dark Horse Comics';
SELECT COUNT(T2.hero_id) FROM attribute AS T1 INNER JOIN hero_attribute AS T2 ON T1.id = T2.attribute_id WHERE T2.attribute_value = 100 AND T1.attribute_name = 'Speed'
SELECT SUM(IIF(publisher_name = 'DC Comics', 1, 0)) - SUM(IIF(publisher_name = 'Marvel Comics', 1, 0)) FROM publisher
SELECT T3.attribute_name FROM superhero AS T1 INNER JOIN hero_attribute AS T2 ON T1.id = T2.hero_id INNER JOIN attribute AS T3 ON T2.attribute_id = T3.id WHERE T1.superhero_name = 'Black Panther' ORDER BY T2.attribute_value ASC LIMIT 1
SELECT T2.colour FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.eye_colour_id = T2.id WHERE T1.superhero_name = 'Abomination'
SELECT superhero_name  FROM superhero  ORDER BY height_cm DESC  LIMIT 1;
SELECT superhero_name FROM superhero WHERE full_name = 'Charles Chandler'
SELECT      CAST(SUM(CASE WHEN gender.gender = 'Female' THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(*) AS female_percentage FROM      superhero INNER JOIN      publisher ON superhero.publisher_id = publisher.id INNER JOIN      gender ON superhero.gender_id = gender.id WHERE      publisher.publisher_name = 'George Lucas';
SELECT      CAST(SUM(CASE WHEN T3.alignment = 'Good' THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(T1.id) AS good_superhero_percentage FROM      superhero AS T1 INNER JOIN      publisher AS T2 ON T1.publisher_id = T2.id INNER JOIN      alignment AS T3 ON T1.alignment_id = T3.id WHERE      T2.publisher_name = 'Marvel Comics';
SELECT COUNT(id) FROM superhero WHERE full_name LIKE 'John%'
SELECT hero_id FROM hero_attribute ORDER BY attribute_value ASC LIMIT 1
SELECT DISTINCT full_name  FROM superhero  WHERE superhero_name = 'Alien';
SELECT superhero.full_name FROM superhero INNER JOIN colour ON superhero.eye_colour_id = colour.id WHERE superhero.weight_kg < 100 AND colour.colour = 'Brown';
SELECT T2.attribute_value FROM superhero AS T1 INNER JOIN hero_attribute AS T2 ON T1.id = T2.hero_id WHERE T1.superhero_name = 'Aquababy'
SELECT T1.weight_kg, T2.race FROM superhero AS T1 INNER JOIN race AS T2 ON T1.race_id = T2.id WHERE T1.id = 40
SELECT AVG(superhero.height_cm) FROM superhero INNER JOIN alignment ON superhero.alignment_id = alignment.id WHERE alignment.alignment = 'Neutral';
SELECT T1.id FROM superhero AS T1 INNER JOIN hero_power AS T2 ON T1.id = T2.hero_id INNER JOIN superpower AS T3 ON T2.power_id = T3.id WHERE T3.power_name = 'Intelligence'
SELECT T2.colour FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.eye_colour_id = T2.id WHERE T1.superhero_name = 'Blackwulf'
SELECT T3.power_name FROM superhero AS T1 INNER JOIN hero_power AS T2 ON T1.id = T2.hero_id INNER JOIN superpower AS T3 ON T2.power_id = T3.id WHERE T1.height_cm > ( SELECT AVG(T1.height_cm) * 0.8 FROM superhero AS T1 )
SELECT driverRef FROM drivers WHERE driverId IN ( SELECT driverId FROM qualifying WHERE raceId = 18 ORDER BY q1 DESC LIMIT 5 )
SELECT d.surname FROM qualifying q INNER JOIN drivers d ON q.driverId = d.driverId WHERE q.raceId = 19 ORDER BY q.q2 ASC LIMIT 1;
SELECT races.year FROM races INNER JOIN circuits ON races.circuitId = circuits.circuitId WHERE circuits.location = 'Shanghai';
SELECT races.url FROM races INNER JOIN circuits ON races.circuitId = circuits.circuitId WHERE circuits.name = 'Circuit de Barcelona-Catalunya';
SELECT races.name FROM races INNER JOIN circuits ON races.circuitId = circuits.circuitId WHERE circuits.country = 'Germany';
SELECT DISTINCT T1.position FROM constructorStandings AS T1 INNER JOIN constructors AS T2 ON T1.constructorId = T2.constructorId WHERE T2.name = 'Renault';
SELECT COUNT(*)  FROM races  INNER JOIN circuits ON races.circuitId = circuits.circuitId  WHERE races.year = 2010    AND circuits.country NOT IN ('Asia', 'Europe');
SELECT DISTINCT T2.name FROM circuits AS T1 INNER JOIN races AS T2 ON T2.circuitId = T1.circuitId WHERE T1.country = 'Spain'
SELECT DISTINCT T1.lat, T1.lng FROM circuits AS T1 INNER JOIN races AS T2 ON T2.circuitId = T1.circuitId WHERE T2.name = 'Australian Grand Prix'
SELECT DISTINCT T2.url FROM circuits AS T1 INNER JOIN races AS T2 ON T2.circuitId = T1.circuitId WHERE T1.name = 'Sepang International Circuit'
SELECT DISTINCT T2.time FROM circuits AS T1 INNER JOIN races AS T2 ON T2.circuitId = T1.circuitId WHERE T1.name = 'Sepang International Circuit'
SELECT DISTINCT T1.lat, T1.lng FROM circuits AS T1 INNER JOIN races AS T2 ON T2.circuitId = T1.circuitId WHERE T2.name = 'Abu Dhabi Grand Prix'
SELECT DISTINCT constructors.nationality FROM constructorResults INNER JOIN constructors ON constructorResults.constructorId = constructors.constructorId WHERE constructorResults.raceId = 24 AND constructorResults.points = 1;
SELECT q1 FROM qualifying WHERE driverId = ( SELECT driverId FROM drivers WHERE forename = 'Bruno' AND surname = 'Senna' ) AND raceId = 354
SELECT DISTINCT T2.nationality FROM qualifying AS T1 INNER JOIN drivers AS T2 ON T2.driverId = T1.driverId WHERE T1.raceId = 355 AND T1.q2 LIKE '1:40%'
SELECT T2.number FROM qualifying AS T1 INNER JOIN drivers AS T2 ON T2.driverId = T1.driverId WHERE T1.raceId = 903 AND T1.q3 LIKE '1:54%'
SELECT COUNT(T2.driverId) FROM races AS T1 INNER JOIN results AS T2 ON T2.raceId = T1.raceId WHERE T1.year = 2007 AND T1.name = 'Bahrain Grand Prix' AND T2.time IS NULL
SELECT DISTINCT seasons.url FROM races INNER JOIN seasons ON races.year = seasons.year WHERE races.raceId = 901;
SELECT COUNT(driverId) FROM results WHERE raceId = ( SELECT raceId FROM races WHERE date = '2015-11-29' )
SELECT T2.forename, T2.surname FROM results AS T1 INNER JOIN drivers AS T2 ON T1.driverId = T2.driverId WHERE T1.raceId = 592 AND T1.time <> '' ORDER BY T2.dob ASC LIMIT 1
SELECT T1.url FROM drivers AS T1 INNER JOIN results AS T2 ON T1.driverId = T2.driverId INNER JOIN races AS T3 ON T2.raceId = T3.raceId INNER JOIN lapTimes AS T4 ON T2.driverId = T4.driverId WHERE T3.raceId = 161 AND T4.time = '0:01:27'
SELECT T1.nationality FROM drivers AS T1 INNER JOIN results AS T2 ON T1.driverId = T2.driverId WHERE T2.fastestLapSpeed = ( SELECT MAX(fastestLapSpeed) FROM results WHERE raceId = 933 ) AND T2.raceId = 933
SELECT DISTINCT T1.lat, T1.lng FROM circuits AS T1 INNER JOIN races AS T2 ON T2.circuitId = T1.circuitId WHERE T2.name = 'Malaysian Grand Prix'
SELECT T1.url FROM constructors AS T1 INNER JOIN constructorStandings AS T2 ON T1.constructorId = T2.constructorId WHERE T2.raceId = 9 ORDER BY T2.points DESC LIMIT 1
SELECT T1.q1 FROM qualifying AS T1 INNER JOIN drivers AS T2 ON T2.driverId = T1.driverId WHERE T1.raceId = 345 AND T2.forename = 'Lucas' AND T2.surname = 'di Grassi'
SELECT DISTINCT T2.nationality FROM qualifying AS T1 INNER JOIN drivers AS T2 ON T2.driverId = T1.driverId WHERE T1.raceId = 347 AND T1.q2 LIKE '1:15%'
SELECT T2.code FROM qualifying AS T1 INNER JOIN drivers AS T2 ON T2.driverId = T1.driverId WHERE T1.raceId = 45 AND T1.q3 LIKE '1:33%'
SELECT T1.milliseconds FROM results AS T1 INNER JOIN drivers AS T2 ON T1.driverId = T2.driverId WHERE T2.forename = 'Bruce' AND T2.surname = 'McLaren' AND T1.raceId = 743
SELECT T1.surname FROM drivers AS T1 INNER JOIN results AS T2 ON T1.driverId = T2.driverId INNER JOIN races AS T3 ON T2.raceId = T3.raceId WHERE T3.name = 'San Marino Grand Prix' AND T3.year = 2006 AND T2.position = 2
SELECT DISTINCT seasons.url FROM races INNER JOIN seasons ON races.year = seasons.year WHERE races.raceId = 901;
SELECT COUNT(DISTINCT T1.driverId) FROM results AS T1 INNER JOIN races AS T2 ON T1.raceId = T2.raceId WHERE T2.date = '2015-11-29'
SELECT T2.forename, T2.surname FROM results AS T1 INNER JOIN drivers AS T2 ON T1.driverId = T2.driverId WHERE T1.raceId = 872 AND T1.time <> '' ORDER BY T2.dob DESC LIMIT 1
SELECT DISTINCT drivers.forename, drivers.surname FROM lapTimes INNER JOIN drivers ON lapTimes.driverId = drivers.driverId WHERE lapTimes.raceId = 348 ORDER BY lapTimes.time ASC LIMIT 1;
SELECT d.nationality FROM results r INNER JOIN drivers d ON r.driverId = d.driverId ORDER BY r.fastestLapSpeed DESC LIMIT 1;
SELECT CAST((SELECT T1.fastestLapSpeed FROM results AS T1 INNER JOIN drivers AS T2 ON T1.driverId = T2.driverId WHERE T2.forename = 'Paul' AND T2.surname = 'di Resta' AND T1.raceId = 853) - ( SELECT T1.fastestLapSpeed FROM results AS T1 INNER JOIN drivers AS T2 ON T1.driverId = T2.driverId WHERE T2.forename = 'Paul' AND T2.surname = 'di Resta' AND T1.raceId = 854) AS REAL) * 100 / ( SELECT T1.fastestLapSpeed FROM results AS T1 INNER JOIN drivers AS T2 ON T1.driverId = T2.driverId WHERE T2.forename = 'Paul' AND T2.surname = 'di Resta' AND T1.raceId = 853)
SELECT CAST(SUM(CASE WHEN T1.time IS NOT NULL THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM results AS T1 INNER JOIN races AS T2 ON T1.raceId = T2.raceId WHERE T2.date = '1983-07-16'
SELECT year FROM races WHERE name = 'Singapore Grand Prix' ORDER BY year ASC LIMIT 1
SELECT name FROM races WHERE year = 2005 ORDER BY name DESC
SELECT name FROM races WHERE STRFTIME('%Y-%m', date) = ( SELECT STRFTIME('%Y-%m', date) FROM races ORDER BY date ASC LIMIT 1 )
SELECT name, date FROM races WHERE year = 1999 ORDER BY round DESC LIMIT 1
SELECT year FROM races GROUP BY year ORDER BY COUNT(round) DESC LIMIT 1
SELECT name FROM races WHERE year = 2017
SELECT T1.name, T1.location FROM circuits AS T1 INNER JOIN races AS T2 ON T1.circuitId = T2.circuitId WHERE T2.name = 'European Grand Prix' ORDER BY T2.year LIMIT 1
SELECT MAX(races.year) FROM races INNER JOIN circuits ON races.circuitId = circuits.circuitId WHERE races.name = 'British Grand Prix' AND circuits.name = 'Brands Hatch';
SELECT COUNT(T2.year) FROM circuits AS T1 INNER JOIN races AS T2 ON T1.circuitid = T2.circuitid WHERE T1.name = 'Silverstone Circuit' AND T2.name = 'British Grand Prix'
SELECT d.forename, d.surname FROM races r INNER JOIN results res ON r.raceId = res.raceId INNER JOIN drivers d ON res.driverId = d.driverId WHERE r.year = 2010 AND r.name = 'Singapore Grand Prix' ORDER BY res.position;
SELECT T2.forename, T2.surname, T1.points FROM results AS T1 INNER JOIN drivers AS T2 ON T1.driverId = T2.driverId GROUP BY T2.driverId ORDER BY SUM(T1.points) DESC LIMIT 1
SELECT d.forename, d.surname, r.points FROM races AS ra INNER JOIN results AS r ON ra.raceId = r.raceId INNER JOIN drivers AS d ON r.driverId = d.driverId WHERE ra.year = 2017 AND ra.name = 'Chinese Grand Prix' ORDER BY r.points DESC LIMIT 3;
SELECT T1.driverId, T1.raceId FROM results AS T1 INNER JOIN races AS T2 ON T1.raceId = T2.raceId WHERE T1.fastestLapTime = ( SELECT MIN(fastestLapTime) FROM results )
SELECT AVG(T3.time) FROM drivers AS T1 INNER JOIN results AS T2 ON T1.driverId = T2.driverId INNER JOIN lapTimes AS T3 ON T2.driverId = T3.driverId INNER JOIN races AS T4 ON T3.raceId = T4.raceId WHERE T1.forename = 'Sebastian' AND T1.surname = 'Vettel' AND T4.name = 'Chinese Grand Prix' AND T4.year = 2009
SELECT CAST(SUM(CASE WHEN T1.surname = 'Hamilton' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM drivers AS T1 INNER JOIN results AS T2 ON T1.driverId = T2.driverId INNER JOIN races AS T3 ON T2.raceId = T3.raceId WHERE T3.year >= 2010 AND T2.position > 1
SELECT T1.forename, T1.surname, T1.nationality, SUM(T2.points) / COUNT(T2.points) FROM drivers AS T1 INNER JOIN driverStandings AS T2 ON T1.driverId = T2.driverId GROUP BY T1.driverId ORDER BY COUNT(T2.wins) DESC LIMIT 1
SELECT 2022 - STRFTIME('%Y', dob) + 1, forename, surname FROM drivers WHERE nationality = 'Japanese' ORDER BY dob DESC LIMIT 1
SELECT T2.name FROM races AS T1 INNER JOIN circuits AS T2 ON T1.circuitid = T2.circuitid WHERE T1.year BETWEEN 1990 AND 2000 GROUP BY T2.name HAVING COUNT(T2.name) = 4
SELECT circuits.name, circuits.location, races.name FROM races INNER JOIN circuits ON races.circuitId = circuits.circuitId WHERE circuits.country = 'USA' AND races.year = 2006;
SELECT races.name, circuits.name, circuits.location FROM races INNER JOIN circuits ON races.circuitId = circuits.circuitId WHERE STRFTIME('%Y-%m', races.date) = '2005-09';
SELECT T1.name FROM races AS T1 INNER JOIN driverStandings AS T2 ON T2.raceId = T1.raceId INNER JOIN drivers AS T3 ON T3.driverId = T2.driverId WHERE T3.forename = 'Alex' AND T3.surname = 'Yoong' AND T2.position < 10
SELECT SUM(T2.wins) FROM drivers AS T1 INNER JOIN driverStandings AS T2 ON T2.driverId = T1.driverId INNER JOIN races AS T3 ON T3.raceId = T2.raceId INNER JOIN circuits AS T4 ON T4.circuitId = T3.circuitId WHERE T1.forename = 'Michael' AND T1.surname = 'Schumacher' AND T4.name = 'Sepang International Circuit'
SELECT r.name, r.year FROM races r INNER JOIN lapTimes lt ON r.raceId = lt.raceId INNER JOIN drivers d ON lt.driverId = d.driverId WHERE d.forename = 'Michael' AND d.surname = 'Schumacher' ORDER BY lt.milliseconds ASC LIMIT 1;
SELECT AVG(T2.points) FROM drivers AS T1 INNER JOIN driverStandings AS T2 ON T1.driverId = T2.driverId INNER JOIN races AS T3 ON T2.raceId = T3.raceId WHERE T1.forename = 'Eddie' AND T1.surname = 'Irvine' AND T3.year = 2000;
SELECT r.name, ds.points FROM drivers d INNER JOIN driverStandings ds ON d.driverId = ds.driverId INNER JOIN races r ON ds.raceId = r.raceId WHERE d.forename = 'Lewis' AND d.surname = 'Hamilton' ORDER BY r.year ASC LIMIT 1;
SELECT DISTINCT T2.name, T1.country FROM circuits AS T1 INNER JOIN races AS T2 ON T2.circuitId = T1.circuitId WHERE T2.year = 2017 ORDER BY T2.date ASC
SELECT r.name, r.year, c.location FROM results AS res INNER JOIN races AS r ON res.raceId = r.raceId INNER JOIN circuits AS c ON r.circuitId = c.circuitId ORDER BY res.laps DESC LIMIT 1;
SELECT CAST(SUM(CASE WHEN T1.country = 'Germany' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.country) FROM circuits AS T1 INNER JOIN races AS T2 ON T1.circuitid = T2.circuitid WHERE T2.name = 'European Grand Prix'
SELECT lat, lng FROM circuits WHERE name = 'Silverstone Circuit'
SELECT name FROM circuits WHERE name IN ('Silverstone Circuit', 'Hockenheimring', 'Hungaroring') ORDER BY lat DESC LIMIT 1
SELECT circuitRef FROM circuits WHERE name = 'Marina Bay Street Circuit'
SELECT country FROM circuits ORDER BY alt DESC LIMIT 1
SELECT COUNT(*) FROM drivers WHERE code IS NULL
SELECT nationality FROM drivers ORDER BY dob LIMIT 1
SELECT surname  FROM drivers  WHERE nationality = 'Italian';
SELECT url FROM drivers WHERE forename = 'Anthony' AND surname = 'Davidson'
SELECT DISTINCT driverRef  FROM drivers  WHERE forename = 'Lewis' AND surname = 'Hamilton';
SELECT T1.name FROM circuits AS T1 INNER JOIN races AS T2 ON T2.circuitId = T1.circuitId WHERE T2.year = 2009 AND T2.name = 'Spanish Grand Prix'
SELECT DISTINCT races.year FROM races INNER JOIN circuits ON races.circuitId = circuits.circuitId WHERE circuits.name = 'Silverstone Circuit';
SELECT DISTINCT T1.url FROM circuits AS T1 INNER JOIN races AS T2 ON T2.circuitID = T1.circuitId WHERE T1.name = 'Silverstone Circuit'
SELECT T2.time FROM circuits AS T1 INNER JOIN races AS T2 ON T2.circuitId = T1.circuitId WHERE T2.year = 2010 AND T2.name = 'Abu Dhabi Grand Prix'
SELECT COUNT(races.raceId) FROM races INNER JOIN circuits ON races.circuitId = circuits.circuitId WHERE circuits.country = 'Italy';
SELECT races.date FROM races INNER JOIN circuits ON races.circuitId = circuits.circuitId WHERE circuits.name = 'Circuit de Barcelona-Catalunya';
SELECT circuits.url FROM races INNER JOIN circuits ON races.circuitId = circuits.circuitId WHERE races.year = 2009 AND races.name = 'Spanish Grand Prix';
SELECT MIN(T1.fastestLapTime)  FROM results AS T1  INNER JOIN drivers AS T2  ON T1.driverId = T2.driverId  WHERE T2.forename = 'Lewis' AND T2.surname = 'Hamilton';
SELECT T1.forename, T1.surname FROM drivers AS T1 INNER JOIN results AS T2 ON T2.driverId = T1.driverId WHERE T2.fastestLapSpeed IS NOT NULL ORDER BY T2.fastestLapSpeed DESC LIMIT 1
SELECT d.driverRef FROM races AS r INNER JOIN results AS res ON r.raceId = res.raceId INNER JOIN drivers AS d ON res.driverId = d.driverId WHERE r.name = 'Australian Grand Prix'   AND r.year = 2008   AND res.position = 1;
SELECT T1.name FROM races AS T1 INNER JOIN results AS T2 ON T2.raceId = T1.raceId INNER JOIN drivers AS T3 ON T3.driverId = T2.driverId WHERE T3.forename = 'Lewis' AND T3.surname = 'Hamilton'
SELECT r.name FROM results res INNER JOIN drivers d ON res.driverId = d.driverId INNER JOIN races r ON res.raceId = r.raceId WHERE d.forename = 'Lewis' AND d.surname = 'Hamilton' ORDER BY res.rank ASC LIMIT 1;
SELECT MAX(T1.fastestLapSpeed) FROM results AS T1 INNER JOIN races AS T2 ON T1.raceId = T2.raceId WHERE T2.year = 2009 AND T2.name = 'Spanish Grand Prix';
SELECT T1.year FROM races AS T1 INNER JOIN results AS T2 ON T1.raceId = T2.raceId INNER JOIN drivers AS T3 ON T2.driverId = T3.driverId WHERE T3.forename = 'Lewis' AND T3.surname = 'Hamilton'
SELECT T2.positionOrder FROM races AS T1 INNER JOIN results AS T2 ON T2.raceId = T1.raceId INNER JOIN drivers AS T3 ON T3.driverId = T2.driverId WHERE T3.forename = 'Lewis' AND T3.surname = 'Hamilton' AND T1.name = 'Australian Grand Prix' AND T1.year = 2008
SELECT DISTINCT drivers.forename, drivers.surname FROM races INNER JOIN results ON races.raceId = results.raceId INNER JOIN drivers ON results.driverId = drivers.driverId WHERE races.year = 2008   AND races.name = 'Australian Grand Prix'   AND results.grid = 4;
SELECT COUNT(driverId) FROM results WHERE raceId = ( SELECT raceId FROM races WHERE name = 'Australian Grand Prix' AND year = 2008 ) AND time IS NOT NULL
SELECT T2.fastestLapTime FROM drivers AS T1 INNER JOIN results AS T2 ON T1.driverId = T2.driverId INNER JOIN races AS T3 ON T2.raceId = T3.raceId WHERE T1.forename = 'Lewis' AND T3.year = 2008 AND T3.name = 'Australian Grand Prix'
SELECT results.time FROM results INNER JOIN races ON results.raceId = races.raceId WHERE races.year = 2008   AND races.name = 'Australian Grand Prix'   AND results.position = 2;
SELECT T1.forename, T1.surname, T1.url FROM drivers AS T1 INNER JOIN results AS T2 ON T1.driverId = T2.driverId INNER JOIN races AS T3 ON T3.raceId = T2.raceId WHERE T3.name = 'Australian Grand Prix' AND T2.positionOrder = 1 AND T3.year = 2008
SELECT COUNT(*) FROM races INNER JOIN results ON races.raceId = results.raceId INNER JOIN drivers ON results.driverId = drivers.driverId WHERE races.name = 'Australian Grand Prix'   AND races.year = 2008   AND drivers.nationality = 'American';
SELECT COUNT(*) FROM ( SELECT T1.driverId FROM results AS T1 INNER JOIN races AS T2 on T1.raceId = T2.raceId WHERE T2.name = 'Australian Grand Prix' AND T2.year = 2008 AND T1.time IS NOT NULL GROUP BY T1.driverId HAVING COUNT(T2.raceId) > 0 )
SELECT SUM(points) AS total_points FROM results INNER JOIN drivers ON results.driverId = drivers.driverId WHERE drivers.forename = 'Lewis' AND drivers.surname = 'Hamilton';
SELECT AVG(CAST(SUBSTR(fastestLapTime, 1, 2) AS REAL) * 60 + CAST(SUBSTR(fastestLapTime, 4, 2) AS REAL)) FROM results WHERE driverId = 1
SELECT CAST(SUM(CASE WHEN T2.time IS NOT NULL THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.raceId) FROM races AS T1 INNER JOIN results AS T2 ON T1.raceId = T2.raceId WHERE T1.name = 'Australian Grand Prix' AND T1.year = 2008
SELECT (MAX(T2.milliseconds) - MIN(T2.milliseconds)) * 100.0 / MAX(T2.milliseconds) FROM races AS T1 INNER JOIN results AS T2 ON T1.raceId = T2.raceId WHERE T1.name = 'Australian Grand Prix' AND T1.year = 2008
SELECT COUNT(*)  FROM circuits  WHERE country = 'Australia' AND location = 'Melbourne';
SELECT lat, lng FROM circuits WHERE country = 'USA'
SELECT COUNT(*)  FROM drivers  WHERE nationality = 'British'    AND CAST(SUBSTR(dob, 1, 4) AS INTEGER) > 1980;
SELECT AVG(T2.points) FROM constructors AS T1 INNER JOIN constructorStandings AS T2 ON T1.constructorId = T2.constructorId WHERE T1.nationality = 'British';
SELECT T2.name FROM constructorStandings AS T1 INNER JOIN constructors AS T2 ON T1.constructorId = T2.constructorId ORDER BY T1.points DESC LIMIT 1
SELECT constructors.name FROM constructors INNER JOIN constructorResults ON constructors.constructorId = constructorResults.constructorId WHERE constructorResults.raceId = 291   AND constructorResults.points = 0;
SELECT COUNT(T1.name) FROM constructors AS T1 INNER JOIN constructorResults AS T2 ON T1.constructorId = T2.constructorId WHERE T1.nationality = 'Japanese' AND T2.points = 0
SELECT DISTINCT T2.name FROM results AS T1 INNER JOIN constructors AS T2 ON T1.constructorId = T2.constructorId WHERE T1.rank = 1
SELECT COUNT(T1.constructorid) FROM constructors AS T1 INNER JOIN results AS T2 ON T1.constructorid = T2.constructorid WHERE T1.nationality = 'French' AND T2.laps > 50
SELECT      CAST(SUM(CASE WHEN T1.time IS NOT NULL THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(*) AS race_completion_percentage FROM      results AS T1 INNER JOIN      drivers AS T2 ON T1.driverId = T2.driverId INNER JOIN      races AS T3 ON T1.raceId = T3.raceId WHERE      T3.year BETWEEN 2007 AND 2009     AND T2.nationality = 'Japanese';
SELECT AVG(CASE WHEN SUBSTR(time, 1, 1) = '1' THEN (CAST(SUBSTR(time, 2, 2) AS REAL) * 3600 + CAST(SUBSTR(time, 4, 2) AS REAL) * 60 + CAST(SUBSTR(time, 6, 2) AS REAL)) ELSE 0 END) FROM results
SELECT forename, surname FROM drivers WHERE STRFTIME('%Y', dob) > '1975'
SELECT COUNT(DISTINCT T1.driverId) FROM drivers AS T1 INNER JOIN results AS T2 ON T1.driverId = T2.driverId WHERE T1.nationality = 'Italian' AND T2.time IS NULL
SELECT d.forename, d.surname FROM drivers d INNER JOIN results r ON d.driverId = r.driverId ORDER BY r.fastestLapTime ASC LIMIT 1;
SELECT T2.fastestLap FROM races AS T1 INNER JOIN results AS T2 ON T1.raceId = T2.raceId WHERE T1.year = 2009 ORDER BY T2.milliseconds ASC LIMIT 1
SELECT AVG(results.fastestLapSpeed) FROM results INNER JOIN races ON results.raceId = races.raceId WHERE races.name = 'Spanish Grand Prix' AND races.year = 2009;
SELECT T1.name, T1.year FROM races AS T1 INNER JOIN results AS T2 ON T2.raceId = T1.raceId WHERE T2.milliseconds IS NOT NULL ORDER BY T2.milliseconds ASC LIMIT 1
SELECT      CAST(SUM(CASE WHEN STRFTIME('%Y', drivers.dob) < '1985' AND results.laps > 50 THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(results.driverId) AS percentage FROM      drivers INNER JOIN      results ON drivers.driverId = results.driverId INNER JOIN      races ON results.raceId = races.raceId WHERE      races.year BETWEEN 2000 AND 2005;
SELECT COUNT(DISTINCT T1.driverId) FROM drivers AS T1 INNER JOIN lapTimes AS T2 ON T1.driverId = T2.driverId WHERE T1.nationality = 'French' AND T2.time < '01:00.00'
SELECT code  FROM drivers  WHERE nationality = 'American';
SELECT raceId FROM races WHERE year = 2009
SELECT COUNT(driverId)  FROM results  WHERE raceId = 18;
SELECT code FROM drivers ORDER BY dob DESC LIMIT 3
SELECT driverRef  FROM drivers  WHERE forename = 'Robert' AND surname = 'Kubica';
SELECT COUNT(driverid) FROM drivers WHERE STRFTIME('%Y', dob) = '1980'
SELECT T2.driverId FROM lapTimes AS T1 INNER JOIN drivers AS T2 ON T1.driverId = T2.driverId WHERE T2.nationality = 'German' AND STRFTIME('%Y', T2.dob) BETWEEN '1980' AND '1990' ORDER BY T1.time LIMIT 3
SELECT driverRef  FROM drivers  WHERE nationality = 'German'  ORDER BY dob ASC  LIMIT 1;
SELECT DISTINCT T1.driverId, T1.code FROM drivers AS T1 INNER JOIN results AS T2 ON T1.driverId = T2.driverId WHERE STRFTIME('%Y', T1.dob) = '1971' AND T2.fastestLapTime IS NOT NULL;
SELECT DISTINCT T1.forename, T1.surname FROM drivers AS T1 INNER JOIN lapTimes AS T2 ON T1.driverId = T2.driverId WHERE T1.nationality = 'Spanish' AND STRFTIME('%Y', T1.dob) < '1982' ORDER BY T2.time DESC LIMIT 10;
SELECT T2.year FROM results AS T1 INNER JOIN races AS T2 ON T1.raceId = T2.raceId WHERE T1.fastestLapTime IS NOT NULL ORDER BY T1.fastestLapTime LIMIT 1
SELECT year FROM races ORDER BY time DESC LIMIT 1
SELECT driverId FROM lapTimes ORDER BY time LIMIT 5
SELECT SUM(IIF(time IS NOT NULL, 1, 0)) FROM results WHERE statusId = 2 AND raceId < 100 AND raceId > 50
SELECT DISTINCT location, lat, lng FROM circuits WHERE country = 'Austria'
SELECT raceId FROM results GROUP BY raceId ORDER BY COUNT(time IS NOT NULL) DESC LIMIT 1
SELECT DISTINCT T2.driverRef, T2.nationality, T2.dob FROM qualifying AS T1 INNER JOIN drivers AS T2 ON T1.driverId = T2.driverId WHERE T1.raceId = 23 AND T1.q2 IS NOT NULL;
SELECT T3.year, T3.date, T3.time FROM drivers AS T1 INNER JOIN qualifying AS T2 ON T1.driverId = T2.driverId INNER JOIN races AS T3 ON T2.raceId = T3.raceId ORDER BY T1.dob DESC LIMIT 1
SELECT COUNT(T1.driverId) FROM drivers AS T1 INNER JOIN results AS T2 on T1.driverId = T2.driverId INNER JOIN status AS T3 on T2.statusId = T3.statusId WHERE T3.status = 2 AND T1.nationality = 'American'
SELECT T1.url FROM constructors AS T1 INNER JOIN constructorStandings AS T2 ON T1.constructorId = T2.constructorId WHERE T1.nationality = 'Italian' GROUP BY T1.url ORDER BY SUM(T2.points) DESC LIMIT 1
SELECT constructors.url FROM constructors INNER JOIN constructorStandings ON constructors.constructorId = constructorStandings.constructorId GROUP BY constructors.constructorId ORDER BY SUM(constructorStandings.wins) DESC LIMIT 1;
SELECT T2.surname FROM races AS T1 INNER JOIN drivers AS T2 ON T2.driverId = T3.driverId INNER JOIN lapTimes AS T3 ON T3.raceId = T1.raceId WHERE T1.name = 'French Grand Prix' AND T3.lap = 3 ORDER BY T3.time DESC LIMIT 1
SELECT raceId, milliseconds FROM lapTimes WHERE lap = 1 ORDER BY milliseconds ASC LIMIT 1
SELECT AVG(results.fastestLapTime) FROM results INNER JOIN races ON results.raceId = races.raceId WHERE races.name = 'United States Grand Prix'   AND races.year = 2006   AND results.rank < 11;
SELECT T1.surname FROM drivers AS T1 INNER JOIN pitStops AS T2 ON T1.driverId = T2.driverId WHERE T1.nationality = 'German' AND T1.dob BETWEEN '1980-01-01' AND '1985-12-31' GROUP BY T1.surname ORDER BY AVG(T2.duration) LIMIT 5
SELECT T2.forename, T2.surname FROM results AS T1 INNER JOIN drivers AS T2 ON T1.driverId = T2.driverId INNER JOIN races AS T3 ON T3.raceId = T1.raceId WHERE T3.year = 2008 AND T3.name = 'Canadian Grand Prix' AND T1.position = 1
SELECT T1.constructorRef, T1.url FROM constructors AS T1 INNER JOIN constructorStandings AS T2 ON T1.constructorId = T2.constructorId INNER JOIN races AS T3 ON T2.raceId = T3.raceId WHERE T3.name = 'Singapore Grand Prix' AND T3.year = 2009 AND T2.position = 1
SELECT forename, surname FROM drivers WHERE nationality = 'Austrian' AND STRFTIME('%Y', dob) BETWEEN '1981' AND '1991'
SELECT forename, surname, url, dob FROM drivers WHERE nationality = 'German' AND STRFTIME('%Y', dob) BETWEEN '1971' AND '1985' ORDER BY dob DESC
SELECT location, country, lat, lng FROM circuits WHERE name = 'Hungaroring'
SELECT T4.points, T3.name, T3.nationality FROM races AS T1 INNER JOIN constructorStandings AS T4 ON T1.raceId = T4.raceId INNER JOIN constructors AS T3 ON T3.constructorId = T4.constructorId WHERE T1.name = 'Monaco Grand Prix' AND T1.year BETWEEN 1980 AND 2010 ORDER BY T4.points DESC LIMIT 1
SELECT AVG(T3.points) FROM races AS T1 INNER JOIN results AS T2 ON T1.raceId = T2.raceId INNER JOIN driverStandings AS T3 ON T2.raceId = T3.raceId INNER JOIN drivers AS T4 ON T3.driverId = T4.driverId WHERE T4.forename = 'Lewis' AND T4.surname = 'Hamilton' AND T1.name = 'Turkish Grand Prix'
SELECT CAST(SUM(CASE WHEN year BETWEEN 2000 AND 2010 THEN 1 ELSE 0 END) AS REAL) / 10 FROM races WHERE date BETWEEN '2000-01-01' AND '2010-12-31'
SELECT nationality FROM drivers GROUP BY nationality ORDER BY COUNT(*) DESC LIMIT 1;
SELECT wins FROM driverstandings WHERE points = 91
SELECT races.name FROM results INNER JOIN races ON results.raceId = races.raceId ORDER BY results.fastestLapTime ASC LIMIT 1;
SELECT T2.location FROM races AS T1 INNER JOIN circuits AS T2 ON T1.circuitId = T2.circuitId ORDER BY T1.date DESC LIMIT 1
SELECT DISTINCT d.forename, d.surname FROM qualifying AS q INNER JOIN races AS r ON q.raceId = r.raceId INNER JOIN circuits AS c ON r.circuitId = c.circuitId INNER JOIN drivers AS d ON q.driverId = d.driverId WHERE r.year = 2008   AND c.name = 'Marina Bay Street Circuit'   AND q.position = 1;
SELECT T1.forename, T1.surname, T1.nationality, T3.name FROM drivers AS T1 INNER JOIN driverStandings AS T2 on T1.driverId = T2.driverId INNER JOIN races AS T3 on T2.raceId = T3.raceId ORDER BY JULIANDAY(T1.dob) DESC LIMIT 1
SELECT COUNT(T1.driverId) FROM results AS T1 INNER JOIN status AS T2 ON T1.statusId = T2.statusId INNER JOIN races AS T3 ON T1.raceId = T3.raceId WHERE T2.status = 'Accident' AND T3.name = 'Canadian Grand Prix'
SELECT MIN(dob), forename, surname FROM drivers
SELECT MAX(duration) AS longest_pit_stop_time FROM pitStops;
SELECT time  FROM lapTimes  ORDER BY time  LIMIT 1;
SELECT MAX(T1.duration) FROM pitStops AS T1 INNER JOIN drivers AS T2 ON T1.driverId = T2.driverId WHERE T2.forename = 'Lewis' AND T2.surname = 'Hamilton';
SELECT pitStops.lap FROM pitStops INNER JOIN drivers ON pitStops.driverId = drivers.driverId INNER JOIN races ON pitStops.raceId = races.raceId WHERE drivers.forename = 'Lewis'   AND drivers.surname = 'Hamilton'   AND races.year = 2011   AND races.name = 'Australian Grand Prix';
SELECT duration FROM pitStops WHERE raceId = 841
SELECT T2.time FROM drivers AS T1 INNER JOIN results AS T2 ON T1.driverId = T2.driverId WHERE T1.forename = 'Lewis' AND T1.surname = 'Hamilton' ORDER BY T2.time LIMIT 1
SELECT T2.forename, T2.surname FROM lapTimes AS T1 INNER JOIN drivers AS T2 ON T1.driverId = T2.driverId WHERE T1.time = ( SELECT MIN(time) FROM lapTimes )
SELECT T2.position FROM drivers AS T1 INNER JOIN results AS T2 ON T1.driverId = T2.driverId WHERE T1.forename = 'Lewis' AND T1.surname = 'Hamilton' ORDER BY T2.time LIMIT 1
WITH fastest_lap_times AS (   SELECT T1.raceId, T1.fastestLapTime   FROM results AS T1   WHERE T1.FastestLapTime IS NOT NULL ) SELECT MIN(fastest_lap_times.fastestLapTime) AS lap_record FROM fastest_lap_times INNER JOIN races AS T2 ON fastest_lap_times.raceId = T2.raceId INNER JOIN circuits AS T3 ON T2.circuitId = T3.circuitId WHERE T2.name = 'Austrian Grand Prix'
SELECT T2.time FROM circuits AS T1 INNER JOIN lapTimes AS T2 ON T1.circuitId = T2.raceId WHERE T1.country = 'Italy' ORDER BY T2.time LIMIT 1
SELECT T1.time FROM lapTimes AS T1 INNER JOIN races AS T2 ON T1.raceId = T2.raceId WHERE T2.name = 'Austrian Grand Prix' ORDER BY T1.time LIMIT 1
WITH fastest_lap_times AS (     SELECT T1.raceId, T1.driverId, T1.FastestLapTime,            (CAST(SUBSTR(T1.FastestLapTime, 1, INSTR(T1.FastestLapTime, ':') - 1) AS REAL) * 60) +            (CAST(SUBSTR(T1.FastestLapTime, INSTR(T1.FastestLapTime, ':') + 1, INSTR(T1.FastestLapTime, '.') - INSTR(T1.FastestLapTime, ':') - 1) AS REAL)) +            (CAST(SUBSTR(T1.FastestLapTime, INSTR(T1.FastestLapTime, '.') + 1) AS REAL) / 1000) as time_in_seconds     FROM results AS T1     WHERE T1.FastestLapTime IS NOT NULL ), lap_record_race AS (     SELECT T1.raceId, T1.driverId     FROM results AS T1     INNER JOIN races AS T2 on T1.raceId = T2.raceId     INNER JOIN circuits AS T3 on T2.circuitId = T3.circuitId     INNER JOIN (         SELECT MIN(fastest_lap_times.time_in_seconds) as min_time_in_seconds         FROM fastest_lap_times         INNER JOIN races AS T2 on fastest_lap_times.raceId = T2.raceId         INNER JOIN circuits AS T3 on T2.circuitId = T3.circuitId         WHERE T2.name = 'Austrian Grand Prix'     ) AS T4 ON (CAST(SUBSTR(T1.FastestLapTime, 1, INSTR(T1.FastestLapTime, ':') - 1) AS REAL) * 60) +            (CAST(SUBSTR(T1.FastestLapTime, INSTR(T1.FastestLapTime, ':') + 1, INSTR(T1.FastestLapTime, '.') - INSTR(T1.FastestLapTime, ':') - 1) AS REAL)) +            (CAST(SUBSTR(T1.FastestLapTime, INSTR(T1.FastestLapTime, '.') + 1) AS REAL) / 1000) = T4.min_time_in_seconds     WHERE T2.name = 'Austrian Grand Prix' ) SELECT T4.duration FROM lap_record_race INNER JOIN pitStops AS T4 on lap_record_race.raceId = T4.raceId AND lap_record_race.driverId = T4.driverId
SELECT T3.lat, T3.lng FROM lapTimes AS T1 INNER JOIN races AS T2 ON T1.raceId = T2.raceId INNER JOIN circuits AS T3 ON T2.circuitId = T3.circuitId WHERE T1.time = '1:29.488'
SELECT AVG(T1.milliseconds) FROM pitStops AS T1 INNER JOIN drivers AS T2 ON T1.driverId = T2.driverId WHERE T2.forename = 'Lewis' AND T2.surname = 'Hamilton';
SELECT AVG(lapTimes.milliseconds) FROM lapTimes INNER JOIN races ON lapTimes.raceId = races.raceId INNER JOIN circuits ON races.circuitId = circuits.circuitId WHERE circuits.country = 'Italy';
SELECT player_api_id  FROM Player_Attributes  ORDER BY overall_rating DESC  LIMIT 1;
SELECT player_name, height  FROM Player  ORDER BY height DESC  LIMIT 1;
SELECT preferred_foot FROM Player_Attributes ORDER BY potential LIMIT 1
SELECT COUNT(id) FROM Player_Attributes WHERE defensive_work_rate = 'low' AND overall_rating BETWEEN 60 AND 65
SELECT player_api_id FROM Player_Attributes ORDER BY crossing DESC LIMIT 5
SELECT t2.name FROM Match AS t1 INNER JOIN League AS t2 ON t1.league_id = t2.id WHERE t1.season = '2015/2016' GROUP BY t2.name ORDER BY SUM(t1.home_team_goal + t1.away_team_goal) DESC LIMIT 1
SELECT T1.team_long_name FROM Team AS T1 INNER JOIN Match AS T2 ON T1.team_api_id = T2.home_team_api_id WHERE T2.season = '2015/2016' ORDER BY T2.home_team_goal - T2.away_team_goal ASC LIMIT 1
SELECT DISTINCT t1.player_name FROM Player AS t1 INNER JOIN Player_Attributes AS t2 ON t1.player_api_id = t2.player_api_id ORDER BY t2.penalties DESC LIMIT 10
SELECT T2.away_team_api_id FROM League AS T1 INNER JOIN Match AS T2 ON T1.id = T2.league_id WHERE T1.name = 'Scotland Premier League' AND T2.season = '2009/2010' AND T2.away_team_goal > T2.home_team_goal ORDER BY T2.away_team_goal DESC LIMIT 1
SELECT buildUpPlaySpeed  FROM Team_Attributes  ORDER BY buildUpPlaySpeed DESC  LIMIT 4;
SELECT T2.name FROM Match AS T1 INNER JOIN League AS T2 ON T1.league_id = T2.id WHERE T1.season = '2015/2016' GROUP BY T2.name ORDER BY SUM(T1.home_team_goal = T1.away_team_goal) DESC LIMIT 1
SELECT AVG(T1.age) FROM ( SELECT CAST((strftime('%Y', 'now') - strftime('%Y', T2.birthday)) AS REAL) AS age FROM Player_Attributes AS T1 INNER JOIN Player AS T2 ON T1.player_api_id = T2.player_api_id WHERE T1.sprint_speed >= 97 AND T1.date BETWEEN '2013-01-01 00:00:00' AND '2015-12-31 00:00:00' ) T1
SELECT L.name, COUNT(M.league_id) AS match_count FROM `Match` AS M INNER JOIN League AS L ON M.league_id = L.id GROUP BY M.league_id ORDER BY match_count DESC LIMIT 1;
SELECT AVG(height)  FROM Player  WHERE birthday >= '1990-01-01 00:00:00' AND birthday < '1996-01-01 00:00:00';
SELECT player_api_id FROM Player_Attributes WHERE strftime('%Y', `date`) = '2010' ORDER BY overall_rating DESC LIMIT 1
SELECT team_fifa_api_id  FROM Team_Attributes  WHERE buildUpPlaySpeed BETWEEN 51 AND 59;
SELECT DISTINCT T1.team_long_name FROM Team AS T1 INNER JOIN Team_Attributes AS T2 ON T1.team_api_id = T2.team_api_id WHERE T2.buildUpPlayPassing > ( SELECT AVG(buildUpPlayPassing) FROM Team_Attributes ) AND STRFTIME('%Y', T2.date) = '2012'
SELECT CAST(SUM(CASE WHEN T1.birthday BETWEEN '1987-01-01 00:00:00' AND '1992-12-31 00:00:00' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.player_api_id) FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T2.preferred_foot = 'left'
SELECT t1.name, SUM(t2.home_team_goal) + SUM(t2.away_team_goal) FROM League AS t1 INNER JOIN Match AS t2 ON t1.id = t2.league_id GROUP BY t1.name ORDER BY SUM(t2.home_team_goal) + SUM(t2.away_team_goal) ASC LIMIT 5
SELECT CAST(SUM(T1.long_shots) AS REAL) / COUNT(T1.player_api_id) FROM Player_Attributes AS T1 INNER JOIN Player AS T2 ON T1.player_api_id = T2.player_api_id WHERE T2.player_name = 'Ahmed Samir Farag'
SELECT t1.player_name FROM Player AS t1 INNER JOIN Player_Attributes AS t2 ON t1.player_api_id = t2.player_api_id WHERE t1.height > 180 GROUP BY t1.id ORDER BY CAST(SUM(t2.heading_accuracy) AS REAL) / COUNT(t2.`player_fifa_api_id`) DESC LIMIT 10
SELECT T1.team_long_name FROM Team AS T1 INNER JOIN Team_Attributes AS T2 ON T1.team_api_id = T2.team_api_id WHERE T2.buildUpPlayDribblingClass = 'Normal' AND T2.date LIKE '2014%' AND T2.chanceCreationPassing < ( SELECT AVG(chanceCreationPassing) FROM Team_Attributes ) ORDER BY T2.chanceCreationPassing DESC
SELECT T2.name FROM Match AS T1 INNER JOIN League AS T2 ON T1.league_id = T2.id WHERE T1.season = '2009/2010' GROUP BY T1.league_id HAVING AVG(T1.home_team_goal) > AVG(T1.away_team_goal)
SELECT DISTINCT team_short_name  FROM Team  WHERE team_long_name = 'Queens Park Rangers';
SELECT player_name FROM Player WHERE birthday LIKE '1970-10%'
SELECT DISTINCT t2.attacking_work_rate FROM Player AS t1 INNER JOIN Player_Attributes AS t2 ON t1.player_api_id = t2.player_api_id WHERE t1.player_name = 'Franco Zennaro'
SELECT DISTINCT T2.buildUpPlayPositioningClass FROM Team AS T1 INNER JOIN Team_Attributes AS T2 ON T1.team_api_id = T2.team_api_id WHERE T1.team_long_name = 'ADO Den Haag'
SELECT t2.heading_accuracy FROM Player AS t1 INNER JOIN Player_Attributes AS t2 ON t1.player_api_id = t2.player_api_id WHERE t1.player_name = 'Francois Affolter' AND t2.date = '2014-09-18 00:00:00'
SELECT T1.overall_rating FROM Player_Attributes AS T1 INNER JOIN Player AS T2 ON T1.player_api_id = T2.player_api_id WHERE T2.player_name = 'Gabriel Tamas' AND CAST(STRFTIME('%Y', T1.date) AS INT) = 2011
SELECT COUNT(*) AS match_count FROM `Match` AS T1 INNER JOIN League AS T2 ON T1.league_id = T2.id WHERE T1.season = '2015/2016' AND T2.name = 'Scotland Premier League';
SELECT T2.preferred_foot FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id ORDER BY T1.birthday DESC LIMIT 1;
SELECT player_api_id FROM Player_Attributes WHERE potential = ( SELECT MAX(potential) FROM Player_Attributes )
SELECT COUNT(*) FROM Player INNER JOIN Player_Attributes ON Player.player_api_id = Player_Attributes.player_api_id WHERE Player.weight < 130 AND Player_Attributes.preferred_foot = 'left';
SELECT DISTINCT T1.team_short_name FROM Team AS T1 INNER JOIN Team_Attributes AS T2 ON T1.team_api_id = T2.team_api_id WHERE T2.chanceCreationPassingClass = 'Risky';
SELECT DISTINCT T2.defensive_work_rate FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T1.player_name = 'David Wilson';
SELECT T1.birthday FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id ORDER BY T2.overall_rating DESC LIMIT 1;
SELECT name FROM League WHERE country_id = ( SELECT id FROM Country WHERE name = 'Netherlands' )
SELECT CAST(SUM(t2.home_team_goal) AS REAL) / COUNT(t2.id) FROM Country AS t1 INNER JOIN Match AS t2 ON t1.id = t2.country_id WHERE t1.name = 'Poland' AND t2.season = '2010/2011'
SELECT T1.player_name FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id ORDER BY T2.finishing DESC LIMIT 1
SELECT player_name FROM Player WHERE height > 180
SELECT COUNT(id)  FROM Player  WHERE STRFTIME('%Y', birthday) > '1990';
SELECT COUNT(*) FROM Player WHERE SUBSTR(player_name, 1, 4) = 'Adam' AND weight > 170
SELECT T1.player_name FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T2.date LIKE '2008%' AND T2.overall_rating > 80 UNION SELECT T1.player_name FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T2.date LIKE '2009%' AND T2.overall_rating > 80 UNION SELECT T1.player_name FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T2.date LIKE '2010%' AND T2.overall_rating > 80
SELECT t2.potential FROM Player AS t1 INNER JOIN Player_Attributes AS t2 ON t1.player_api_id = t2.player_api_id WHERE t1.player_name = 'Aaron Doran'
SELECT player_api_id FROM Player_Attributes WHERE preferred_foot = 'left'
SELECT DISTINCT T1.team_long_name FROM Team AS T1 INNER JOIN Team_Attributes AS T2 ON T1.team_api_id = T2.team_api_id WHERE T2.buildUpPlaySpeedClass = 'Fast';
SELECT DISTINCT t2.buildUpPlayPassingClass FROM Team AS t1 INNER JOIN Team_Attributes AS t2 ON t1.team_api_id = t2.team_api_id WHERE t1.team_short_name = 'CLB'
SELECT T1.team_short_name FROM Team AS T1 INNER JOIN Team_Attributes AS T2 ON T1.team_api_id = T2.team_api_id WHERE T2.buildUpPlayPassing > 70;
SELECT CAST(SUM(t2.overall_rating) AS REAL) / COUNT(t2.id) FROM Player AS t1 INNER JOIN Player_Attributes AS t2 ON t1.player_api_id = t2.player_api_id WHERE t1.height > 170 AND SUBSTR(t2.`date`, 1, 4) BETWEEN '2010' AND '2015'
SELECT player_name FROM Player WHERE height = ( SELECT MIN(height) FROM Player )
SELECT t1.name FROM Country AS t1 INNER JOIN League AS t2 ON t1.id = t2.country_id WHERE t2.name = 'Italy Serie A'
SELECT T1.team_short_name FROM Team AS T1 INNER JOIN Team_Attributes AS T2 ON T1.team_api_id = T2.team_api_id WHERE T2.buildUpPlaySpeed = 31 AND T2.buildUpPlayDribbling = 53 AND T2.buildUpPlayPassing = 32
SELECT AVG(t2.overall_rating) FROM Player AS t1 INNER JOIN Player_Attributes AS t2 ON t1.player_api_id = t2.player_api_id WHERE t1.player_name = 'Aaron Doran'
SELECT COUNT(T1.id) FROM Match AS T1 INNER JOIN League AS T2 ON T1.league_id = T2.id WHERE T2.name = 'Germany 1. Bundesliga' AND strftime('%Y-%m', T1.date) BETWEEN '2008-08' AND '2008-10'
SELECT DISTINCT T2.team_short_name FROM Match AS T1 INNER JOIN Team AS T2 ON T1.home_team_api_id = T2.team_api_id WHERE T1.home_team_goal = 10;
SELECT player_api_id FROM Player_Attributes WHERE potential = 61 ORDER BY balance DESC LIMIT 1
SELECT ( SELECT AVG(T2.ball_control) FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T1.player_name = 'Abdou Diallo' ) - ( SELECT AVG(T2.ball_control) FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T1.player_name = 'Aaron Appindangoye' )
SELECT DISTINCT team_long_name  FROM Team  WHERE team_short_name = 'GEN';
SELECT player_name FROM Player WHERE player_name IN ('Aaron Lennon', 'Abdelaziz Barrada') ORDER BY birthday ASC LIMIT 1
SELECT player_name  FROM Player  ORDER BY height DESC  LIMIT 1;
SELECT COUNT(player_api_id) FROM Player_Attributes WHERE preferred_foot = 'left' AND attacking_work_rate = 'low'
SELECT Country.name FROM League INNER JOIN Country ON League.country_id = Country.id WHERE League.name = 'Belgium Jupiler League';
SELECT t1.name FROM League AS t1 INNER JOIN Country AS t2 ON t1.country_id = t2.id WHERE t2.name = 'Germany'
SELECT player_api_id FROM Player_Attributes ORDER BY overall_rating DESC LIMIT 1
SELECT COUNT(T1.id) FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T1.birthday < '1986-01-01' AND T2.defensive_work_rate = 'high'
SELECT T1.player_name FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T1.player_name IN ('Alexis', 'Ariel Borysiuk', 'Arouna Kone') ORDER BY T2.crossing DESC LIMIT 1;
SELECT t2.heading_accuracy FROM Player AS t1 INNER JOIN Player_Attributes AS t2 ON t1.player_api_id = t2.player_api_id WHERE t1.player_name = 'Ariel Borysiuk'
SELECT COUNT(*) FROM Player INNER JOIN Player_Attributes ON Player.player_api_id = Player_Attributes.player_api_id WHERE Player.height > 180 AND Player_Attributes.volleys > 70;
SELECT DISTINCT T1.player_name FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T2.volleys > 70 AND T2.dribbling > 70;
SELECT COUNT(*) FROM Country AS T1 INNER JOIN League AS T2 ON T1.id = T2.country_id INNER JOIN Match AS T3 ON T2.id = T3.league_id WHERE T1.name = 'Belgium' AND T3.season = '2008/2009'
SELECT T2.long_passing FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id ORDER BY T1.birthday LIMIT 1
SELECT COUNT(T1.id) FROM Match AS T1 INNER JOIN League AS T2 ON T1.league_id = T2.id WHERE T2.name = 'Belgium Jupiler League' AND T1.date LIKE '2009-04%'
SELECT league_id FROM Match WHERE season = '2008/2009' GROUP BY league_id ORDER BY COUNT(id) DESC LIMIT 1
SELECT CAST(SUM(T1.overall_rating) AS REAL) / COUNT(T2.id) FROM Player_Attributes AS T1 INNER JOIN Player AS T2 ON T1.player_api_id = T2.player_api_id WHERE strftime('%Y', T2.birthday) < '1986'
SELECT CAST((SELECT T2.overall_rating FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T1.player_name = 'Ariel Borysiuk') - ( SELECT T2.overall_rating FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T1.player_name = 'Paulin Puel') AS REAL) * 100 / ( SELECT T2.overall_rating FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T1.player_name = 'Paulin Puel')
SELECT AVG(TA.buildUpPlaySpeed) FROM Team AS T INNER JOIN Team_Attributes AS TA ON T.team_api_id = TA.team_api_id WHERE T.team_long_name = 'Heart of Midlothian';
SELECT CAST(SUM(t2.overall_rating) AS REAL) / COUNT(t2.id) FROM Player AS t1 INNER JOIN Player_Attributes AS t2 ON t1.player_api_id = t2.player_api_id WHERE t1.player_name = 'Pietro Marino'
SELECT SUM(T2.crossing) AS total_crossing_score FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T1.player_name = 'Aaron Lennox';
SELECT MAX(TA.chanceCreationPassing), TA.chanceCreationPassingClass FROM Team AS T INNER JOIN Team_Attributes AS TA ON T.team_api_id = TA.team_api_id WHERE T.team_long_name = 'Ajax';
SELECT DISTINCT T2.preferred_foot FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T1.player_name = 'Abdou Diallo';
SELECT T1.overall_rating FROM Player_Attributes AS T1 INNER JOIN Player AS T2 ON T1.player_api_id = T2.player_api_id WHERE T2.player_name = 'Dorlan Pabon' ORDER BY T1.overall_rating DESC LIMIT 1
SELECT AVG(T1.away_team_goal) FROM Match AS T1 INNER JOIN Team AS T2 ON T1.away_team_api_id = T2.team_api_id INNER JOIN League AS T3 ON T1.league_id = T3.id INNER JOIN Country AS T4 ON T3.country_id = T4.id WHERE T2.team_long_name = 'Parma' AND T4.name = 'Italy'
SELECT t1.player_name FROM Player AS t1 INNER JOIN Player_Attributes AS t2 ON t1.player_api_id = t2.player_api_id WHERE SUBSTR(t2.`date`, 1, 10) = '2016-06-23' AND t2.overall_rating = 77 ORDER BY t1.birthday ASC LIMIT 1
SELECT T2.overall_rating FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T1.player_name = 'Aaron Mooy'   AND T2.date = '2016-02-04 00:00:00';
SELECT t2.potential FROM Player AS t1 INNER JOIN Player_Attributes AS t2 ON t1.player_api_id = t2.player_api_id WHERE SUBSTR(t2.`date`, 1, 10) = '2010-08-30' AND t1.player_name = 'Francesco Parravicini'
SELECT T2.attacking_work_rate FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T1.player_name = 'Francesco Migliore' AND T2.date = '2015-05-01 00:00:00'
SELECT T2.defensive_work_rate FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T1.player_name = 'Kevin Berigaud'   AND T2.date = '2013-02-22 00:00:00';
SELECT T2.date FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T1.player_name = 'Kevin Constant' ORDER BY T2.crossing DESC LIMIT 1;
SELECT T2.buildUpPlaySpeedClass FROM Team AS T1 INNER JOIN Team_Attributes AS T2 ON T1.team_api_id = T2.team_api_id WHERE T1.team_long_name = 'Willem II'   AND T2.date = '2011-02-22 00:00:00';
SELECT T2.buildUpPlayDribblingClass FROM Team AS T1 INNER JOIN Team_Attributes AS T2 ON T1.team_api_id = T2.team_api_id WHERE T1.team_short_name = 'LEI'   AND T2.date = '2015-09-10 00:00:00';
SELECT T1.buildUpPlayPassingClass FROM Team_Attributes AS T1 INNER JOIN Team AS T2 ON T1.team_api_id = T2.team_api_id WHERE T2.team_long_name = 'FC Lorient' AND T1.date = '2010-02-22 00:00:00'
SELECT T2.chanceCreationPassingClass FROM Team AS T1 INNER JOIN Team_Attributes AS T2 ON T1.team_api_id = T2.team_api_id WHERE T1.team_long_name = 'PEC Zwolle'   AND T2.date = '2013-09-20 00:00:00';
SELECT T2.chanceCreationCrossingClass FROM Team AS T1 INNER JOIN Team_Attributes AS T2 ON T1.team_api_id = T2.team_api_id WHERE T1.team_long_name = 'Hull City'   AND T2.date = '2010-02-22 00:00:00';
SELECT T2.defenceAggressionClass FROM Team AS T1 INNER JOIN Team_Attributes AS T2 ON T1.team_api_id = T2.team_api_id WHERE T2.date = '2015-09-10 00:00:00' AND T1.team_long_name = 'Hannover 96'
SELECT AVG(T2.overall_rating) FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T1.player_name = 'Marko Arnautovic' AND T2.date >= '2007-02-22 00:00:00' AND T2.date <= '2016-04-21 00:00:00'
SELECT CAST(( SELECT T1.overall_rating FROM Player_Attributes AS T1 INNER JOIN Player AS T2 ON T1.player_api_id = T2.player_api_id WHERE T2.player_name = 'Landon Donovan' AND T1.date = '2013/7/12' ) - ( SELECT T1.overall_rating FROM Player_Attributes AS T1 INNER JOIN Player AS T2 ON T1.player_api_id = T2.player_api_id WHERE T2.player_name = 'Jordan Bowery' AND T1.date = '2013/7/12' ) AS REAL) * 100 / ( SELECT T1.overall_rating FROM Player_Attributes AS T1 INNER JOIN Player AS T2 ON T1.player_api_id = T2.player_api_id WHERE T2.player_name = 'Landon Donovan' AND T1.date = '2013/7/12' )
SELECT player_name  FROM Player  ORDER BY height DESC  LIMIT 5;
SELECT player_api_id FROM Player ORDER BY weight DESC LIMIT 10
SELECT player_name FROM Player WHERE CAST((strftime('%J', 'now') - strftime('%J', birthday)) / 365 AS INT) >= 35
SELECT SUM(t2.home_team_goal) FROM Player AS t1 INNER JOIN match AS t2 ON t1.player_api_id = t2.away_player_9 WHERE t1.player_name = 'Aaron Lennon'
SELECT SUM(T2.away_team_goal) FROM Player AS T1 INNER JOIN Match AS T2 ON T1.player_api_id = T2.away_player_1 WHERE T1.player_name = 'Daan Smith' OR T1.player_name = 'Filipe Ferreira'
SELECT SUM(T1.home_team_goal) FROM Match AS T1 INNER JOIN Player AS T2 ON T1.home_player_1 = T2.player_api_id WHERE strftime('%Y', CURRENT_TIMESTAMP) - strftime('%Y', T2.birthday) < 31
SELECT player_name FROM Player WHERE player_api_id IN ( SELECT player_api_id FROM Player_Attributes ORDER BY overall_rating DESC LIMIT 10 )
SELECT P.player_name FROM Player AS P INNER JOIN Player_Attributes AS PA ON P.player_api_id = PA.player_api_id ORDER BY PA.potential DESC LIMIT 1;
SELECT player_name FROM Player WHERE player_api_id IN ( SELECT player_api_id FROM Player_Attributes WHERE attacking_work_rate = 'high' )
SELECT T1.player_name FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T2.finishing = 1 ORDER BY strftime('%Y', T1.birthday) LIMIT 1
SELECT T1.player_name FROM Player AS T1 INNER JOIN Country AS T2 ON T1.id = T2.id WHERE T2.name = 'Belgium'
SELECT DISTINCT t4.name FROM Player_Attributes AS t1 INNER JOIN Player AS t2 ON t1.player_api_id = t2.player_api_id INNER JOIN Match AS t3 ON t2.player_api_id = t3.home_player_8 INNER JOIN Country AS t4 ON t3.country_id = t4.id WHERE t1.vision > 89
SELECT t1.name FROM Country AS t1 INNER JOIN Match AS t2 ON t1.id = t2.country_id INNER JOIN Player AS t3 ON t2.home_player_1 = t3.player_api_id GROUP BY t1.name ORDER BY AVG(t3.weight) DESC LIMIT 1
SELECT T1.team_long_name FROM Team AS T1 INNER JOIN Team_Attributes AS T2 ON T1.team_api_id = T2.team_api_id WHERE T2.buildUpPlaySpeedClass = 'Slow';
SELECT T1.team_short_name FROM Team AS T1 INNER JOIN Team_Attributes AS T2 ON T1.team_api_id = T2.team_api_id WHERE T2.chanceCreationPassingClass = 'Safe'
SELECT CAST(SUM(T1.height) AS REAL) / COUNT(T1.id) FROM Player AS T1 INNER JOIN Match AS T2 ON T1.id = T2.id INNER JOIN Country AS T3 ON T2.country_id = T3.id WHERE T3.name = 'Italy'
SELECT player_name  FROM Player  WHERE height > 180  ORDER BY player_name ASC  LIMIT 3;
SELECT COUNT(*)  FROM Player  WHERE player_name LIKE 'Aaron%'    AND birthday > '1990';
SELECT ( SELECT T2.jumping FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T1.id = 6 ) - ( SELECT T2.jumping FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T1.id = 23 )
SELECT player_api_id  FROM Player_Attributes  WHERE preferred_foot = 'right'  ORDER BY potential ASC  LIMIT 3;
SELECT COUNT(player_api_id) FROM Player_Attributes WHERE preferred_foot = 'left' ORDER BY crossing DESC LIMIT 1
SELECT CAST(SUM(CASE WHEN stamina > 80 AND strength > 80 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM Player_Attributes
SELECT name FROM Country WHERE id IN ( SELECT country_id FROM League WHERE name = 'Poland Ekstraklasa' )
SELECT home_team_goal, away_team_goal FROM Match WHERE date LIKE '2008-09-24%'
SELECT sprint_speed, agility, acceleration FROM Player_Attributes WHERE player_api_id IN ( SELECT player_api_id FROM Player WHERE player_name = 'Alexis Blin' )
SELECT DISTINCT t2.buildUpPlaySpeedClass FROM Team AS t1 INNER JOIN Team_Attributes AS t2 ON t1.team_api_id = t2.team_api_id WHERE t1.team_long_name = 'KSV Cercle Brugge'
SELECT COUNT(id) FROM Match WHERE season = '2015/2016' AND league_id = 1491
SELECT MAX(T1.home_team_goal) FROM Match AS T1 INNER JOIN League AS T2 ON T1.league_id = T2.id INNER JOIN Country AS T3 ON T2.country_id = T3.id WHERE T3.name = 'Netherlands' AND T2.name = 'Eredivisie'
SELECT finishing, curve FROM Player_Attributes WHERE player_api_id = ( SELECT player_api_id FROM Player ORDER BY weight DESC LIMIT 1 ) LIMIT 1
SELECT T1.team_long_name FROM Team AS T1 INNER JOIN Match AS T2 ON T1.team_api_id = T2.home_team_api_id WHERE T2.season = '2015/2016' GROUP BY T1.team_long_name ORDER BY COUNT(T2.id) DESC LIMIT 1
SELECT T2.team_long_name FROM Match AS T1 INNER JOIN Team AS T2 ON T1.away_team_api_id = T2.team_api_id GROUP BY T1.away_team_api_id ORDER BY SUM(T1.away_team_goal) DESC LIMIT 1
SELECT player_api_id FROM Player_Attributes WHERE overall_rating = ( SELECT MAX(overall_rating) FROM Player_Attributes )
SELECT CAST(SUM(CASE WHEN T1.height < 180 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM Player AS T1 INNER JOIN Player_Attributes AS T2 ON T1.player_api_id = T2.player_api_id WHERE T2.strength > 70
SELECT CAST(SUM(IIF(Admission = '+', 1, 0)) AS REAL) * 100 / SUM(IIF(Admission = '-', 1, 0)) FROM Patient WHERE SEX = 'M'
SELECT CAST(SUM(IIF(STRFTIME('%Y', Birthday) > 1930, 1, 0)) AS REAL) * 100 / COUNT(ID) FROM Patient WHERE SEX = 'F'
SELECT      CAST(SUM(CASE WHEN Admission = '+' THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(*) AS percentage_inpatients FROM      Patient WHERE      STRFTIME('%Y', Birthday) BETWEEN '1930' AND '1940';
SELECT CAST(SUM(IIF(Admission = '+', 1, 0)) AS REAL) / SUM(IIF(Admission = '-', 1, 0)) FROM Patient WHERE Diagnosis = 'SLE'
SELECT T1.Diagnosis, T2.Date FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.ID = 30609
SELECT      Patient.SEX,      Patient.Birthday,      Examination.`Examination Date`,      Examination.Symptoms FROM      Patient INNER JOIN      Examination  ON      Patient.ID = Examination.ID WHERE      Patient.ID = 163109;
SELECT DISTINCT Patient.ID, Patient.SEX, Patient.Birthday FROM Patient INNER JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Laboratory.LDH > 500;
SELECT      P.ID,      STRFTIME('%Y', 'now') - STRFTIME('%Y', P.Birthday) AS Age FROM      Patient P INNER JOIN      Examination E ON      P.ID = E.ID WHERE      E.RVVT = '+';
SELECT T1.ID, T1.SEX, T1.Diagnosis FROM Patient AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID WHERE T2.Thrombosis = 2
SELECT DISTINCT Patient.ID FROM Patient INNER JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE STRFTIME('%Y', Patient.Birthday) = '1937'   AND Laboratory.`T-CHO` >= 250;
SELECT DISTINCT T1.ID, T1.SEX, T1.Diagnosis FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.ALB < 3.5
SELECT CAST(SUM(CASE WHEN T1.SEX = 'F' AND (T2.TP < 6 OR T2.TP > 8.5) THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID
SELECT AVG(E.`aCL IgG`) AS Average_aCL_IgG FROM Patient AS P INNER JOIN Examination AS E ON P.ID = E.ID WHERE P.Admission = '+'   AND (strftime('%Y', 'now') - strftime('%Y', P.Birthday)) >= 50;
SELECT COUNT(ID) FROM Patient WHERE Description LIKE '1997%' AND Admission = '-' AND SEX = 'F'
SELECT MIN(STRFTIME('%Y', `First Date`) - STRFTIME('%Y', Birthday)) FROM Patient
SELECT CAST(SUM(CASE WHEN T1.SEX = 'F' THEN 1 ELSE 0 END) AS REAL) / COUNT(*) FROM Patient AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID WHERE STRFTIME('%Y', T2.`Examination Date`) = '1997' AND T2.Thrombosis = 1
SELECT MAX(STRFTIME('%Y', Birthday)) - MIN(STRFTIME('%Y', Birthday)) FROM Patient WHERE ID IN ( SELECT ID FROM Laboratory WHERE TG >= 200 )
SELECT E.Symptoms, E.Diagnosis FROM Patient AS P INNER JOIN Examination AS E ON P.ID = E.ID ORDER BY P.Birthday ASC LIMIT 1;
SELECT CAST(COUNT(T1.ID) AS REAL) / 12 FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE STRFTIME('%Y', T2.Date) = '1998' AND T1.SEX = 'M'
SELECT DISTINCT T1.`First Date`, strftime('%Y', T1.`First Date`) - strftime('%Y', T1.Birthday) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.Diagnosis = 'SJS'
SELECT CAST(SUM(IIF(T2.SEX = 'M' AND T1.UA <= 8.0, 1, 0)) AS REAL) / SUM(IIF(T2.SEX = 'F' AND T1.UA <= 6.5, 1, 0)) FROM Laboratory AS T1 INNER JOIN Patient AS T2 ON T1.ID = T2.ID
SELECT COUNT(*)  FROM Patient AS P INNER JOIN Examination AS E ON P.ID = E.ID WHERE CAST(STRFTIME('%Y', E.`Examination Date`) AS INTEGER) - CAST(STRFTIME('%Y', P.`First Date`) AS INTEGER) >= 1;
SELECT COUNT(T1.ID) FROM Patient AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID WHERE T2.`Examination Date` BETWEEN '1990-01-01' AND '1993-12-31' AND strftime('%Y', T1.Birthday) < 18
SELECT COUNT(T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.SEX = 'M' AND T2.`T-BIL` > 2
SELECT Diagnosis FROM Examination WHERE `Examination Date` BETWEEN '1985-01-01' AND '1995-12-31' GROUP BY Diagnosis ORDER BY COUNT(Diagnosis) DESC LIMIT 1
SELECT AVG('1999' - STRFTIME('%Y', T2.Birthday)) FROM Laboratory AS T1 INNER JOIN Patient AS T2 ON T1.ID = T2.ID WHERE T1.Date BETWEEN '1991-10-01' AND '1991-10-30'
SELECT STRFTIME('%Y', T2.Date) - STRFTIME('%Y', T1.Birthday), T1.Diagnosis FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID ORDER BY T2.HGB DESC LIMIT 1
SELECT ANA  FROM Examination  WHERE ID = 3605340 AND `Examination Date` = '1996-12-02';
SELECT      CASE          WHEN `T-CHO` < 250 THEN 'YES'          ELSE 'NO'      END AS Cholesterol_Status FROM      Laboratory WHERE      ID = 2927464      AND Date = '1995-09-04';
SELECT SEX FROM Patient WHERE Diagnosis = 'AORTITIS'
SELECT `aCL IgA`, `aCL IgG`, `aCL IgM` FROM Examination WHERE ID IN ( SELECT ID FROM Patient WHERE Diagnosis = 'SLE' AND Description = '1994-02-19' ) AND `Examination Date` = '1993-11-12'
SELECT T1.SEX FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.GPT = 9 AND T2.Date = '1992-06-12'
SELECT T1.ID, strftime('%Y', T2.Date) - strftime('%Y', T1.Birthday) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.Date = '1991-10-21' AND T2.UA = 8.4
SELECT COUNT(*) FROM Laboratory WHERE ID = ( SELECT ID FROM Patient WHERE `First Date` = '1991-06-13' AND Diagnosis = 'SJS' ) AND STRFTIME('%Y', Date) = '1995'
SELECT DISTINCT Patient.Diagnosis FROM Patient INNER JOIN Examination ON Patient.ID = Examination.ID WHERE Examination.`Examination Date` = '1997-01-27'   AND Examination.Diagnosis = 'SLE';
SELECT T2.Symptoms FROM Patient AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID WHERE T1.Birthday = '1959-03-01' AND T2.`Examination Date` = '1993-09-27';
SELECT SUM(CASE WHEN T2.Date LIKE '1981-11%' THEN T2.`T-CHO` ELSE 0 END) - SUM(CASE WHEN T2.Date LIKE '1981-12%' THEN T2.`T-CHO` ELSE 0 END) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.Birthday = '1959-02-18'
SELECT ID FROM Examination WHERE Diagnosis = 'Behcet'   AND `Examination Date` BETWEEN '1997-01-01' AND '1997-12-31';
SELECT DISTINCT ID FROM Laboratory WHERE Date BETWEEN '1987-07-06' AND '1996-01-31' AND GPT > 30 AND ALB < 4
SELECT ID FROM Patient WHERE Birthday LIKE '%1964%' AND Admission = '+' AND SEX = 'F'
SELECT COUNT(ID) FROM Examination WHERE Thrombosis = 2 AND `ANA Pattern` = 'S' AND `aCL IgM` > ( SELECT AVG(`aCL IgM`) FROM Examination )
SELECT CAST(SUM(CASE WHEN T1.UA <= 6.5 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM Laboratory AS T1 INNER JOIN Patient AS T2 ON T1.ID = T2.ID WHERE T1.`U-PRO` BETWEEN 0 AND 30
SELECT CAST(COUNT(CASE WHEN Diagnosis = 'BEHCET' THEN 1 ELSE NULL END) AS REAL) * 100 / COUNT(*) FROM Patient WHERE STRFTIME('%Y', `First Date`) = '1981' AND SEX = 'M'
SELECT DISTINCT Patient.ID FROM Patient INNER JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Patient.Admission = '-'   AND Laboratory.Date LIKE '1991-10%'   AND Laboratory.`T-BIL` < 2.0;
SELECT COUNT(P.ID) FROM Patient AS P INNER JOIN Examination AS E ON P.ID = E.ID WHERE P.SEX = 'F'   AND P.Birthday BETWEEN '1980-01-01' AND '1989-12-31'   AND E.`ANA Pattern` != 'P';
SELECT T1.SEX FROM Patient AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID INNER JOIN Laboratory AS T3 ON T3.ID = T2.ID WHERE T2.Diagnosis = 'PSS' AND T3.CRP = '2+' AND T3.CRE = 1.0 AND T3.LDH = 123
SELECT AVG(T2.ALB) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.PLT > 400 AND T1.Diagnosis = 'SLE' AND T1.SEX = 'F'
SELECT Symptoms FROM Examination WHERE Diagnosis = 'SLE' GROUP BY Symptoms ORDER BY COUNT(Symptoms) DESC LIMIT 1
SELECT Description, Diagnosis FROM Patient WHERE ID = 48473
SELECT COUNT(*) FROM Patient WHERE Diagnosis = 'APS' AND SEX = 'F'
SELECT COUNT(ID) FROM Laboratory WHERE TP < 6 OR TP > 8.5
SELECT CAST(SUM(CASE WHEN T2.Diagnosis LIKE '%ITP%' THEN 1 ELSE 0 END) AS REAL) * 100 / SUM(CASE WHEN T2.Diagnosis LIKE '%SLE%' THEN 1 ELSE 0 END) FROM Laboratory AS T1 INNER JOIN Patient AS T2 ON T1.ID = T2.ID
SELECT CAST(SUM(CASE WHEN T1.SEX = 'F' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.SEX) FROM Patient AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID WHERE T2.Diagnosis = 'RA' AND STRFTIME('%Y', T1.Birthday) = '1980'
SELECT COUNT(Patient.ID) FROM Patient INNER JOIN Examination ON Patient.ID = Examination.ID WHERE Patient.SEX = 'M'   AND Examination.`Examination Date` BETWEEN '1995-01-01' AND '1997-12-31'   AND Patient.Diagnosis = 'BEHCET'   AND Patient.Admission = '-';
SELECT COUNT(T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.WBC < 3.5 AND T1.SEX = 'F'
SELECT JULIANDAY(T2.`Examination Date`) - JULIANDAY(T1.`First Date`) AS Days_Difference FROM Patient AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID WHERE T1.ID = 821298;
SELECT CASE WHEN (T1.SEX = 'F' AND T2.UA > 6.5) OR (T1.SEX = 'M' AND T2.UA < 8.0) THEN true ELSE false END FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.ID = 57266
SELECT Date FROM Laboratory WHERE ID = 48473 AND GOT >= 60
SELECT DISTINCT T1.SEX, T1.Birthday FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.GOT < 60 AND STRFTIME('%Y', T2.Date) = '1994'
SELECT T1.ID FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.SEX = 'M' AND T2.GPT > 60
SELECT T1.Diagnosis FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.GPT > 60 ORDER BY T1.Birthday ASC
SELECT AVG(LDH) FROM Laboratory WHERE LDH < 500
SELECT T1.ID, strftime('%Y', CURRENT_TIMESTAMP) - strftime('%Y', T1.Birthday) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.LDH BETWEEN 600 AND 800
SELECT DISTINCT T1.Admission FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.ALP < 300
SELECT T1.ID , CASE WHEN T2.ALP < 300 THEN 'normal' ELSE 'abNormal' END FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.Birthday = '1982-04-01'
SELECT DISTINCT T1.ID, T1.SEX, T1.Birthday FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.TP < 6.0
SELECT T2.TP - 8.5 FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.SEX = 'F' AND T2.TP > 8.5
SELECT * FROM Patient INNER JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Patient.SEX = 'M' AND (Laboratory.ALB <= 3.5 OR Laboratory.ALB >= 5.5) ORDER BY Patient.Birthday DESC;
SELECT T1.ID, CASE WHEN T2.ALB BETWEEN 3.5 AND 5.5 THEN 'Within' ELSE 'Out of' END FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE STRFTIME('%Y', T1.Birthday) = '1982'
SELECT      CAST(SUM(CASE WHEN T1.SEX = 'F' AND T2.UA > 6.5 THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(*) AS percentage FROM      Patient AS T1 INNER JOIN      Laboratory AS T2 ON      T1.ID = T2.ID WHERE      T1.SEX = 'F';
SELECT AVG(L.UA) AS Average_UA FROM Patient P INNER JOIN Laboratory L ON P.ID = L.ID WHERE L.Date = (     SELECT MAX(Date)     FROM Laboratory     WHERE ID = P.ID ) AND (     (P.SEX = 'M' AND L.UA < 8.0) OR     (P.SEX = 'F' AND L.UA < 6.5) );
SELECT DISTINCT T1.ID, T1.SEX, T1.Birthday FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.UN = 29
SELECT DISTINCT Patient.ID, Patient.SEX, Patient.Birthday FROM Patient INNER JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Patient.Diagnosis = 'RA' AND Laboratory.UN < 30;
SELECT COUNT(T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.CRE >= 1.5 AND T1.SEX = 'M'
SELECT SUM(CASE WHEN T1.SEX = 'M' THEN 1 ELSE 0 END) > SUM(CASE WHEN T1.SEX = 'F' THEN 1 ELSE 0 END) AS res FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.CRE >= 1.5
SELECT P.ID, P.SEX, P.Birthday FROM Patient AS P INNER JOIN Laboratory AS L ON P.ID = L.ID ORDER BY L.`T-BIL` DESC LIMIT 1;
SELECT DISTINCT CASE WHEN T1.SEX = 'F' THEN T1.ID END , CASE WHEN T1.SEX = 'M' THEN T1.ID END FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.`T-BIL` >= 2.0
SELECT T1.ID, T2.`T-CHO` FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID ORDER BY T1.Birthday, T2.`T-CHO` LIMIT 1
SELECT CAST(SUM(CASE WHEN T2.SEX = 'M' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T2.SEX) FROM Laboratory AS T1 INNER JOIN Patient AS T2 ON T1.ID = T2.ID WHERE T1.`T-CHO` >= 250
SELECT DISTINCT T1.ID, T1.Diagnosis FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.TG > 300
SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE strftime('%Y', CURRENT_TIMESTAMP) - strftime('%Y', T1.Birthday) > 50 AND T2.TG >= 200
SELECT T1.ID FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.Admission = '-' AND T2.CPK < 250
SELECT COUNT(*) AS MalePatientsWithHighCPK FROM Patient INNER JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Patient.SEX = 'M'   AND STRFTIME('%Y', Patient.Birthday) BETWEEN '1936' AND '1956'   AND Laboratory.CPK >= 250;
SELECT T1.ID, T1.SEX, strftime('%Y', 'now') - strftime('%Y', T1.Birthday) AS age FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.GLU >= 180 AND T2.`T-CHO` < 250
SELECT DISTINCT T1.ID, T2.GLU FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE STRFTIME('%Y', T1.Description) = '1991'   AND T2.GLU < 180;
SELECT T1.ID, T1.SEX, T1.Birthday FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.WBC < 3.5 OR T2.WBC > 9.0 ORDER BY T1.SEX, T1.Birthday ASC
SELECT DISTINCT T1.ID, strftime('%Y', CURRENT_TIMESTAMP) - strftime('%Y', T1.Birthday) AS age FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.RBC < 3.5
SELECT DISTINCT T1.Admission FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.SEX = 'F' AND T1.Birthday < DATE('now', '-50 years') AND (T2.RBC <= 3.5 OR T2.RBC >= 6.0)
SELECT DISTINCT Patient.ID, Patient.SEX FROM Patient INNER JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Patient.Admission = '-' AND Laboratory.HGB < 10;
SELECT T1.ID, T1.SEX FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.Diagnosis = 'SLE' AND 10 < T2.HGB < 17 ORDER BY T1.Birthday ASC LIMIT 1
SELECT ID, strftime('%Y', 'now') - strftime('%Y', Birthday) AS age FROM Patient WHERE ID IN ( SELECT ID FROM Laboratory WHERE HCT >= 52 GROUP BY ID HAVING COUNT(ID) >= 2 )
SELECT AVG(HCT)  FROM Laboratory  WHERE Date LIKE '1991%' AND HCT < 29;
SELECT SUM(IIF(PLT < 100, 1, 0)) - SUM(IIF(PLT > 400, 1, 0)) FROM Laboratory
SELECT T1.ID FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.Date LIKE '1984%' AND T1.Birthday IS NOT NULL AND (strftime('%Y', 'now') - strftime('%Y', T1.Birthday) < 50) AND T2.PLT BETWEEN 100 AND 400
SELECT CAST(SUM(CASE WHEN T2.SEX = 'F' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM Laboratory AS T1 INNER JOIN Patient AS T2 ON T1.ID = T2.ID WHERE strftime('%Y', 'now') - strftime('%Y', T2.Birthday) > 55 AND T1.PT >= 14
SELECT DISTINCT Patient.ID FROM Patient INNER JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE STRFTIME('%Y', Patient.`First Date`) > '1992' AND Laboratory.PT < 14;
SELECT COUNT(ID) FROM Laboratory WHERE APTT > 45 AND Date > '1997-01-01'
SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID INNER JOIN Examination AS T3 ON T1.ID = T3.ID WHERE T2.APTT > 45 AND T3.Thrombosis = 3
SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.SEX = 'M' AND T2.WBC BETWEEN 3.5 AND 9.0 AND (T2.FG <= 150 OR T2.FG >= 450)
SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.Birthday > '1980-01-01' AND (T2.FG <= 150 OR T2.FG >= 450)
SELECT DISTINCT T1.Diagnosis FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.`U-PRO` >= 30
SELECT DISTINCT Patient.ID FROM Patient INNER JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Laboratory.`U-PRO` > 0 AND Laboratory.`U-PRO` < 30   AND Patient.Diagnosis = 'SLE';
SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID INNER JOIN Examination AS T3 ON T1.ID = T3.ID WHERE T2.IGG < 900 AND T3.Symptoms = 'abortion'
SELECT COUNT(T1.ID) FROM Examination AS T1 INNER JOIN Patient AS T2 ON T1.ID = T2.ID INNER JOIN Laboratory AS T3 ON T3.ID = T2.ID WHERE T3.IGG BETWEEN 900 AND 2000 AND T1.Symptoms IS NOT NULL
SELECT T1.Diagnosis FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.IGA BETWEEN 80 AND 500 ORDER BY T2.IGA DESC LIMIT 1
SELECT COUNT(*)  FROM Patient  INNER JOIN Laboratory ON Patient.ID = Laboratory.ID  WHERE STRFTIME('%Y', Patient.`First Date`) >= '1990'    AND Laboratory.IGA BETWEEN 80 AND 500;
SELECT T2.Diagnosis FROM Laboratory AS T1 INNER JOIN Patient AS T2 ON T1.ID = T2.ID WHERE T1.IGM < 40 OR T1.IGM > 400 GROUP BY T2.Diagnosis ORDER BY COUNT(T2.Diagnosis) DESC LIMIT 1
SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE (T2.CRP LIKE '+' OR T2.CRP LIKE '-' OR T2.CRP < 1.0) AND T1.Description IS NULL
SELECT COUNT(T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE strftime('%Y', T1.Birthday) - strftime('%Y', date('now')) < -18 AND T2.CRP >= 1.0
SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID INNER JOIN Examination AS T3 ON T3.ID = T1.ID WHERE T2.RA IN ('-', '+-') AND T3.KCT = '+'
SELECT T1.Diagnosis FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE (T2.RA = '-' OR T2.RA = '+-') AND STRFTIME('%Y', T1.Birthday) >= '1995'
SELECT DISTINCT T1.ID FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.RF < 20   AND (CAST(STRFTIME('%Y', 'now') AS INTEGER) - CAST(STRFTIME('%Y', T1.Birthday) AS INTEGER)) > 60;
SELECT COUNT(*) FROM Laboratory AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID WHERE T1.RF < 20 AND T2.Thrombosis = 0
SELECT COUNT(DISTINCT Laboratory.ID) FROM Laboratory INNER JOIN Examination ON Laboratory.ID = Examination.ID WHERE Laboratory.C3 > 35 AND Examination.`ANA Pattern` = 'P';
SELECT T1.ID FROM Patient AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID INNER JOIN Laboratory AS T3 ON T1.ID = T3.ID WHERE T3.HCT NOT BETWEEN 29 AND 52 ORDER BY T2.`aCL IgA` DESC LIMIT 1
SELECT COUNT(DISTINCT T2.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.C4 > 10
SELECT COUNT(DISTINCT Patient.ID) FROM Patient INNER JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Laboratory.RNP IN ('-', '+-') AND Patient.Admission = '+';
SELECT P.Birthday FROM Patient AS P INNER JOIN Laboratory AS L ON P.ID = L.ID WHERE L.RNP NOT IN ('-', '+-') ORDER BY P.Birthday DESC LIMIT 1;
SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID INNER JOIN Laboratory AS T3 ON T1.ID = T3.ID WHERE T2.Thrombosis = 1 AND T3.SM IN ('-', '+-')
SELECT T1.ID FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.SM NOT IN ('-', '+-') ORDER BY T1.Birthday DESC LIMIT 3
SELECT T1.ID FROM Patient AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID INNER JOIN Laboratory AS T3 ON T1.ID = T3.ID WHERE T2.`Examination Date` >= '1997-01-01' AND T3.SC170 IN ('-', '+-')
SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID INNER JOIN Examination AS T3 ON T3.ID = T1.ID WHERE (T2.SC170 = '-' OR T2.SC170 = '+-') AND T1.SEX = 'M' AND T3.Symptoms = 'vertigo'
SELECT COUNT(DISTINCT Patient.ID) FROM Patient INNER JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Laboratory.SSA IN ('-', '+-')   AND STRFTIME('%Y', Patient.`First Date`) < '1990';
SELECT T1.ID FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.SSA NOT IN ('-', '+-') ORDER BY T1.`First Date` ASC LIMIT 1
SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID INNER JOIN Examination AS T3 ON T2.ID = T3.ID WHERE T2.SSB IN ('-', '+-') AND T3.Diagnosis = 'SLE'
SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID INNER JOIN Laboratory AS T3 ON T1.ID = T3.ID WHERE T3.SSB IN ('-', '+-') AND T2.Symptoms IS NOT NULL
SELECT COUNT(*)  FROM Patient  INNER JOIN Laboratory ON Patient.ID = Laboratory.ID  WHERE Laboratory.CENTROMEA IN ('-', '+-')    AND Laboratory.SSB IN ('-', '+-')    AND Patient.SEX = 'M';
SELECT DISTINCT T2.Diagnosis FROM Laboratory AS T1 INNER JOIN Patient AS T2 ON T1.ID = T2.ID WHERE T1.DNA >= 8
SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.DNA < 8 AND T1.Description IS NULL
SELECT COUNT(*)  FROM Laboratory AS L INNER JOIN Patient AS P  ON L.ID = P.ID WHERE L.`DNA-II` >= 8 AND P.Admission = '+';
SELECT CAST(SUM(CASE WHEN T1.GOT >= 60 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.ID) FROM Laboratory AS T1 INNER JOIN Patient AS T2 ON T1.ID = T2.ID WHERE T2.Diagnosis = 'SLE'
SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.SEX = 'M' AND T2.GOT < 60
SELECT P.Birthday FROM Patient AS P INNER JOIN Laboratory AS L ON P.ID = L.ID WHERE L.GOT >= 60 ORDER BY P.Birthday DESC LIMIT 1;
SELECT T1.Birthday FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.GPT < 60 ORDER BY T2.GPT DESC LIMIT 3
SELECT COUNT(T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.GOT < 60 AND T1.SEX = 'M'
SELECT P.Description FROM Laboratory AS L INNER JOIN Patient AS P ON L.ID = P.ID WHERE L.LDH < 500 ORDER BY L.LDH DESC LIMIT 1;
SELECT P.`First Date` FROM Patient AS P INNER JOIN Laboratory AS L ON P.ID = L.ID WHERE L.LDH >= 500 ORDER BY P.`First Date` DESC LIMIT 1;
SELECT COUNT(*) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.ALP >= 300 AND T1.Admission = '+'
SELECT COUNT(T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.ALP < 300 AND T1.Admission = '-'
SELECT DISTINCT T1.Diagnosis FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.TP < 6.0
SELECT COUNT(*)  FROM Patient  INNER JOIN Laboratory ON Patient.ID = Laboratory.ID  WHERE Patient.Diagnosis = 'SJS'    AND Laboratory.TP > 6.0    AND Laboratory.TP < 8.5;
SELECT Date  FROM Laboratory  WHERE ALB > 3.5 AND ALB < 5.5  ORDER BY ALB DESC  LIMIT 1;
SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.SEX = 'M' AND T2.TP > 6.0 AND T2.TP < 8.5 AND T2.ALB > 3.5 AND T2.ALB < 5.5
SELECT T1.`aCL IgG`, T1.`aCL IgM`, T1.`aCL IgA` FROM Examination AS T1 INNER JOIN Patient AS T2 ON T1.ID = T2.ID INNER JOIN Laboratory AS T3 ON T2.ID = T3.ID WHERE T2.SEX = 'F' ORDER BY T3.UA DESC LIMIT 1
SELECT T2.ANA FROM Laboratory AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID WHERE T1.CRE < 1.5 ORDER BY T2.ANA DESC LIMIT 1
SELECT T2.ID FROM Laboratory AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID WHERE T1.CRE < 1.5 ORDER BY T2.`aCL IgA` DESC LIMIT 1
SELECT COUNT(DISTINCT T1.ID) FROM Patient AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID INNER JOIN Laboratory AS T3 ON T1.ID = T3.ID WHERE T3.`T-BIL` >= 2 AND T2.`ANA Pattern` = 'P'
SELECT T1.ANA FROM Examination AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.`T-BIL` < 2.0 ORDER BY T2.`T-BIL` DESC LIMIT 1
SELECT COUNT(*)  FROM Laboratory AS L INNER JOIN Examination AS E  ON L.ID = E.ID WHERE L.`T-CHO` >= 250 AND E.KCT = '-';
SELECT COUNT(T1.ID) FROM Patient AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID INNER JOIN Laboratory AS T3 ON T1.ID = T3.ID WHERE T3.`T-CHO` < 250 AND T2.`ANA Pattern` = 'P'
SELECT COUNT(*) FROM Laboratory AS L INNER JOIN Examination AS E ON L.ID = E.ID WHERE L.TG < 200 AND E.Symptoms IS NOT NULL;
SELECT T1.Diagnosis FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T2.TG < 200 ORDER BY T2.TG DESC LIMIT 1
SELECT DISTINCT T2.ID FROM Examination AS T1 INNER JOIN Patient AS T2 ON T1.ID = T2.ID INNER JOIN Laboratory AS T3 ON T2.ID = T3.ID WHERE T1.Thrombosis = 0 AND T3.CPK < 250
SELECT COUNT(T1.ID) FROM Patient AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID WHERE T2.KCT = '+' OR T2.RVVT = '+' OR T2.LAC = '+' AND T1.ID IN ( SELECT ID FROM Laboratory WHERE CPK < 250 )
SELECT P.Birthday FROM Patient AS P INNER JOIN Laboratory AS L ON P.ID = L.ID WHERE L.GLU > 180 ORDER BY P.Birthday ASC LIMIT 1;
SELECT COUNT(L.ID) FROM Laboratory AS L INNER JOIN Examination AS E ON L.ID = E.ID WHERE L.GLU < 180 AND E.Thrombosis = 0;
SELECT COUNT(*) AS Normal_WBC_Count FROM Patient INNER JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Patient.Admission = '+' AND Laboratory.WBC BETWEEN 3.5 AND 9.0;
SELECT COUNT(*) AS SLE_Patient_Count FROM Patient INNER JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE Patient.Diagnosis = 'SLE' AND Laboratory.WBC BETWEEN 3.5 AND 9.0;
SELECT DISTINCT Patient.ID FROM Patient INNER JOIN Laboratory ON Patient.ID = Laboratory.ID WHERE (Laboratory.RBC <= 3.5 OR Laboratory.RBC >= 6.0)   AND Patient.Admission = '-';
SELECT COUNT(T1.ID) FROM Patient AS T1 INNER JOIN Examination AS T2 ON T1.ID = T2.ID WHERE T1.SEX = 'F' AND T2.Thrombosis = 0
SELECT T2.PLT FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID INNER JOIN Examination AS T3 ON T3.ID = T2.ID WHERE T1.Diagnosis = 'MCTD' AND T2.PLT > 100 AND T2.PLT < 400
SELECT AVG(T2.PT) FROM Patient AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.SEX = 'M' AND T2.PT < 14
SELECT COUNT(*) FROM Examination AS T1 INNER JOIN Laboratory AS T2 ON T1.ID = T2.ID WHERE T1.Thrombosis IN (1, 2) AND T2.PT < 14;
SELECT major.major_name FROM member INNER JOIN major ON member.link_to_major = major.major_id WHERE member.first_name = 'Angela' AND member.last_name = 'Sanders';
SELECT COUNT(T1.member_id) FROM member AS T1 INNER JOIN major AS T2 ON T1.link_to_major = T2.major_id WHERE T2.college = 'College of Engineering'
SELECT member.first_name, member.last_name FROM member INNER JOIN major ON member.link_to_major = major.major_id WHERE major.department = 'Art and Design Department';
SELECT COUNT(*) AS number_of_attendees FROM event INNER JOIN attendance ON event.event_id = attendance.link_to_event WHERE event.event_name = 'Women''s Soccer';
SELECT T3.phone FROM event AS T1 INNER JOIN attendance AS T2 ON T1.event_id = T2.link_to_event INNER JOIN member AS T3 ON T2.link_to_member = T3.member_id WHERE T1.event_name = 'Women''s Soccer'
SELECT COUNT(*) FROM attendance AS T1 INNER JOIN member AS T2 ON T2.member_id = T1.link_to_member INNER JOIN event AS T3 ON T3.event_id = T1.link_to_event WHERE T2.t_shirt_size = 'Medium' AND T3.event_name = 'Women''s Soccer'
SELECT T1.event_name FROM event AS T1 INNER JOIN attendance AS T2 ON T1.event_id = T2.link_to_event INNER JOIN member AS T3 ON T2.link_to_member = T3.member_id GROUP BY T1.event_name ORDER BY COUNT(T1.event_name) DESC LIMIT 1
SELECT DISTINCT major.college FROM member INNER JOIN major ON member.link_to_major = major.major_id WHERE member.position = 'Vice President';
SELECT e.event_name FROM member AS m INNER JOIN attendance AS a ON m.member_id = a.link_to_member INNER JOIN event AS e ON a.link_to_event = e.event_id WHERE m.first_name = 'Maya' AND m.last_name = 'Mclean';
SELECT COUNT(*) FROM event AS T1 INNER JOIN attendance AS T2 ON T1.event_id = T2.link_to_event INNER JOIN member AS T3 ON T3.member_id = T2.link_to_member WHERE T3.first_name = 'Sacha' AND T3.last_name = 'Harrison' AND STRFTIME('%Y', T1.event_date) = '2019'
SELECT COUNT(*)  FROM (     SELECT T1.event_id     FROM event AS T1     INNER JOIN attendance AS T2      ON T1.event_id = T2.link_to_event     WHERE T1.type = 'Meeting'     GROUP BY T1.event_id     HAVING COUNT(T2.link_to_member) > 10 ) subquery;
SELECT T1.event_name FROM event AS T1 INNER JOIN attendance AS T2 ON T1.event_id = T2.link_to_event GROUP BY T1.event_id HAVING COUNT(T2.link_to_event) > 20
SELECT CAST(COUNT(T1.link_to_event) AS REAL) / COUNT(DISTINCT T2.event_name) FROM attendance AS T1 INNER JOIN event AS T2 ON T1.link_to_event = T2.event_id WHERE T2.type = 'Meeting' AND STRFTIME('%Y', T2.event_date) = '2020'
SELECT expense_description  FROM expense  ORDER BY cost DESC  LIMIT 1;
SELECT COUNT(*)  FROM member  INNER JOIN major  ON member.link_to_major = major.major_id  WHERE major.major_name = 'Environmental Engineering';
SELECT member.first_name, member.last_name FROM member INNER JOIN attendance ON member.member_id = attendance.link_to_member INNER JOIN event ON attendance.link_to_event = event.event_id WHERE event.event_name = 'Laugh Out Loud';
SELECT member.last_name FROM member INNER JOIN major ON member.link_to_major = major.major_id WHERE major.major_name = 'Law and Constitutional Studies';
SELECT T2.county FROM member AS T1 INNER JOIN zip_code AS T2 ON T1.zip = T2.zip_code WHERE T1.first_name = 'Sherri' AND T1.last_name = 'Ramsey'
SELECT DISTINCT major.college FROM member INNER JOIN major ON member.link_to_major = major.major_id WHERE member.first_name = 'Tyler' AND member.last_name = 'Hewitt';
SELECT SUM(T2.amount) FROM member AS T1 INNER JOIN income AS T2 ON T1.member_id = T2.link_to_member WHERE T1.position = 'Vice President'
SELECT SUM(T2.spent) FROM event AS T1 INNER JOIN budget AS T2 ON T1.event_id = T2.link_to_event WHERE T1.event_name = 'September Meeting' AND T2.category = 'Food'
SELECT DISTINCT zip_code.city, zip_code.state FROM member INNER JOIN zip_code ON member.zip = zip_code.zip_code WHERE member.position = 'President';
SELECT member.first_name, member.last_name FROM member INNER JOIN zip_code ON member.zip = zip_code.zip_code WHERE zip_code.state = 'Illinois' AND member.position = 'Member';
SELECT SUM(T1.spent) FROM budget AS T1 INNER JOIN event AS T2 ON T1.link_to_event = T2.event_id WHERE T2.event_name = 'September Meeting' AND T1.category = 'Advertisement'
SELECT DISTINCT major.department FROM member INNER JOIN major ON member.link_to_major = major.major_id WHERE member.last_name = 'Pierce' OR member.last_name = 'Guidi';
SELECT SUM(T2.amount) FROM event AS T1 INNER JOIN budget AS T2 ON T1.event_id = T2.link_to_event WHERE T1.event_name = 'October Speaker'
SELECT T1.approved FROM expense AS T1 INNER JOIN budget AS T2 ON T2.budget_id = T1.link_to_budget INNER JOIN event AS T3 ON T3.event_id = T2.link_to_event WHERE T3.event_name = 'October Meeting' AND T3.event_date = '2019-10-08T12:00:00'
SELECT SUM(T2.cost) FROM member AS T1 INNER JOIN expense AS T2 ON T1.member_id = T2.link_to_member WHERE T1.first_name = 'Elijah' AND T1.last_name = 'Allen' AND (STRFTIME('%m', T2.expense_date) = '09' OR STRFTIME('%m', T2.expense_date) = '10')
SELECT SUM(CASE WHEN SUBSTR(T2.event_date, 1, 4) = '2019' THEN T1.spent ELSE 0 END) - SUM(CASE WHEN SUBSTR(T2.event_date, 1, 4) = '2020' THEN T1.spent ELSE 0 END) FROM budget AS T1 INNER JOIN event AS T2 ON T1.link_to_event = T2.event_id
SELECT location  FROM event  WHERE event_name = 'Spring Budget Review';
SELECT cost FROM expense WHERE expense_description = 'Posters' AND expense_date = '2019-09-04'
SELECT remaining  FROM budget  WHERE category = 'Food'  ORDER BY amount DESC  LIMIT 1;
SELECT notes FROM income WHERE source = 'Fundraising' AND date_received = '2019-09-14'
SELECT COUNT(*)  FROM major  WHERE college = 'College of Humanities and Social Sciences';
SELECT phone  FROM member  WHERE first_name = 'Carlo' AND last_name = 'Jacobs';
SELECT zip_code.county FROM member INNER JOIN zip_code ON member.zip = zip_code.zip_code WHERE member.first_name = 'Adela' AND member.last_name = 'O''Gallagher';
SELECT COUNT(T1.event_name) FROM event AS T1 INNER JOIN budget AS T2 ON T1.event_id = T2.link_to_event WHERE T1.event_name = 'November Meeting' AND T2.remaining < 0
SELECT SUM(budget.amount) FROM budget INNER JOIN event ON budget.link_to_event = event.event_id WHERE event.event_name = 'September Speaker';
SELECT T1.event_status FROM budget AS T1 INNER JOIN expense AS T2 ON T1.budget_id = T2.link_to_budget WHERE T2.expense_description = 'Post Cards, Posters' AND T2.expense_date = '2019-08-20'
SELECT major.major_name FROM member INNER JOIN major ON member.link_to_major = major.major_id WHERE member.first_name = 'Brent' AND member.last_name = 'Thomason';
SELECT COUNT(*) FROM member AS T1 INNER JOIN major AS T2 ON T1.link_to_major = T2.major_id WHERE T1.t_shirt_size = 'Large' AND T2.major_name = 'Human Development and Family Studies'
SELECT T2.type FROM member AS T1 INNER JOIN zip_code AS T2 ON T1.zip = T2.zip_code WHERE T1.first_name = 'Christof' AND T1.last_name = 'Nielson'
SELECT T2.major_name FROM member AS T1 INNER JOIN major AS T2 ON T1.link_to_major = T2.major_id WHERE T1.position = 'Vice President'
SELECT T2.state FROM member AS T1 INNER JOIN zip_code AS T2 ON T1.zip = T2.zip_code WHERE T1.first_name = 'Sacha' AND T1.last_name = 'Harrison'
SELECT major.department FROM member INNER JOIN major ON member.link_to_major = major.major_id WHERE member.position = 'President';
SELECT T2.date_received FROM member AS T1 INNER JOIN income AS T2 ON T1.member_id = T2.link_to_member WHERE T1.first_name = 'Connor' AND T1.last_name = 'Hilton' AND T2.source = 'Dues'
SELECT T1.first_name, T1.last_name FROM member AS T1 INNER JOIN income AS T2 ON T1.member_id = T2.link_to_member WHERE T2.source = 'Dues' ORDER BY T2.date_received LIMIT 1
SELECT SUM(IIF(T1.event_name = 'Yearly Kickoff', T2.amount, 0)) / SUM(IIF(T1.event_name = 'October Meeting', T2.amount, 0)) AS num FROM event AS T1 INNER JOIN budget AS T2 ON T1.event_id = T2.link_to_event WHERE T2.category = 'Advertisement'
SELECT CAST(SUM(CASE WHEN T1.category = 'Parking' THEN T1.amount ELSE 0 END) AS REAL) * 100 / SUM(T1.amount) FROM budget AS T1 INNER JOIN event AS T2 ON T1.link_to_event = T2.event_id WHERE T2.event_name = 'November Speaker'
SELECT SUM(cost) AS total_pizza_cost FROM expense WHERE expense_description = 'Pizza';
SELECT COUNT(city)  FROM zip_code  WHERE county = 'Orange County' AND state = 'Virginia';
SELECT department FROM major WHERE college = 'College of Humanities and Social Sciences'
SELECT T2.city, T2.county, T2.state FROM member AS T1 INNER JOIN zip_code AS T2 ON T1.zip = T2.zip_code WHERE T1.first_name = 'Amy' AND T1.last_name = 'Firth';
SELECT T2.expense_description FROM budget AS T1 INNER JOIN expense AS T2 ON T1.budget_id = T2.link_to_budget ORDER BY T1.remaining LIMIT 1
SELECT DISTINCT T3.member_id FROM event AS T1 INNER JOIN attendance AS T2 ON T1.event_id = T2.link_to_event INNER JOIN member AS T3 ON T2.link_to_member = T3.member_id WHERE T1.event_name = 'October Meeting'
SELECT major.college FROM member INNER JOIN major ON member.link_to_major = major.major_id GROUP BY major.college ORDER BY COUNT(*) DESC LIMIT 1;
SELECT major.major_name FROM member INNER JOIN major ON member.link_to_major = major.major_id WHERE member.phone = '809-555-3360';
SELECT T2.event_name FROM budget AS T1 INNER JOIN event AS T2 ON T1.link_to_event = T2.event_id ORDER BY T1.amount DESC LIMIT 1
SELECT T2.expense_description FROM member AS T1 INNER JOIN expense AS T2 ON T1.member_id = T2.link_to_member WHERE T1.position = 'Vice President'
SELECT COUNT(*)  FROM event  INNER JOIN attendance  ON event.event_id = attendance.link_to_event  WHERE event.event_name = 'Women''s Soccer';
SELECT income.date_received FROM income INNER JOIN member ON income.link_to_member = member.member_id WHERE member.first_name = 'Casey' AND member.last_name = 'Mason';
SELECT COUNT(*) FROM member AS T1 INNER JOIN zip_code AS T2 ON T1.zip = T2.zip_code WHERE T2.state = 'Maryland'
SELECT COUNT(T2.link_to_event) FROM member AS T1 INNER JOIN attendance AS T2 ON T1.member_id = T2.link_to_member WHERE T1.phone = '954-555-6240'
SELECT T1.first_name, T1.last_name FROM member AS T1 INNER JOIN major AS T2 ON T1.link_to_major = T2.major_id WHERE T2.department = 'School of Applied Sciences, Technology and Education'
SELECT T2.event_name FROM budget AS T1 INNER JOIN event AS T2 ON T1.link_to_event = T2.event_id WHERE T2.status = 'Closed' ORDER BY CAST(T1.spent AS REAL) / T1.amount DESC LIMIT 1
SELECT COUNT(*)  FROM member  WHERE position = 'President';
SELECT MAX(spent) AS highest_spent FROM budget;
SELECT COUNT(*) FROM event WHERE type = 'Meeting' AND STRFTIME('%Y', event_date) = '2020'
SELECT SUM(spent) FROM budget WHERE category = 'Food'
SELECT m.first_name, m.last_name FROM attendance AS a INNER JOIN member AS m ON a.link_to_member = m.member_id GROUP BY m.first_name, m.last_name HAVING COUNT(a.link_to_event) > 7;
SELECT T2.first_name, T2.last_name FROM major AS T1 INNER JOIN member AS T2 ON T1.major_id = T2.link_to_major INNER JOIN attendance AS T3 ON T2.member_id = T3.link_to_member INNER JOIN event AS T4 ON T3.link_to_event = T4.event_id WHERE T4.event_name = 'Community Theater' AND T1.major_name = 'Interior Design'
SELECT member.first_name, member.last_name FROM member INNER JOIN zip_code ON member.zip = zip_code.zip_code WHERE zip_code.city = 'Georgetown' AND zip_code.state = 'South Carolina';
SELECT T2.amount FROM member AS T1 INNER JOIN income AS T2 ON T1.member_id = T2.link_to_member WHERE T1.first_name = 'Grant' AND T1.last_name = 'Gilmour'
SELECT DISTINCT member.first_name, member.last_name FROM member INNER JOIN income ON member.member_id = income.link_to_member WHERE income.amount > 40;
SELECT SUM(T1.cost) FROM expense AS T1 INNER JOIN budget AS T2 ON T1.link_to_budget = T2.budget_id INNER JOIN event AS T3 ON T2.link_to_event = T3.event_id WHERE T3.event_name = 'Baseball game'
SELECT DISTINCT member.first_name, member.last_name FROM event INNER JOIN budget ON event.event_id = budget.link_to_event INNER JOIN expense ON budget.budget_id = expense.link_to_budget INNER JOIN member ON expense.link_to_member = member.member_id WHERE event.event_name = 'Yearly Kickoff';
SELECT T1.first_name, T1.last_name, T2.source FROM member AS T1 INNER JOIN income AS T2 ON T1.member_id = T2.link_to_member GROUP BY T1.first_name, T1.last_name, T2.source ORDER BY SUM(T2.amount) DESC LIMIT 1
SELECT e.event_name FROM event e INNER JOIN budget b ON e.event_id = b.link_to_event INNER JOIN expense ex ON b.budget_id = ex.link_to_budget ORDER BY ex.cost ASC LIMIT 1;
SELECT SUM(CASE WHEN T1.event_name = 'Yearly Kickoff' THEN T3.cost ELSE 0 END) * 100 / SUM(T3.cost) FROM event AS T1 INNER JOIN budget AS T2 ON T1.event_id = T2.link_to_event INNER JOIN expense AS T3 ON T2.budget_id = T3.link_to_budget
SELECT CAST(SUM(CASE WHEN T1.major_name = 'Finance' THEN 1 ELSE 0 END) AS REAL) / SUM(CASE WHEN T1.major_name = 'Physics' THEN 1 ELSE 0 END) AS radio FROM major AS T1 INNER JOIN member AS T2 ON T1.major_id = T2.link_to_major
SELECT source FROM income WHERE date_received LIKE '2019-09%' ORDER BY amount DESC LIMIT 1
SELECT first_name, last_name, email FROM member WHERE position = 'Secretary'
SELECT COUNT(T2.member_id) FROM major AS T1 INNER JOIN member AS T2 ON T1.major_id = T2.link_to_major WHERE T1.major_name = 'Physics Teaching'
SELECT COUNT(*) FROM attendance INNER JOIN event ON attendance.link_to_event = event.event_id WHERE event.event_name = 'Community Theater'   AND STRFTIME('%Y', event.event_date) = '2019';
SELECT COUNT(T1.link_to_event) , T2.major_name FROM attendance AS T1 INNER JOIN major AS T2 ON T1.link_to_member = T2.major_id INNER JOIN member AS T3 ON T3.member_id = T1.link_to_member WHERE T3.first_name = 'Luisa' AND T3.last_name = 'Guidi'
SELECT SUM(T1.spent) / COUNT(T1.event_status) FROM budget AS T1 INNER JOIN event AS T2 ON T1.link_to_event = T2.event_id WHERE T1.category = 'Food' AND T1.event_status = 'Closed'
SELECT e.event_name FROM budget AS b INNER JOIN event AS e ON b.link_to_event = e.event_id WHERE b.category = 'Advertisement' ORDER BY b.spent DESC LIMIT 1;
SELECT T2.event_name FROM attendance AS T1 INNER JOIN event AS T2 ON T1.link_to_event = T2.event_id INNER JOIN member AS T3 ON T1.link_to_member = T3.member_id WHERE T3.first_name = 'Maya' AND T3.last_name = 'Mclean' AND T2.event_name = 'Women''s Soccer'
SELECT      CAST(SUM(CASE WHEN type = 'Community Service' THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(event_id) AS community_service_percentage FROM      event WHERE      event_date LIKE '2019-%';
SELECT expense.cost FROM expense INNER JOIN budget ON expense.link_to_budget = budget.budget_id INNER JOIN event ON budget.link_to_event = event.event_id WHERE expense.expense_description = 'Posters' AND event.event_name = 'September Speaker';
SELECT t_shirt_size FROM member GROUP BY t_shirt_size ORDER BY COUNT(t_shirt_size) DESC LIMIT 1
SELECT T2.event_name FROM budget AS T1 INNER JOIN event AS T2 ON T2.event_id = T1.link_to_event WHERE T1.event_status = 'Closed' AND T1.remaining < 0 ORDER BY T1.remaining LIMIT 1
SELECT SUM(T3.cost) FROM event AS T1 INNER JOIN budget AS T2 ON T1.event_id = T2.link_to_event INNER JOIN expense AS T3 ON T2.budget_id = T3.link_to_budget WHERE T1.event_name = 'October Meeting' AND T3.approved = 'true'
SELECT budget.category, budget.amount FROM budget INNER JOIN event ON budget.link_to_event = event.event_id WHERE event.event_name = 'April Speaker' ORDER BY budget.amount ASC;
SELECT budget_id FROM budget WHERE category = 'Food' ORDER BY amount DESC LIMIT 1
SELECT budget_id FROM budget WHERE category = 'Advertisement' ORDER BY amount DESC LIMIT 3
SELECT SUM(cost)  FROM expense  WHERE expense_description = 'Parking';
SELECT SUM(cost) AS total_expense FROM expense WHERE expense_date = '2019-08-20';
SELECT T1.first_name, T1.last_name, SUM(T2.cost) FROM member AS T1 INNER JOIN expense AS T2 ON T1.member_id = T2.link_to_member WHERE T1.member_id = 'rec4BLdZHS2Blfp4v'
SELECT T2.expense_description FROM member AS T1 INNER JOIN expense AS T2 ON T1.member_id = T2.link_to_member WHERE T1.first_name = 'Sacha' AND T1.last_name = 'Harrison'
SELECT DISTINCT T2.expense_description FROM member AS T1 INNER JOIN expense AS T2 ON T1.member_id = T2.link_to_member WHERE T1.t_shirt_size = 'X-Large'
SELECT DISTINCT member.zip FROM member INNER JOIN expense ON member.member_id = expense.link_to_member WHERE expense.cost < 50;
SELECT major.major_name FROM member INNER JOIN major ON member.link_to_major = major.major_id WHERE member.first_name = 'Phillip' AND member.last_name = 'Cullen';
SELECT T2.position FROM major AS T1 INNER JOIN member AS T2 ON T1.major_id = T2.link_to_major WHERE T1.major_name = 'Business'
SELECT COUNT(T2.member_id) FROM major AS T1 INNER JOIN member AS T2 ON T1.major_id = T2.link_to_major WHERE T1.major_name = 'Business' AND T2.t_shirt_size = 'Medium'
SELECT DISTINCT event.type FROM budget INNER JOIN event ON budget.link_to_event = event.event_id WHERE budget.remaining > 30;
SELECT type FROM event WHERE location = 'MU 215'
SELECT type FROM event WHERE event_date = '2020-03-24T12:00:00'
SELECT T1.major_name FROM major AS T1 INNER JOIN member AS T2 ON T1.major_id = T2.link_to_major WHERE T2.position = 'Vice President'
SELECT CAST(SUM(CASE WHEN T1.position = 'Member' AND T2.major_name = 'Mathematics' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM member AS T1 INNER JOIN major AS T2 ON T1.link_to_major = T2.major_id
SELECT DISTINCT T2.category FROM event AS T1 INNER JOIN budget AS T2 ON T1.event_id = T2.link_to_event WHERE T1.location = 'MU 215'
SELECT COUNT(*)  FROM income  WHERE amount = 50;
SELECT COUNT(*)  FROM member  WHERE position = 'Member' AND t_shirt_size = 'X-Large';
SELECT COUNT(major_id) FROM major WHERE department = 'School of Applied Sciences, Technology and Education' AND college = 'College of Agriculture and Applied Sciences'
SELECT member.last_name, major.department, major.college FROM member INNER JOIN major ON member.link_to_major = major.major_id WHERE major.major_name = 'Environmental Engineering';
SELECT DISTINCT T2.category, T1.type FROM event AS T1 INNER JOIN budget AS T2 ON T1.event_id = T2.link_to_event WHERE T1.location = 'MU 215' AND T2.spent = 0 AND T1.type = 'Guest Speaker'
SELECT T2.city, T2.state FROM member AS T1 INNER JOIN zip_code AS T2 ON T2.zip_code = T1.zip INNER JOIN major AS T3 ON T3.major_id = T1.link_to_major WHERE T3.department = 'Electrical and Computer Engineering Department'
SELECT T1.event_name FROM event AS T1 INNER JOIN attendance AS T2 ON T1.event_id = T2.link_to_event INNER JOIN member AS T3 ON T3.member_id = T2.link_to_member WHERE T1.location = '900 E. Washington St.' AND T3.position = 'Vice President'
SELECT T2.last_name, T2.position FROM expense AS T1 INNER JOIN member AS T2 ON T2.member_id = T1.link_to_member WHERE T1.expense_date LIKE '2019-09-10' AND T1.expense_description = 'Pizza'
SELECT T3.last_name FROM attendance AS T1 INNER JOIN event AS T2 ON T2.event_id = T1.link_to_event INNER JOIN member AS T3 ON T1.link_to_member = T3.member_id WHERE T2.event_name = 'Women''s Soccer' AND T3.position = 'Member'
SELECT CAST(SUM(CASE WHEN T1.amount = 50 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM income AS T1 INNER JOIN member AS T2 ON T2.member_id = T1.link_to_member WHERE T2.t_shirt_size = 'Medium' AND T2.position = 'Member'
SELECT state FROM zip_code WHERE type = 'PO Box'
SELECT zip_code FROM zip_code WHERE type = 'PO Box' AND county = 'San Juan Municipio' AND state = 'Puerto Rico'
SELECT event_name FROM event WHERE type = 'Game' AND status = 'Closed' AND event_date BETWEEN '2019-03-15' AND '2020-03-20'
SELECT T2.link_to_event FROM expense AS T1 INNER JOIN attendance AS T2 ON T2.link_to_member = T1.link_to_member WHERE T1.cost > 50
SELECT link_to_member, link_to_event FROM attendance WHERE link_to_member IN ( SELECT link_to_member FROM expense WHERE approved = 'true' AND expense_date BETWEEN '2019-01-10' AND '2019-11-19' )
SELECT major.college FROM member INNER JOIN major ON member.link_to_major = major.major_id WHERE member.first_name = 'Katy' AND member.link_to_major = 'rec1N0upiVLy5esTO';
SELECT T1.phone FROM member AS T1 INNER JOIN major AS T2 ON T2.major_id = T1.link_to_major WHERE T2.major_name = 'Business' AND T2.college = 'College of Agriculture and Applied Sciences'
SELECT DISTINCT member.email FROM expense INNER JOIN member ON expense.link_to_member = member.member_id WHERE expense.expense_date BETWEEN '2019-09-10' AND '2019-11-19'   AND expense.cost > 20;
SELECT COUNT(*) AS member_count FROM member INNER JOIN major ON member.link_to_major = major.major_id WHERE member.position = 'Member'   AND major.college = 'College of Education & Human Services';
SELECT CAST(SUM(CASE WHEN remaining < 0 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM budget
SELECT event_id, location, status FROM event WHERE event_date BETWEEN '2019-11-01' AND '2020-03-31';
SELECT expense_description FROM expense GROUP BY expense_description HAVING SUM(cost) / COUNT(expense_id) > 50
SELECT first_name, last_name FROM member WHERE t_shirt_size = 'X-Large'
SELECT CAST(SUM(IIF(type = 'PO Box', 1, 0)) AS REAL) * 100 / COUNT(zip_code) FROM zip_code
SELECT T1.event_name, T1.location FROM event AS T1 INNER JOIN budget AS T2 ON T1.event_id = T2.link_to_event WHERE T2.remaining > 0
SELECT T1.event_name, T1.event_date FROM event AS T1 INNER JOIN budget AS T2 ON T1.event_id = T2.link_to_event INNER JOIN expense AS T3 ON T2.budget_id = T3.link_to_budget WHERE T3.expense_description = 'Pizza' AND T3.cost > 50 AND T3.cost < 100
SELECT DISTINCT      member.first_name,      member.last_name,      major.major_name FROM      expense INNER JOIN      member ON expense.link_to_member = member.member_id INNER JOIN      major ON member.link_to_major = major.major_id WHERE      expense.cost > 100;
SELECT T3.city, T3.county FROM income AS T1 INNER JOIN member AS T2 ON T1.link_to_member = T2.member_id INNER JOIN zip_code AS T3 ON T2.zip = T3.zip_code GROUP BY T1.link_to_member HAVING SUM(T1.amount) > 40
SELECT m.first_name, m.last_name FROM expense e INNER JOIN member m ON e.link_to_member = m.member_id GROUP BY e.link_to_member HAVING COUNT(*) > 1 ORDER BY SUM(e.cost) DESC LIMIT 1;
SELECT SUM(T3.cost) / COUNT(T1.member_id) FROM member AS T1 INNER JOIN attendance AS T2 ON T1.member_id = T2.link_to_member INNER JOIN expense AS T3 ON T2.link_to_member = T3.link_to_member WHERE T1.position != 'Member'
SELECT DISTINCT T1.event_name FROM event AS T1 INNER JOIN budget AS T2 ON T1.event_id = T2.link_to_event INNER JOIN expense AS T3 ON T2.budget_id = T3.link_to_budget WHERE T2.category = 'Parking'   AND T3.cost < (     SELECT SUM(T6.cost) / COUNT(T4.event_id)     FROM event AS T4     INNER JOIN budget AS T5 ON T4.event_id = T5.link_to_event     INNER JOIN expense AS T6 ON T5.budget_id = T6.link_to_budget     WHERE T5.category = 'Parking'   )
SELECT SUM(CASE WHEN T1.type = 'Game' THEN T3.cost ELSE 0 END) * 100 / SUM(T3.cost) FROM event AS T1 INNER JOIN budget AS T2 ON T1.event_id = T2.link_to_event INNER JOIN expense AS T3 ON T2.budget_id = T3.link_to_budget
SELECT T2.category FROM expense AS T1 INNER JOIN budget AS T2 ON T1.link_to_budget = T2.budget_id WHERE T1.expense_description = 'Water, chips, cookies' ORDER BY T1.cost DESC LIMIT 1
SELECT T1.first_name, T1.last_name FROM member AS T1 INNER JOIN expense AS T2 ON T1.member_id = T2.link_to_member ORDER BY T2.cost DESC LIMIT 5
SELECT T1.first_name, T1.last_name, T1.phone FROM member AS T1 INNER JOIN expense AS T2 ON T1.member_id = T2.link_to_member WHERE T2.cost > ( SELECT AVG(T2.cost) FROM member AS T1 INNER JOIN expense AS T2 ON T1.member_id = T2.link_to_member )
SELECT SUM(CASE WHEN T2.state = 'Maine' THEN 1 ELSE 0 END) / COUNT(T1.position) - SUM(CASE WHEN T2.state = 'Vermont' THEN 1 ELSE 0 END) / COUNT(T1.position) FROM member AS T1 INNER JOIN zip_code AS T2 ON T1.zip = T2.zip_code
SELECT T2.major_name, T2.department FROM member AS T1 INNER JOIN major AS T2 ON T1.link_to_major = T2.major_id WHERE T1.first_name = 'Garrett' AND T1.last_name = 'Gerke'
SELECT T1.first_name, T1.last_name, T2.cost FROM member AS T1 INNER JOIN expense AS T2 ON T1.member_id = T2.link_to_member WHERE T2.expense_description = 'Water, Veggie tray, supplies'
SELECT member.last_name, member.phone FROM member INNER JOIN major ON member.link_to_major = major.major_id WHERE major.major_name = 'Elementary Education';
SELECT T1.category, T1.amount FROM budget AS T1 INNER JOIN event AS T2 ON T1.link_to_event = T2.event_id WHERE T2.event_name = 'January Speaker'
SELECT event.event_name FROM budget INNER JOIN event ON budget.link_to_event = event.event_id WHERE budget.category = 'Food';
SELECT member.first_name, member.last_name, income.amount FROM member INNER JOIN income ON member.member_id = income.link_to_member WHERE income.date_received = '2019-09-09';
SELECT DISTINCT T2.category FROM expense AS T1 INNER JOIN budget AS T2 ON T1.link_to_budget = T2.budget_id WHERE T1.expense_description = 'Posters'
SELECT member.first_name, member.last_name, major.college FROM member INNER JOIN major ON member.link_to_major = major.major_id WHERE member.position = 'Secretary';
SELECT SUM(b.spent) AS total_spent, e.event_name FROM budget AS b INNER JOIN event AS e ON b.link_to_event = e.event_id WHERE b.category = 'Speaker Gifts';
SELECT T2.city FROM member AS T1 INNER JOIN zip_code AS T2 ON T2.zip_code = T1.zip WHERE T1.first_name = 'Garrett' AND T1.last_name = 'Girke'
SELECT member.first_name, member.last_name, member.position FROM member INNER JOIN zip_code ON member.zip = zip_code.zip_code WHERE zip_code.city = 'Lincolnton'   AND zip_code.state = 'North Carolina'   AND member.zip = 28092;
SELECT COUNT(GasStationID) FROM gasstations WHERE Country = 'CZE' AND Segment = 'Premium'
SELECT CAST(SUM(IIF(Currency = 'EUR', 1, 0)) AS FLOAT) / SUM(IIF(Currency = 'CZK', 1, 0)) FROM customers
SELECT T1.CustomerID FROM customers AS T1 INNER JOIN yearmonth AS T2 ON T1.CustomerID = T2.CustomerID WHERE T1.Segment = 'LAM' AND T2.Date BETWEEN '201201' AND '201212' ORDER BY T2.Consumption LIMIT 1
SELECT CAST(SUM(T2.Consumption) AS REAL) / 12 FROM customers AS T1 INNER JOIN yearmonth AS T2 ON T1.CustomerID = T2.CustomerID WHERE T1.Segment = 'SME' AND SUBSTR(T2.Date, 1, 4) = '2013'
SELECT T1.CustomerID FROM yearmonth AS T1 INNER JOIN customers AS T2 ON T1.CustomerID = T2.CustomerID WHERE T2.Currency = 'CZK' AND T1.Date LIKE '2011%' ORDER BY T1.Consumption DESC LIMIT 1
SELECT COUNT(T1.CustomerID) FROM customers AS T1 INNER JOIN yearmonth AS T2 ON T1.CustomerID = T2.CustomerID WHERE T1.Segment = 'KAM' AND T2.Date BETWEEN '201201' AND '201212' AND T2.Consumption < 30000
SELECT SUM(IIF(T1.Currency = 'CZK', T2.Consumption, 0)) - SUM(IIF(T1.Currency = 'EUR', T2.Consumption, 0)) FROM customers AS T1 INNER JOIN yearmonth AS T2 ON T1.CustomerID = T2.CustomerID WHERE SUBSTRING(T2.Date, 1, 4) = '2012'
SELECT T1.Date FROM yearmonth AS T1 INNER JOIN customers AS T2 ON T1.CustomerID = T2.CustomerID WHERE T2.Currency = 'EUR' GROUP BY T1.Date ORDER BY COUNT(T1.Date) DESC LIMIT 1
SELECT T1.Segment FROM customers AS T1 INNER JOIN yearmonth AS T2 ON T1.CustomerID = T2.CustomerID ORDER BY T2.Consumption LIMIT 1
SELECT SUBSTR(Date, 1, 4) FROM yearmonth ORDER BY Consumption DESC LIMIT 1
SELECT T2.date FROM customers AS T1 INNER JOIN yearmonth AS T2 ON T1.CustomerID = T2.CustomerID WHERE T1.Segment = 'SME' AND T2.date LIKE '2013%' ORDER BY T2.Consumption DESC LIMIT 1
SELECT SUM(CASE WHEN T2.Segment = 'SME' THEN T1.Consumption ELSE 0 END) - SUM(CASE WHEN T2.Segment = 'LAM' THEN T1.Consumption ELSE 0 END), SUM(CASE WHEN T2.Segment = 'LAM' THEN T1.Consumption ELSE 0 END) - SUM(CASE WHEN T2.Segment = 'KAM' THEN T1.Consumption ELSE 0 END), SUM(CASE WHEN T2.Segment = 'KAM' THEN T1.Consumption ELSE 0 END) - SUM(CASE WHEN T2.Segment = 'SME' THEN T1.Consumption ELSE 0 END) FROM yearmonth AS T1 INNER JOIN customers AS T2 ON T1.CustomerID = T2.CustomerID WHERE T1.Date LIKE '2013%'
SELECT CASE WHEN SUM(CASE WHEN T2.Date LIKE '2012%' THEN T2.Consumption ELSE 0 END) > SUM(CASE WHEN T2.Date LIKE '2013%' THEN T2.Consumption ELSE 0 END) THEN 'SME' ELSE 'LAM' END AS MAX FROM customers AS T1 INNER JOIN yearmonth AS T2 ON T1.CustomerID = T2.CustomerID WHERE T1.Segment = 'SME'
SELECT SUM(Consumption) FROM yearmonth WHERE CustomerID = 6 AND Date BETWEEN '201308' AND '201311'
SELECT SUM(IIF(Country = 'CZE', 1, 0)) - SUM(IIF(Country = 'SVK', 1, 0)) FROM gasstations WHERE Segment = 'Discount'
SELECT T2.Consumption - T1.Consumption FROM yearmonth AS T1 INNER JOIN yearmonth AS T2 ON T1.Date = '201304' AND T2.Date = '201304' WHERE T1.CustomerID = 5 AND T2.CustomerID = 7
SELECT SUM(CASE WHEN T1.Currency = 'CZK' THEN 1 ELSE 0 END) - SUM(CASE WHEN T1.Currency = 'EUR' THEN 1 ELSE 0 END) FROM customers AS T1 INNER JOIN yearmonth AS T2 ON T1.CustomerID = T2.CustomerID WHERE T1.Segment = 'SME'
SELECT T1.CustomerID FROM customers AS T1 INNER JOIN yearmonth AS T2 ON T1.CustomerID = T2.CustomerID WHERE T1.Segment = 'LAM' AND T1.Currency = 'EUR' AND T2.Date = 201310 ORDER BY T2.Consumption DESC LIMIT 1
SELECT T1.CustomerID, MAX(T2.Consumption) FROM customers AS T1 INNER JOIN yearmonth AS T2 ON T1.CustomerID = T2.CustomerID WHERE T1.Segment = 'KAM'
SELECT SUM(T2.Consumption) FROM customers AS T1 INNER JOIN yearmonth AS T2 ON T1.CustomerID = T2.CustomerID WHERE T1.Segment = 'KAM' AND T2.Date = '201305';
SELECT CAST(SUM(CASE WHEN T1.Segment = 'LAM' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM customers AS T1 INNER JOIN yearmonth AS T2 ON T1.CustomerID = T2.CustomerID WHERE T2.Consumption > 46.73
SELECT Country, COUNT(GasStationID) AS TotalValueForMoneyStations FROM gasstations WHERE Segment = 'Value for money' GROUP BY Country ORDER BY TotalValueForMoneyStations DESC;
SELECT CAST(SUM(CASE WHEN T1.Segment = 'KAM' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.Segment) FROM customers AS T1 INNER JOIN yearmonth AS T2 ON T1.CustomerID = T2.CustomerID WHERE T1.Currency = 'EUR'
SELECT CAST(SUM(CASE WHEN T2.Consumption > 528.3 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(T1.CustomerID) FROM customers AS T1 INNER JOIN yearmonth AS T2 ON T1.CustomerID = T2.CustomerID WHERE T2.Date = 201202
SELECT      CAST(SUM(CASE WHEN Segment = 'Premium' THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(*) AS PremiumPercentage FROM      gasstations WHERE      Country = 'SVK';
SELECT CustomerID FROM yearmonth WHERE Date = '201309' ORDER BY Consumption DESC LIMIT 1
SELECT customers.Segment FROM yearmonth INNER JOIN customers ON yearmonth.CustomerID = customers.CustomerID WHERE yearmonth.Date = '201309' GROUP BY customers.Segment ORDER BY SUM(yearmonth.Consumption) ASC LIMIT 1;
SELECT T2.CustomerID FROM customers AS T1 INNER JOIN yearmonth AS T2 ON T1.CustomerID = T2.CustomerID WHERE T2.Date = '201206' AND T1.Segment = 'SME' ORDER BY T2.Consumption LIMIT 1
SELECT MAX(Consumption) FROM yearmonth WHERE Date LIKE '2012%'
SELECT MAX(T1.Consumption) AS BiggestMonthlyConsumption FROM yearmonth AS T1 INNER JOIN customers AS T2 ON T1.CustomerID = T2.CustomerID WHERE T2.Currency = 'EUR';
SELECT T1.Description FROM products AS T1 INNER JOIN transactions_1k AS T2 ON T1.ProductID = T2.ProductID INNER JOIN yearmonth AS T3 ON T2.CustomerID = T3.CustomerID WHERE T3.Date = 201309
SELECT DISTINCT T2.Country FROM transactions_1k AS T1 INNER JOIN gasstations AS T2 ON T1.GasStationID = T2.GasStationID INNER JOIN yearmonth AS T3 ON T1.CustomerID = T3.CustomerID WHERE T3.Date LIKE '201306%'
SELECT DISTINCT T3.ChainID FROM transactions_1k AS T1 INNER JOIN customers AS T2 ON T1.CustomerID = T2.CustomerID INNER JOIN gasstations AS T3 ON T1.GasStationID = T3.GasStationID WHERE T2.Currency = 'EUR'
SELECT T3.Description FROM transactions_1k AS T1 INNER JOIN customers AS T2 ON T1.CustomerID = T2.CustomerID INNER JOIN products AS T3 ON T1.ProductID = T3.ProductID WHERE T2.Currency = 'EUR'
SELECT AVG(Amount * Price) FROM transactions_1k WHERE STRFTIME('%Y-%m', Date) = '2012-01'
SELECT COUNT(*)  FROM customers  INNER JOIN yearmonth  ON customers.CustomerID = yearmonth.CustomerID  WHERE customers.Currency = 'EUR'    AND yearmonth.Consumption > 1000;
SELECT DISTINCT products.Description FROM products INNER JOIN transactions_1k ON products.ProductID = transactions_1k.ProductID INNER JOIN gasstations ON transactions_1k.GasStationID = gasstations.GasStationID WHERE gasstations.Country = 'CZE';
SELECT DISTINCT T1.Time FROM transactions_1k AS T1 INNER JOIN gasstations AS T2 ON T1.GasStationID = T2.GasStationID WHERE T2.ChainID = 11
SELECT COUNT(*)  FROM transactions_1k  INNER JOIN gasstations  ON transactions_1k.GasStationID = gasstations.GasStationID  WHERE gasstations.Country = 'CZE'    AND transactions_1k.Price > 1000;
SELECT COUNT(T1.TransactionID) FROM transactions_1k AS T1 INNER JOIN gasstations AS T2 ON T1.GasStationID = T2.GasStationID WHERE T2.Country = 'CZE' AND strftime('%Y', T1.Date) >= '2012'
SELECT SUM(T2.Amount * T2.Price) / COUNT(T2.CardID) FROM gasstations AS T1 INNER JOIN transactions_1k AS T2 ON T1.GasStationID = T2.GasStationID WHERE T1.Country = 'CZE'
SELECT SUM(T2.Amount * T2.Price) / COUNT(T2.CustomerID) FROM customers AS T1 INNER JOIN transactions_1k AS T2 ON T1.CustomerID = T2.CustomerID WHERE T1.Currency = 'EUR'
SELECT CustomerID FROM transactions_1k WHERE Date = '2012-08-25' ORDER BY Amount DESC LIMIT 1
SELECT T2.Country FROM transactions_1k AS T1 INNER JOIN gasstations AS T2 ON T1.GasStationID = T2.GasStationID WHERE T1.Date = '2012-08-25' ORDER BY T1.Time ASC LIMIT 1
SELECT DISTINCT customers.Currency FROM transactions_1k INNER JOIN customers ON transactions_1k.CustomerID = customers.CustomerID WHERE transactions_1k.Date = '2012-08-24' AND transactions_1k.Time = '16:25:00';
SELECT DISTINCT T2.Segment FROM transactions_1k AS T1 INNER JOIN customers AS T2 ON T1.CustomerID = T2.CustomerID WHERE T1.Date = '2012-08-23' AND T1.Time = '21:20:00';
SELECT COUNT(TransactionID) FROM transactions_1k WHERE Date = '2012-08-26' AND Time < '13:00:00'
SELECT Segment FROM customers ORDER BY CustomerID ASC LIMIT 1
SELECT DISTINCT T2.Country FROM transactions_1k AS T1 INNER JOIN gasstations AS T2 ON T1.GasStationID = T2.GasStationID WHERE T1.Date = '2012-08-24' AND T1.Time = '12:42:00';
SELECT ProductID FROM transactions_1k WHERE Date = '2012-08-23' AND Time = '21:20:00'
SELECT SUM(T2.Consumption), T2.Date FROM transactions_1k AS T1 INNER JOIN yearmonth AS T2 ON T1.CustomerID = T2.CustomerID WHERE T1.Date = '2012-08-24' AND T1.Price = 124.05
SELECT COUNT(T1.GasStationID) FROM gasstations AS T1 INNER JOIN transactions_1k AS T2 ON T1.GasStationID = T2.GasStationID WHERE T2.Date = '2012-08-26' AND T1.Country = 'CZE' AND T2.Time >= '08:00:00' AND T2.Time < '09:00:00'
SELECT customers.Currency FROM yearmonth INNER JOIN customers ON yearmonth.CustomerID = customers.CustomerID WHERE yearmonth.Date = '201306' AND yearmonth.Consumption = 214582.17;
SELECT DISTINCT gasstations.Country FROM transactions_1k INNER JOIN gasstations ON transactions_1k.GasStationID = gasstations.GasStationID WHERE transactions_1k.CardID = 667467;
SELECT T2.Country FROM transactions_1k AS T1 INNER JOIN gasstations AS T2 ON T1.GasStationID = T2.GasStationID WHERE T1.Date = '2012-08-24' AND T1.Price = 548.4
SELECT CAST(SUM(IIF(T2.Currency = 'EUR', 1, 0)) AS FLOAT) * 100 / COUNT(T1.CustomerID) FROM transactions_1k AS T1 INNER JOIN customers AS T2 ON T1.CustomerID = T2.CustomerID WHERE T1.Date = '2012-08-25'
SELECT CAST(SUM(T1.Consumption) - SUM(T2.Consumption) AS REAL) / SUM(T1.Consumption) FROM yearmonth AS T1 INNER JOIN yearmonth AS T2 ON T1.CustomerID = T2.CustomerID WHERE T1.Date = 201208 AND T2.Date = 201308
SELECT GasStationID FROM transactions_1k GROUP BY GasStationID ORDER BY SUM(Amount * Price) DESC LIMIT 1;
SELECT CAST(COUNT(CASE WHEN Segment = 'Premium' THEN GasStationID ELSE NULL END) AS REAL) * 100 / COUNT(GasStationID) FROM gasstations WHERE Country = 'SVK'
SELECT SUM(T1.Price) , SUM(T2.Consumption) FROM transactions_1k AS T1 INNER JOIN yearmonth AS T2 ON T1.CustomerID = T2.CustomerID WHERE T1.CustomerID = 38508 AND T2.Date = '201201'
SELECT Description FROM products ORDER BY ProductID LIMIT 5
SELECT T1.CustomerID, T2.Price / T2.Amount, T1.Currency FROM customers AS T1 INNER JOIN transactions_1k AS T2 ON T1.CustomerID = T2.CustomerID ORDER BY T2.Amount DESC LIMIT 1
SELECT T2.Country FROM transactions_1k AS T1 INNER JOIN gasstations AS T2 ON T1.GasStationID = T2.GasStationID WHERE T1.ProductID = 2 ORDER BY T1.Price DESC LIMIT 1;
SELECT T1.Consumption FROM yearmonth AS T1 INNER JOIN transactions_1k AS T2 ON T1.CustomerID = T2.CustomerID WHERE T2.ProductID = 5 AND T2.Price / T2.Amount > 29.00 AND T1.Date LIKE '201208%'
